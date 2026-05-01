import uuid
import gc
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.room_scan import RoomScan, ScanStatus
from app.models.recommendation import Recommendation
from app.models.product import Product
from app.schemas.room_scan import ScanStatusOut
from app.core.dependencies import get_current_user
from app.services.color_extractor import extract_palette
from app.services.style_detector import detect_style
from app.services.recommender import get_recommendations, save_recommendations
from app.services.storage import upload_room_image

router = APIRouter(prefix="/analyze", tags=["Analyze"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def run_deep_analysis(scan_id: uuid.UUID, image_bytes: bytes):
    """
    Фонова функція. Ми створюємо НОВУ сесію через AsyncSessionLocal(),
    щоб вона не залежала від життєвого циклу HTTP-запиту.
    """
    async with AsyncSessionLocal() as db:
        try:
            # 1. Знаходимо наш запис
            result = await db.execute(select(RoomScan).where(RoomScan.id == scan_id))
            scan = result.scalar_one_or_none()
            if not scan:
                return

            # 2. Витягуємо колірну палітру
            palette = extract_palette(image_bytes, n_colors=5)
            gc.collect()
            # 3. Визначаємо стиль (YOLOv8)
            try:
                # На локалхості можеш лишити imgsz=640, але для Render краще 320
                detected_style = detect_style(image_bytes)
                gc.collect()
            except Exception as e:
                print(f"Error in YOLO: {e}")
                detected_style = "Modern"

            # 4. Отримуємо рекомендації з бази
            products = await get_recommendations(db, style=detected_style, limit=12)

            # 5. Оновлюємо об'єкт скан
            scan.color_palette = palette
            scan.detected_style = detected_style
            scan.status = ScanStatus.DONE

            # Зберігаємо зв'язки з продуктами
            await save_recommendations(db, scan=scan, products=products)

            # ФІНАЛЬНИЙ КОМІТ
            await db.commit()
            print(f"Successfully analyzed scan {scan_id}")

        except Exception as e:
            print(f"Background process failed: {e}")
            if scan:
                scan.status = ScanStatus.ERROR
                await db.commit()


@router.post("/", response_model=ScanStatusOut)
async def analyze_room(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail="Непідтримуваний тип файлу")

    image_bytes = await file.read()

    # 1. Завантажуємо фото (Cloudinary або локально)
    filename = str(uuid.uuid4())
    image_url = await upload_room_image(image_bytes, filename)

    # 2. Створюємо запис у БД
    scan = RoomScan(
        user_id=current_user.id,
        image_path=image_url,
        status=ScanStatus.PROCESSING,
    )
    db.add(scan)
    await db.commit()  # Комітимо відразу, щоб запис з'явився в БД
    await db.refresh(scan)

    # 3. Запускаємо фонове завдання
    background_tasks.add_task(run_deep_analysis, scan.id, image_bytes)

    return ScanStatusOut(
        scan_id=scan.id,
        status=scan.status.value
    )

@router.get("/status/{scan_id}", response_model=ScanStatusOut)
async def get_scan_status(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # 1. Спершу отримуємо основну інформацію про скан
        result = await db.execute(
            select(RoomScan).where(
                RoomScan.id == scan_id,
                RoomScan.user_id == current_user.id
            )
        )
        scan = result.scalar_one_or_none()

        if not scan:
            raise HTTPException(status_code=404, detail="Скан не знайдено")

        # 2. Якщо аналіз готовий, підтягуємо товари окремим кроком
        recommended_products = []
        if scan.status == ScanStatus.DONE:
            # Використовуємо зв'язок через таблицю рекомендацій
            rec_result = await db.execute(
                select(Recommendation)
                .options(selectinload(Recommendation.product))
                .where(Recommendation.scan_id == scan_id)
            )
            recs = rec_result.scalars().all()
            recommended_products = [r.product for r in recs if r.product]

        return ScanStatusOut(
            scan_id=scan.id,
            status=scan.status.value,
            detected_style=scan.detected_style,
            color_palette=scan.color_palette,
            products=recommended_products
        )

    except Exception as e:
        # Це виведе реальну причину 502 помилки в консоль Render
        print(f"CRITICAL ERROR in get_scan_status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Внутрішня помилка сервера під час отримання статусу"
        )