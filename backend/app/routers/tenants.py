"""Tenant management - hanya superadmin."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
import re

from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User, UserRole
from app.core.deps import require_admin, require_roles, get_current_user
from app.core.security import hash_password

router = APIRouter(prefix="/api/v1/tenants", tags=["Tenants"])


class TenantCreate(BaseModel):
    name: str
    slug: str
    plan: str = "basic"
    address: Optional[str] = None
    phone: Optional[str] = None
    timezone: str = "Asia/Jakarta"
    currency: str = "IDR"
    # Sekaligus buat admin pertama
    admin_username: str
    admin_password: str
    admin_email: Optional[str] = None
    admin_full_name: Optional[str] = None


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    plan: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    features: Optional[dict] = None


def _tenant_to_dict(t: Tenant) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "slug": t.slug,
        "plan": t.plan,
        "is_active": t.is_active,
        "address": t.address,
        "phone": t.phone,
        "timezone": t.timezone,
        "currency": t.currency,
        "features": t.features,
        "created_at": t.created_at,
    }


@router.get("/", response_model=List[dict])
def list_tenants(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    tenants = db.query(Tenant).all()
    result = []
    for t in tenants:
        d = _tenant_to_dict(t)
        d["user_count"] = len(t.users)
        result.append(d)
    return result


@router.post("/", status_code=201)
def create_tenant(
    body: TenantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    slug = re.sub(r"[^a-z0-9-]", "", body.slug.lower().replace(" ", "-"))
    if db.query(Tenant).filter(Tenant.slug == slug).first():
        raise HTTPException(status_code=400, detail=f"Slug '{slug}' sudah dipakai")

    tenant = Tenant(
        name=body.name,
        slug=slug,
        plan=body.plan,
        address=body.address,
        phone=body.phone,
        timezone=body.timezone,
        currency=body.currency,
        features={"whatsapp": False, "ai": True, "multi_outlet": False},
    )
    db.add(tenant)
    db.flush()  # dapat ID

    # Buat admin pertama
    if db.query(User).filter(User.username == body.admin_username).first():
        raise HTTPException(status_code=400, detail="Username admin sudah dipakai")

    admin = User(
        tenant_id=tenant.id,
        username=body.admin_username,
        email=body.admin_email,
        full_name=body.admin_full_name or body.admin_username,
        password_hash=hash_password(body.admin_password),
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()
    db.refresh(tenant)

    return {**_tenant_to_dict(tenant), "admin_created": body.admin_username}


@router.get("/{tenant_id}")
def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant tidak ditemukan")
    return _tenant_to_dict(tenant)


@router.patch("/{tenant_id}")
def update_tenant(
    tenant_id: int,
    body: TenantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant tidak ditemukan")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(tenant, field, value)

    db.commit()
    db.refresh(tenant)
    return _tenant_to_dict(tenant)


@router.delete("/{tenant_id}", status_code=204)
def delete_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPERADMIN)),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant tidak ditemukan")
    db.delete(tenant)
    db.commit()
