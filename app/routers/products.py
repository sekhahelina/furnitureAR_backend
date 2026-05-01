from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.database import get_db
from app.models.product import Product
from app.schemas.product import ProductOut, ProductCreate

router = APIRouter(prefix="/products", tags=["Products"])

VALID_STYLES = ["Modern", "Loft", "Scandi", "Classic", "Boho", "Industrial"]


@router.get("/", response_model=list[ProductOut])
async def list_products(
    style: str | None = Query(None, description="Фільтр за стилем"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Product).where(Product.in_stock == True)

    if style:
        if style not in VALID_STYLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Невідомий стиль. Доступні: {', '.join(VALID_STYLES)}",
            )
        query = query.where(Product.style_tag == style)

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return [ProductOut.model_validate(p) for p in result.scalars().all()]


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не знайдено")

    return ProductOut.model_validate(product)


@router.post("/", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate, db: AsyncSession = Depends(get_db)):
    """Адмін-ендпоінт для додавання товарів у каталог."""
    product = Product(**payload.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    return ProductOut.model_validate(product)
