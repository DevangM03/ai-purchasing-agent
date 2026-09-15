from sqlalchemy.orm import Session

from app.services.inventory import get_inventory_context
from app.services.suppliers import get_supplier_options
from app.services.purchasing import get_open_purchase_orders
from app.services.validation import validate_purchase


def investigate_product(
    db: Session,
    product_sku: str
):
    inventory = get_inventory_context(
        db,
        product_sku
    )

    suppliers = get_supplier_options(
        db,
        product_sku
    )

    purchase_orders = get_open_purchase_orders(
        db,
        product_sku
    )

    return {
        "inventory": inventory,
        "suppliers": suppliers,
        "purchase_orders": purchase_orders,
    }


def validate_purchase_action(
    db: Session,
    product_sku: str,
    supplier_id: int,
    quantity: int,
    budget_override: float | None = None,
    storage_override: int | None = None,
):
    return validate_purchase(
        db=db,
        product_sku=product_sku,
        supplier_id=supplier_id,
        quantity=quantity,
        budget_override=budget_override,
        storage_override=storage_override,
    )