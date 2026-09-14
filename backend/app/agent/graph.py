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


def analysis_node(
    state: PurchasingState
):
    inventory = state["inventory"]
    suppliers = state["suppliers"]

    required_demand = inventory["required_demand"]

    available_after_incoming = (
        inventory["inventory_plus_incoming"]
    )

    additional_required = max(
        0,
        required_demand - available_after_incoming
    )

    return {
        "analysis": {
            "required_demand": required_demand,
            "available_after_incoming": available_after_incoming,
            "additional_required": additional_required,
            "recommendation": state["recommended_quantity"],
            "supplier_count": len(suppliers),
        }
    }


def decision_node(
    state: PurchasingState
):
    user_context = {
        "recommendation": state["recommended_quantity"],
        "inventory": state["inventory"],
        "suppliers": state["suppliers"],
        "purchase_orders": state["purchase_orders"],
        "analysis": state["analysis"],
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
        "selected_supplier_id": result.get(
            "supplier_id"
        ),
        "approved_quantity": result.get(
            "quantity"
        ),
    }


def validation_node(
    state: PurchasingState,
    db: Session
):
    decision = state["decision"]

    if decision["decision"] in [
        "REJECT",
        "INVESTIGATE"
    ]:
        return {
            "validation": {
                "valid": True,
                "skipped": True,
                "reason": (
                    "No purchase action required"
                ),
            }
        }

    supplier_id = decision.get("supplier_id")
    quantity = decision.get("quantity")

    if not supplier_id or not quantity:
        return {
            "validation": {
                "valid": False,
                "reason": (
                    "Purchase decision is missing "
                    "supplier or quantity"
                ),
            }
        }

    validation = validate_purchase_action(
        db,
        state["product_sku"],
        supplier_id,
        quantity,
    )

    return {
        "validation": validation
    }


def recovery_node(
    state: PurchasingState,
    db: Session
):
    """
    Recover from a failed purchase validation.

    The LLM may propose a quantity that violates a
    purchasing constraint such as budget, supplier
    capacity, MOQ, or storage.

    Instead of simply blocking the purchase, this
    node searches for the largest feasible quantity
    that satisfies all constraints.
    """

    validation = state["validation"]
    decision = state["decision"]

    # Nothing to recover from.
    if validation.get("valid"):
        return {
            "recovery": {
                "attempted": False,
                "reason": "Initial validation passed"
            }
        }

    # REJECT and INVESTIGATE do not require recovery.
    if decision["decision"] in [
        "REJECT",
        "INVESTIGATE"
    ]:
        return {
            "recovery": {
                "attempted": False,
                "reason": (
                    "Decision does not require "
                    "purchase recovery"
                )
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
                "reason": "Product not found"
            }
        }

    if not budget:
        return {
            "recovery": {
                "attempted": True,
                "successful": False,
                "reason": "Budget information unavailable"
            }
        }

    suppliers = state["suppliers"]

    candidates = []

    for supplier in suppliers:

        supplier_id = supplier["supplier_id"]

        unit_price = supplier["unit_price"]

        minimum_order_quantity = (
            supplier["minimum_order_quantity"]
        )

        available_quantity = (
            supplier["available_quantity"]
        )

        # Maximum quantity allowed by budget.
        budget_quantity = int(
            budget.available_amount
            // unit_price
        )

        # Maximum quantity allowed by storage.
        storage_quantity = (
            product.storage_capacity
            - product.current_inventory
        )

        # Maximum quantity allowed by every constraint.
        maximum_quantity = min(
            available_quantity,
            budget_quantity,
            storage_quantity
        )

        # Supplier cannot satisfy even its MOQ.
        if maximum_quantity < minimum_order_quantity:
            continue

        # We want to buy as much as possible,
        # because the original requirement was to
        # cover additional demand.
        candidates.append(
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier["supplier_name"],
                "quantity": maximum_quantity,
                "unit_price": unit_price,
                "cost": (
                    maximum_quantity
                    * unit_price
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
                    "purchasing constraints"
                )
            }
        }

    required_quantity = state["analysis"][
        "additional_required"
    ]

    # Prefer the candidate that gets closest to
    # the required quantity without violating constraints.
    candidates.sort(
        key=lambda candidate: (
            abs(
                required_quantity
                - candidate["quantity"]
            ),
            candidate["cost"]
        )
    )

    best = candidates[0]

    remaining_shortfall = max(
        0,
        required_quantity
        - best["quantity"]
    )

    recovered_decision = {
        "decision": "MODIFY",
        "quantity": best["quantity"],
        "supplier_id": best["supplier_id"],
        "reasoning": (
            f"The original purchase decision failed "
            f"validation. The largest feasible purchase "
            f"is {best['quantity']} units from "
            f"{best['supplier_name']} at "
            f"{best['unit_price']} per unit. "
            f"This satisfies the purchasing constraints."
        ),
        "risk": (
            f"{remaining_shortfall} units of the "
            f"required additional inventory remain "
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
        "approved_quantity": best["quantity"],
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
                best["quantity"]
            ),
            "remaining_shortfall": (
                remaining_shortfall
            ),
        },
    }


def revalidation_node(
    state: PurchasingState,
    db: Session
):
    """
    Validate the recovered purchase decision again.

    This is important because the recovery action must
    itself be validated before execution.
    """

    decision = state["decision"]

    if decision["decision"] in [
        "REJECT",
        "INVESTIGATE"
    ]:
        return {
            "validation": {
                "valid": True,
                "skipped": True,
                "reason": (
                    "No purchase action required"
                ),
            }
        }

    supplier_id = decision.get("supplier_id")
    quantity = decision.get("quantity")

    if not supplier_id or not quantity:
        return {
            "validation": {
                "valid": False,
                "reason": (
                    "Recovered decision is missing "
                    "supplier or quantity"
                ),
            }
        }

    validation = validate_purchase_action(
        db,
        state["product_sku"],
        supplier_id,
        quantity,
    )

    return {
        "validation": validation
    }


def execute_node(
    state: PurchasingState,
    db: Session
):
    validation = state["validation"]
    decision = state["decision"]

    if decision["decision"] in [
        "REJECT",
        "INVESTIGATE"
    ]:
        return {
            "action": {
                "executed": False,
                "message": (
                    "No purchase order created"
                ),
            }
        }

    if not validation.get("valid"):
        return {
            "action": {
                "executed": False,
                "message": (
                    "Purchase blocked by "
                    "constraint validation"
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


def final_node(
    state: PurchasingState
):
    return {
        "final_result": {
            "decision": state["decision"],
            "analysis": state["analysis"],
            "validation": state["validation"],
            "action": state["action"],
            "recovery": state.get(
                "recovery"
            ),
        }
    }


def build_graph(db: Session):
    workflow = StateGraph(PurchasingState)

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

    workflow.set_entry_point("investigate")

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