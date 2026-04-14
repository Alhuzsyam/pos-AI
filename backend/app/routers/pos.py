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
from app.models.tenant import Tenant
from app.core.deps import (
    get_current_user, require_kasir, require_manager, require_admin,
    resolve_tenant_id,
)
from app.models.tenant_settings import TenantSettings

router = APIRouter(prefix="/api/v1/pos", tags=["POS"])


# ==================== MENU ITEMS ====================

class RecipeItemIn(BaseModel):
    product_id: int
    amount_needed: float


class MenuItemCreate(BaseModel):
    name: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None
    division: str = "Bar"
    image_url: Optional[str] = None
    is_available: bool = True
    recipes: List[RecipeItemIn] = []


class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    division: Optional[str] = None
    is_available: Optional[bool] = None
    recipes: Optional[List[RecipeItemIn]] = None


@router.get("/menu")
def list_menu(
    search: Optional[str] = Query(None),
    division: Optional[str] = Query(None),
    available_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    q = db.query(MenuItem).options(
        joinedload(MenuItem.recipes)
    ).filter(MenuItem.tenant_id == tid)
    if search:
        q = q.filter(MenuItem.name.ilike(f"%{search}%"))
    if division:
        q = q.filter(MenuItem.division == division)
    if available_only:
        q = q.filter(MenuItem.is_available == True)
    items = q.order_by(MenuItem.category, MenuItem.name).all()
    return [_menu_to_dict(item) for item in items]


def _menu_to_dict(item: MenuItem) -> dict:
    return {
        "id": item.id,
        "tenant_id": item.tenant_id,
        "name": item.name,
        "description": item.description,
        "price": item.price,
        "category": item.category,
        "division": item.division,
        "image_url": item.image_url,
        "is_available": item.is_available,
        "recipes": [
            {"id": r.id, "product_id": r.product_id, "amount_needed": r.amount_needed,
             "product_name": r.product.name if r.product else None,
             "product_unit": r.product.unit if r.product else None}
            for r in (item.recipes or [])
        ],
    }


@router.post("/menu", status_code=201)
def create_menu_item(
    body: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    tid = resolve_tenant_id(current_user, db)
    data = body.model_dump(exclude={"recipes"})
    item = MenuItem(tenant_id=tid, **data)
    db.add(item)
    db.flush()

    for r in body.recipes:
        db.add(Recipe(menu_item_id=item.id, product_id=r.product_id, amount_needed=r.amount_needed))

    db.commit()
    db.refresh(item)
    return _menu_to_dict(item)


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

    for field, value in body.model_dump(exclude_none=True, exclude={"recipes"}).items():
        setattr(item, field, value)

    # Sync recipes if provided
    if body.recipes is not None:
        db.query(Recipe).filter(Recipe.menu_item_id == item.id).delete()
        for r in body.recipes:
            db.add(Recipe(menu_item_id=item.id, product_id=r.product_id, amount_needed=r.amount_needed))

    db.commit()
    db.refresh(item)
    return _menu_to_dict(item)


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
    is_debt: bool = False          # True = hutang, don't pay now
    phone: Optional[str] = None    # for debt customer phone


def _generate_transaction_code(tenant_id: int) -> str:
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"TRX-{tenant_id}-{ts}"


def _deduct_stock(menu_item_id: int, quantity: int, tenant_id: int, username: str, db: Session):
    """Kurangi stok bahan baku via resep menu item."""
    recipes = db.query(Recipe).filter(Recipe.menu_item_id == menu_item_id).all()
    for recipe in recipes:
        product = db.query(Product).filter(
            Product.id == recipe.product_id,
            Product.tenant_id == tenant_id,
        ).first()
        if product:
            deduct = recipe.amount_needed * quantity
            product.current_stock = max(0, product.current_stock - int(deduct))
            db.add(StockMovement(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                product_id=product.id,
                qty_change=-int(deduct),
                balance_after=product.current_stock,
                transaction_type="OUT",
                source="POS",
                created_by=username,
            ))


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

    payment = "DEBT" if body.is_debt else body.payment_method
    status = "PENDING" if body.is_debt else "COMPLETED"

    sale = Sale(
        tenant_id=tid,
        transaction_code=_generate_transaction_code(tid),
        total_amount=total,
        discount_amount=body.discount_amount,
        tax_amount=tax,
        final_amount=final,
        customer_name=body.customer_name,
        table_number=body.table_number,
        payment_method=payment,
        status=status,
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
            _deduct_stock(item_in.menu_item_id, item_in.quantity, tid, current_user.username, db)

    # If debt, auto-create Debt record
    if body.is_debt:
        if not body.customer_name:
            raise HTTPException(400, "Nama pelanggan wajib untuk hutang")
        debt = Debt(
            tenant_id=tid,
            sale_id=sale.id,
            customer_name=body.customer_name,
            phone=body.phone,
            total_amount=final,
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


# ==================== EDIT PAYMENT METHOD ====================

class PaymentMethodUpdate(BaseModel):
    payment_method: str   # CASH | QRIS | TRANSFER | DEBIT | CREDIT


@router.patch("/sales/{sale_id}/payment")
def update_payment_method(
    sale_id: int,
    body: PaymentMethodUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    """Edit metode pembayaran transaksi."""
    valid_methods = ["CASH", "QRIS", "TRANSFER", "DEBIT", "CREDIT"]
    if body.payment_method not in valid_methods:
        raise HTTPException(400, f"Metode tidak valid: {valid_methods}")

    tid = resolve_tenant_id(current_user, db)
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.tenant_id == tid).first()
    if not sale:
        raise HTTPException(404, "Transaksi tidak ditemukan")

    old_method = sale.payment_method
    sale.payment_method = body.payment_method
    db.commit()
    return {
        "message": f"Metode bayar diubah dari {old_method} ke {body.payment_method}",
        "sale_id": sale_id,
    }


# ==================== RECEIPT / STRUK ====================

@router.get("/sales/{sale_id}/receipt")
def get_receipt(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Data struk untuk di-print (browser print / thermal)."""
    tid = resolve_tenant_id(current_user, db)
    sale = db.query(Sale).options(joinedload(Sale.items)).filter(
        Sale.id == sale_id, Sale.tenant_id == tid,
    ).first()
    if not sale:
        raise HTTPException(404, "Transaksi tidak ditemukan")

    # Get tenant info for receipt header
    tenant = db.query(Tenant).filter(Tenant.id == tid).first()

    return {
        "store_name": tenant.name if tenant else "POS-AI",
        "store_address": tenant.address if tenant else "",
        "store_phone": tenant.phone if tenant else "",
        "transaction_code": sale.transaction_code,
        "date": sale.transaction_date.strftime("%d/%m/%Y %H:%M") if sale.transaction_date else "",
        "cashier": current_user.full_name or current_user.username,
        "customer_name": sale.customer_name,
        "table_number": sale.table_number,
        "payment_method": sale.payment_method,
        "items": [
            {
                "name": item.menu_name,
                "qty": item.quantity,
                "price": item.price_at_moment,
                "subtotal": item.subtotal,
                "note": item.note,
            }
            for item in sale.items
        ],
        "total_amount": sale.total_amount,
        "discount_amount": sale.discount_amount,
        "tax_amount": sale.tax_amount,
        "final_amount": sale.final_amount,
        "notes": sale.notes,
    }


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
    table_number: Optional[str] = None
    items: List[DebtItemIn]
    due_date: Optional[date] = None
    notes: Optional[str] = None
    discount_amount: float = 0.0


class DebtPayBody(BaseModel):
    payment_method: str = "CASH"   # CASH | QRIS | TRANSFER


class DebtAddItems(BaseModel):
    items: List[DebtItemIn]


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
    """
    Create debt + linked Sale with SaleItems (items masuk watchlist).
    Stok auto deduct via resep.
    """
    if not body.items:
        raise HTTPException(400, "Minimal 1 item")

    tid = resolve_tenant_id(current_user, db)
    total = sum(i.quantity * i.price_at_moment for i in body.items)
    final = total - body.discount_amount

    # Create Sale (payment_method=DEBT, status=PENDING until paid)
    sale = Sale(
        tenant_id=tid,
        transaction_code=_generate_transaction_code(tid),
        total_amount=total,
        discount_amount=body.discount_amount,
        tax_amount=0.0,
        final_amount=final,
        customer_name=body.customer_name,
        table_number=body.table_number,
        payment_method="DEBT",
        status="PENDING",
        notes=body.notes,
        cashier_id=current_user.id,
    )
    db.add(sale)
    db.flush()

    # Create SaleItems (go to watchlist as PENDING)
    for item_in in body.items:
        db.add(SaleItem(
            sale_id=sale.id,
            menu_item_id=item_in.menu_item_id,
            menu_name=item_in.menu_name,
            quantity=item_in.quantity,
            price_at_moment=item_in.price_at_moment,
            subtotal=item_in.quantity * item_in.price_at_moment,
        ))
        # Deduct stock via recipe
        if item_in.menu_item_id:
            _deduct_stock(item_in.menu_item_id, item_in.quantity, tid, current_user.username, db)

    # Create Debt record
    debt = Debt(
        tenant_id=tid,
        sale_id=sale.id,
        customer_name=body.customer_name,
        phone=body.phone,
        total_amount=final,
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


@router.post("/debts/{debt_id}/add-items", status_code=201)
def add_debt_items(
    debt_id: int,
    body: DebtAddItems,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    """Tambah item ke hutang yang sudah ada. Only new items go to watchlist."""
    if not body.items:
        raise HTTPException(400, "Minimal 1 item")

    tid = resolve_tenant_id(current_user, db)
    debt = db.query(Debt).filter(Debt.id == debt_id, Debt.tenant_id == tid, Debt.is_paid == False).first()
    if not debt:
        raise HTTPException(404, "Hutang tidak ditemukan atau sudah lunas")

    added_total = sum(i.quantity * i.price_at_moment for i in body.items)

    # Add new SaleItems to linked sale (only new items to watchlist)
    if debt.sale_id:
        for item_in in body.items:
            db.add(SaleItem(
                sale_id=debt.sale_id,
                menu_item_id=item_in.menu_item_id,
                menu_name=item_in.menu_name,
                quantity=item_in.quantity,
                price_at_moment=item_in.price_at_moment,
                subtotal=item_in.quantity * item_in.price_at_moment,
            ))
            if item_in.menu_item_id:
                _deduct_stock(item_in.menu_item_id, item_in.quantity, tid, current_user.username, db)

        # Update sale totals
        sale = db.query(Sale).filter(Sale.id == debt.sale_id).first()
        if sale:
            sale.total_amount += added_total
            sale.final_amount += added_total

    # Add DebtItems
    for item_in in body.items:
        db.add(DebtItem(
            debt_id=debt.id,
            menu_item_id=item_in.menu_item_id,
            menu_name=item_in.menu_name,
            quantity=item_in.quantity,
            price_at_moment=item_in.price_at_moment,
        ))

    debt.total_amount += added_total
    db.commit()
    db.refresh(debt)
    return debt


@router.patch("/debts/{debt_id}/pay")
def pay_debt(
    debt_id: int,
    body: DebtPayBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    """
    Lunasi hutang — creates revenue entry on payment date.
    Updates linked Sale to COMPLETED + payment_method.
    """
    tid = resolve_tenant_id(current_user, db)
    debt = db.query(Debt).filter(
        Debt.id == debt_id,
        Debt.tenant_id == tid,
    ).first()
    if not debt:
        raise HTTPException(status_code=404, detail="Hutang tidak ditemukan")
    if debt.is_paid:
        raise HTTPException(400, "Hutang sudah lunas")

    now = datetime.now()
    debt.is_paid = True
    debt.paid_amount = debt.total_amount
    debt.paid_at = now
    debt.payment_method = body.payment_method

    # Update linked sale — mark completed + update date to NOW (revenue hits today)
    if debt.sale_id:
        sale = db.query(Sale).filter(Sale.id == debt.sale_id).first()
        if sale:
            sale.status = "COMPLETED"
            sale.payment_method = body.payment_method
            sale.transaction_date = now  # revenue masuk di tgl bayar

    db.commit()
    return {"message": f"Hutang dilunasi via {body.payment_method}", "debt_id": debt_id}


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
    res = db.query(Reservation).options(joinedload(Reservation.items)).filter(
        Reservation.id == res_id,
        Reservation.tenant_id == tid,
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservasi tidak ditemukan")

    valid_statuses = ["PENDING", "CONFIRMED", "SERVING", "COMPLETED", "CANCELLED"]
    new_status = body.get("status")
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status tidak valid: {valid_statuses}")

    res.status = new_status
    db.commit()
    return {"message": f"Status diupdate ke {new_status}"}


class ReservationServeBody(BaseModel):
    settlement_method: str = "CASH"  # CASH | QRIS | TRANSFER


@router.post("/reservations/{res_id}/serve")
def serve_reservation(
    res_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    """
    Sajikan reservasi — item masuk watchlist, BELUM bayar.
    Pelunasan dilakukan setelah makan via /settle.
    """
    tid = resolve_tenant_id(current_user, db)
    res = db.query(Reservation).options(joinedload(Reservation.items)).filter(
        Reservation.id == res_id,
        Reservation.tenant_id == tid,
    ).first()
    if not res:
        raise HTTPException(404, "Reservasi tidak ditemukan")
    if res.status not in ("CONFIRMED", "PENDING"):
        raise HTTPException(400, f"Reservasi status {res.status}, harus CONFIRMED/PENDING")
    if not res.items:
        raise HTTPException(400, "Reservasi belum punya item menu")

    total = sum(i.quantity * i.price_at_moment for i in res.items)

    # Buat Sale dengan status PENDING — masuk watchlist, belum completed
    sale = Sale(
        tenant_id=tid,
        transaction_code=_generate_transaction_code(tid),
        total_amount=total,
        discount_amount=0.0,
        tax_amount=0.0,
        final_amount=total,
        customer_name=res.customer_name,
        table_number=res.table_number,
        payment_method="PENDING",
        status="PENDING",
        notes=f"Reservasi #{res.id} - DP: {res.dp_amount} ({res.dp_method})",
        cashier_id=current_user.id,
    )
    db.add(sale)
    db.flush()

    # Buat SaleItems — masuk watchlist
    for item in res.items:
        db.add(SaleItem(
            sale_id=sale.id,
            menu_item_id=item.menu_item_id,
            menu_name=item.menu_name,
            quantity=item.quantity,
            price_at_moment=item.price_at_moment,
            subtotal=item.quantity * item.price_at_moment,
            note=item.note,
        ))
        if item.menu_item_id:
            _deduct_stock(item.menu_item_id, item.quantity, tid, current_user.username, db)

    res.sale_id = sale.id
    res.total_amount = total
    res.status = "SERVING"

    db.commit()
    return {
        "message": "Reservasi disajikan! Item masuk watchlist. Lakukan pelunasan setelah makan.",
        "sale_id": sale.id,
        "sisa_bayar": total - res.dp_amount,
    }


@router.post("/reservations/{res_id}/settle")
def settle_reservation(
    res_id: int,
    body: ReservationServeBody,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    """Pelunasan setelah makan — sale jadi COMPLETED."""
    tid = resolve_tenant_id(current_user, db)
    res = db.query(Reservation).filter(
        Reservation.id == res_id, Reservation.tenant_id == tid,
    ).first()
    if not res:
        raise HTTPException(404, "Reservasi tidak ditemukan")
    if res.status != "SERVING":
        raise HTTPException(400, "Reservasi harus dalam status SERVING untuk dilunasi")

    settlement = (res.total_amount or 0) - res.dp_amount

    # Update sale jadi COMPLETED
    if res.sale_id:
        sale = db.query(Sale).filter(Sale.id == res.sale_id).first()
        if sale:
            sale.status = "COMPLETED"
            sale.payment_method = body.settlement_method
            sale.notes = (sale.notes or "") + f", Pelunasan: {settlement} ({body.settlement_method})"

    res.settlement_amount = settlement
    res.settlement_method = body.settlement_method
    res.status = "COMPLETED"

    db.commit()
    return {"message": "Pelunasan berhasil! Reservasi selesai.", "settlement": settlement}


@router.patch("/reservations/{res_id}/complete")
def complete_reservation(
    res_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_kasir),
):
    """Mark reservation as completed after serving."""
    tid = resolve_tenant_id(current_user, db)
    res = db.query(Reservation).filter(
        Reservation.id == res_id, Reservation.tenant_id == tid,
    ).first()
    if not res:
        raise HTTPException(404, "Reservasi tidak ditemukan")
    res.status = "COMPLETED"
    db.commit()
    return {"message": "Reservasi selesai"}
