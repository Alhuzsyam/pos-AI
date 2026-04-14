"""Analytics & reporting endpoints."""
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from typing import Optional
from datetime import date, timedelta, datetime
from io import BytesIO

from app.database import get_db
from app.models.user import User
from app.models.pos import Sale, SaleItem, Expense, MenuItem
from app.models.inventory import Product, StockMovement
from app.models.tenant import Tenant
from app.core.deps import get_current_user, require_manager, resolve_tenant_id

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get("/dashboard")
def dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """KPI summary untuk dashboard utama."""
    tid = resolve_tenant_id(current_user, db)
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
    tid = resolve_tenant_id(current_user, db)
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
    tid = resolve_tenant_id(current_user, db)
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


@router.get("/closing")
def closing_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Laporan closing: total transaksi & breakdown per metode pembayaran untuk rentang tanggal."""
    today = date.today()
    d_from = date_from or today
    d_to = date_to or today

    tid = resolve_tenant_id(current_user, db)

    # Per-method breakdown
    rows = db.query(
        Sale.payment_method,
        func.sum(Sale.final_amount).label("total"),
        func.count(Sale.id).label("count"),
    ).filter(
        Sale.tenant_id == tid,
        Sale.status == "COMPLETED",
        func.date(Sale.transaction_date) >= d_from,
        func.date(Sale.transaction_date) <= d_to,
    ).group_by(Sale.payment_method).all()

    breakdown = [{"method": r.payment_method, "total": float(r.total or 0), "count": int(r.count)} for r in rows]
    grand_total = sum(b["total"] for b in breakdown)
    grand_count = sum(b["count"] for b in breakdown)

    # Expenses in the same range
    expenses = db.query(func.sum(Expense.price)).filter(
        Expense.tenant_id == tid,
        Expense.purchase_date >= d_from,
        Expense.purchase_date <= d_to,
    ).scalar() or 0

    return {
        "date_from": str(d_from),
        "date_to": str(d_to),
        "grand_total": grand_total,
        "grand_count": grand_count,
        "breakdown": breakdown,
        "total_expenses": float(expenses),
        "net_profit": grand_total - float(expenses),
    }


@router.get("/menu/performance")
def menu_performance(
    days: int = Query(30, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Top & bottom performing menu items."""
    tid = resolve_tenant_id(current_user, db)
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
    tid = resolve_tenant_id(current_user, db)
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


@router.get("/export-excel")
def export_excel(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_manager),
):
    """
    Export laporan keuangan ke Excel.
    3 sheet: Ringkasan Keuangan, Rekap Penjualan Menu, Detail Belanja.
    """
    import xlsxwriter

    tid = resolve_tenant_id(current_user, db)
    if not date_from:
        date_from = date.today().replace(day=1)
    if not date_to:
        date_to = date.today()

    tenant = db.query(Tenant).filter(Tenant.id == tid).first()
    store_name = tenant.name if tenant else "POS-AI"

    # ---- Data queries ----
    sales = db.query(Sale).filter(
        Sale.tenant_id == tid,
        Sale.status == "COMPLETED",
        func.date(Sale.transaction_date) >= date_from,
        func.date(Sale.transaction_date) <= date_to,
    ).all()

    menu_sales = db.query(
        SaleItem.menu_name,
        func.sum(SaleItem.quantity).label("qty"),
        func.sum(SaleItem.subtotal).label("revenue"),
    ).join(Sale).filter(
        Sale.tenant_id == tid,
        Sale.status == "COMPLETED",
        func.date(Sale.transaction_date) >= date_from,
        func.date(Sale.transaction_date) <= date_to,
    ).group_by(SaleItem.menu_name).order_by(func.sum(SaleItem.subtotal).desc()).all()

    expenses = db.query(Expense).filter(
        Expense.tenant_id == tid,
        Expense.purchase_date >= date_from,
        Expense.purchase_date <= date_to,
    ).order_by(Expense.purchase_date).all()

    total_revenue = sum(s.final_amount for s in sales)
    total_expense = sum(e.price for e in expenses)

    # Cash vs QRIS breakdown
    cash_total = sum(s.final_amount for s in sales if s.payment_method == "CASH")
    qris_total = sum(s.final_amount for s in sales if s.payment_method == "QRIS")
    other_total = total_revenue - cash_total - qris_total

    # ---- Build Excel ----
    output = BytesIO()
    wb = xlsxwriter.Workbook(output, {"in_memory": True})

    # Formats
    header_fmt = wb.add_format({
        "bold": True, "bg_color": "#2c4a3b", "font_color": "white",
        "border": 1, "align": "center",
    })
    currency_fmt = wb.add_format({"num_format": "#,##0", "border": 1})
    text_fmt = wb.add_format({"border": 1})
    bold_fmt = wb.add_format({"bold": True, "border": 1})
    title_fmt = wb.add_format({"bold": True, "font_size": 14})
    subtitle_fmt = wb.add_format({"italic": True, "font_color": "#666666"})

    # --- Sheet 1: Ringkasan Keuangan ---
    ws1 = wb.add_worksheet("Ringkasan Keuangan")
    ws1.set_column("A:A", 30)
    ws1.set_column("B:B", 20)
    ws1.write(0, 0, store_name, title_fmt)
    ws1.write(1, 0, f"Periode: {date_from} s/d {date_to}", subtitle_fmt)

    row = 3
    for label, value in [
        ("Total Penjualan", total_revenue),
        ("  - Cash", cash_total),
        ("  - QRIS", qris_total),
        ("  - Lainnya", other_total),
        ("Total Pengeluaran", total_expense),
        ("Laba Bersih (estimasi)", total_revenue - total_expense),
        ("Jumlah Transaksi", len(sales)),
    ]:
        ws1.write(row, 0, label, bold_fmt if "Total" in label or "Laba" in label else text_fmt)
        ws1.write(row, 1, value, currency_fmt)
        row += 1

    # --- Sheet 2: Rekap Penjualan Menu ---
    ws2 = wb.add_worksheet("Rekap Penjualan Menu")
    ws2.set_column("A:A", 35)
    ws2.set_column("B:C", 18)
    for i, h in enumerate(["Menu", "Qty Terjual", "Revenue (Rp)"]):
        ws2.write(0, i, h, header_fmt)
    for idx, r in enumerate(menu_sales, 1):
        ws2.write(idx, 0, r.menu_name, text_fmt)
        ws2.write(idx, 1, r.qty, text_fmt)
        ws2.write(idx, 2, r.revenue, currency_fmt)

    # --- Sheet 3: Detail Belanja ---
    ws3 = wb.add_worksheet("Detail Belanja")
    ws3.set_column("A:A", 15)
    ws3.set_column("B:B", 35)
    ws3.set_column("C:C", 18)
    ws3.set_column("D:D", 25)
    for i, h in enumerate(["Tanggal", "Item", "Harga (Rp)", "Catatan"]):
        ws3.write(0, i, h, header_fmt)
    for idx, e in enumerate(expenses, 1):
        ws3.write(idx, 0, str(e.purchase_date) if e.purchase_date else "", text_fmt)
        ws3.write(idx, 1, e.item_name, text_fmt)
        ws3.write(idx, 2, e.price, currency_fmt)
        ws3.write(idx, 3, e.note or "", text_fmt)

    wb.close()
    output.seek(0)

    filename = f"laporan_{store_name}_{date_from}_{date_to}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
