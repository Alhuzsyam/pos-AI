from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"   # God mode - manage all tenants
    ADMIN = "admin"             # Full access dalam 1 tenant
    MANAGER = "manager"         # Reports + staff management
    KASIR = "kasir"             # POS only
    INVENTORY = "inventory"     # Inventory management only
    DAPUR = "dapur"             # Kitchen display - watchlist dapur/bar
    WAITER = "waiter"           # Waiter display - watchlist delivery


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    # nullable=True untuk superadmin yang tidak punya tenant

    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), nullable=True)
    full_name = Column(String(100), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default=UserRole.KASIR, nullable=False)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    tenant = relationship("Tenant", back_populates="users")
