"""
Tenant settings termasuk API key management dan weekly insights.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import date, timedelta, datetime

from app.database import get_db
from app.models.user import User
from app.models.tenant_settings import TenantSettings, WeeklyInsight
from app.models.pos import Sale, SaleItem, Expense
from app.models.inventory import Product
from app.core.deps import get_current_user, require_admin, resolve_tenant_id

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])


# ====================================================
# Schemas
# ====================================================

class SettingsUpdate(BaseModel):
    ai_provider: Optional[str] = None      # openai | gemini | groq | ollama
    openai_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    ollama_host: Optional[str] = None
    ai_model: Optional[str] = None
    weekly_insights_enabled: Optional[bool] = None
    business_type: Optional[str] = None
    business_description: Optional[str] = None
    target_daily_revenue: Optional[int] = None
    whatsapp_notify: Optional[bool] = None
    whatsapp_number: Optional[str] = None
    waha_url: Optional[str] = None
    waha_api_key: Optional[str] = None
    waha_session: Optional[str] = None
    whatsapp_group_id: Optional[str] = None
    whatsapp_schedule_hour: Optional[int] = None
    whatsapp_schedule_minute: Optional[int] = None
    divisions: Optional[list] = None
    watchlist_enabled: Optional[bool] = None
    printer_name: Optional[str] = None
    printer_address: Optional[str] = None


def _mask_key(key: Optional[str]) -> Optional[str]:
    """Sembunyikan sebagian API key untuk response."""
    if not key:
        return None
    return key[:8] + "•" * (len(key) - 12) + key[-4:] if len(key) > 12 else "••••••••"


def _get_or_create_settings(tenant_id: int, db: Session) -> TenantSettings:
    settings = db.query(TenantSettings).filter(TenantSettings.tenant_id == tenant_id).first()
    if not settings:
        settings = TenantSettings(tenant_id=tenant_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


# ====================================================
# Endpoints
# ====================================================

@router.get("/")
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    s = _get_or_create_settings(resolve_tenant_id(current_user, db), db)
    return {
        "ai_provider": s.ai_provider,
        "ai_model": s.ai_model,
        "openai_api_key": _mask_key(s.openai_api_key),
        "gemini_api_key": _mask_key(s.gemini_api_key),
        "groq_api_key": _mask_key(s.groq_api_key),
        "ollama_host": s.ollama_host,
        "has_openai_key": bool(s.openai_api_key),
        "has_gemini_key": bool(s.gemini_api_key),
        "has_groq_key": bool(s.groq_api_key),
        "weekly_insights_enabled": s.weekly_insights_enabled,
        "last_weekly_insight_at": s.last_weekly_insight_at,
        "business_type": s.business_type,
        "business_description": s.business_description,
        "target_daily_revenue": s.target_daily_revenue,
        "whatsapp_notify": s.whatsapp_notify,
        "whatsapp_number": s.whatsapp_number,
        "waha_url": s.waha_url,
        "waha_api_key": _mask_key(s.waha_api_key),
        "has_waha_key": bool(s.waha_api_key),
        "waha_session": s.waha_session,
        "whatsapp_group_id": s.whatsapp_group_id,
        "whatsapp_schedule_hour": s.whatsapp_schedule_hour,
        "whatsapp_schedule_minute": s.whatsapp_schedule_minute,
        "divisions": s.divisions or ["Bar", "Kitchen", "Titipan"],
        "watchlist_enabled": s.watchlist_enabled if s.watchlist_enabled is not None else True,
        "printer_name": s.printer_name,
        "printer_address": s.printer_address,
    }


@router.patch("/")
def update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    s = _get_or_create_settings(resolve_tenant_id(current_user, db), db)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(s, field, value)

    db.commit()
    db.refresh(s)
    return {"message": "Settings disimpan", "ai_provider": s.ai_provider, "has_key": bool(s.openai_api_key or s.gemini_api_key or s.groq_api_key)}


# ====================================================
# WhatsApp Test
# ====================================================

@router.post("/whatsapp/test")
async def test_whatsapp(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Kirim pesan test ke WA group untuk verifikasi koneksi."""
    from app.services.whatsapp import send_whatsapp_message, build_daily_report

    tid = resolve_tenant_id(current_user, db)
    s = _get_or_create_settings(tid, db)

    if not s.whatsapp_group_id:
        raise HTTPException(400, "WhatsApp Group ID belum diset")

    message = build_daily_report(tid, db)
    try:
        await send_whatsapp_message(
            waha_url=s.waha_url or "http://localhost:3000",
            api_key=s.waha_api_key or "",
            session=s.waha_session or "default",
            chat_id=s.whatsapp_group_id,
            text=message,
        )
        return {"message": "Pesan test berhasil dikirim!"}
    except Exception as e:
        raise HTTPException(500, f"Gagal kirim: {str(e)}")


# ====================================================
# Weekly Insights
# ====================================================

@router.get("/insights/weekly")
def get_weekly_insights(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil riwayat weekly insights."""
    tid = resolve_tenant_id(current_user, db)
    insights = db.query(WeeklyInsight).filter(
        WeeklyInsight.tenant_id == tid
    ).order_by(WeeklyInsight.created_at.desc()).limit(limit).all()
    return insights


@router.post("/insights/generate")
async def generate_weekly_insight(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Generate weekly insight on-demand menggunakan API key tenant sendiri."""
    s = _get_or_create_settings(resolve_tenant_id(current_user, db), db)

    has_key = any([s.openai_api_key, s.gemini_api_key, s.groq_api_key])
    is_ollama = (s.ai_provider == "ollama" and s.ollama_host)
    if not has_key and not is_ollama:
        raise HTTPException(
            status_code=400,
            detail="Belum ada API key terkonfigurasi. Pergi ke Settings → AI Settings untuk setup."
        )

    # Collect metrics
    tid = resolve_tenant_id(current_user, db)
    metrics = _collect_metrics(tid, db)

    background_tasks.add_task(
        _generate_insight_background,
        tenant_id=tid,
        settings=s,
        metrics=metrics,
    )

    return {"message": "Generating insight di background... Refresh dalam beberapa detik.", "metrics": metrics}


@router.get("/insights/latest")
def get_latest_insight(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ambil insight terbaru."""
    tid = resolve_tenant_id(current_user, db)
    insight = db.query(WeeklyInsight).filter(
        WeeklyInsight.tenant_id == tid
    ).order_by(WeeklyInsight.created_at.desc()).first()

    if not insight:
        return {"message": "Belum ada insight. Generate dulu dari menu Settings."}

    return insight


# ====================================================
# Internal helpers
# ====================================================

def _collect_metrics(tenant_id: int, db: Session) -> dict:
    today = date.today()
    week_start = today - timedelta(days=7)
    prev_week_start = week_start - timedelta(days=7)

    def revenue_in(d_from, d_to):
        return db.query(func.sum(Sale.final_amount)).filter(
            Sale.tenant_id == tenant_id,
            func.date(Sale.transaction_date) >= d_from,
            func.date(Sale.transaction_date) <= d_to,
            Sale.status == "COMPLETED",
        ).scalar() or 0

    def trx_count(d_from, d_to):
        return db.query(func.count(Sale.id)).filter(
            Sale.tenant_id == tenant_id,
            func.date(Sale.transaction_date) >= d_from,
            func.date(Sale.transaction_date) <= d_to,
            Sale.status == "COMPLETED",
        ).scalar() or 0

    this_week_rev = revenue_in(week_start, today)
    prev_week_rev = revenue_in(prev_week_start, week_start)
    this_week_trx = trx_count(week_start, today)
    prev_week_trx = trx_count(prev_week_start, week_start)

    # Top menu minggu ini
    top_menu = db.query(
        SaleItem.menu_name,
        func.sum(SaleItem.quantity).label("qty"),
        func.sum(SaleItem.subtotal).label("rev"),
    ).join(Sale).filter(
        Sale.tenant_id == tenant_id,
        func.date(Sale.transaction_date) >= week_start,
        Sale.status == "COMPLETED",
    ).group_by(SaleItem.menu_name).order_by(func.sum(SaleItem.subtotal).desc()).limit(5).all()

    # Pengeluaran minggu ini
    expenses = db.query(func.sum(Expense.price)).filter(
        Expense.tenant_id == tenant_id,
        Expense.purchase_date >= week_start,
    ).scalar() or 0

    # Low stock
    low_stock = db.query(Product.name, Product.current_stock, Product.min_stock_level).filter(
        Product.tenant_id == tenant_id,
        Product.current_stock <= Product.min_stock_level,
    ).all()

    rev_growth = ((this_week_rev - prev_week_rev) / prev_week_rev * 100) if prev_week_rev else 0

    return {
        "week_start": str(week_start),
        "week_end": str(today),
        "this_week_revenue": this_week_rev,
        "prev_week_revenue": prev_week_rev,
        "revenue_growth_pct": round(rev_growth, 1),
        "this_week_transactions": this_week_trx,
        "prev_week_transactions": prev_week_trx,
        "this_week_expenses": expenses,
        "net_profit_estimate": this_week_rev - expenses,
        "top_menu": [{"name": r.menu_name, "qty": r.qty, "revenue": r.rev} for r in top_menu],
        "low_stock_items": [{"name": r.name, "stock": r.current_stock, "min": r.min_stock_level} for r in low_stock],
        "avg_daily_revenue": round(this_week_rev / 7, 0),
    }


async def _generate_insight_background(tenant_id: int, settings: TenantSettings, metrics: dict):
    """Generate insight menggunakan API key tenant sendiri."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        # Reload settings in this background session to avoid DetachedInstanceError
        fresh_settings = db.query(TenantSettings).filter(TenantSettings.tenant_id == tenant_id).first()
        if not fresh_settings:
            return
        prompt = _build_insight_prompt(metrics, fresh_settings)
        insight_text, action_items = await _call_ai(fresh_settings, prompt)

        insight = WeeklyInsight(
            tenant_id=tenant_id,
            week_start=metrics["week_start"],
            week_end=metrics["week_end"],
            metrics=metrics,
            insight_text=insight_text,
            action_items=action_items,
            ai_provider_used=fresh_settings.ai_provider,
        )
        db.add(insight)

        # Update cache di settings
        s = db.query(TenantSettings).filter(TenantSettings.tenant_id == tenant_id).first()
        if s:
            s.last_weekly_insight_at = datetime.now()
            s.last_weekly_insight_text = insight_text[:500]

        db.commit()
    except Exception as e:
        print(f"[WeeklyInsight ERROR] tenant={tenant_id}: {e}")
    finally:
        db.close()


def _build_insight_prompt(metrics: dict, settings: TenantSettings) -> str:
    biz = settings.business_type or "cafe/toko"
    target = settings.target_daily_revenue or 0
    desc = settings.business_description or ""

    low_stock_str = ", ".join(f"{i['name']} ({i['stock']} tersisa)" for i in metrics["low_stock_items"]) or "Tidak ada"
    top_menu_str = "\n".join(f"  - {i['name']}: {i['qty']}x terjual, Rp {i['revenue']:,.0f}" for i in metrics["top_menu"]) or "  Tidak ada data"

    return f"""Kamu adalah business advisor AI untuk {biz}. {desc}

DATA MINGGU INI ({metrics['week_start']} s/d {metrics['week_end']}):
- Revenue: Rp {metrics['this_week_revenue']:,.0f} ({'+' if metrics['revenue_growth_pct'] >= 0 else ''}{metrics['revenue_growth_pct']}% vs minggu lalu)
- Transaksi: {metrics['this_week_transactions']}x ({'+' if metrics['this_week_transactions'] >= metrics['prev_week_transactions'] else ''}{metrics['this_week_transactions'] - metrics['prev_week_transactions']} vs minggu lalu)
- Pengeluaran: Rp {metrics['this_week_expenses']:,.0f}
- Estimasi Profit: Rp {metrics['net_profit_estimate']:,.0f}
- Rata-rata per hari: Rp {metrics['avg_daily_revenue']:,.0f}
- Target harian: Rp {target:,.0f}

TOP MENU MINGGU INI:
{top_menu_str}

STOK RENDAH (perlu perhatian):
{low_stock_str}

Berikan analisis bisnis dalam Bahasa Indonesia dengan format:
1. **Ringkasan Performa** - Evaluasi singkat hasil minggu ini
2. **Yang Berjalan Baik** - Hal positif yang perlu dipertahankan
3. **Area yang Perlu Diperbaiki** - Masalah konkret yang terdeteksi
4. **5 Langkah Aksi Minggu Depan** - Rekomendasi spesifik dan actionable untuk meningkatkan bisnis
5. **Tips Cepat** - 1-2 quick win yang bisa langsung dilakukan

Gunakan bahasa yang mudah dipahami pemilik toko kecil. Berikan angka spesifik jika relevan."""


async def _call_ai(settings: TenantSettings, prompt: str) -> tuple[str, list]:
    """Call AI provider menggunakan key milik tenant."""
    provider = settings.ai_provider or "openai"

    try:
        if provider == "openai" and settings.openai_api_key:
            return await _call_openai(settings.openai_api_key, settings.ai_model or "gpt-4o-mini", prompt)

        elif provider == "gemini" and settings.gemini_api_key:
            return await _call_gemini(settings.gemini_api_key, prompt)

        elif provider == "groq" and settings.groq_api_key:
            return await _call_groq(settings.groq_api_key, settings.ai_model or "llama-3.3-70b-versatile", prompt)

        elif provider == "ollama":
            return await _call_ollama(settings.ollama_host or "http://localhost:11434", settings.ai_model or "llama3", prompt)

        else:
            return _fallback_insight(prompt), []

    except Exception as e:
        print(f"AI call error ({provider}): {e}")
        return f"[Error generating insight: {str(e)}]", []


async def _call_openai(api_key: str, model: str, prompt: str) -> tuple[str, list]:
    import httpx
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "Kamu adalah business advisor AI yang ahli di bidang F&B dan retail Indonesia."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500,
                "temperature": 0.7,
            }
        )
        res.raise_for_status()
        data = res.json()
        text = data["choices"][0]["message"]["content"]
        return text, _extract_action_items(text)


async def _call_gemini(api_key: str, prompt: str) -> tuple[str, list]:
    import httpx
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}]}
        )
        res.raise_for_status()
        data = res.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return text, _extract_action_items(text)


async def _call_groq(api_key: str, model: str, prompt: str) -> tuple[str, list]:
    import httpx
    async with httpx.AsyncClient(timeout=60) as client:
        res = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500,
                "temperature": 0.7,
            }
        )
        res.raise_for_status()
        data = res.json()
        text = data["choices"][0]["message"]["content"]
        return text, _extract_action_items(text)


async def _call_ollama(host: str, model: str, prompt: str) -> tuple[str, list]:
    import httpx
    async with httpx.AsyncClient(timeout=120) as client:
        res = await client.post(
            f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False}
        )
        res.raise_for_status()
        text = res.json()["response"]
        return text, _extract_action_items(text)


def _extract_action_items(text: str) -> list:
    """Extract bullet points / numbered items dari AI response."""
    import re
    items = re.findall(r'(?:^|\n)\s*(?:\d+\.|[-•*])\s+(.+)', text)
    return [item.strip() for item in items[:10]]


def _fallback_insight(prompt: str) -> str:
    return "Insight tidak dapat di-generate karena tidak ada API key yang terkonfigurasi. Silakan setup API key di halaman Settings."
