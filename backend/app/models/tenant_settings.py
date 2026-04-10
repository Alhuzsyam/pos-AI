"""
Tenant-level settings termasuk API keys untuk AI provider.
Tiap tenant setup sendiri -> subscription model.
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class TenantSettings(Base):
    """One-to-one dengan Tenant. Simpan konfigurasi sensitif per-tenant."""
    __tablename__ = "tenant_settings"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # AI Provider settings (per-tenant)
    ai_provider = Column(String(20), default="openai")  # openai | gemini | groq | ollama
    openai_api_key = Column(String(255), nullable=True)
    gemini_api_key = Column(String(255), nullable=True)
    groq_api_key = Column(String(255), nullable=True)
    ollama_host = Column(String(255), nullable=True)
    ai_model = Column(String(50), default="gpt-4o-mini")

    # Weekly insights
    weekly_insights_enabled = Column(Boolean, default=True)
    last_weekly_insight_at = Column(DateTime(timezone=True), nullable=True)
    last_weekly_insight_text = Column(Text, nullable=True)  # cache

    # Business profile untuk context AI
    business_type = Column(String(50), default="cafe")     # cafe | restaurant | warung | retail
    business_description = Column(Text, nullable=True)
    target_daily_revenue = Column(Integer, default=0)       # target omzet per hari (Rp)

    # Notification
    whatsapp_notify = Column(Boolean, default=False)
    whatsapp_number = Column(String(30), nullable=True)     # nomor untuk kirim weekly report

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class WeeklyInsight(Base):
    """Riwayat weekly insights per tenant."""
    __tablename__ = "weekly_insights"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    week_start = Column(String(10), nullable=False)   # YYYY-MM-DD
    week_end = Column(String(10), nullable=False)

    # Metrics snapshot minggu itu
    metrics = Column(JSON, nullable=True)

    # AI-generated insight
    insight_text = Column(Text, nullable=True)
    action_items = Column(JSON, nullable=True)        # list of actionable steps
    ai_provider_used = Column(String(20), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
