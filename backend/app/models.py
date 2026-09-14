from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    Text
)

from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    sku = Column(String, unique=True, nullable=False)
    current_inventory = Column(Integer, nullable=False)
    expected_daily_demand = Column(Integer, nullable=False)
    forecast_days = Column(Integer, nullable=False)
    storage_capacity = Column(Integer, nullable=False)


class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    product_sku = Column(String, nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    minimum_order_quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    available_quantity = Column(Integer, nullable=False)
    reliability_score = Column(Float, nullable=False)


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True)
    product_sku = Column(String, nullable=False)
    supplier_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    unit_price = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    available_amount = Column(Float, nullable=False)


class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id = Column(Integer, primary_key=True)
    product_sku = Column(String, nullable=False)
    recommendation_quantity = Column(Integer, nullable=False)
    decision = Column(String, nullable=False)
    reasoning = Column(Text, nullable=False)
    validation_passed = Column(Boolean, nullable=False)
    action_taken = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)