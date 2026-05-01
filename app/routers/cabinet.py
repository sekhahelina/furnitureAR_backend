import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.room_scan import RoomScan
from app.models.recommendation import SavedProduct
from app.models.product import Product
from app.schemas.room_scan import ScanHistoryOut
from app.schemas.product import ProductOut
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/cabinet", tags=["Cabinet"])


@router.get("/history", response_model=list[ScanHistoryOut])
async def get_scan_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Повертає всі скани поточного користувача."""
    result = await db.execute(
        select(RoomScan)
        .where(RoomScan.user_id == current_user.id)
        .order_by(RoomScan.created_at.desc())
    )
    scans = result.scalars().all()
    return [ScanHistoryOut.model_validate(s) for s in scans]


@router.get("/saved", response_model=list[ProductOut])
async def get_saved_products(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Повертає збережені товари користувача."""
    result = await db.execute(
        select(Product)
        .join(SavedProduct, SavedProduct.product_id == Product.id)
        .where(SavedProduct.user_id == current_user.id)
        .order_by(SavedProduct.saved_at.desc())
    )
    products = result.scalars().all()
    return [ProductOut.model_validate(p) for p in products]


@router.post("/saved/{product_id}", status_code=status.HTTP_201_CREATED)
async def save_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Додає товар до збережених."""
    # Перевірка існування товару
    result = await db.execute(select(Product).where(Product.id == product_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не знайдено")

    # Перевірка чи вже збережено
    existing = await db.execute(
        select(SavedProduct).where(
            SavedProduct.user_id == current_user.id,
            SavedProduct.product_id == product_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Товар вже збережено")

    saved = SavedProduct(user_id=current_user.id, product_id=product_id)
    db.add(saved)
    await db.flush()
    return {"message": "Товар збережено"}


@router.delete("/saved/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_saved_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Видаляє товар зі збережених."""
    await db.execute(
        delete(SavedProduct).where(
            SavedProduct.user_id == current_user.id,
            SavedProduct.product_id == product_id,
        )
    )
