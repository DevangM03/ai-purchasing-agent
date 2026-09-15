from app.database import Base, SessionLocal, engine
from app.models import Product, Supplier, PurchaseOrder, Budget
from app.services.validation import validate_purchase


def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    product = Product(
        name="Test Coffee",
        sku="TEST-001",
        current_inventory=300,
        expected_daily_demand=100,
        forecast_days=10,
        storage_capacity=1200,
    )

    supplier = Supplier(
        name="Test Supplier",
        product_sku="TEST-001",
        lead_time_days=3,
        minimum_order_quantity=100,
        unit_price=10.0,
        available_quantity=800,
        reliability_score=0.95,
    )

    budget = Budget(available_amount=5000)

    db.add(product)
    db.add(supplier)
    db.add(budget)
    db.commit()

    return db, supplier.id


def test_purchase_within_constraints():
    """
    A valid purchase should pass all constraints.
    """

    db, supplier_id = setup_database()

    result = validate_purchase(
        db=db,
        product_sku="TEST-001",
        supplier_id=supplier_id,
        quantity=500,
    )

    assert result["valid"] is True
    assert result["checks"]["minimum_order_quantity"] is True
    assert result["checks"]["supplier_capacity"] is True
    assert result["checks"]["storage_capacity"] is True
    assert result["checks"]["budget"] is True

    db.close()


def test_moq_constraint():
    """
    Quantity below MOQ should be rejected.
    """

    db, supplier_id = setup_database()

    result = validate_purchase(
        db=db,
        product_sku="TEST-001",
        supplier_id=supplier_id,
        quantity=50,
    )

    assert result["valid"] is False
    assert "minimum_order_quantity" in result["failed_checks"]

    db.close()


def test_storage_constraint():
    """
    Purchase should not exceed storage capacity.
    """

    db, supplier_id = setup_database()

    result = validate_purchase(
        db=db,
        product_sku="TEST-001",
        supplier_id=supplier_id,
        quantity=1000,
    )

    assert result["valid"] is False
    assert "storage_capacity" in result["failed_checks"]

    db.close()


def test_budget_constraint():
    """
    Purchase should not exceed the available budget.
    """

    db, supplier_id = setup_database()

    result = validate_purchase(
        db=db,
        product_sku="TEST-001",
        supplier_id=supplier_id,
        quantity=600,
    )

    assert result["valid"] is False
    assert "budget" in result["failed_checks"]

    db.close()


def test_supplier_capacity_constraint():
    """
    Purchase should not exceed supplier availability.
    """

    db, supplier_id = setup_database()

    result = validate_purchase(
        db=db,
        product_sku="TEST-001",
        supplier_id=supplier_id,
        quantity=900,
    )

    assert result["valid"] is False
    assert "supplier_capacity" in result["failed_checks"]

    db.close()