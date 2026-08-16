from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db
from app.database.models import User
from app.schemas.analytics import URLAnalyticsResponse
from app.services.analytics_service import get_url_analytics
from app.services.url_service import get_url_by_short_code

router = APIRouter(prefix="/analytics")


@router.get(
    "/{short_code}",
    response_model=URLAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get URL Click Analytics",
    description="Retrieves total click count, last click timestamp, and recent access event details for a short URL."
)
def get_analytics(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Analytics retrieval endpoint (owner only)."""
    url_obj = get_url_by_short_code(db=db, short_code=short_code)
    if not url_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
    if url_obj.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not own this URL"
        )
        
    return get_url_analytics(db=db, url_obj=url_obj)
