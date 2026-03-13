"""Pydantic schemas for template API."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class TemplateRead(BaseModel):
    id: str
    title: str
    description: str
    category: str
    status: str
    image: str
    negativePrompt: Optional[str] = None


class TemplateCreate(BaseModel):
    title: str
    description: str
    category: str
    status: str = "active"
    image: Optional[str] = None
    negativePrompt: Optional[str] = None


class TemplateUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    image: Optional[str] = None
    negativePrompt: Optional[str] = None
