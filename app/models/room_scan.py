import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base
import enum


class ScanStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"


class RoomScan(Base):
    __tablename__ = "room_scans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_path: Mapped[str] = mapped_column(Text, nullable=False)
    detected_style: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    color_palette: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # JSONB формат: ["#A3B5C1", "#F0EAD6", "#8B7355", "#C4A882", "#6B8E7F"]
    status: Mapped[ScanStatus] = mapped_column(
        SAEnum(ScanStatus), default=ScanStatus.PENDING, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="room_scans")
    recommendations: Mapped[list["Recommendation"]] = relationship(
        "Recommendation", back_populates="scan", cascade="all, delete-orphan"
    )
