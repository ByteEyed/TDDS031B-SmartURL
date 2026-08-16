from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    """Schema for health check endpoint status."""
    status: str
    database: str
