from typing import Literal, Optional
from pydantic import BaseModel, Field

class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"] = Field(
        ..., description="Current health status of the service"
    )
    redis: Optional[Literal["ok", "unavailable"]] = Field(
        default=None, description="Redis connection status"
    )

class VersionResponse(BaseModel):
    version: str = Field(..., description="Application version from FastAPI.version")
    name: Optional[str] = Field(None, description="Application title from FastAPI.title")