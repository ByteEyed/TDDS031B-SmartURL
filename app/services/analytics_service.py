from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.models import ClickEvent, URL
from app.schemas.analytics import ClickEventResponse, URLAnalyticsResponse


def record_click_event(
    db: Session,
    url_obj: URL,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    referrer: Optional[str] = None
) -> ClickEvent:
    """Increment URL click_count and record a ClickEvent entry for analytics."""
    # Increment total click count counter
    url_obj.click_count += 1
    
    # Create individual ClickEvent record
    click_event = ClickEvent(
        url_id=url_obj.id,
        timestamp=datetime.now(timezone.utc),
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )
    
    db.add(click_event)
    db.commit()
    db.refresh(click_event)
    return click_event


def get_url_analytics(db: Session, url_obj: URL, limit: int = 10) -> URLAnalyticsResponse:
    """Fetch total clicks, last click timestamp, and recent click events for a URL."""
    # Fetch recent click events ordered by timestamp descending
    statement = (
        select(ClickEvent)
        .where(ClickEvent.url_id == url_obj.id)
        .order_by(ClickEvent.timestamp.desc())
        .limit(limit)
    )
    recent_events = db.execute(statement).scalars().all()
    
    last_clicked_at = recent_events[0].timestamp if recent_events else None
    
    recent_clicks_schema = [
        ClickEventResponse(
            timestamp=event.timestamp,
            ip_address=event.ip_address,
            user_agent=event.user_agent,
            referrer=event.referrer
        )
        for event in recent_events
    ]
    
    return URLAnalyticsResponse(
        short_code=url_obj.short_code,
        total_clicks=url_obj.click_count,
        created_at=url_obj.created_at,
        last_clicked_at=last_clicked_at,
        recent_clicks=recent_clicks_schema
    )
