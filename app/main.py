from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.config import settings
from app.database.database import Base, engine
from app.middleware.logging import RequestLoggingMiddleware
from app.routers import analytics, auth, health, urls


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for database initialization."""
    # Clean table initialization at application startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "SmartURL is a RESTful URL shortening API built for academic demonstration. "
        "It features user authentication (JWT + Argon2), URL shortening, custom aliases, "
        "expiration control, status toggling, public redirects, and click analytics."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add custom request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include management API routers under /api/v1
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth.router, prefix=settings.API_V1_STR, tags=["Authentication"])
app.include_router(urls.router, prefix=settings.API_V1_STR, tags=["URL Management"])
app.include_router(analytics.router, prefix=settings.API_V1_STR, tags=["Analytics"])

# Include public redirect router (GET /{short_code} from app.routers.urls)
app.include_router(urls.redirect_router, tags=["Public Redirect"])


@app.get("/", include_in_schema=False)
def root():
    """Root landing endpoint directing users to API documentation."""
    return {
        "message": "Welcome to SmartURL API",
        "documentation": "/docs",
        "health_check": f"{settings.API_V1_STR}/health"
    }
