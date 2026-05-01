import uuid
from datetime import datetime
from pydantic import BaseModel


class ProductOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    style_tag: str
    price: float
    currency: str
    store_url: str | None
    image_url: str | None
    model_glb_path: str | None
    model_usdz_path: str | None
    in_stock: bool

    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    style_tag: str
    price: float
    currency: str = "UAH"
    store_url: str | None = None
    image_url: str | None = None
    model_glb_path: str | None = None
    model_usdz_path: str | None = None
    in_stock: bool = True
