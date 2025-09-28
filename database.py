"""Database setup and ORM models for PostgreSQL backend.

Uses SQLAlchemy 2.x async API with asyncpg driver and JSONB columns
for flexible storage of nested certificate detail structures.
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Engine & Session
# ---------------------------------------------------------------------------
POSTGRES_URL = os.getenv(
    "POSTGRES_URL",
    os.getenv(
        "DATABASE_URL",  # commonly used
        "postgresql+asyncpg://postgres:12345678@localhost:5432/vehicle_conspicuity",
    ),
)

engine = create_async_engine(POSTGRES_URL, echo=bool(int(os.getenv("SQL_ECHO", "0"))))
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:  # type: ignore
        yield session


# ---------------------------------------------------------------------------
# Base Model
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# ORM Models
# ---------------------------------------------------------------------------
class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(150), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    password_salt: Mapped[bytes] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), index=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    created_users: Mapped[list["UserModel"]] = relationship(remote_side=[id])
    retailer_relationships: Mapped[list["RelationshipModel"]] = relationship(
        back_populates="distributor", foreign_keys="RelationshipModel.distributor_id"
    )
    distributor_relationships: Mapped[list["RelationshipModel"]] = relationship(
        back_populates="retailer", foreign_keys="RelationshipModel.retailer_id"
    )
    certificates: Mapped[list["CertificateModel"]] = relationship(back_populates="retailer")


class RelationshipModel(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint("distributor_id", "retailer_id", name="uq_distributor_retailer"),
        Index("ix_relationship_distributor", "distributor_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    distributor_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    retailer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    distributor: Mapped[UserModel] = relationship(
        "UserModel", foreign_keys=[distributor_id], back_populates="retailer_relationships"
    )
    retailer: Mapped[UserModel] = relationship(
        "UserModel", foreign_keys=[retailer_id], back_populates="distributor_relationships"
    )


class CertificateModel(Base):
    __tablename__ = "certificates"
    __table_args__ = (
        Index("ix_certificate_retailer", "retailer_id"),
        Index("ix_certificate_status", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_no: Mapped[str] = mapped_column(
        String(32), unique=True, default=lambda: f"CERT{str(uuid.uuid4())[:8].upper()}"
    )
    retailer_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"))
    dealer_name: Mapped[str] = mapped_column(String(255))
    dealer_license: Mapped[str] = mapped_column(String(255))
    vehicle_details: Mapped[dict] = mapped_column(JSONB)
    owner_details: Mapped[dict] = mapped_column(JSONB)
    fitment_details: Mapped[dict] = mapped_column(JSONB)
    fitment_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    images: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    retailer: Mapped[UserModel] = relationship("UserModel", back_populates="certificates")


# ---------------------------------------------------------------------------
# Helper query functions (optional convenience)
# ---------------------------------------------------------------------------
async def count_users(session: AsyncSession) -> int:
    result = await session.execute(func.count(UserModel.id))
    return int(result.scalar() or 0)


async def count_certificates(session: AsyncSession) -> int:
    result = await session.execute(func.count(CertificateModel.id))
    return int(result.scalar() or 0)
