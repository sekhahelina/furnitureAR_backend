from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, analyze, products, cabinet

app = FastAPI(
    title="Furniture AR Recommendations API",
    description="Інтелектуальна система рекомендацій меблів з AR-візуалізацією",
    version="1.0.0",
)

# 1. Спочатку визначаємо список дозволених адрес
origins = [
    "https://furniture-ar-pis.netlify.app", # Твій фронтенд на Netlify
    "http://localhost:5173",                # Локальна розробка
    "http://localhost:3000",
]

# Додаємо адреси з налаштувань, якщо вони там є
if hasattr(settings, "ALLOWED_ORIGINS"):
    # Переконуємось, що це список, і додаємо його
    if isinstance(settings.ALLOWED_ORIGINS, list):
        origins.extend(settings.ALLOWED_ORIGINS)

# 2. Додаємо CORS ТІЛЬКИ ОДИН РАЗ
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роутери
app.include_router(auth.router)
app.include_router(analyze.router)
app.include_router(products.router)
app.include_router(cabinet.router)

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Furniture AR API is running"}