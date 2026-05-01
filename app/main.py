from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import auth, analyze, products, cabinet

app = FastAPI(
    title="Furniture AR Recommendations API",
    description="Інтелектуальна система рекомендацій меблів з AR-візуалізацією",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
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
    return {"status": "ok", "message": "Furniture AR API is running "}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}