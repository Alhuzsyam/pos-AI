from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import User, UserRole
from app.models.tenant import Tenant
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token, decode_token
from app.core.deps import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    tenant_slug: str
    role: str = "kasir"


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.username == form.username,
        User.is_active == True
    ).first()

    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
        )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    payload = {"sub": str(user.id), "role": user.role, "tenant_id": user.tenant_id}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)

    tenant_name = None
    if user.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        tenant_name = tenant.name if tenant else None

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": user.id,
            "username": user.username,
            "full_name": user.full_name,
            "role": user.role,
            "tenant_id": user.tenant_id,
            "tenant_name": tenant_name,
        },
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Token bukan refresh token")
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Refresh token tidak valid")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User tidak ditemukan")

    new_payload = {"sub": str(user.id), "role": user.role, "tenant_id": user.tenant_id}
    return TokenResponse(
        access_token=create_access_token(new_payload),
        refresh_token=create_refresh_token(new_payload),
        user={"id": user.id, "username": user.username, "role": user.role},
    )


@router.get("/me")
def me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant_name = None
    tenant_slug = None
    if current_user.tenant_id:
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if tenant:
            tenant_name = tenant.name
            tenant_slug = tenant.slug

    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
        "tenant_id": current_user.tenant_id,
        "tenant_name": tenant_name,
        "tenant_slug": tenant_slug,
    }


@router.post("/change-password")
def change_password(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    old_password = body.get("old_password")
    new_password = body.get("new_password")

    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Password lama salah")

    current_user.password_hash = hash_password(new_password)
    db.commit()
    return {"message": "Password berhasil diubah"}
