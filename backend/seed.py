from app.database import Base, engine, SessionLocal

from app.models import (
    Product,
    Supplier,
    PurchaseOrder,
    Budget,
    AgentDecision,
)


# Create all database tables if they do not already exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()


try:
    # Clear existing data so every seed starts from a clean state
    db.query(AgentDecision).delete()
    db.query(PurchaseOrder).delete()
    db.query(Supplier).delete()
    db.query(Product).delete()
    db.query(Budget).delete()

    # ---------------------------------------------------------
    # PRODUCT
    # ---------------------------------------------------------

    product = Product(
        name="Premium Coffee Beans 1kg",
        sku="COFFEE-001",
        current_inventory=300,
        expected_daily_demand=100,
        forecast_days=10,
        storage_capacity=1200,
    )

    db.add(product)

    # ---------------------------------------------------------
    # SUPPLIERS
    # ---------------------------------------------------------

    supplier_1 = Supplier(
        name="Supplier A",
        product_sku="COFFEE-001",
        lead_time_days=3,
        minimum_order_quantity=100,
        unit_price=10.0,
        available_quantity=800,
        reliability_score=0.95,
    )

    supplier_2 = Supplier(
        name="Supplier B",
        product_sku="COFFEE-001",
        lead_time_days=5,
        minimum_order_quantity=200,
        unit_price=9.5,
        available_quantity=400,
        reliability_score=0.87,
    )

    db.add_all([
        supplier_1,
        supplier_2,
    ])

    # ---------------------------------------------------------
    # EXISTING PURCHASE ORDER
    # ---------------------------------------------------------

    existing_order = PurchaseOrder(
        product_sku="COFFEE-001",
        supplier_id=1,
        quantity=100,
        status="OPEN",
        unit_price=10.0,
    )

    db.add(existing_order)

    # ---------------------------------------------------------
    # BUDGET
    # ---------------------------------------------------------

    budget = Budget(
        available_amount=5000,
    )

    db.add(budget)

    # ---------------------------------------------------------
    # COMMIT
    # ---------------------------------------------------------

    db.commit()

    print("Database seeded successfully.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()