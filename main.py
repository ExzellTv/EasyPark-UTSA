"""
Easy Park UTSA - Smart Parking Management System

This application provides real-time parking spot detection using computer vision
and exposes the data through a REST API and web interface.
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import app.config  # noqa: F401 - Load environment variables first
import app.routers.parking as parking

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown."""
    # Startup
    logger.info("Easy Park UTSA application started")
    yield
    # Shutdown
    logger.info("Easy Park UTSA application shutting down")
    if parking.cap is not None:
        parking.cap.stop()
        logger.info("Video capture stopped")


# Create FastAPI application
app = FastAPI(
    title="Easy Park UTSA",
    description="Smart parking management system with real-time occupancy detection",
    version="1.0.0",
    lifespan=lifespan
)

# --- Handle both cases for static directory ---
root_static = Path(__file__).parent / "static"
app_static = Path(__file__).parent / "app" / "static"

if root_static.is_dir():
    static_dir = root_static
elif app_static.is_dir():
    static_dir = app_static
else:
    logger.error("Static directory not found")
    raise RuntimeError("Static directory not found. Expected at ./static or ./app/static")

logger.info(f"Using static directory: {static_dir}")

# --- Register the parking API routes ---
app.include_router(parking.router)
logger.info("Parking API routes registered")

# --- Mount static files (HTML, CSS, JS) ---
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

