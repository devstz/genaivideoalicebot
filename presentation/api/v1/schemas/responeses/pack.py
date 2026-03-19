"""Pydantic schemas for pack API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PackRead(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    generations_count: int
    price: float
    icon: str = "payments"
    is_active: bool = True
    is_bestseller: bool = False
    lava_offer_id: Optional[str] = None
    created_at: Optional[datetime] = None


class PackCreate(BaseModel):
    name: str
    description: Optional[str] = None
    generations_count: int
    price: float
    icon: str = "payments"
    is_active: bool = True
    is_bestseller: bool = False
    lava_offer_id: Optional[str] = None


class PackUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    generations_count: Optional[int] = None
    price: Optional[float] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    is_bestseller: Optional[bool] = None
    lava_offer_id: Optional[str] = None
