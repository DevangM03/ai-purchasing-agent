from typing import TypedDict


class PurchasingState(TypedDict, total=False):
    product_sku: str
    recommended_quantity: int
    reason: str

    inventory: dict
    suppliers: list
    purchase_orders: list

    analysis: dict
    decision: dict

    selected_supplier_id: int
    approved_quantity: int

    validation: dict
    recovery: dict
    action: dict

    final_result: dict