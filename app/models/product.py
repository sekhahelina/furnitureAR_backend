import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Numeric, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    style_tag: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Можливі значення: Modern, Loft, Scandi, Classic, Boho, Industrial
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, index=True)
    currency: Mapped[str] = mapped_column(String(10), default="UAH")
    store_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_glb_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_usdz_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="product"
    )
    saved_by: Mapped[list["SavedProduct"]] = relationship(
        "SavedProduct", back_populates="product"
    )
