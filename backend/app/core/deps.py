"""Dependency injection untuk FastAPI routes."""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import decode_token
from app.models.user import User, UserRole
from app.models.tenant import Tenant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau kadaluarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id), User.is_active == True).first()
    if not user:
        raise credentials_exception
    return user


def get_current_tenant(current_user: User = Depends(get_current_user)) -> Optional[int]:
    """Return tenant_id dari user aktif (None jika superadmin)."""
    return current_user.tenant_id


def resolve_tenant_id(current_user: User, db: Session) -> int:
    """
    Tenant_id yang dipakai user ini buat operasi tenant-scoped.

    - User biasa: tenant_id dari row mereka.
    - Superadmin (tenant_id = None): fallback ke tenant pertama di DB.
      Kalau belum ada tenant sama sekali, auto-create "Demo Cafe" biar
      superadmin tetap bisa operasional tanpa harus setup tenant dulu.
    """
    if current_user.tenant_id is not None:
        return current_user.tenant_id

    tenant = db.query(Tenant).order_by(Tenant.id).first()
    if tenant is None:
        tenant = Tenant(
            name="Demo Cafe",
            slug="demo",
            plan="basic",
            timezone="Asia/Jakarta",
            currency="IDR",
            features={"whatsapp": False, "ai": True, "multi_outlet": False},
        )
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    return tenant.id


def get_active_tenant_id(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> int:
    """FastAPI dep bungkus resolve_tenant_id buat dipakai via Depends()."""
    return resolve_tenant_id(current_user, db)


# --- Role Guards ---

def require_roles(*roles: UserRole):
    """Factory: buat dependency yang check role."""
    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in [r.value for r in roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Akses ditolak. Role dibutuhkan: {[r.value for r in roles]}",
            )
        return current_user
    return _checker


# Shorthand
require_superadmin = require_roles(UserRole.SUPERADMIN)
require_admin = require_roles(UserRole.SUPERADMIN, UserRole.ADMIN)
require_manager = require_roles(UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.MANAGER)
require_kasir = require_roles(
    UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.MANAGER, UserRole.KASIR
)
require_inventory = require_roles(
    UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.MANAGER, UserRole.INVENTORY
)
require_dapur = require_roles(
    UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.MANAGER, UserRole.DAPUR
)
require_waiter = require_roles(
    UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.MANAGER, UserRole.WAITER
)
require_station = require_roles(
    UserRole.SUPERADMIN, UserRole.ADMIN, UserRole.MANAGER,
    UserRole.KASIR, UserRole.DAPUR, UserRole.WAITER
)


def get_tenant_filter(current_user: User = Depends(get_current_user)) -> Optional[int]:
    """
    Superadmin bisa lihat semua (return None).
    User biasa hanya lihat tenant sendiri.
    """
    if current_user.role == UserRole.SUPERADMIN:
        return None  # no filter
    return current_user.tenant_id


def apply_tenant_filter(query, model, tenant_id: Optional[int]):
    """Helper untuk apply tenant filter ke query SQLAlchemy."""
    if tenant_id is not None:
        query = query.filter(model.tenant_id == tenant_id)
    return query
