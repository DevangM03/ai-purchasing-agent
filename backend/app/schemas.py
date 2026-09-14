from pydantic import BaseModel


class PurchaseRequest(BaseModel):
    product_sku: str
    recommended_quantity: int
    reason: str
