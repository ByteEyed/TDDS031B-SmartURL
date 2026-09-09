import re
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_serializer, field_validator


class URLCreate(BaseModel):
    """Schema for shortening a new URL."""
    original_url: str = Field(..., max_length=2048, description="Original HTTP or HTTPS URL to shorten")
    custom_alias: Optional[str] = Field(
        None,
        min_length=3,
        max_length=30,
        description="Optional custom short code (3-30 characters, letters, numbers, hyphen, underscore)"
    )
    expires_at: Optional[datetime] = Field(None, description="Optional expiration timestamp (leave null for non-expiring links)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "original_url": "https://fastapi.tiangolo.com/tutorial/",
                "custom_alias": "fastapi-guide"
            }
        }
    )

    @field_validator("original_url")
    @classmethod
    def validate_original_url(cls, v: str) -> str:
        v_stripped = v.strip()
        if not (v_stripped.startswith("http://") or v_stripped.startswith("https://")):
            raise ValueError("URL must start with http:// or https://")
        return v_stripped

    @field_validator("custom_alias")
    @classmethod
    def validate_custom_alias(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_stripped = v.strip()
        if not re.match(r"^[a-zA-Z0-9_-]+$", v_stripped):
            raise ValueError("Custom alias can only contain letters, numbers, hyphens, and underscores")
        return v_stripped


class URLUpdate(BaseModel):
    """Schema for updating URL details (expiration and active status)."""
    expires_at: Optional[datetime] = Field(None, description="Updated expiration timestamp (ISO format)")
    is_active: Optional[bool] = Field(None, description="Activation status toggle")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_active": True
            }
        }
    )


class URLResponse(BaseModel):
    """Schema for returning URL details."""
    id: int
    original_url: str
    short_code: str
    short_url: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None
    is_active: bool
    click_count: int

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context):
        if not self.short_url and self.short_code:
            self.short_url = f"http://127.0.0.1:8000/{self.short_code}"

    @field_serializer("created_at", "expires_at")
    def serialize_datetimes(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class URLListResponse(BaseModel):
    """Paginated list schema for user URLs."""
    urls: List[URLResponse]
    total: int
    page: int
    limit: int
