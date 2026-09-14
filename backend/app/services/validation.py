from sqlalchemy.orm import Session

from app.models import Budget, Product, Supplier


def validate_purchase(
    db: Session,
    product_sku: str,
    supplier_id: int,
    quantity: int
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

    if not budget:
        return {
            "valid": False,
            "reason": "Budget information unavailable"
        }

    checks = {}

    checks["minimum_order_quantity"] = (
        quantity >= supplier.minimum_order_quantity
    )

    checks["supplier_capacity"] = (
        quantity <= supplier.available_quantity
    )

    checks["storage_capacity"] = (
        product.current_inventory + quantity
        <= product.storage_capacity
    )

    total_cost = quantity * supplier.unit_price

    checks["budget"] = (
        total_cost <= budget.available_amount
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
        "available_budget": budget.available_amount,
        "failed_checks": failed_checks,
        "reason": (
            "All purchasing constraints satisfied"
            if valid
            else f"Failed constraints: {', '.join(failed_checks)}"
        )
    }