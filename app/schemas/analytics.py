from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_serializer


class ClickEventResponse(BaseModel):
    """Schema for individual click tracking event."""
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime) -> str:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class URLAnalyticsResponse(BaseModel):
    """Schema for URL analytics details."""
    short_code: str
    total_clicks: int
    created_at: datetime
    last_clicked_at: Optional[datetime] = None
    recent_clicks: List[ClickEventResponse]

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "last_clicked_at")
    def serialize_datetimes(self, dt: Optional[datetime]) -> Optional[str]:
        if dt is None:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
