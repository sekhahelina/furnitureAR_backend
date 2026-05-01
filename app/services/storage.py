import cloudinary
import cloudinary.uploader
from app.config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


async def upload_room_image(image_bytes: bytes, filename: str) -> str:
    """
    Завантажує фото кімнати на Cloudinary.
    Повертає публічний URL зображення.
    """
    result = cloudinary.uploader.upload(
        image_bytes,
        folder="furniture-ar/rooms",
        public_id=filename.replace(".", "_"),
        resource_type="image",
        transformation=[
            {"width": 1200, "height": 900, "crop": "limit"},  # максимальний розмір
            {"quality": "auto"},                                # авто-оптимізація
            {"fetch_format": "auto"},                           # авто webp/avif
        ],
    )
    return result["secure_url"]