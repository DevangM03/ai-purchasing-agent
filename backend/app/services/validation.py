from sqlalchemy.orm import Session

from app.models import Budget, Product, PurchaseOrder, Supplier


def validate_purchase(
    db: Session,
    product_sku: str,
    supplier_id: int,
    quantity: int,
    budget_override: float | None = None,
    storage_override: int | None = None,
):
    product = (
        db.query(Product)
        .filter(Product.sku == product_sku)
        .first()
    )

    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id)
        .first()
    )

    budget = db.query(Budget).first()

    if not product:
        return {
            "valid": False,
            "reason": "Product not found"
        }

    if not supplier:
        return {
            "valid": False,
            "reason": "Supplier not found"
        }

    if not budget and budget_override is None:
        return {
            "valid": False,
            "reason": "Budget information unavailable"
        }

    if quantity <= 0:
        return {
            "valid": False,
            "reason": "Purchase quantity must be greater than zero"
        }

    available_budget = (
        budget_override
        if budget_override is not None
        else budget.available_amount
    )

    storage_capacity = (
        storage_override
        if storage_override is not None
        else product.storage_capacity
    )

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

    checks = {}

    checks["minimum_order_quantity"] = (
        quantity >= supplier.minimum_order_quantity
    )

    checks["supplier_capacity"] = (
        quantity <= supplier.available_quantity
    )

    checks["storage_capacity"] = (
        product.current_inventory
        + incoming_quantity
        + quantity
        <= storage_capacity
    )

    total_cost = quantity * supplier.unit_price

    checks["budget"] = (
        total_cost <= available_budget
    )

    valid = all(checks.values())

    failed_checks = [
        name
        for name, passed in checks.items()
        if not passed
    ]

    return {
        "valid": valid,
        "checks": checks,
        "total_cost": total_cost,
        "available_budget": available_budget,
        "current_inventory": product.current_inventory,
        "incoming_quantity": incoming_quantity,
        "storage_capacity": storage_capacity,
        "projected_inventory": (
            product.current_inventory
            + incoming_quantity
            + quantity
        ),
        "failed_checks": failed_checks,
        "reason": (
            "All purchasing constraints satisfied"
            if valid
            else f"Failed constraints: {', '.join(failed_checks)}"
        )
    }