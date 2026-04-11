from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional, List
import uuid

from app.database import get_db
from app.models.user import User
from app.models.inventory import Category, Product, StockMovement
from app.core.deps import (
    get_current_user, require_inventory, require_manager,
    require_admin, resolve_tenant_id,
)

router = APIRouter(prefix="/api/v1/inventory", tags=["Inventory"])


# ==================== CATEGORIES ====================

class CategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None


@router.get("/categories")
def list_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    return db.query(Category).filter(Category.tenant_id == tid).all()


@router.post("/categories", status_code=201)
def create_category(
    body: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inventory),
):
    tid = resolve_tenant_id(current_user, db)
    cat = Category(tenant_id=tid, **body.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


# ==================== PRODUCTS ====================

class ProductCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    category_id: Optional[int] = None
    unit: str = "pcs"
    current_stock: int = 0
    min_stock_level: int = 5
    max_stock_level: int = 100
    cost_price: float = 0.0
    division: Optional[str] = None
    aliases: Optional[list] = []


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    category_id: Optional[int] = None
    unit: Optional[str] = None
    min_stock_level: Optional[int] = None
    max_stock_level: Optional[int] = None
    cost_price: Optional[float] = None
    division: Optional[str] = None
    aliases: Optional[list] = None


@router.get("/products")
def list_products(
    search: Optional[str] = Query(None),
    low_stock: bool = Query(False),
    division: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    q = db.query(Product).filter(Product.tenant_id == tid)

    if search:
        q = q.filter(Product.name.ilike(f"%{search}%"))
    if low_stock:
        q = q.filter(Product.current_stock <= Product.min_stock_level)
    if division:
        q = q.filter(Product.division == division)

    return q.order_by(Product.name).all()


@router.post("/products", status_code=201)
def create_product(
    body: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inventory),
):
    tid = resolve_tenant_id(current_user, db)
    product = Product(tenant_id=tid, **body.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/products/{product_id}")
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    p = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == tid,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    return p


@router.patch("/products/{product_id}")
def update_product(
    product_id: int,
    body: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inventory),
):
    tid = resolve_tenant_id(current_user, db)
    p = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == tid,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(p, field, value)

    db.commit()
    db.refresh(p)
    return p


@router.delete("/products/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    tid = resolve_tenant_id(current_user, db)
    p = db.query(Product).filter(
        Product.id == product_id,
        Product.tenant_id == tid,
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")
    db.delete(p)
    db.commit()


# ==================== STOCK MOVEMENTS ====================

class MovementCreate(BaseModel):
    product_id: int
    qty_change: int
    transaction_type: str   # IN | OUT | ADJUSTMENT
    source: str = "MANUAL"
    raw_input_text: Optional[str] = None


@router.get("/movements")
def list_movements(
    product_id: Optional[int] = Query(None),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tid = resolve_tenant_id(current_user, db)
    q = db.query(StockMovement).filter(StockMovement.tenant_id == tid)
    if product_id:
        q = q.filter(StockMovement.product_id == product_id)
    return q.order_by(StockMovement.created_at.desc()).limit(limit).all()


@router.post("/movements", status_code=201)
def create_movement(
    body: MovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inventory),
):
    tid = resolve_tenant_id(current_user, db)
    product = db.query(Product).filter(
        Product.id == body.product_id,
        Product.tenant_id == tid,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produk tidak ditemukan")

    product.current_stock += body.qty_change
    if product.current_stock < 0:
        raise HTTPException(status_code=400, detail="Stok tidak boleh negatif")

    movement = StockMovement(
        id=str(uuid.uuid4()),
        tenant_id=tid,
        product_id=body.product_id,
        qty_change=body.qty_change,
        balance_after=product.current_stock,
        transaction_type=body.transaction_type,
        source=body.source,
        raw_input_text=body.raw_input_text,
        created_by=current_user.username,
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    return movement
