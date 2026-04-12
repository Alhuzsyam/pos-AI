from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    category = Column(String(50), nullable=True)
    division = Column(String(20), default="Bar")  # Bar | Kitchen
    image_url = Column(String(255), nullable=True)
    is_available = Column(Boolean, default=True)

    tenant = relationship("Tenant", back_populates="menu_items")
    recipes = relationship("Recipe", back_populates="menu_item", cascade="all, delete-orphan")


class Recipe(Base):
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    amount_needed = Column(Float, nullable=False)

    menu_item = relationship("MenuItem", back_populates="recipes")
    product = relationship("Product", back_populates="recipes")


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    transaction_code = Column(String(30), unique=True, nullable=True)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    total_amount = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    final_amount = Column(Float, default=0.0)

    customer_name = Column(String(100), nullable=True)
    table_number = Column(String(20), nullable=True)
    payment_method = Column(String(20), default="CASH")
    status = Column(String(20), default="COMPLETED")   # PENDING | COMPLETED | CANCELLED
    notes = Column(Text, nullable=True)
    cashier_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    tenant = relationship("Tenant", back_populates="sales")
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)

    menu_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_moment = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    note = Column(String(255), nullable=True)
    status = Column(String(20), default="PENDING")   # PENDING | PREPARED | DELIVERED | SERVED

    sale = relationship("Sale", back_populates="items")
    menu_item = relationship("MenuItem")


class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    item_name = Column(String(255), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    price = Column(Float, default=0.0)
    category = Column(String(50), nullable=True)
    is_completed = Column(Boolean, default=False)
    purchase_date = Column(Date, nullable=True)
    note = Column(String(500), nullable=True)
    created_by = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="expenses")


class Debt(Base):
    __tablename__ = "debts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)  # linked sale for watchlist

    customer_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    total_amount = Column(Float, default=0.0)
    paid_amount = Column(Float, default=0.0)
    is_paid = Column(Boolean, default=False)
    due_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    payment_method = Column(String(20), nullable=True)  # method used when paying off

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    paid_at = Column(DateTime, nullable=True)

    sale = relationship("Sale", foreign_keys=[sale_id])
    items = relationship("DebtItem", back_populates="debt", cascade="all, delete-orphan")


class DebtItem(Base):
    __tablename__ = "debt_items"

    id = Column(Integer, primary_key=True, index=True)
    debt_id = Column(Integer, ForeignKey("debts.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)

    menu_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_moment = Column(Float, nullable=False)

    debt = relationship("Debt", back_populates="items")


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=True)  # linked sale when served

    customer_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    table_number = Column(String(20), nullable=True)
    pax = Column(Integer, default=1)
    reservation_date = Column(DateTime(timezone=True), nullable=True)
    total_amount = Column(Float, default=0.0)
    dp_amount = Column(Float, default=0.0)
    dp_method = Column(String(20), default="CASH")
    settlement_amount = Column(Float, default=0.0)       # pelunasan saat hari H
    settlement_method = Column(String(20), nullable=True)  # CASH | QRIS
    status = Column(String(20), default="PENDING")  # PENDING | CONFIRMED | SERVING | COMPLETED | CANCELLED
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sale = relationship("Sale", foreign_keys=[sale_id])
    tenant = relationship("Tenant", back_populates="reservations")
    items = relationship("ReservationItem", back_populates="reservation", cascade="all, delete-orphan")


class ReservationItem(Base):
    __tablename__ = "reservation_items"

    id = Column(Integer, primary_key=True, index=True)
    reservation_id = Column(Integer, ForeignKey("reservations.id", ondelete="CASCADE"), nullable=False)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True)

    menu_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_moment = Column(Float, nullable=False)
    note = Column(String(255), nullable=True)

    reservation = relationship("Reservation", back_populates="items")
