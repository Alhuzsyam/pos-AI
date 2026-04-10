from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, JSON, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)

    tenant = relationship("Tenant", back_populates="categories")
    products = relationship("Product", back_populates="category")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    name = Column(String(100), nullable=False, index=True)
    sku = Column(String(50), nullable=True, index=True)

    current_stock = Column(Integer, default=0)
    unit = Column(String(20), default="pcs")
    min_stock_level = Column(Integer, default=5)
    max_stock_level = Column(Integer, default=100)
    cost_price = Column(Float, default=0.0)
    division = Column(String(50), nullable=True)
    aliases = Column(JSON, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", back_populates="products")
    category = relationship("Category", back_populates="products")
    movements = relationship("StockMovement", back_populates="product")
    recipes = relationship("Recipe", back_populates="product")


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    qty_change = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # IN | OUT | ADJUSTMENT
    source = Column(String(30), default="MANUAL")           # MANUAL | POS | AI | IMPORT
    raw_input_text = Column(Text, nullable=True)
    created_by = Column(String(50), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="movements")
