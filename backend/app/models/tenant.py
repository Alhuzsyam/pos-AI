from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Tenant(Base):
    """Satu tenant = satu toko/cafe."""
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    plan = Column(String(20), default="basic")   # basic | pro | enterprise
    is_active = Column(Boolean, default=True)

    # Metadata toko
    address = Column(Text, nullable=True)
    phone = Column(String(20), nullable=True)
    logo_url = Column(String(255), nullable=True)
    timezone = Column(String(50), default="Asia/Jakarta")
    currency = Column(String(10), default="IDR")

    # Konfigurasi fitur per-tenant
    features = Column(JSON, default=dict)   # {"whatsapp": true, "ai": true, ...}

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    categories = relationship("Category", back_populates="tenant", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="tenant", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="tenant", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="tenant", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="tenant", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="tenant", cascade="all, delete-orphan")
