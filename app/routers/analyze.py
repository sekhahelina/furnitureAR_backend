import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.room_scan import RoomScan, ScanStatus
from app.schemas.room_scan import AnalyzeResponse, ScanStatusOut
from app.schemas.product import ProductOut
from app.core.dependencies import get_current_user
from app.services.color_extractor import extract_palette
from app.services.style_detector import detect_style
from app.services.recommender import get_recommendations, save_recommendations
from app.services.storage import upload_room_image

router = APIRouter(prefix="/analyze", tags=["Analyze"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/", response_model=AnalyzeResponse)
async def analyze_room(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Валідація типу файлу
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Підтримуються тільки: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    # Читаємо байти
    image_bytes = await file.read()

    # Перевірка розміру
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Файл занадто великий. Максимум {settings.MAX_FILE_SIZE_MB} МБ",
        )


    filename = str(uuid.uuid4())
    image_url = await upload_room_image(image_bytes, filename)

    scan = RoomScan(
        user_id=current_user.id,
        image_path=image_url,  # тепер це повний https:// URL
        status=ScanStatus.PROCESSING,
    )

    db.add(scan)
    await db.flush()
    await db.refresh(scan)

    try:
        # 1. Витягуємо колірну палітру (OpenCV + K-Means)
        palette = extract_palette(image_bytes, n_colors=5)

        # 2. Визначаємо стиль (YOLOv8)
        detected_style = detect_style(image_bytes)

        # 3. Оновлюємо скан
        scan.color_palette = palette
        scan.detected_style = detected_style
        scan.status = ScanStatus.DONE
        await db.flush()

        # 4. Отримуємо рекомендації з БД
        products = await get_recommendations(db, style=detected_style, limit=12)

        # 5. Зберігаємо рекомендації
        await save_recommendations(db, scan=scan, products=products)

        return AnalyzeResponse(
            scan_id=scan.id,
            style=detected_style,
            palette=palette,
            products=[ProductOut.model_validate(p) for p in products],
        )

    except Exception as e:
        scan.status = ScanStatus.ERROR
        await db.flush()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Помилка аналізу: {str(e)}",
        )


@router.get("/status/{scan_id}", response_model=ScanStatusOut)
async def get_scan_status(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RoomScan).where(RoomScan.id == scan_id, RoomScan.user_id == current_user.id)
    )
    scan = result.scalar_one_or_none()

    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Скан не знайдено")

    return ScanStatusOut(
        scan_id=scan.id,
        status=scan.status.value,
        detected_style=scan.detected_style,
        color_palette=scan.color_palette,
    )
