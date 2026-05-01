import uuid
from datetime import datetime
from pydantic import BaseModel
from app.schemas.product import ProductOut
from typing import Optional, List

class AnalyzeResponse(BaseModel):
    scan_id: uuid.UUID
    style: str
    palette: list[str]          # ["#A3B5C1", "#F0EAD6", ...]
    products: list[ProductOut]


class ScanStatusOut(BaseModel):
    scan_id: uuid.UUID
    status: str
    # Додаємо Optional та значення None за замовчуванням
    detected_style: Optional[str] = None
    color_palette: Optional[List[str]] = None
    products: List[ProductOut] = []
    class Config:
        from_attributes = True


class ScanHistoryOut(BaseModel):
    id: uuid.UUID
    image_path: str
    detected_style: str | None
    color_palette: list[str] | None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}
