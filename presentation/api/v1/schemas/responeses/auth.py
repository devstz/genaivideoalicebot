"""Response schemas for authentication endpoints."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """Response schema for token issuance."""

    access_token: str = Field(
        ...,
        description="JWT access token for API authentication.",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type, always 'bearer' for JWT tokens.",
    )


class TokenRevokeResponse(BaseModel):
    """Response schema for token revocation."""

    detail: str = Field(
        ...,
        description="Message confirming token revocation.",
    )


class TokenUsageHistoryEntry(BaseModel):
    """Schema for a single token usage history entry."""

    timestamp: float = Field(..., description="Unix timestamp of the usage")
    datetime: str = Field(..., description="ISO format datetime of the usage")
    path: str | None = Field(None, description="API path that was accessed")
    method: str | None = Field(None, description="HTTP method used")
    client_host: str | None = Field(None, description="Client IP address")


class TokenUsageStatsResponse(BaseModel):
    """Response schema for token usage statistics."""

    usage_count: int = Field(..., description="Current production usage count")
    usage_limit: int | None = Field(None, description="Production usage limit if set")
    remaining_uses: int | None = Field(None, description="Remaining production uses if limit is set")
    
    sandbox_usage_count: int = Field(..., description="Current sandbox usage count")
    sandbox_limit: int | None = Field(None, description="Sandbox usage limit if set")
    sandbox_remaining_uses: int | None = Field(None, description="Remaining sandbox uses if limit is set")
    
    total_usage_count: int = Field(..., description="Total usage count (production + sandbox)")
    total_limit: int | None = Field(None, description="Total usage limit if set")
    total_remaining_uses: int | None = Field(None, description="Remaining total uses if limit is set")
    
    history_count: int = Field(..., description="Number of entries in usage history")
    
    # Additional info
    countries: list[str] | None = Field(None, description="Supported countries (production)")
    sandbox_countries: list[str] | None = Field(None, description="Supported countries (sandbox)")
    environment_restriction: str | None = Field(None, description="Environment restriction (e.g. 'sandbox_only', 'production_only')")
    
    last_used_at: datetime | None = Field(None, description="Timestamp of the last usage")
    issued_at: datetime = Field(..., description="Token issuance timestamp")
    expires_at: datetime = Field(..., description="Token expiration timestamp")
    scopes: list[str] = Field(default_factory=list, description="Token scopes")
    roles: list[str] = Field(default_factory=list, description="Token roles")


class TokenUsageHistoryResponse(BaseModel):
    """Response schema for token usage history."""

    entries: list[TokenUsageHistoryEntry] = Field(
        ...,
        description="List of usage history entries, sorted by timestamp (newest first)",
    )
    total: int = Field(..., description="Total number of entries")
    limit: int | None = Field(None, description="Limit applied to the query")
    offset: int = Field(default=0, description="Offset applied to the query")

