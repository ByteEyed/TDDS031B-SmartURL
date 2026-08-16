from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ClickEventResponse(BaseModel):
    """Schema for individual click tracking event."""
    timestamp: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class URLAnalyticsResponse(BaseModel):
    """Schema for URL analytics details."""
    short_code: str
    total_clicks: int
    created_at: datetime
    last_clicked_at: Optional[datetime] = None
    recent_clicks: List[ClickEventResponse]

    model_config = ConfigDict(from_attributes=True)
