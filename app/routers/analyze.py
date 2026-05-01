import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db, sessionmanager  # припускаємо, що у вас є доступ до фабрики сесій
from app.config import settings
from app.models.user import User
from app.models.room_scan import RoomScan, ScanStatus
from app.schemas.room_scan import AnalyzeResponse, ScanStatusOut
from app.core.dependencies import get_current_user
from app.services.color_extractor import extract_palette
from app.services.style_detector import detect_style
from app.services.recommender import get_recommendations, save_recommendations
from app.services.storage import upload_room_image

router = APIRouter(prefix="/analyze", tags=["Analyze"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def run_deep_analysis(scan_id: uuid.UUID, image_bytes: bytes):
    """
    Фонова функція для аналізу зображення.
    Вона працює окремо від основного запиту.
    """
    # Створюємо окрему сесію для фонового завдання
    async with sessionmanager.session() as db:
        result = await db.execute(select(RoomScan).where(RoomScan.id == scan_id))
        scan = result.scalar_one_or_none()
        if not scan:
            return

        try:
            # 1. Витягуємо колірну палітру
            palette = extract_palette(image_bytes, n_colors=5)

            # 2. Визначаємо стиль (YOLOv8)
            try:
                # В сервісі detect_style ОБОВ'ЯЗКОВО поставте imgsz=320
                detected_style = detect_style(image_bytes)
            except Exception:
                detected_style = "Modern"  # Fallback для стабільності

            # 3. Отримуємо рекомендації
            products = await get_recommendations(db, style=detected_style, limit=12)

            # 4. Оновлюємо статус та дані
            scan.color_palette = palette
            scan.detected_style = detected_style
            scan.status = ScanStatus.DONE

            # 5. Зберігаємо рекомендації в проміжну таблицю
            await save_recommendations(db, scan=scan, products=products)

            await db.commit()

        except Exception as e:
            print(f"Background analysis error: {e}")
            scan.status = ScanStatus.ERROR
            await db.commit()


@router.post("/", response_model=ScanStatusOut)
async def analyze_room(
        background_tasks: BackgroundTasks,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    # 1. Валідація
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Підтримуються тільки: {', '.join(ALLOWED_CONTENT_TYPES)}",
        )

    image_bytes = await file.read()
    if len(image_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Файл занадто великий",
        )

    # 2. Завантаження фото в хмару (Cloudinary/S3)
    filename = str(uuid.uuid4())
    image_url = await upload_room_image(image_bytes, filename)

    # 3. Створюємо запис у БД зі статусом PROCESSING
    scan = RoomScan(
        user_id=current_user.id,
        image_path=image_url,
        status=ScanStatus.PROCESSING,
    )
    db.add(scan)
    await db.commit()  # Фіксуємо негайно, щоб статус був доступний для GET
    await db.refresh(scan)

    # 4. Додаємо важкий аналіз у чергу фонових завдань
    # Це дозволяє FastAPI відразу повернути відповідь 200 OK
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
    # Отримуємо результат аналізу
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