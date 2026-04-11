from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
import uuid
import re
from datetime import datetime, date

from app.database import get_db
from app.models.user import User
from app.models.pos import (
    MenuItem, Recipe, Sale, SaleItem,
    Expense, Debt, DebtItem, Reservation, ReservationItem
)
from app.models.inventory import Product, StockMovement
from app.core.deps import (
    get_current_user, require_kasir, require_manager, require_admin,
    resolve_tenant_id,
)

router = APIRouter(prefix="/api/v1/pos", tags=["POS"])


# ==================== MENU ITEMS ====================

class MenuItemCreate(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None
    division: str = "Bar"
    image_url: Optional[str] = None
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    division: Optional[str] = None
    is_available: Optional[bool] = None


@router.get("/menu")
def list_menu(
    search: Optional[str] = Query(None),
    division: Optional[str] = Query(None),
    available_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    q = db.query(MenuItem).filter(MenuItem.tenant_id == tid)
    if search:
        q = q.filter(MenuItem.name.ilike(f"%{search}%"))
    if division:
        q = q.filter(MenuItem.division == division)
    if available_only:
        q = q.filter(MenuItem.is_available == True)
    return q.order_by(MenuItem.category, MenuItem.name).all()


@router.post("/menu", status_code=201)
def create_menu_item(
    body: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    tid = resolve_tenant_id(current_user, db)
    item = MenuItem(tenant_id=tid, **body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/menu/{item_id}")
def update_menu_item(
    item_id: int,
    body: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    tid = resolve_tenant_id(current_user, db)
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.tenant_id == tid,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu tidak ditemukan")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/menu/{item_id}", status_code=204)
def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    item = db.query(MenuItem).filter(
        MenuItem.id == item_id,
        MenuItem.tenant_id == tid,
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Menu tidak ditemukan")
    db.delete(item)
    db.commit()


# ==================== SALES / TRANSACTIONS ====================

class SaleItemIn(BaseModel):
    menu_item_id: Optional[int] = None
    menu_name: str
    quantity: int
    price_at_moment: float
    note: Optional[str] = None


class SaleCreate(BaseModel):
    items: List[SaleItemIn]
    customer_name: Optional[str] = None
    table_number: Optional[str] = None
    payment_method: str = "CASH"
    discount_amount: float = 0.0
    notes: Optional[str] = None


def _generate_transaction_code(tenant_id: int) -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TRX-{tenant_id}-{ts}"


@router.get("/sales")
def list_sales(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    q = db.query(Sale).options(joinedload(Sale.items)).filter(
        Sale.tenant_id == tid
    )
    if date_from:
        q = q.filter(func.date(Sale.transaction_date) >= date_from)
    if date_to:
        q = q.filter(func.date(Sale.transaction_date) <= date_to)
    return q.order_by(Sale.transaction_date.desc()).limit(limit).all()


@router.post("/sales", status_code=201)
def create_sale(
    body: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    if not body.items:
        raise HTTPException(status_code=400, detail="Minimal 1 item transaksi")

    tid = resolve_tenant_id(current_user, db)
    total = sum(i.quantity * i.price_at_moment for i in body.items)
    tax = total * 0.0   # bisa dikonfigurasi per-tenant nanti
    final = total - body.discount_amount + tax

    sale = Sale(
        tenant_id=tid,
        transaction_code=_generate_transaction_code(tid),
        total_amount=total,
        discount_amount=body.discount_amount,
        tax_amount=tax,
        final_amount=final,
        customer_name=body.customer_name,
        table_number=body.table_number,
        payment_method=body.payment_method,
        notes=body.notes,
        cashier_id=current_user.id,
    )
    db.add(sale)
    db.flush()

    for item_in in body.items:
        si = SaleItem(
            sale_id=sale.id,
            menu_item_id=item_in.menu_item_id,
            menu_name=item_in.menu_name,
            quantity=item_in.quantity,
            price_at_moment=item_in.price_at_moment,
            subtotal=item_in.quantity * item_in.price_at_moment,
            note=item_in.note,
        )
        db.add(si)

        # Kurangi stok bahan baku via resep
        if item_in.menu_item_id:
            recipes = db.query(Recipe).filter(Recipe.menu_item_id == item_in.menu_item_id).all()
            for recipe in recipes:
                product = db.query(Product).filter(
                    Product.id == recipe.product_id,
                    Product.tenant_id == tid,
                ).first()
                if product:
                    deduct = recipe.amount_needed * item_in.quantity
                    product.current_stock = max(0, product.current_stock - int(deduct))
                    db.add(StockMovement(
                        id=str(uuid.uuid4()),
                        tenant_id=tid,
                        product_id=product.id,
                        qty_change=-int(deduct),
                        balance_after=product.current_stock,
                        transaction_type="OUT",
                        source="POS",
                        created_by=current_user.username,
                    ))

    db.commit()
    db.refresh(sale)
    return sale


@router.get("/sales/{sale_id}")
def get_sale(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    sale = db.query(Sale).options(joinedload(Sale.items)).filter(
        Sale.id == sale_id,
        Sale.tenant_id == tid,
    ).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Transaksi tidak ditemukan")
    return sale


# ==================== EXPENSES ====================

class ExpenseCreate(BaseModel):
    item_name: str
    price: float
    category: Optional[str] = None
    purchase_date: Optional[date] = None
    note: Optional[str] = None


@router.get("/expenses")
def list_expenses(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    q = db.query(Expense).filter(Expense.tenant_id == tid)
    if date_from:
        q = q.filter(Expense.purchase_date >= date_from)
    if date_to:
        q = q.filter(Expense.purchase_date <= date_to)
    return q.order_by(Expense.created_at.desc()).all()


@router.post("/expenses", status_code=201)
def create_expense(
    body: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    tid = resolve_tenant_id(current_user, db)
    expense = Expense(
        tenant_id=tid,
        created_by=current_user.username,
        **body.model_dump(),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


# ==================== DEBTS ====================

class DebtItemIn(BaseModel):
    menu_item_id: Optional[int] = None
    menu_name: str
    quantity: int
    price_at_moment: float


class DebtCreate(BaseModel):
    customer_name: str
    phone: Optional[str] = None
    items: List[DebtItemIn]
    due_date: Optional[date] = None
    notes: Optional[str] = None


@router.get("/debts")
def list_debts(
    is_paid: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    q = db.query(Debt).options(joinedload(Debt.items)).filter(
        Debt.tenant_id == tid
    )
    if is_paid is not None:
        q = q.filter(Debt.is_paid == is_paid)
    return q.order_by(Debt.created_at.desc()).all()


@router.post("/debts", status_code=201)
def create_debt(
    body: DebtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    tid = resolve_tenant_id(current_user, db)
    total = sum(i.quantity * i.price_at_moment for i in body.items)
    debt = Debt(
        tenant_id=tid,
        customer_name=body.customer_name,
        phone=body.phone,
        total_amount=total,
        due_date=body.due_date,
        notes=body.notes,
    )
    db.add(debt)
    db.flush()

    for item_in in body.items:
        db.add(DebtItem(
            debt_id=debt.id,
            menu_item_id=item_in.menu_item_id,
            menu_name=item_in.menu_name,
            quantity=item_in.quantity,
            price_at_moment=item_in.price_at_moment,
        ))

    db.commit()
    db.refresh(debt)
    return debt


@router.patch("/debts/{debt_id}/pay")
def pay_debt(
    debt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    tid = resolve_tenant_id(current_user, db)
    debt = db.query(Debt).filter(
        Debt.id == debt_id,
        Debt.tenant_id == tid,
    ).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Hutang tidak ditemukan")

    debt.is_paid = True
    debt.paid_amount = debt.total_amount
    debt.paid_at = datetime.now()
    db.commit()
    return {"message": "Hutang sudah dilunasi", "debt_id": debt_id}


# ==================== RESERVATIONS ====================

class ReservationItemIn(BaseModel):
    menu_item_id: Optional[int] = None
    menu_name: str
    quantity: int
    price_at_moment: float
    note: Optional[str] = None


class ReservationCreate(BaseModel):
    customer_name: str
    phone: Optional[str] = None
    table_number: Optional[str] = None
    pax: int = 1
    reservation_date: Optional[datetime] = None
    items: List[ReservationItemIn] = []
    dp_amount: float = 0.0
    dp_method: str = "CASH"
    notes: Optional[str] = None


@router.get("/reservations")
def list_reservations(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    q = db.query(Reservation).options(joinedload(Reservation.items)).filter(
        Reservation.tenant_id == tid
    )
    if status:
        q = q.filter(Reservation.status == status)
    return q.order_by(Reservation.reservation_date.desc()).all()


@router.post("/reservations", status_code=201)
def create_reservation(
    body: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    tid = resolve_tenant_id(current_user, db)
    total = sum(i.quantity * i.price_at_moment for i in body.items)
    res = Reservation(
        tenant_id=tid,
        customer_name=body.customer_name,
        phone=body.phone,
        table_number=body.table_number,
        pax=body.pax,
        reservation_date=body.reservation_date,
        total_amount=total,
        dp_amount=body.dp_amount,
        dp_method=body.dp_method,
        notes=body.notes,
    )
    db.add(res)
    db.flush()

    for item_in in body.items:
        db.add(ReservationItem(
            reservation_id=res.id,
            menu_item_id=item_in.menu_item_id,
            menu_name=item_in.menu_name,
            quantity=item_in.quantity,
            price_at_moment=item_in.price_at_moment,
            note=item_in.note,
        ))

    db.commit()
    db.refresh(res)
    return res


@router.patch("/reservations/{res_id}/status")
def update_reservation_status(
    res_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    tid = resolve_tenant_id(current_user, db)
    res = db.query(Reservation).filter(
        Reservation.id == res_id,
        Reservation.tenant_id == tid,
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservasi tidak ditemukan")

    valid_statuses = ["PENDING", "CONFIRMED", "COMPLETED", "CANCELLED"]
    new_status = body.get("status")
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status tidak valid: {valid_statuses}")

    res.status = new_status
    db.commit()
    return {"message": f"Status diupdate ke {new_status}"}
