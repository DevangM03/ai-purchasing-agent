from typing import TypedDict


class PurchasingState(TypedDict, total=False):
    # Common scenario information
    scenario: str
    product_sku: str
    reason: str

    # Scenario 1: Purchase Recommendation Review
    recommended_quantity: int

    # Scenario 2: Supplier Cannot Fulfil Purchase
    purchase_order_quantity: int
    supplier_name: str
    supplier_available_quantity: int

    # Scenario 3: Demand / Forecast Changed
    previous_forecast: int
    new_forecast: int
    current_inventory: int
    existing_purchase_order: int

    # Scenario 4: Purchasing Constraint
    budget: float
    storage_capacity: int

    # Investigated purchasing data
    inventory: dict
    suppliers: list
    purchase_orders: list

    # Agent reasoning and decision
    analysis: dict
    decision: dict

    # Selected purchasing action
    selected_supplier_id: int
    approved_quantity: int

    # Validation and recovery
    validation: dict
    recovery: dict

    # Executed action
    action: dict

    # Final response
    final_result: dict