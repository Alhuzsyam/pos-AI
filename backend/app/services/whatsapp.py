"""
WhatsApp notification service via WAHA API.
Kirim notif stok habis + ringkasan harian ke group WA.
"""
import httpx
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models.tenant_settings import TenantSettings
from app.models.inventory import Product
from app.models.pos import Sale, SaleItem, Expense
from app.models.tenant import Tenant


async def send_whatsapp_message(waha_url: str, api_key: str, session: str, chat_id: str, text: str):
    """Kirim pesan teks ke WhatsApp via WAHA API."""
    async with httpx.AsyncClient(timeout=30) as client:
        res = await client.post(
            f"{waha_url}/api/sendText",
            headers={"X-Api-Key": api_key} if api_key else {},
            json={
                "session": session,
                "chatId": chat_id,
                "text": text,
            }
        )
        res.raise_for_status()
        return res.json()


def build_daily_report(tenant_id: int, db: Session) -> str:
    """Build pesan laporan harian + alert stok rendah."""
    today = date.today()
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    store_name = tenant.name if tenant else "Toko"

    # Ambil settings untuk target omzet
    settings = db.query(TenantSettings).filter(TenantSettings.tenant_id == tenant_id).first()
    target_daily = (settings.target_daily_revenue or 0) if settings else 0

    # Revenue hari ini
    today_revenue = db.query(func.sum(Sale.final_amount)).filter(
        Sale.tenant_id == tenant_id,
        func.date(Sale.transaction_date) == today,
        Sale.status == "COMPLETED",
    ).scalar() or 0

    trx_count = db.query(func.count(Sale.id)).filter(
        Sale.tenant_id == tenant_id,
        func.date(Sale.transaction_date) == today,
        Sale.status == "COMPLETED",
    ).scalar() or 0

    # Top menu hari ini
    top_menu = db.query(
        SaleItem.menu_name,
        func.sum(SaleItem.quantity).label("qty"),
    ).join(Sale).filter(
        Sale.tenant_id == tenant_id,
        func.date(Sale.transaction_date) == today,
        Sale.status == "COMPLETED",
    ).group_by(SaleItem.menu_name).order_by(
        func.sum(SaleItem.quantity).desc()
    ).limit(5).all()

    # Pengeluaran hari ini
    today_expense = db.query(func.sum(Expense.price)).filter(
        Expense.tenant_id == tenant_id,
        Expense.purchase_date == today,
    ).scalar() or 0

    # Low stock items
    low_stock = db.query(Product).filter(
        Product.tenant_id == tenant_id,
        Product.current_stock <= Product.min_stock_level,
    ).all()

    net_profit = today_revenue - today_expense

    # Build message — skip baris yang nilainya 0
    lines = [
        f"📊 *Laporan Harian - {store_name}*",
        f"📅 {today.strftime('%d/%m/%Y')}",
        "",
    ]

    if trx_count > 0:
        lines.append(f"🧾 *Transaksi:* {trx_count}x")
    if today_revenue > 0:
        lines.append(f"💰 *Revenue:* Rp {today_revenue:,.0f}")
    if today_expense > 0:
        lines.append(f"💸 *Pengeluaran:* Rp {today_expense:,.0f}")
    if net_profit != 0:
        lines.append(f"📈 *Laba Estimasi:* Rp {net_profit:,.0f}")

    # Target capaian
    if target_daily > 0:
        pct = (today_revenue / target_daily) * 100
        pct_capped = min(pct, 100)
        bar_filled = int(pct_capped / 10)
        progress_bar = "█" * bar_filled + "░" * (10 - bar_filled)
        if pct >= 100:
            status_icon = "✅"
            keterangan = "🚀 Target tercapai!"
        elif pct >= 70:
            status_icon = "⚡"
            sisa = target_daily - today_revenue
            keterangan = f"💡 Kurang Rp {sisa:,.0f} lagi"
        else:
            status_icon = "🔴"
            sisa = target_daily - today_revenue
            keterangan = f"💡 Kurang Rp {sisa:,.0f} lagi"
        lines.append(f"🎯 *Target Harian:* Rp {target_daily:,.0f}")
        lines.append(f"   {status_icon} [{progress_bar}] {pct:.1f}%")
        lines.append(f"   {keterangan}")

    if top_menu:
        lines.append("")
        lines.append("🏆 *Top Menu Hari Ini:*")
        for i, m in enumerate(top_menu, 1):
            lines.append(f"  {i}. {m.menu_name} ({m.qty}x)")

    if low_stock:
        lines.append("")
        lines.append("⚠️ *STOK RENDAH - Perlu Dibeli:*")

        # Kelompokkan per divisi secara dinamis
        division_map: dict[str, list] = {}
        for p in low_stock:
            div = (p.division or "Lainnya").strip()
            division_map.setdefault(div, []).append(p)

        div_icons = {"bar": "🍹", "kitchen": "🍳", "snack": "🍿", "titipan": "📦"}
        for div_name, items in division_map.items():
            icon = div_icons.get(div_name.lower(), "📋")
            lines.append(f"  {icon} *{div_name}:*")
            for p in items:
                lines.append(f"    • {p.name}: {p.current_stock}/{p.max_stock_level} {p.unit}")
    else:
        lines.append("")
        lines.append("✅ Semua stok aman!")

    lines.append("")
    lines.append("_Dikirim otomatis oleh POS-AI by Alhuzwiri_")

    return "\n".join(lines)


async def send_scheduled_report(tenant_id: int):
    """Background task: kirim laporan harian ke WA group."""
    db = SessionLocal()
    try:
        settings = db.query(TenantSettings).filter(
            TenantSettings.tenant_id == tenant_id
        ).first()

        if not settings or not settings.whatsapp_notify:
            return

        # Tentukan chat_id: group prioritas, fallback ke personal number
        chat_id = settings.whatsapp_group_id
        if not chat_id:
            if not settings.whatsapp_number:
                return
            number = settings.whatsapp_number.lstrip("+").replace("-", "").replace(" ", "")
            chat_id = f"{number}@c.us"

        message = build_daily_report(tenant_id, db)
        await send_whatsapp_message(
            waha_url=settings.waha_url or "http://localhost:3003",
            api_key=settings.waha_api_key or "",
            session=settings.waha_session or "default",
            chat_id=chat_id,
            text=message,
        )
    except Exception as e:
        print(f"[WhatsApp ERROR] tenant={tenant_id}: {e}")
    finally:
        db.close()
