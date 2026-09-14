from sqlalchemy.orm import Session

from app.models import Supplier


def get_supplier_options(
    db: Session,
    product_sku: str
):
    suppliers = (
        db.query(Supplier)
        .filter(
            Supplier.product_sku == product_sku
        )
        .all()
    )

    return [
        {
            "supplier_id": supplier.id,
            "supplier_name": supplier.name,
            "lead_time_days": supplier.lead_time_days,
            "minimum_order_quantity": supplier.minimum_order_quantity,
            "unit_price": supplier.unit_price,
            "available_quantity": supplier.available_quantity,
            "reliability_score": supplier.reliability_score,
        }
        for supplier in suppliers
    ]