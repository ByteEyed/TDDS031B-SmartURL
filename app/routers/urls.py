from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.dependencies import get_current_user, get_db
from app.database.models import User
from app.schemas.url import URLCreate, URLListResponse, URLResponse, URLUpdate
from app.services.analytics_service import record_click_event
from app.services.url_service import (
    create_url,
    delete_url,
    get_url_by_short_code,
    get_user_urls,
    process_url_redirect,
    update_url,
)

# Management router for authenticated URL operations (/api/v1/urls)
router = APIRouter(prefix="/urls")

# Public router for short code redirect endpoint (/{short_code})
redirect_router = APIRouter()


@router.post(
    "",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a short URL",
    description="Shortens a long URL with an optional custom alias and expiration date."
)
def create_short_url(
    url_in: URLCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create short URL endpoint (authenticated)."""
    return create_url(db=db, url_in=url_in, user_id=current_user.id)


@router.get(
    "",
    response_model=URLListResponse,
    status_code=status.HTTP_200_OK,
    summary="List authenticated user's URLs",
    description="Returns a paginated list of short URLs created by the currently authenticated user."
)
def list_urls(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
    active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List user's URLs with pagination and optional active status filtering."""
    urls, total = get_user_urls(
        db=db,
        user_id=current_user.id,
        page=page,
        limit=limit,
        active=active
    )
    return URLListResponse(urls=urls, total=total, page=page, limit=limit)


@router.get(
    "/{short_code}",
    response_model=URLResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve details of a short URL",
    description="Retrieves administrative details of a short URL owned by the authenticated user."
)
def get_url_detail(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve URL detail management endpoint."""
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
    return url_obj


@router.patch(
    "/{short_code}",
    response_model=URLResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a short URL",
    description="Updates expiration date or active state of a short URL owned by the authenticated user."
)
def update_short_url(
    short_code: str,
    url_update: URLUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update URL endpoint."""
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
    return update_url(db=db, url_obj=url_obj, url_update=url_update)


@router.delete(
    "/{short_code}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a short URL",
    description="Deletes a short URL owned by the authenticated user."
)
def delete_short_url(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete URL endpoint."""
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
    delete_url(db=db, url_obj=url_obj)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# -------------------------------------------------------------------
# Public Short URL Redirect Endpoint (GET /{short_code})
# -------------------------------------------------------------------

@redirect_router.get(
    "/{short_code}",
    status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    summary="Public Short URL Redirect",
    description="Public endpoint that redirects visitors to the target original URL and records click analytics."
)
def redirect_to_url(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Public redirect endpoint with validation, click tracking, and 307 redirect."""
    url_obj, target_url = process_url_redirect(db=db, short_code=short_code)
    
    # Extract client metadata safely
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")
    
    # Record click event and update click_count
    record_click_event(
        db=db,
        url_obj=url_obj,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=referrer
    )
    
    return RedirectResponse(url=target_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
