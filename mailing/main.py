#!/usr/bin/env python3
"""
LumTrails Mailing Service - Main Application

FastAPI application for email management with Brevo (SendInBlue) integration.
Handles email verification, welcome emails, subscription notifications, 
account deletion notifications, and newsletter functionality.

SECURITY: This service is internal-only and protected by Cloud Run IAM.
Only authenticated service accounts can invoke endpoints (except /health).
"""
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes import router as mailing_router
from brevo_service import BrevoService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Mailing service starting up...")
    brevo = BrevoService()
    if brevo.is_configured():
        logger.info("Brevo service configured successfully")
    else:
        logger.warning("Brevo service not configured - check BREVO_API_KEY")
    yield
    # Shutdown
    logger.info("Mailing service shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title="LumTrails Mailing Service",
    description="Email management with Brevo integration for verification, notifications, and newsletters",
    version="1.0.0",
    lifespan=lifespan,
    # Disable docs in production for security
    docs_url="/docs" if os.getenv("ENVIRONMENT", "dev") == "dev" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT", "dev") == "dev" else None,
    openapi_url="/openapi.json" if os.getenv("ENVIRONMENT", "dev") == "dev" else None
)

# Configuration - only allow internal service origins (no wildcards for security)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
FRONTEND_PROD_URL = os.getenv("FRONTEND_PROD_URL", "")
FRONTEND_PROD_WWW_URL = os.getenv("FRONTEND_PROD_WWW_URL", "")
MAIN_API_URL = os.getenv("MAIN_API_URL", "")
PRICING_SERVICE_URL = os.getenv("PRICING_SERVICE_URL", "")

# CORS middleware - restricted to known origins only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, FRONTEND_PROD_URL, FRONTEND_PROD_WWW_URL, MAIN_API_URL, PRICING_SERVICE_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include router with all endpoints
app.include_router(mailing_router, tags=["Email"])


@app.get("/")
async def root():
    """Root endpoint - basic service info"""
    return {
        "service": "LumTrails Mailing Service",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - used by Cloud Run for health checks"""
    brevo = BrevoService()
    return {
        "status": "healthy",
        "service": "mailing",
        "version": "1.0.0",
        "brevo_configured": brevo.is_configured()
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
