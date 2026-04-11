"""
AI & Agentic endpoints.
Kompatibel dengan OpenAI function calling format.
"""
import time
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import date, timedelta

from app.database import get_db
from app.models.user import User
from app.models.pos import Sale, SaleItem, Expense, MenuItem
from app.models.inventory import Product, StockMovement
from app.models.ai_log import AIQueryLog
from app.core.deps import get_current_user, resolve_tenant_id

router = APIRouter(prefix="/api/v1/ai", tags=["AI & Agents"])


# ======================================================
# 1. Tool Definitions (OpenAI-compatible)
# ======================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_sales_summary",
            "description": "Ambil ringkasan penjualan untuk rentang tanggal tertentu. Bisa untuk hari ini, minggu ini, bulan ini, atau custom range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "format": "date", "description": "Tanggal mulai (YYYY-MM-DD)"},
                    "date_to": {"type": "string", "format": "date", "description": "Tanggal akhir (YYYY-MM-DD)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_menu",
            "description": "Ambil menu terlaris berdasarkan jumlah terjual atau revenue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Berapa hari ke belakang (default 30)"},
                    "limit": {"type": "integer", "description": "Jumlah menu yang dikembalikan (default 10)"},
                    "sort_by": {"type": "string", "enum": ["qty", "revenue"], "description": "Urutkan berdasarkan quantity atau revenue"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_stock",
            "description": "Cek stok produk/bahan baku. Bisa cek semua atau yang low stock.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Nama produk yang dicari (opsional)"},
                    "low_stock_only": {"type": "boolean", "description": "Hanya tampilkan yang stok rendah"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_stock_movement",
            "description": "Tambah atau kurangi stok produk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Nama produk"},
                    "qty_change": {"type": "integer", "description": "Jumlah perubahan stok (positif = masuk, negatif = keluar)"},
                    "transaction_type": {"type": "string", "enum": ["IN", "OUT", "ADJUSTMENT"]},
                    "notes": {"type": "string", "description": "Catatan tambahan"},
                },
                "required": ["product_name", "qty_change", "transaction_type"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_expenses_summary",
            "description": "Ambil ringkasan pengeluaran untuk periode tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "date_from": {"type": "string", "format": "date"},
                    "date_to": {"type": "string", "format": "date"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_business_insights",
            "description": "Dapatkan analisis bisnis otomatis: tren penjualan, rekomendasi stok, perbandingan periode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "enum": ["today", "week", "month"], "description": "Periode analisis"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_sale",
            "description": "Buat transaksi penjualan baru (untuk integrasi chatbot/kasir AI).",
            "parameters": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "menu_name": {"type": "string"},
                                "quantity": {"type": "integer"},
                                "price": {"type": "number"},
                            },
                            "required": ["menu_name", "quantity", "price"],
                        },
                    },
                    "customer_name": {"type": "string"},
                    "table_number": {"type": "string"},
                    "payment_method": {"type": "string", "enum": ["CASH", "TRANSFER", "QRIS", "DEBIT", "CREDIT"]},
                },
                "required": ["items"],
            },
        },
    },
]


# ======================================================
# 2. Endpoints
# ======================================================

@router.get("/tools")
def get_tools():
    """
    Return definisi semua tools dalam format OpenAI function calling.
    Endpoint ini untuk agent eksternal yang mau tahu apa yang bisa dilakukan.
    """
    return {
        "tools": TOOL_DEFINITIONS,
        "version": "2.0.0",
        "description": "POS-AI SaaS Tool Registry",
    }


class ToolCallRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}


class AgentQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    source: str = "api"


@router.post("/execute")
def execute_tool(
    body: ToolCallRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Eksekusi tool call langsung (untuk agentic framework).
    Agent bisa call ini setelah decide tool dari /ai/tools.
    """
    tid = resolve_tenant_id(current_user, db)
    start = time.time()
    result = _dispatch_tool(body.tool_name, body.arguments, tid, current_user, db)
    latency = int((time.time() - start) * 1000)

    # Log
    log = AIQueryLog(
        tenant_id=tid,
        user_id=current_user.id,
        query_text=f"TOOL:{body.tool_name}",
        tool_called=body.tool_name,
        tool_args=body.arguments,
        response_text=str(result)[:500],
        latency_ms=latency,
        source="api",
    )
    db.add(log)
    db.commit()

    return {"tool": body.tool_name, "result": result, "latency_ms": latency}


@router.get("/context")
def get_business_context(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Berikan konteks bisnis lengkap untuk AI agent.
    Agent bisa inject ini ke system prompt.
    """
    tid = resolve_tenant_id(current_user, db)
    today = date.today()
    first_of_month = today.replace(day=1)

    today_rev = db.query(func.sum(Sale.final_amount)).filter(
        Sale.tenant_id == tid,
        func.date(Sale.transaction_date) == today,
        Sale.status == "COMPLETED",
    ).scalar() or 0

    month_rev = db.query(func.sum(Sale.final_amount)).filter(
        Sale.tenant_id == tid,
        func.date(Sale.transaction_date) >= first_of_month,
        Sale.status == "COMPLETED",
    ).scalar() or 0

    low_stock = db.query(Product).filter(
        Product.tenant_id == tid,
        Product.current_stock <= Product.min_stock_level,
    ).count()

    menu_count = db.query(MenuItem).filter(
        MenuItem.tenant_id == tid,
        MenuItem.is_available == True,
    ).count()

    return {
        "tenant_id": tid,
        "date": str(today),
        "metrics": {
            "revenue_today": today_rev,
            "revenue_this_month": month_rev,
            "low_stock_items": low_stock,
            "active_menu_count": menu_count,
        },
        "available_tools": [t["function"]["name"] for t in TOOL_DEFINITIONS],
        "system_prompt_hint": (
            f"Kamu adalah AI assistant untuk sistem POS-AI SaaS. "
            f"Hari ini tanggal {today}. Revenue hari ini: Rp {today_rev:,.0f}. "
            f"Ada {low_stock} produk dengan stok rendah. "
            f"Gunakan tools yang tersedia untuk membantu operasional toko."
        ),
    }


@router.get("/logs")
def get_ai_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Riwayat semua AI query untuk audit."""
    tid = resolve_tenant_id(current_user, db)
    logs = db.query(AIQueryLog).filter(
        AIQueryLog.tenant_id == tid
    ).order_by(AIQueryLog.created_at.desc()).limit(limit).all()
    return logs


# ======================================================
# 3. Tool Dispatcher (internal)
# ======================================================

def _dispatch_tool(tool_name: str, args: dict, tenant_id: int, user: User, db: Session) -> Any:
    today = date.today()

    if tool_name == "get_sales_summary":
        date_from = args.get("date_from", str(today))
        date_to = args.get("date_to", str(today))
        return _tool_sales_summary(tenant_id, date_from, date_to, db)

    elif tool_name == "get_top_menu":
        days = args.get("days", 30)
        limit = args.get("limit", 10)
        sort_by = args.get("sort_by", "revenue")
        return _tool_top_menu(tenant_id, days, limit, sort_by, db)

    elif tool_name == "check_stock":
        return _tool_check_stock(tenant_id, args.get("product_name"), args.get("low_stock_only", False), db)

    elif tool_name == "add_stock_movement":
        return _tool_add_stock(tenant_id, args, user, db)

    elif tool_name == "get_expenses_summary":
        date_from = args.get("date_from", str(today.replace(day=1)))
        date_to = args.get("date_to", str(today))
        return _tool_expenses_summary(tenant_id, date_from, date_to, db)

    elif tool_name == "get_business_insights":
        return _tool_business_insights(tenant_id, args.get("period", "today"), db)

    elif tool_name == "create_sale":
        return _tool_create_sale(tenant_id, args, user, db)

    else:
        raise HTTPException(status_code=400, detail=f"Tool '{tool_name}' tidak dikenal")


def _tool_sales_summary(tenant_id, date_from, date_to, db):
    rows = db.query(
        func.sum(Sale.final_amount).label("revenue"),
        func.count(Sale.id).label("count"),
        func.avg(Sale.final_amount).label("avg"),
    ).filter(
        Sale.tenant_id == tenant_id,
        func.date(Sale.transaction_date) >= date_from,
        func.date(Sale.transaction_date) <= date_to,
        Sale.status == "COMPLETED",
    ).first()
    return {
        "period": {"from": date_from, "to": date_to},
        "total_revenue": round(rows.revenue or 0, 2),
        "transaction_count": rows.count or 0,
        "average_transaction": round(rows.avg or 0, 2),
    }


def _tool_top_menu(tenant_id, days, limit, sort_by, db):
    date_from = date.today() - timedelta(days=days)
    order_col = func.sum(SaleItem.subtotal) if sort_by == "revenue" else func.sum(SaleItem.quantity)

    rows = db.query(
        SaleItem.menu_name,
        func.sum(SaleItem.quantity).label("qty"),
        func.sum(SaleItem.subtotal).label("revenue"),
    ).join(Sale).filter(
        Sale.tenant_id == tenant_id,
        func.date(Sale.transaction_date) >= date_from,
        Sale.status == "COMPLETED",
    ).group_by(SaleItem.menu_name).order_by(order_col.desc()).limit(limit).all()

    return [{"name": r.menu_name, "qty_sold": r.qty, "revenue": round(r.revenue, 2)} for r in rows]


def _tool_check_stock(tenant_id, product_name, low_stock_only, db):
    q = db.query(Product).filter(Product.tenant_id == tenant_id)
    if product_name:
        q = q.filter(Product.name.ilike(f"%{product_name}%"))
    if low_stock_only:
        q = q.filter(Product.current_stock <= Product.min_stock_level)
    products = q.all()
    return [
        {
            "id": p.id, "name": p.name, "sku": p.sku,
            "current_stock": p.current_stock, "unit": p.unit,
            "min_stock": p.min_stock_level, "status": "LOW" if p.current_stock <= p.min_stock_level else "OK"
        }
        for p in products
    ]


def _tool_add_stock(tenant_id, args, user, db):
    import uuid
    product = db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.name.ilike(f"%{args['product_name']}%"),
    ).first()
    if not product:
        return {"error": f"Produk '{args['product_name']}' tidak ditemukan"}

    product.current_stock += args["qty_change"]
    if product.current_stock < 0:
        return {"error": "Stok tidak boleh negatif"}

    db.add(StockMovement(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        product_id=product.id,
        qty_change=args["qty_change"],
        balance_after=product.current_stock,
        transaction_type=args["transaction_type"],
        source="AI",
        raw_input_text=args.get("notes"),
        created_by=f"ai:{user.username}",
    ))
    db.commit()
    return {"success": True, "product": product.name, "new_stock": product.current_stock}


def _tool_expenses_summary(tenant_id, date_from, date_to, db):
    row = db.query(
        func.sum(Expense.price).label("total"),
        func.count(Expense.id).label("count"),
    ).filter(
        Expense.tenant_id == tenant_id,
        Expense.purchase_date >= date_from,
        Expense.purchase_date <= date_to,
    ).first()
    return {"period": {"from": date_from, "to": date_to}, "total": row.total or 0, "count": row.count or 0}


def _tool_business_insights(tenant_id, period, db):
    today = date.today()
    if period == "today":
        date_from = today
    elif period == "week":
        date_from = today - timedelta(days=7)
    else:
        date_from = today.replace(day=1)

    sales = _tool_sales_summary(tenant_id, str(date_from), str(today), db)
    top_menu = _tool_top_menu(tenant_id, (today - date_from).days + 1, 5, "revenue", db)
    low_stock = _tool_check_stock(tenant_id, None, True, db)

    insights = []
    if sales["transaction_count"] == 0:
        insights.append("Belum ada transaksi hari ini.")
    if low_stock:
        items = ", ".join(i["name"] for i in low_stock[:3])
        insights.append(f"Stok rendah: {items}. Segera lakukan pembelian.")
    if top_menu:
        insights.append(f"Menu terlaris: {top_menu[0]['name']} (Rp {top_menu[0]['revenue']:,.0f}).")

    return {
        "period": period,
        "summary": sales,
        "top_menu": top_menu,
        "low_stock_alerts": low_stock,
        "insights": insights,
    }


def _tool_create_sale(tenant_id, args, user, db):
    import uuid as _uuid
    from datetime import datetime
    items_in = args.get("items", [])
    if not items_in:
        return {"error": "Tidak ada item transaksi"}

    total = sum(i["quantity"] * i["price"] for i in items_in)
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    sale = Sale(
        tenant_id=tenant_id,
        transaction_code=f"AI-{tenant_id}-{ts}",
        total_amount=total,
        final_amount=total,
        customer_name=args.get("customer_name"),
        table_number=args.get("table_number"),
        payment_method=args.get("payment_method", "CASH"),
        cashier_id=user.id,
    )
    db.add(sale)
    db.flush()

    for item in items_in:
        db.add(SaleItem(
            sale_id=sale.id,
            menu_name=item["menu_name"],
            quantity=item["quantity"],
            price_at_moment=item["price"],
            subtotal=item["quantity"] * item["price"],
        ))

    db.commit()
    return {"success": True, "transaction_code": sale.transaction_code, "total": total}
