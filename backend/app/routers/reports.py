"""Analytics & reporting endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from typing import Optional
from datetime import date, timedelta, datetime

from app.database import get_db
from app.models.user import User
from app.models.pos import Sale, SaleItem, Expense, MenuItem
from app.models.inventory import Product, StockMovement
from app.core.deps import get_current_user, require_manager

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get("/dashboard")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """KPI summary untuk dashboard utama."""
    tid = current_user.tenant_id
    today = date.today()
    first_of_month = today.replace(day=1)

    # Revenue hari ini
    today_revenue = db.query(func.sum(Sale.final_amount)).filter(
        Sale.tenant_id == tid,
        func.date(Sale.transaction_date) == today,
        Sale.status == "COMPLETED",
    ).scalar() or 0

    # Revenue bulan ini
    month_revenue = db.query(func.sum(Sale.final_amount)).filter(
        Sale.tenant_id == tid,
        func.date(Sale.transaction_date) >= first_of_month,
        Sale.status == "COMPLETED",
    ).scalar() or 0

    # Total transaksi hari ini
    today_trx_count = db.query(func.count(Sale.id)).filter(
        Sale.tenant_id == tid,
        func.date(Sale.transaction_date) == today,
        Sale.status == "COMPLETED",
    ).scalar() or 0

    # Pengeluaran bulan ini
    month_expense = db.query(func.sum(Expense.price)).filter(
        Expense.tenant_id == tid,
        Expense.purchase_date >= first_of_month,
    ).scalar() or 0

    # Low stock products
    low_stock_count = db.query(func.count(Product.id)).filter(
        Product.tenant_id == tid,
        Product.current_stock <= Product.min_stock_level,
    ).scalar() or 0

    # Top menu hari ini
    top_menu = db.query(
        SaleItem.menu_name,
        func.sum(SaleItem.quantity).label("total_qty"),
        func.sum(SaleItem.subtotal).label("total_revenue"),
    ).join(Sale).filter(
        Sale.tenant_id == tid,
        func.date(Sale.transaction_date) == today,
        Sale.status == "COMPLETED",
    ).group_by(SaleItem.menu_name).order_by(
        func.sum(SaleItem.quantity).desc()
    ).limit(5).all()

    return {
        "today": {
            "revenue": today_revenue,
            "transaction_count": today_trx_count,
            "avg_transaction": today_revenue / today_trx_count if today_trx_count else 0,
        },
        "month": {
            "revenue": month_revenue,
            "expense": month_expense,
            "profit_estimate": month_revenue - month_expense,
        },
        "alerts": {
            "low_stock_count": low_stock_count,
        },
        "top_menu_today": [
            {"name": r.menu_name, "qty": r.total_qty, "revenue": r.total_revenue}
            for r in top_menu
        ],
    }


@router.get("/revenue/daily")
def daily_revenue(
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revenue per hari untuk chart."""
    tid = current_user.tenant_id
    date_from = date.today() - timedelta(days=days)

    rows = db.query(
        func.date(Sale.transaction_date).label("day"),
        func.sum(Sale.final_amount).label("revenue"),
        func.count(Sale.id).label("trx_count"),
    ).filter(
        Sale.tenant_id == tid,
        func.date(Sale.transaction_date) >= date_from,
        Sale.status == "COMPLETED",
    ).group_by(func.date(Sale.transaction_date)).order_by("day").all()

    return [{"date": str(r.day), "revenue": r.revenue, "trx_count": r.trx_count} for r in rows]


@router.get("/revenue/by-payment-method")
def revenue_by_payment(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = current_user.tenant_id
    q = db.query(
        Sale.payment_method,
        func.sum(Sale.final_amount).label("total"),
        func.count(Sale.id).label("count"),
    ).filter(Sale.tenant_id == tid, Sale.status == "COMPLETED")

    if date_from:
        q = q.filter(func.date(Sale.transaction_date) >= date_from)
    if date_to:
        q = q.filter(func.date(Sale.transaction_date) <= date_to)

    rows = q.group_by(Sale.payment_method).all()
    return [{"method": r.payment_method, "total": r.total, "count": r.count} for r in rows]


@router.get("/menu/performance")
def menu_performance(
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Top & bottom performing menu items."""
    tid = current_user.tenant_id
    date_from = date.today() - timedelta(days=days)

    rows = db.query(
        SaleItem.menu_name,
        func.sum(SaleItem.quantity).label("total_qty"),
        func.sum(SaleItem.subtotal).label("total_revenue"),
    ).join(Sale).filter(
        Sale.tenant_id == tid,
        func.date(Sale.transaction_date) >= date_from,
        Sale.status == "COMPLETED",
    ).group_by(SaleItem.menu_name).order_by(
        func.sum(SaleItem.subtotal).desc()
    ).all()

    return [
        {"name": r.menu_name, "qty_sold": r.total_qty, "revenue": r.total_revenue}
        for r in rows
    ]


@router.get("/inventory/summary")
def inventory_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ringkasan stok untuk semua produk."""
    tid = current_user.tenant_id
    products = db.query(Product).filter(Product.tenant_id == tid).all()

    total_value = sum(p.current_stock * p.cost_price for p in products)
    low_stock = [p for p in products if p.current_stock <= p.min_stock_level]
    out_of_stock = [p for p in products if p.current_stock == 0]

    return {
        "total_products": len(products),
        "total_stock_value": total_value,
        "low_stock_count": len(low_stock),
        "out_of_stock_count": len(out_of_stock),
        "low_stock_items": [
            {"id": p.id, "name": p.name, "current_stock": p.current_stock, "min_stock": p.min_stock_level}
            for p in low_stock
        ],
    }
