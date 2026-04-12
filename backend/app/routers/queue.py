"""
Kitchen Display System (KDS) / Watchlist endpoints.
Tiga station: Bar, Kitchen, Waiter.
Flow: PENDING → PREPARED (dapur/bar selesai) → DELIVERED (waiter antarkan) → SERVED
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.pos import Sale, SaleItem, MenuItem
from app.core.deps import get_current_user, require_station, resolve_tenant_id

router = APIRouter(prefix="/api/v1/queue", tags=["Queue / KDS"])


@router.get("/")
def get_queue(
    division: Optional[str] = Query(None, description="Bar | Kitchen | waiter"),
    status: Optional[str] = Query(None, description="PENDING | PREPARED | DELIVERED"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ambil antrian order grouped by sale.
    - Bar/Kitchen station: filter by division, status=PENDING
    - Waiter station: status=PREPARED (siap diantar)
    """
    tid = resolve_tenant_id(current_user, db)

    q = (
        db.query(SaleItem)
        .join(Sale, SaleItem.sale_id == Sale.id)
        .outerjoin(MenuItem, SaleItem.menu_item_id == MenuItem.id)
        .filter(Sale.tenant_id == tid, Sale.status.in_(["COMPLETED", "PENDING"]))
    )

    if division and division.lower() != "waiter":
        q = q.filter(MenuItem.division == division)
    if status:
        q = q.filter(SaleItem.status == status)
    else:
        # Default: show active items (not yet fully served)
        q = q.filter(SaleItem.status.in_(["PENDING", "PREPARED", "DELIVERED"]))

    items = q.order_by(Sale.transaction_date.asc(), SaleItem.id.asc()).all()

    # Group by sale
    grouped = {}
    for item in items:
        sid = item.sale_id
        if sid not in grouped:
            sale = item.sale
            grouped[sid] = {
                "sale_id": sid,
                "transaction_code": sale.transaction_code,
                "customer_name": sale.customer_name,
                "table_number": sale.table_number,
                "created_at": sale.transaction_date.isoformat() if sale.transaction_date else None,
                "items": [],
            }
        grouped[sid]["items"].append({
            "id": item.id,
            "menu_name": item.menu_name,
            "quantity": item.quantity,
            "note": item.note,
            "status": item.status,
            "division": item.menu_item.division if item.menu_item else None,
        })

    return list(grouped.values())


@router.get("/counts")
def queue_counts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Jumlah item per station — untuk badge/counter."""
    tid = resolve_tenant_id(current_user, db)

    base = (
        db.query(SaleItem)
        .join(Sale, SaleItem.sale_id == Sale.id)
        .outerjoin(MenuItem, SaleItem.menu_item_id == MenuItem.id)
        .filter(Sale.tenant_id == tid, Sale.status.in_(["COMPLETED", "PENDING"]))
    )

    bar_pending = base.filter(
        MenuItem.division == "Bar", SaleItem.status == "PENDING"
    ).count()
    kitchen_pending = base.filter(
        MenuItem.division == "Kitchen", SaleItem.status == "PENDING"
    ).count()
    waiter_ready = base.filter(SaleItem.status == "PREPARED").count()

    return {
        "bar": bar_pending,
        "kitchen": kitchen_pending,
        "waiter": waiter_ready,
    }


@router.put("/{item_id}/prepare")
def mark_prepared(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_station),
):
    """Dapur/Bar selesai membuat — item siap diantar."""
    item = _get_sale_item(item_id, current_user, db)
    if item.status != "PENDING":
        raise HTTPException(400, f"Item status {item.status}, harus PENDING")
    item.status = "PREPARED"
    db.commit()
    return {"message": "Item siap diantar", "id": item_id, "status": "PREPARED"}


@router.put("/{item_id}/deliver")
def mark_delivered(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_station),
):
    """Waiter sudah antarkan ke meja."""
    item = _get_sale_item(item_id, current_user, db)
    if item.status != "PREPARED":
        raise HTTPException(400, f"Item status {item.status}, harus PREPARED")
    item.status = "DELIVERED"
    db.commit()
    return {"message": "Item sudah diantar", "id": item_id, "status": "DELIVERED"}


@router.put("/{item_id}/serve")
def mark_served(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_station),
):
    """Item sudah sampai ke customer — final."""
    item = _get_sale_item(item_id, current_user, db)
    if item.status not in ("PREPARED", "DELIVERED"):
        raise HTTPException(400, f"Item status {item.status}, harus PREPARED atau DELIVERED")
    item.status = "SERVED"
    db.commit()
    return {"message": "Item served", "id": item_id, "status": "SERVED"}


@router.put("/order/{sale_id}/prepare-all")
def prepare_all_items(
    sale_id: int,
    division: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_station),
):
    """Tandai semua item PENDING dalam 1 order sebagai PREPARED (batch)."""
    tid = resolve_tenant_id(current_user, db)
    q = (
        db.query(SaleItem)
        .join(Sale)
        .outerjoin(MenuItem, SaleItem.menu_item_id == MenuItem.id)
        .filter(Sale.id == sale_id, Sale.tenant_id == tid, SaleItem.status == "PENDING")
    )
    if division:
        q = q.filter(MenuItem.division == division)

    items = q.all()
    if not items:
        raise HTTPException(404, "Tidak ada item PENDING untuk order ini")

    for item in items:
        item.status = "PREPARED"
    db.commit()
    return {"message": f"{len(items)} item siap diantar", "sale_id": sale_id}


@router.put("/order/{sale_id}/deliver-all")
def deliver_all_items(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_station),
):
    """Tandai semua item PREPARED dalam 1 order sebagai DELIVERED (batch)."""
    tid = resolve_tenant_id(current_user, db)
    items = (
        db.query(SaleItem)
        .join(Sale)
        .filter(Sale.id == sale_id, Sale.tenant_id == tid, SaleItem.status == "PREPARED")
        .all()
    )
    if not items:
        raise HTTPException(404, "Tidak ada item PREPARED untuk order ini")

    for item in items:
        item.status = "DELIVERED"
    db.commit()
    return {"message": f"{len(items)} item diantar", "sale_id": sale_id}


def _get_sale_item(item_id: int, current_user: User, db: Session) -> SaleItem:
    tid = resolve_tenant_id(current_user, db)
    item = (
        db.query(SaleItem)
        .join(Sale)
        .filter(SaleItem.id == item_id, Sale.tenant_id == tid)
        .first()
    )
    if not item:
        raise HTTPException(404, "Sale item tidak ditemukan")
    return item
