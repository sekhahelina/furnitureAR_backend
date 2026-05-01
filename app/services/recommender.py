from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.product import Product
from app.models.room_scan import RoomScan
from app.models.recommendation import Recommendation


async def get_recommendations(
    db: AsyncSession,
    style: str,
    limit: int = 12,
) -> list[Product]:
    """
    Вибирає товари з БД за style_tag.
    """
    result = await db.execute(
        select(Product)
        .where(Product.style_tag == style, Product.in_stock == True)
        .order_by(Product.price)
        .limit(limit)
    )
    return list(result.scalars().all())


async def save_recommendations(
    db: AsyncSession,
    scan: RoomScan,
    products: list[Product],
) -> None:
    """
    Зберігає зв'язки між скан-ом та рекомендованими товарами в БД.
    """
    for product in products:
        recommendation = Recommendation(
            scan_id=scan.id,
            product_id=product.id,
            score=None,  # Резерв для ML-ранжування
        )
        db.add(recommendation)
    await db.flush()
