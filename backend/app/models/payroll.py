from sqlalchemy import Column, Integer, String, Float, Boolean, Date, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from app.database import Base


class MonthlyCost(Base):
    """Biaya operasional bulanan custom: listrik, air, pajak, dll."""
    __tablename__ = "monthly_costs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    period_month = Column(Integer, nullable=False)
    period_year = Column(Integer, nullable=False)
    name = Column(String(100), nullable=False)   # "Listrik", "Air", "Pajak", dll
    amount = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    position = Column(String(100), nullable=True)       # Jabatan
    phone = Column(String(20), nullable=True)
    base_salary = Column(Float, default=0)              # Gaji pokok
    join_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PayrollRecord(Base):
    __tablename__ = "payroll_records"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    employee_name = Column(String(100), nullable=False)  # snapshot nama saat dibuat
    period_month = Column(Integer, nullable=False)        # 1-12
    period_year = Column(Integer, nullable=False)
    base_salary = Column(Float, default=0)
    bonus = Column(Float, default=0)
    deduction = Column(Float, default=0)                  # Potongan
    total = Column(Float, default=0)                      # base + bonus - deduction
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="draft")          # draft | paid
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
