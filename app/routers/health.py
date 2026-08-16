from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.dependencies import get_db
from app.schemas.health import HealthCheckResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    summary="API & Database Health Check",
    description="Verifies the operational status of the API and tests active SQLite database connectivity."
)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint performing a light SELECT 1 database ping."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
        overall_status = "healthy"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        overall_status = "unhealthy"
        
    return HealthCheckResponse(
        status=overall_status,
        database=db_status
    )
