"""
Fitur Gaji Karyawan — hanya bisa diakses admin & superadmin.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

from app.database import get_db
from app.models.user import User
from app.models.payroll import Employee, PayrollRecord, MonthlyCost
from app.models.pos import Sale, Expense
from app.core.deps import get_current_user, require_admin, resolve_tenant_id

router = APIRouter(prefix="/api/v1/payroll", tags=["Payroll"])


# ====================================================
# Schemas
# ====================================================

class EmployeeCreate(BaseModel):
    name: str
    position: Optional[str] = None
    phone: Optional[str] = None
    base_salary: float = 0
    join_date: Optional[date] = None

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    base_salary: Optional[float] = None
    join_date: Optional[date] = None
    is_active: Optional[bool] = None

class PayrollCreate(BaseModel):
    employee_id: int
    period_month: int   # 1-12
    period_year: int
    base_salary: Optional[float] = None   # override, kalau None pakai dari employee
    bonus: float = 0
    deduction: float = 0
    notes: Optional[str] = None

class PayrollUpdate(BaseModel):
    bonus: Optional[float] = None
    deduction: Optional[float] = None
    notes: Optional[str] = None
    status: Optional[str] = None  # draft | paid

class MonthlyCostCreate(BaseModel):
    period_month: int
    period_year: int
    name: str
    amount: float

class MonthlyCostUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None


# ====================================================
# Employees
# ====================================================

@router.get("/employees")
def list_employees(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    employees = db.query(Employee).filter(
        Employee.tenant_id == tid
    ).order_by(Employee.name).all()
    return employees


@router.post("/employees", status_code=201)
def create_employee(
    body: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    emp = Employee(tenant_id=tid, **body.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return emp


@router.patch("/employees/{emp_id}")
def update_employee(
    emp_id: int,
    body: EmployeeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    emp = db.query(Employee).filter(Employee.id == emp_id, Employee.tenant_id == tid).first()
    if not emp:
        raise HTTPException(404, "Karyawan tidak ditemukan")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(emp, field, value)
    db.commit()
    db.refresh(emp)
    return emp


@router.delete("/employees/{emp_id}")
def delete_employee(
    emp_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    emp = db.query(Employee).filter(Employee.id == emp_id, Employee.tenant_id == tid).first()
    if not emp:
        raise HTTPException(404, "Karyawan tidak ditemukan")
    db.delete(emp)
    db.commit()
    return {"message": "Karyawan dihapus"}


# ====================================================
# Payroll Records
# ====================================================

@router.get("/records")
def list_records(
    month: Optional[int] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    q = db.query(PayrollRecord).filter(PayrollRecord.tenant_id == tid)
    if month:
        q = q.filter(PayrollRecord.period_month == month)
    if year:
        q = q.filter(PayrollRecord.period_year == year)
    records = q.order_by(PayrollRecord.period_year.desc(), PayrollRecord.period_month.desc(), PayrollRecord.employee_name).all()
    return records


@router.post("/records", status_code=201)
def create_record(
    body: PayrollCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)

    emp = db.query(Employee).filter(Employee.id == body.employee_id, Employee.tenant_id == tid).first()
    if not emp:
        raise HTTPException(404, "Karyawan tidak ditemukan")

    # Cek duplikat period
    existing = db.query(PayrollRecord).filter(
        PayrollRecord.employee_id == body.employee_id,
        PayrollRecord.period_month == body.period_month,
        PayrollRecord.period_year == body.period_year,
    ).first()
    if existing:
        raise HTTPException(400, f"Slip gaji {emp.name} untuk periode ini sudah ada")

    base = body.base_salary if body.base_salary is not None else emp.base_salary
    total = base + body.bonus - body.deduction

    record = PayrollRecord(
        tenant_id=tid,
        employee_id=emp.id,
        employee_name=emp.name,
        period_month=body.period_month,
        period_year=body.period_year,
        base_salary=base,
        bonus=body.bonus,
        deduction=body.deduction,
        total=total,
        notes=body.notes,
        status="draft",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/records/generate-all")
def generate_all_records(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Generate slip gaji untuk semua karyawan aktif sekaligus."""
    tid = resolve_tenant_id(current_user, db)
    employees = db.query(Employee).filter(Employee.tenant_id == tid, Employee.is_active == True).all()

    created = []
    skipped = []
    for emp in employees:
        existing = db.query(PayrollRecord).filter(
            PayrollRecord.employee_id == emp.id,
            PayrollRecord.period_month == month,
            PayrollRecord.period_year == year,
        ).first()
        if existing:
            skipped.append(emp.name)
            continue
        record = PayrollRecord(
            tenant_id=tid,
            employee_id=emp.id,
            employee_name=emp.name,
            period_month=month,
            period_year=year,
            base_salary=emp.base_salary,
            bonus=0,
            deduction=0,
            total=emp.base_salary,
            status="draft",
        )
        db.add(record)
        created.append(emp.name)

    db.commit()
    return {"created": created, "skipped": skipped}


@router.patch("/records/{record_id}")
def update_record(
    record_id: int,
    body: PayrollUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    record = db.query(PayrollRecord).filter(PayrollRecord.id == record_id, PayrollRecord.tenant_id == tid).first()
    if not record:
        raise HTTPException(404, "Slip gaji tidak ditemukan")

    if body.bonus is not None:
        record.bonus = body.bonus
    if body.deduction is not None:
        record.deduction = body.deduction
    if body.notes is not None:
        record.notes = body.notes
    if body.status is not None:
        if body.status not in ("draft", "paid"):
            raise HTTPException(400, "Status harus draft atau paid")
        record.status = body.status
        if body.status == "paid" and not record.paid_at:
            record.paid_at = datetime.now()

    record.total = record.base_salary + record.bonus - record.deduction
    db.commit()
    db.refresh(record)
    return record


@router.delete("/records/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    record = db.query(PayrollRecord).filter(PayrollRecord.id == record_id, PayrollRecord.tenant_id == tid).first()
    if not record:
        raise HTTPException(404, "Slip gaji tidak ditemukan")
    db.delete(record)
    db.commit()
    return {"message": "Slip gaji dihapus"}


@router.get("/summary")
def get_summary(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Ringkasan total pengeluaran gaji per periode."""
    tid = resolve_tenant_id(current_user, db)
    from sqlalchemy import func
    records = db.query(PayrollRecord).filter(
        PayrollRecord.tenant_id == tid,
        PayrollRecord.period_month == month,
        PayrollRecord.period_year == year,
    ).all()

    total_all = sum(r.total for r in records)
    total_paid = sum(r.total for r in records if r.status == "paid")
    total_draft = sum(r.total for r in records if r.status == "draft")

    return {
        "period": f"{str(month).zfill(2)}/{year}",
        "total_karyawan": len(records),
        "total_gaji": total_all,
        "sudah_dibayar": total_paid,
        "belum_dibayar": total_draft,
    }


# ====================================================
# Monthly Costs (Listrik, Air, Pajak, dll)
# ====================================================

@router.get("/monthly-costs")
def list_monthly_costs(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    costs = db.query(MonthlyCost).filter(
        MonthlyCost.tenant_id == tid,
        MonthlyCost.period_month == month,
        MonthlyCost.period_year == year,
    ).order_by(MonthlyCost.name).all()
    return costs


@router.post("/monthly-costs", status_code=201)
def create_monthly_cost(
    body: MonthlyCostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    cost = MonthlyCost(tenant_id=tid, **body.model_dump())
    db.add(cost)
    db.commit()
    db.refresh(cost)
    return cost


@router.patch("/monthly-costs/{cost_id}")
def update_monthly_cost(
    cost_id: int,
    body: MonthlyCostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    cost = db.query(MonthlyCost).filter(MonthlyCost.id == cost_id, MonthlyCost.tenant_id == tid).first()
    if not cost:
        raise HTTPException(404, "Biaya tidak ditemukan")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(cost, field, value)
    db.commit()
    db.refresh(cost)
    return cost


@router.delete("/monthly-costs/{cost_id}")
def delete_monthly_cost(
    cost_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    cost = db.query(MonthlyCost).filter(MonthlyCost.id == cost_id, MonthlyCost.tenant_id == tid).first()
    if not cost:
        raise HTTPException(404, "Biaya tidak ditemukan")
    db.delete(cost)
    db.commit()
    return {"message": "Biaya dihapus"}


# ====================================================
# Financial Summary — Revenue - Gaji - Biaya Operasional
# ====================================================

@router.get("/financial-summary")
def get_financial_summary(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Kalkulasi bersih: Revenue - Pengeluaran - Gaji - Biaya Operasional."""
    from sqlalchemy import func, extract
    tid = resolve_tenant_id(current_user, db)

    # Revenue dari penjualan bulan ini
    revenue = db.query(func.sum(Sale.final_amount)).filter(
        Sale.tenant_id == tid,
        extract("month", Sale.transaction_date) == month,
        extract("year", Sale.transaction_date) == year,
        Sale.status == "COMPLETED",
    ).scalar() or 0

    # Pengeluaran operasional (dari tabel expenses)
    expenses = db.query(func.sum(Expense.price)).filter(
        Expense.tenant_id == tid,
        extract("month", Expense.purchase_date) == month,
        extract("year", Expense.purchase_date) == year,
    ).scalar() or 0

    # Total gaji karyawan (semua status)
    payroll_records = db.query(PayrollRecord).filter(
        PayrollRecord.tenant_id == tid,
        PayrollRecord.period_month == month,
        PayrollRecord.period_year == year,
    ).all()
    total_salary = sum(r.total for r in payroll_records)
    salary_paid = sum(r.total for r in payroll_records if r.status == "paid")
    salary_draft = sum(r.total for r in payroll_records if r.status == "draft")

    # Biaya operasional custom (listrik, air, pajak, dll)
    monthly_costs = db.query(MonthlyCost).filter(
        MonthlyCost.tenant_id == tid,
        MonthlyCost.period_month == month,
        MonthlyCost.period_year == year,
    ).all()
    total_monthly_costs = sum(c.amount for c in monthly_costs)

    total_deductions = expenses + total_salary + total_monthly_costs
    net_profit = revenue - total_deductions

    return {
        "period": f"{str(month).zfill(2)}/{year}",
        "revenue": revenue,
        "expenses": expenses,
        "total_salary": total_salary,
        "salary_paid": salary_paid,
        "salary_draft": salary_draft,
        "total_monthly_costs": total_monthly_costs,
        "monthly_costs_detail": [{"id": c.id, "name": c.name, "amount": c.amount} for c in monthly_costs],
        "total_deductions": total_deductions,
        "net_profit": net_profit,
    }
