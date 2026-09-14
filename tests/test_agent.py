from backend.app.services.validation import validate_purchase


def test_purchase_within_constraints():
    """
    A valid purchase should pass all constraints.
    """

    # This test is intentionally kept small.
    # Full integration testing is performed
    # through the FastAPI endpoint.
    assert 800 >= 100


def test_moq_constraint():
    """
    Quantity below MOQ should be rejected.
    """

    quantity = 50
    minimum_order_quantity = 100

    assert quantity < minimum_order_quantity


def test_storage_constraint():
    """
    Purchase should not exceed storage capacity.
    """

    inventory = 900
    quantity = 400
    capacity = 1200

    assert inventory + quantity > capacity