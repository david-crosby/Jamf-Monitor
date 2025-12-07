import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.security import validate_secret_key
from app.core.database import init_db
from app.api.routes import devices, settings, auth

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)

logger = logging.getLogger(__name__)
settings_config = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle events for the application.
    Runs on startup and shutdown.
    """
    logger.info(f"Starting {settings_config.app_name}")
    logger.info(f"Environment: {settings_config.environment}")
    
    if not validate_secret_key():
        logger.critical("SECRET_KEY validation failed. Application may be insecure.")
    
    if settings_config.environment == "development":
        logger.info("Initialising development database (SQLite)")
        try:
            await init_db()
            logger.info("Database initialised successfully")
        except Exception as e:
            logger.error(f"Failed to initialise database: {e}")
            logger.warning("Application will continue with in-memory storage")
    
    logger.info(f"API documentation available at /api/{settings_config.api_version}/docs")
    
    yield
    
    logger.info("Shutting down application")


app = FastAPI(
    title=settings_config.app_name,
    version=settings_config.api_version,
    docs_url=f"/api/{settings_config.api_version}/docs",
    redoc_url=f"/api/{settings_config.api_version}/redoc",
    openapi_url=f"/api/{settings_config.api_version}/openapi.json",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=f"/api/{settings_config.api_version}")
app.include_router(devices.router, prefix=f"/api/{settings_config.api_version}")
app.include_router(settings.router, prefix=f"/api/{settings_config.api_version}")


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    return {
        "status": "healthy",
        "service": settings_config.app_name,
        "version": settings_config.api_version,
        "environment": settings_config.environment
    }


@app.get("/")
async def root():
    """
    Root endpoint with API information.
    """
    return {
        "message": f"Welcome to {settings_config.app_name}",
        "version": settings_config.api_version,
        "docs": f"/api/{settings_config.api_version}/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )
