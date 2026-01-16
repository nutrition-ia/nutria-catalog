from datetime import datetime
from sqlmodel import Field, SQLModel
from uuid import UUID, uuid7


class TimestampMixin(SQLModel):
    """Mixin for created_at and updated_at timestamps"""
    created_at: datetime = Field(default_factory=datetime.timezone.utc, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.timezone.utc, nullable=False)


class UUIDMixin(SQLModel):
    """Mixin for UUID primary key"""
    id: UUID = Field(default_factory=uuid7, primary_key=True, nullable=False)
