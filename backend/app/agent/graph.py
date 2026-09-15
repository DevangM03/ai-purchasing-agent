import json

from groq import Groq
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.agent.state import PurchasingState
from app.agent.prompts import SYSTEM_PROMPT
from app.config import settings

from app.tools.purchasing_tools import (
    investigate_product,
    validate_purchase_action,
)

from app.services.purchasing import create_purchase_order
from app.models import Product, Budget


client = Groq(
    api_key=settings.GROQ_API_KEY
)


# =========================================================
# INVESTIGATION
# =========================================================

def investigate_node(
    state: PurchasingState,
    db: Session
):
    information = investigate_product(
        db,
        state["product_sku"]
    )

    return {
        "inventory": information["inventory"],
        "suppliers": information["suppliers"],
        "purchase_orders": information["purchase_orders"],
    }


# =========================================================
# ANALYSIS
# =========================================================

def analysis_node(
    state: PurchasingState
):
    scenario = state.get(
        "scenario",
        "recommendation"
    )

    inventory = state["inventory"]
    suppliers = state["suppliers"]

    # -----------------------------------------------------
    # SCENARIO 2: SUPPLIER CANNOT FULFIL
    # -----------------------------------------------------

    if scenario == "supplier":
        purchase_order_quantity = state.get(
            "purchase_order_quantity",
            0
        )

        supplier_available_quantity = state.get(
            "supplier_available_quantity",
            0
        )

        uncovered_quantity = max(
            0,
            purchase_order_quantity
            - supplier_available_quantity
        )

        return {
            "analysis": {
                "scenario": scenario,
                "purchase_order_quantity": (
                    purchase_order_quantity
                ),
                "supplier_available_quantity": (
                    supplier_available_quantity
                ),
                "uncovered_quantity": (
                    uncovered_quantity
                ),

                # For Scenario 2, the required additional
                # quantity is the supplier shortfall.
                "additional_required": (
                    uncovered_quantity
                ),

                "supplier_count": len(suppliers),

                # Return supplier information so the
                # frontend can display names instead of IDs.
                "supplier_options": suppliers,
            }
        }

    # -----------------------------------------------------
    # SCENARIO 3: DEMAND / FORECAST CHANGE
    # -----------------------------------------------------

    if scenario == "demand":
        previous_forecast = state.get(
            "previous_forecast",
            inventory["required_demand"]
        )

        new_forecast = state.get(
            "new_forecast",
            previous_forecast
        )

        current_inventory = state.get(
            "current_inventory",
            inventory["current_inventory"]
        )

        existing_purchase_order = state.get(
            "existing_purchase_order",
            inventory["incoming_quantity"]
        )

        available_supply = (
            current_inventory
            + existing_purchase_order
        )

        additional_required = max(
            0,
            new_forecast - available_supply
        )

        forecast_increase = max(
            0,
            new_forecast - previous_forecast
        )

        return {
            "analysis": {
                "scenario": scenario,
                "previous_forecast": previous_forecast,
                "new_forecast": new_forecast,
                "forecast_increase": forecast_increase,
                "current_inventory": current_inventory,
                "existing_purchase_order": (
                    existing_purchase_order
                ),
                "available_supply": available_supply,
                "additional_required": (
                    additional_required
                ),
                "supplier_count": len(suppliers),
                "supplier_options": suppliers,
            }
        }

    # -----------------------------------------------------
    # SCENARIO 4: PURCHASING CONSTRAINT
    # -----------------------------------------------------

    if scenario == "constraint":
        recommended_quantity = state.get(
            "recommended_quantity",
            0
        )

        available_budget = state.get("budget")

        if available_budget is None:
            budget = state.get("inventory", {})
            available_budget = budget.get(
                "available_budget"
            )

        if available_budget is None:
            available_budget = 0

        storage_capacity = state.get(
            "storage_capacity"
        )

        if storage_capacity is None:
            storage_capacity = inventory.get(
                "storage_capacity"
            )

        if storage_capacity is None:
            storage_capacity = 0

        incoming_quantity = inventory.get(
            "incoming_quantity",
            0
        )

        storage_available = max(
            0,
            storage_capacity
            - inventory["current_inventory"]
            - incoming_quantity
        )

        supplier_costs = []

        for supplier in suppliers:
            supplier_costs.append(
                {
                    "supplier_id": supplier[
                        "supplier_id"
                    ],
                    "supplier_name": supplier[
                        "supplier_name"
                    ],
                    "unit_price": supplier[
                        "unit_price"
                    ],
                    "recommended_cost": (
                        recommended_quantity
                        * supplier["unit_price"]
                    ),
                }
            )

        return {
            "analysis": {
                "scenario": scenario,
                "recommended_quantity": (
                    recommended_quantity
                ),
                "budget": available_budget,
                "available_budget": available_budget,
                "storage_capacity": (
                    storage_capacity
                ),
                "incoming_quantity": (
                    incoming_quantity
                ),
                "storage_available": (
                    storage_available
                ),
                "supplier_count": len(suppliers),
                "supplier_costs": supplier_costs,
                "supplier_options": suppliers,
            }
        }

    # -----------------------------------------------------
    # SCENARIO 1: RECOMMENDATION REVIEW
    # -----------------------------------------------------

    required_demand = inventory[
        "required_demand"
    ]

    available_after_incoming = inventory[
        "inventory_plus_incoming"
    ]

    additional_required = max(
        0,
        required_demand
        - available_after_incoming
    )

    return {
        "analysis": {
            "scenario": "recommendation",
            "required_demand": required_demand,
            "available_after_incoming": (
                available_after_incoming
            ),
            "additional_required": (
                additional_required
            ),
            "recommendation": (
                state["recommended_quantity"]
            ),
            "supplier_count": len(suppliers),
            "supplier_options": suppliers,
        }
    }


# =========================================================
# DECISION ROUTER
# =========================================================

def decision_node(
    state: PurchasingState
):
    scenario = state.get(
        "scenario",
        "recommendation"
    )

    if scenario == "supplier":
        return supplier_failure_decision(state)

    if scenario == "demand":
        return demand_change_decision(state)

    if scenario == "constraint":
        return constraint_decision(state)

    return recommendation_decision(state)


# =========================================================
# SCENARIO 1 DECISION
# GROQ USED HERE
# =========================================================

def recommendation_decision(
    state: PurchasingState
):
    user_context = {
        "recommendation": (
            state["recommended_quantity"]
        ),
        "inventory": state["inventory"],
        "suppliers": state["suppliers"],
        "purchase_orders": state["purchase_orders"],
        "analysis": state["analysis"],
        "reason": state.get("reason"),
    }

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": json.dumps(
                    user_context,
                    indent=2
                ),
            },
        ],
        temperature=0.1,
        response_format={
            "type": "json_object"
        },
    )

    result = json.loads(
        response.choices[0].message.content
    )

    return {
        "decision": result,
        "selected_supplier_id": (
            result.get("supplier_id")
        ),
        "approved_quantity": (
            result.get("quantity")
        ),
    }


# =========================================================
# SCENARIO 2 DECISION
# SUPPLIER CANNOT FULFIL
# =========================================================

def supplier_failure_decision(
    state: PurchasingState
):
    analysis = state["analysis"]
    suppliers = state["suppliers"]

    purchase_order_quantity = analysis[
        "purchase_order_quantity"
    ]

    supplier_available_quantity = analysis[
        "supplier_available_quantity"
    ]

    uncovered_quantity = analysis[
        "uncovered_quantity"
    ]

    # Supplier can fulfill the entire PO.
    if uncovered_quantity <= 0:
        return {
            "decision": {
                "decision": "ACCEPT",
                "quantity": 0,
                "supplier_id": None,
                "reasoning": (
                    "The supplier can fulfill the "
                    "entire purchase order, so no "
                    "additional purchase action is "
                    "required."
                ),
                "risk": "No supplier shortfall.",
            },
            "approved_quantity": 0,
        }

    original_supplier_name = state.get(
        "supplier_name"
    )

    alternate_suppliers = []

    for supplier in suppliers:
        supplier_name = supplier[
            "supplier_name"
        ]

        # Don't choose the supplier that already
        # reported the fulfillment problem.
        if (
            original_supplier_name
            and supplier_name.lower()
            == original_supplier_name.lower()
        ):
            continue

        if (
            supplier["available_quantity"]
            >= supplier["minimum_order_quantity"]
        ):
            alternate_suppliers.append(
                supplier
            )

    # No alternate supplier is feasible.
    if not alternate_suppliers:
        return {
            "decision": {
                "decision": "INVESTIGATE",
                "quantity": 0,
                "supplier_id": None,
                "reasoning": (
                    f"The original supplier can only "
                    f"provide {supplier_available_quantity} "
                    f"of {purchase_order_quantity} units. "
                    f"No feasible alternate supplier was "
                    f"found for the remaining "
                    f"{uncovered_quantity} units."
                ),
                "risk": (
                    f"{uncovered_quantity} units remain "
                    f"uncovered and require escalation."
                ),
            },
            "approved_quantity": 0,
        }

    # Prefer lower price, then higher availability.
    alternate_suppliers.sort(
        key=lambda supplier: (
            supplier["unit_price"],
            -supplier["available_quantity"],
        )
    )

    best_supplier = alternate_suppliers[0]

    alternate_quantity = min(
        uncovered_quantity,
        best_supplier["available_quantity"],
    )

    if (
        alternate_quantity
        < best_supplier["minimum_order_quantity"]
    ):
        return {
            "decision": {
                "decision": "INVESTIGATE",
                "quantity": 0,
                "supplier_id": None,
                "reasoning": (
                    "An alternate supplier exists, "
                    "but the remaining quantity is below "
                    "the supplier's minimum order quantity."
                ),
                "risk": (
                    f"{uncovered_quantity} units remain "
                    f"uncovered."
                ),
            },
            "approved_quantity": 0,
        }

    remaining_shortfall = max(
        0,
        uncovered_quantity
        - alternate_quantity
    )

    return {
        "decision": {
            "decision": "MODIFY",
            "quantity": alternate_quantity,
            "supplier_id": (
                best_supplier["supplier_id"]
            ),
            "reasoning": (
                f"The original supplier can only "
                f"provide {supplier_available_quantity} "
                f"of {purchase_order_quantity} units. "
                f"The remaining {uncovered_quantity} "
                f"units can be sourced from "
                f"{best_supplier['supplier_name']}."
            ),
            "risk": (
                f"{remaining_shortfall} units remain "
                f"uncovered."
                if remaining_shortfall > 0
                else "The full shortfall can be covered."
            ),
        },
        "selected_supplier_id": (
            best_supplier["supplier_id"]
        ),
        "approved_quantity": alternate_quantity,
    }


# =========================================================
# SCENARIO 3 DECISION
# DEMAND / FORECAST CHANGE
# =========================================================

def demand_change_decision(
    state: PurchasingState
):
    analysis = state["analysis"]
    suppliers = state["suppliers"]

    additional_required = analysis[
        "additional_required"
    ]

    # Updated forecast is already covered.
    if additional_required <= 0:
        return {
            "decision": {
                "decision": "ACCEPT",
                "quantity": 0,
                "supplier_id": None,
                "reasoning": (
                    "The updated forecast is fully "
                    "covered by current inventory and "
                    "existing incoming purchase orders."
                ),
                "risk": (
                    "No additional purchase required."
                ),
            },
            "approved_quantity": 0,
        }

    feasible_suppliers = []

    for supplier in suppliers:
        if (
            supplier["available_quantity"]
            >= supplier["minimum_order_quantity"]
        ):
            quantity = min(
                additional_required,
                supplier["available_quantity"],
            )

            if quantity >= supplier[
                "minimum_order_quantity"
            ]:
                feasible_suppliers.append(
                    {
                        **supplier,
                        "purchase_quantity": quantity,
                        "purchase_cost": (
                            quantity
                            * supplier["unit_price"]
                        ),
                    }
                )

    if not feasible_suppliers:
        return {
            "decision": {
                "decision": "INVESTIGATE",
                "quantity": 0,
                "supplier_id": None,
                "reasoning": (
                    f"The new forecast requires "
                    f"{additional_required} additional "
                    f"units, but no supplier can provide "
                    f"a feasible purchase quantity."
                ),
                "risk": (
                    f"{additional_required} units remain "
                    f"uncovered."
                ),
            },
            "approved_quantity": 0,
        }

    # Prefer suppliers that can cover the complete
    # requirement. Among those, choose lowest cost.
    feasible_suppliers.sort(
        key=lambda supplier: (
            supplier["purchase_quantity"]
            < additional_required,
            supplier["purchase_cost"],
        )
    )

    best_supplier = feasible_suppliers[0]

    remaining_shortfall = max(
        0,
        additional_required
        - best_supplier["purchase_quantity"],
    )

    return {
        "decision": {
            "decision": "MODIFY",
            "quantity": (
                best_supplier["purchase_quantity"]
            ),
            "supplier_id": (
                best_supplier["supplier_id"]
            ),
            "reasoning": (
                f"The forecast increased to "
                f"{analysis['new_forecast']} units. "
                f"After accounting for current inventory "
                f"and existing incoming stock, "
                f"{additional_required} additional units "
                f"are required. The recommended action is "
                f"to purchase "
                f"{best_supplier['purchase_quantity']} "
                f"units from "
                f"{best_supplier['supplier_name']}."
            ),
            "risk": (
                f"{remaining_shortfall} units remain "
                f"uncovered."
                if remaining_shortfall > 0
                else "The updated demand is fully covered."
            ),
        },
        "selected_supplier_id": (
            best_supplier["supplier_id"]
        ),
        "approved_quantity": (
            best_supplier["purchase_quantity"]
        ),
    }


# =========================================================
# SCENARIO 4 DECISION
# PURCHASING CONSTRAINT
# =========================================================

def constraint_decision(
    state: PurchasingState
):
    analysis = state["analysis"]
    suppliers = state["suppliers"]

    recommended_quantity = analysis[
        "recommended_quantity"
    ]

    available_budget = analysis[
        "available_budget"
    ]

    storage_available = analysis[
        "storage_available"
    ]

    candidates = []

    for supplier in suppliers:
        budget_quantity = int(
            available_budget
            // supplier["unit_price"]
        )

        maximum_quantity = min(
            supplier["available_quantity"],
            budget_quantity,
            storage_available,
        )

        if (
            maximum_quantity
            < supplier["minimum_order_quantity"]
        ):
            continue

        quantity = min(
            recommended_quantity,
            maximum_quantity,
        )

        candidates.append(
            {
                **supplier,
                "purchase_quantity": quantity,
                "purchase_cost": (
                    quantity
                    * supplier["unit_price"]
                ),
            }
        )

    # No feasible purchase.
    if not candidates:
        return {
            "decision": {
                "decision": "INVESTIGATE",
                "quantity": 0,
                "supplier_id": None,
                "reasoning": (
                    "The recommended purchase cannot be "
                    "executed because no supplier can "
                    "satisfy the budget, storage, capacity, "
                    "and MOQ constraints."
                ),
                "risk": (
                    "Additional inventory remains "
                    "uncovered."
                ),
            },
            "approved_quantity": 0,
        }

    # Prefer the candidate closest to the recommendation,
    # then lower cost.
    candidates.sort(
        key=lambda candidate: (
            abs(
                recommended_quantity
                - candidate["purchase_quantity"]
            ),
            candidate["purchase_cost"],
        )
    )

    best_supplier = candidates[0]

    remaining_shortfall = max(
        0,
        recommended_quantity
        - best_supplier["purchase_quantity"],
    )

    decision_type = (
        "ACCEPT"
        if best_supplier["purchase_quantity"]
        == recommended_quantity
        else "MODIFY"
    )

    return {
        "decision": {
            "decision": decision_type,
            "quantity": (
                best_supplier["purchase_quantity"]
            ),
            "supplier_id": (
                best_supplier["supplier_id"]
            ),
            "reasoning": (
                f"The recommended purchase was "
                f"{recommended_quantity} units, but "
                f"the purchasing constraints limit the "
                f"feasible purchase to "
                f"{best_supplier['purchase_quantity']} "
                f"units from "
                f"{best_supplier['supplier_name']}."
            ),
            "risk": (
                f"{remaining_shortfall} units remain "
                f"uncovered."
                if remaining_shortfall > 0
                else "No remaining shortfall."
            ),
        },
        "selected_supplier_id": (
            best_supplier["supplier_id"]
        ),
        "approved_quantity": (
            best_supplier["purchase_quantity"]
        ),
    }


# =========================================================
# VALIDATION
# =========================================================

def validation_node(
    state: PurchasingState,
    db: Session
):
    decision = state["decision"]

    if decision["decision"] in [
        "REJECT",
        "INVESTIGATE",
    ]:
        return {
            "validation": {
                "valid": True,
                "skipped": True,
                "reason": (
                    "No purchase action required."
                ),
            }
        }

    supplier_id = decision.get(
        "supplier_id"
    )

    quantity = decision.get(
        "quantity"
    )

    if (
        decision["decision"] == "ACCEPT"
        and not supplier_id
    ):
        return {
            "validation": {
                "valid": True,
                "skipped": True,
                "reason": (
                    "No new purchase order is required."
                ),
            }
        }

    if not supplier_id or not quantity:
        return {
            "validation": {
                "valid": False,
                "reason": (
                    "Purchase decision is missing "
                    "supplier or quantity."
                ),
            }
        }

    budget_override = None
    storage_override = None

    if state.get("scenario") == "constraint":
        budget_override = state.get(
            "budget"
        )

        storage_override = state.get(
            "storage_capacity"
        )

    validation = validate_purchase_action(
        db,
        state["product_sku"],
        supplier_id,
        quantity,
        budget_override=budget_override,
        storage_override=storage_override,
    )

    return {
        "validation": validation
    }


# =========================================================
# RECOVERY
# =========================================================

def recovery_node(
    state: PurchasingState,
    db: Session
):
    validation = state["validation"]
    decision = state["decision"]

    # Initial validation passed.
    if validation.get("valid"):
        return {
            "recovery": {
                "attempted": False,
                "reason": (
                    "Initial validation passed."
                ),
            }
        }

    # Don't attempt recovery for decisions that
    # intentionally require no purchase.
    if decision["decision"] in [
        "REJECT",
        "INVESTIGATE",
    ]:
        return {
            "recovery": {
                "attempted": False,
                "reason": (
                    "Decision does not require "
                    "purchase recovery."
                ),
            }
        }

    product = (
        db.query(Product)
        .filter(
            Product.sku == state["product_sku"]
        )
        .first()
    )

    budget = db.query(Budget).first()

    if not product:
        return {
            "recovery": {
                "attempted": True,
                "successful": False,
                "reason": "Product not found.",
            }
        }

    # Use scenario-specific budget when supplied.
    available_budget = state.get(
        "budget"
    )

    if available_budget is None:
        if not budget:
            return {
                "recovery": {
                    "attempted": True,
                    "successful": False,
                    "reason": (
                        "Budget information unavailable."
                    ),
                }
            }

        available_budget = budget.available_amount

    # Use scenario-specific storage when supplied.
    storage_capacity = state.get(
        "storage_capacity"
    )

    if storage_capacity is None:
        storage_capacity = product.storage_capacity

    incoming_quantity = state[
        "inventory"
    ].get(
        "incoming_quantity",
        0
    )

    storage_quantity = max(
        0,
        storage_capacity
        - product.current_inventory
        - incoming_quantity
    )

    suppliers = state["suppliers"]

    candidates = []

    # Scenario 2 must recover against the supplier
    # shortfall, not the inventory/demand gap.
    if state.get("scenario") == "supplier":
        original_supplier_name = state.get(
            "supplier_name"
        )
    else:
        original_supplier_name = None

    for supplier in suppliers:
        supplier_id = supplier[
            "supplier_id"
        ]

        supplier_name = supplier[
            "supplier_name"
        ]

        # Do not select the supplier that already
        # reported the fulfillment problem.
        if (
            original_supplier_name
            and supplier_name.lower()
            == original_supplier_name.lower()
        ):
            continue

        unit_price = supplier[
            "unit_price"
        ]

        minimum_order_quantity = supplier[
            "minimum_order_quantity"
        ]

        available_quantity = supplier[
            "available_quantity"
        ]

        budget_quantity = int(
            available_budget
            // unit_price
        )

        maximum_quantity = min(
            available_quantity,
            budget_quantity,
            storage_quantity,
        )

        if (
            maximum_quantity
            < minimum_order_quantity
        ):
            continue

        candidates.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "quantity": maximum_quantity,
                "unit_price": unit_price,
                "cost": (
                    maximum_quantity
                    * unit_price
                ),
                "minimum_order_quantity": (
                    minimum_order_quantity
                ),
            }
        )

    if not candidates:
        return {
            "recovery": {
                "attempted": True,
                "successful": False,
                "reason": (
                    "No supplier can satisfy the "
                    "purchasing constraints."
                ),
            }
        }

    # Determine what the recovery is trying to cover.
    if state.get("scenario") == "constraint":
        required_quantity = state[
            "analysis"
        ].get(
            "recommended_quantity",
            decision.get("quantity", 0)
        )

    elif state.get("scenario") == "supplier":
        required_quantity = state[
            "analysis"
        ].get(
            "uncovered_quantity",
            decision.get("quantity", 0)
        )

    else:
        required_quantity = state[
            "analysis"
        ].get(
            "additional_required",
            decision.get("quantity", 0)
        )

    # Pick the feasible quantity closest to the
    # actual requirement, then prefer lower cost.
    candidates.sort(
        key=lambda candidate: (
            abs(
                required_quantity
                - candidate["quantity"]
            ),
            candidate["cost"],
        )
    )

    best = candidates[0]

    recovered_quantity = min(
        required_quantity,
        best["quantity"],
    )

    remaining_shortfall = max(
        0,
        required_quantity
        - recovered_quantity,
    )

    recovered_decision = {
        "decision": "MODIFY",
        "quantity": recovered_quantity,
        "supplier_id": best["supplier_id"],
        "reasoning": (
            f"The original purchase decision failed "
            f"validation. The largest feasible purchase "
            f"is {recovered_quantity} units from "
            f"{best['supplier_name']} at "
            f"{best['unit_price']} per unit."
        ),
        "risk": (
            f"{remaining_shortfall} units remain "
            f"uncovered."
            if remaining_shortfall > 0
            else "No remaining inventory shortfall."
        ),
    }

    return {
        "decision": recovered_decision,
        "selected_supplier_id": (
            best["supplier_id"]
        ),
        "approved_quantity": (
            recovered_quantity
        ),
        "recovery": {
            "attempted": True,
            "successful": True,
            "original_decision": decision,
            "original_validation": validation,
            "recovered_supplier_id": (
                best["supplier_id"]
            ),
            "recovered_supplier_name": (
                best["supplier_name"]
            ),
            "recovered_quantity": (
                recovered_quantity
            ),
            "remaining_shortfall": (
                remaining_shortfall
            ),
        },
    }


# =========================================================
# REVALIDATION
# =========================================================

def revalidation_node(
    state: PurchasingState,
    db: Session
):
    decision = state["decision"]

    if decision["decision"] in [
        "REJECT",
        "INVESTIGATE",
    ]:
        return {
            "validation": {
                "valid": True,
                "skipped": True,
                "reason": (
                    "No purchase action required."
                ),
            }
        }

    supplier_id = decision.get(
        "supplier_id"
    )

    quantity = decision.get(
        "quantity"
    )

    if (
        decision["decision"] == "ACCEPT"
        and not supplier_id
    ):
        return {
            "validation": {
                "valid": True,
                "skipped": True,
                "reason": (
                    "No new purchase order is required."
                ),
            }
        }

    if not supplier_id or not quantity:
        return {
            "validation": {
                "valid": False,
                "reason": (
                    "Recovered decision is missing "
                    "supplier or quantity."
                ),
            }
        }

    budget_override = None
    storage_override = None

    if state.get("scenario") == "constraint":
        budget_override = state.get(
            "budget"
        )

        storage_override = state.get(
            "storage_capacity"
        )

    validation = validate_purchase_action(
        db,
        state["product_sku"],
        supplier_id,
        quantity,
        budget_override=budget_override,
        storage_override=storage_override,
    )

    return {
        "validation": validation
    }


# =========================================================
# EXECUTION
# =========================================================

def execute_node(
    state: PurchasingState,
    db: Session
):
    validation = state["validation"]
    decision = state["decision"]

    if decision["decision"] in [
        "REJECT",
        "INVESTIGATE",
    ]:
        return {
            "action": {
                "executed": False,
                "message": (
                    "No purchase order created."
                ),
            }
        }

    if (
        decision["decision"] == "ACCEPT"
        and not decision.get("supplier_id")
    ):
        return {
            "action": {
                "executed": False,
                "message": (
                    "Existing purchasing plan is "
                    "sufficient; no new purchase order "
                    "was required."
                ),
            }
        }

    # Never execute an invalid purchase.
    if not validation.get("valid"):
        return {
            "action": {
                "executed": False,
                "message": (
                    "Purchase blocked by "
                    "constraint validation."
                ),
            }
        }

    order = create_purchase_order(
        db,
        state["product_sku"],
        decision["supplier_id"],
        decision["quantity"],
    )

    return {
        "action": {
            "executed": True,
            "purchase_order": order,
        }
    }


# =========================================================
# FINAL RESULT
# =========================================================

def final_node(
    state: PurchasingState
):
    return {
        "final_result": {
            "scenario": state.get(
                "scenario",
                "recommendation"
            ),
            "decision": state["decision"],
            "analysis": state["analysis"],
            "validation": state["validation"],
            "action": state["action"],
            "recovery": state.get(
                "recovery"
            ),
        }
    }


# =========================================================
# LANGGRAPH WORKFLOW
# =========================================================

def build_graph(
    db: Session
):
    workflow = StateGraph(
        PurchasingState
    )

    workflow.add_node(
        "investigate",
        lambda state: investigate_node(
            state,
            db
        )
    )

    workflow.add_node(
        "analyze",
        analysis_node
    )

    workflow.add_node(
        "decide",
        decision_node
    )

    workflow.add_node(
        "validate",
        lambda state: validation_node(
            state,
            db
        )
    )

    workflow.add_node(
        "recover",
        lambda state: recovery_node(
            state,
            db
        )
    )

    workflow.add_node(
        "revalidate",
        lambda state: revalidation_node(
            state,
            db
        )
    )

    workflow.add_node(
        "execute",
        lambda state: execute_node(
            state,
            db
        )
    )

    workflow.add_node(
        "finalize",
        final_node
    )

    workflow.set_entry_point(
        "investigate"
    )

    workflow.add_edge(
        "investigate",
        "analyze"
    )

    workflow.add_edge(
        "analyze",
        "decide"
    )

    workflow.add_edge(
        "decide",
        "validate"
    )

    workflow.add_edge(
        "validate",
        "recover"
    )

    workflow.add_edge(
        "recover",
        "revalidate"
    )

    workflow.add_edge(
        "revalidate",
        "execute"
    )

    workflow.add_edge(
        "execute",
        "finalize"
    )

    workflow.add_edge(
        "finalize",
        END
    )

    return workflow.compile()