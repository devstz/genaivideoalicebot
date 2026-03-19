"""Pydantic schemas for pack API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class PackRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    generations_count: int
    price: float
    prices_by_currency: Optional[dict[str, Any]] = None
    icon: str = "payments"
    is_active: bool = True
    is_bestseller: bool = False
    lava_offer_id: Optional[str] = None
    created_at: Optional[datetime] = None


class PackCreate(BaseModel):
    name: str
    description: Optional[str] = None
    generations_count: int
    price: float = Field(description="Цена в RUB для mock; при Lava перезаписывается из каталога")
    prices_by_currency: Optional[dict[str, float]] = None
    icon: str = "payments"
    is_active: bool = True
    is_bestseller: bool = False
    lava_offer_id: Optional[str] = None


class PackUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    generations_count: Optional[int] = None
    price: Optional[float] = None
    prices_by_currency: Optional[dict[str, float]] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    is_bestseller: Optional[bool] = None
    lava_offer_id: Optional[str] = None
