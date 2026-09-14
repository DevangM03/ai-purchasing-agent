from sqlalchemy.orm import Session

from app.models import Product, PurchaseOrder


def get_inventory_context(
    db: Session,
    product_sku: str
):
    product = (
        db.query(Product)
        .filter(Product.sku == product_sku)
        .first()
    )

    if not product:
        raise ValueError("Product not found")

    open_orders = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.product_sku == product_sku,
            PurchaseOrder.status == "OPEN"
        )
        .all()
    )

    incoming_quantity = sum(
        order.quantity
        for order in open_orders
    )

    demand_coverage = (
        product.current_inventory + incoming_quantity
    )

    required_demand = (
        product.expected_daily_demand
        * product.forecast_days
    )

    return {
        "sku": product.sku,
        "product_name": product.name,
        "current_inventory": product.current_inventory,
        "expected_daily_demand": product.expected_daily_demand,
        "forecast_days": product.forecast_days,
        "required_demand": required_demand,
        "incoming_quantity": incoming_quantity,
        "inventory_plus_incoming": demand_coverage,
        "storage_capacity": product.storage_capacity,
    }