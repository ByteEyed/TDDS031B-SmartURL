import secrets
import string
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.database.models import URL
from app.schemas.url import URLCreate, URLUpdate

# Fixed URL-safe alphabet: a-z, A-Z, 0-9
ALPHABET = string.ascii_letters + string.digits


def generate_random_short_code(length: int = 6) -> str:
    """Generate a random URL-safe short code of fixed length using Python's secrets module."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def create_url(db: Session, url_in: URLCreate, user_id: int) -> URL:
    """Create a new short URL with custom alias or generated short code."""
    if url_in.custom_alias:
        # Check if custom alias is already used
        existing = db.execute(
            select(URL).where(URL.short_code == url_in.custom_alias)
        ).scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Custom alias is already in use"
            )
        short_code = url_in.custom_alias
    else:
        # Generate random short code with collision handling
        max_attempts = 10
        for _ in range(max_attempts):
            candidate = generate_random_short_code()
            existing = db.execute(
                select(URL).where(URL.short_code == candidate)
            ).scalar_one_or_none()
            if not existing:
                short_code = candidate
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not generate a unique short code. Please try again."
            )

    new_url = URL(
        original_url=url_in.original_url,
        short_code=short_code,
        user_id=user_id,
        expires_at=url_in.expires_at,
        is_active=True,
        click_count=0
    )
    
    db.add(new_url)
    db.commit()
    db.refresh(new_url)
    return new_url


def get_user_urls(
    db: Session,
    user_id: int,
    page: int = 1,
    limit: int = 10,
    active: Optional[bool] = None
) -> Tuple[List[URL], int]:
    """Retrieve paginated list of URLs owned by the specified user."""
    query = select(URL).where(URL.user_id == user_id)
    
    if active is not None:
        query = query.where(URL.is_active == active)
        
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar_one()
    
    # Apply pagination and sorting
    offset = (page - 1) * limit
    paginated_query = query.order_by(URL.created_at.desc()).offset(offset).limit(limit)
    urls = db.execute(paginated_query).scalars().all()
    
    return list(urls), total


def get_url_by_short_code(db: Session, short_code: str) -> Optional[URL]:
    """Fetch URL record by short_code using SQLAlchemy 2.x select."""
    statement = select(URL).where(URL.short_code == short_code)
    return db.execute(statement).scalar_one_or_none()


def update_url(db: Session, url_obj: URL, url_update: URLUpdate) -> URL:
    """Update URL fields (expires_at, is_active)."""
    if url_update.expires_at is not None or "expires_at" in url_update.model_fields_set:
        url_obj.expires_at = url_update.expires_at
    if url_update.is_active is not None:
        url_obj.is_active = url_update.is_active
        
    db.commit()
    db.refresh(url_obj)
    return url_obj


def delete_url(db: Session, url_obj: URL) -> None:
    """Delete URL record from database."""
    db.delete(url_obj)
    db.commit()


def process_url_redirect(db: Session, short_code: str) -> Tuple[URL, str]:
    """Validate short_code, expiration, and active status for redirection."""
    url_obj = get_url_by_short_code(db, short_code)
    if not url_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short URL not found"
        )
        
    if not url_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Short URL is inactive"
        )
        
    if url_obj.expires_at is not None:
        now = datetime.now(timezone.utc)
        # Ensure comparison is timezone aware
        expires_at = url_obj.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < now:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Short URL has expired"
            )
            
    return url_obj, url_obj.original_url
