from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, JSON
from sqlalchemy.sql import func
from app.database import Base


class AIQueryLog(Base):
    """Log semua query ke AI endpoints - untuk audit & analytics."""
    __tablename__ = "ai_query_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    query_text = Column(Text, nullable=False)
    tool_called = Column(String(100), nullable=True)
    tool_args = Column(JSON, nullable=True)
    response_text = Column(Text, nullable=True)
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    source = Column(String(30), default="api")   # api | whatsapp | webhook

    created_at = Column(DateTime(timezone=True), server_default=func.now())
