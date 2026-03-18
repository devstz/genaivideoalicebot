"""Pydantic schemas for UTM API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UtmCampaignRead(BaseModel):
    id: str
    name: str
    start_code: str
    link: str
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    unique_clicks: int = 0
    registrations: int = 0
    purchases: int = 0
    revenue: float = 0


class UtmCampaignCreate(BaseModel):
    name: str
    start_code: str
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    is_active: bool = True


class UtmCampaignUpdate(BaseModel):
    name: Optional[str] = None
    start_code: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    utm_term: Optional[str] = None
    is_active: Optional[bool] = None


class UtmCampaignListResponse(BaseModel):
    items: list[UtmCampaignRead]
    total: int


class UtmSummaryResponse(BaseModel):
    unique_clicks: int
    new_users: int
    purchases: int
    revenue: float


class UtmStatsResponse(UtmSummaryResponse):
    conversion: float


class UtmSeriesPoint(BaseModel):
    label: str
    full_date: str
    clicks: int
    registrations: int
    purchases: int
    revenue: float


class UtmSeriesResponse(BaseModel):
    items: list[UtmSeriesPoint]


class UtmRegistrationRead(BaseModel):
    user_id: int
    username: Optional[str] = None
    full_name: Optional[str] = None
    created_at: datetime


class UtmRegistrationListResponse(BaseModel):
    items: list[UtmRegistrationRead]
    total: int
