from typing import Optional

from pydantic import BaseModel


class PurchaseRequest(BaseModel):
    scenario: str = "recommendation"

    product_sku: str
    reason: str

    # Scenario 1: Purchase Recommendation Review
    recommended_quantity: Optional[int] = None

    # Scenario 2: Supplier Cannot Fulfil Purchase
    purchase_order_quantity: Optional[int] = None
    supplier_name: Optional[str] = None
    supplier_available_quantity: Optional[int] = None

    # Scenario 3: Demand / Forecast Changed
    previous_forecast: Optional[int] = None
    new_forecast: Optional[int] = None
    current_inventory: Optional[int] = None
    existing_purchase_order: Optional[int] = None

    # Scenario 4: Purchasing Constraint
    budget: Optional[float] = None
    storage_capacity: Optional[int] = None
