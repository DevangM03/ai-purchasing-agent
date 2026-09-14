from sqlalchemy.orm import Session

from app.models import PurchaseOrder, Supplier


def get_open_purchase_orders(
    db: Session,
    product_sku: str
):
    orders = (
        db.query(PurchaseOrder)
        .filter(
            PurchaseOrder.product_sku == product_sku,
            PurchaseOrder.status == "OPEN"
        )
        .all()
    )

    return [
        {
            "id": order.id,
            "supplier_id": order.supplier_id,
            "quantity": order.quantity,
            "unit_price": order.unit_price,
            "status": order.status,
        }
        for order in orders
    ]


def create_purchase_order(
    db: Session,
    product_sku: str,
    supplier_id: int,
    quantity: int
):
    supplier = (
        db.query(Supplier)
        .filter(Supplier.id == supplier_id)
        .first()
    )

    if not supplier:
        raise ValueError("Supplier not found")

    order = PurchaseOrder(
        product_sku=product_sku,
        supplier_id=supplier_id,
        quantity=quantity,
        status="OPEN",
        unit_price=supplier.unit_price,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return {
        "order_id": order.id,
        "product_sku": order.product_sku,
        "supplier_id": order.supplier_id,
        "quantity": order.quantity,
        "status": order.status,
        "unit_price": order.unit_price,
    }