#!/usr/bin/env python3
"""
LumTrails Pricing Service - Main Application

Refactored pricing service with improved architecture:
- Idempotent webhook handling
- Single source of truth for credit granting
- Modular service architecture
- Stripe Checkout Sessions for subscription creation
"""
import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import firebase_admin
from firebase_admin import credentials

from routes import router as pricing_router
from webhooks.handler import router as webhook_router
from cronjob import (
    renew_all_credits,
    renew_free_plan_weekly_credits,
    process_scheduled_account_deletions
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

CET = ZoneInfo("Europe/Paris")


def init_firebase():
    """Initialize Firebase Admin SDK if not already initialized."""
    try:
        firebase_admin.get_app()
        logger.info("Firebase already initialized")
    except ValueError:
        try:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
            logger.info("Firebase initialized with application default credentials")
        except Exception as e:
            logger.warning(f"Firebase initialization with default credentials failed: {e}")
            try:
                firebase_admin.initialize_app()
                logger.info("Firebase initialized without explicit credentials")
            except Exception as e2:
                logger.error(f"All Firebase initialization attempts failed: {e2}")
                raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    init_firebase()
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    environment = os.getenv("ENVIRONMENT", "development")
    logger.info(f"Pricing service starting in {environment} mode (project: {project_id})")
    
    yield
    
    logger.info("Pricing service shutting down")


app = FastAPI(
    title="LumTrails Pricing Service",
    description="Handles subscriptions, billing, and credit management for LumTrails",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        os.getenv("FRONTEND_URL", ""),
        os.getenv("FRONTEND_PROD_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response


app.include_router(pricing_router, prefix="", tags=["Pricing"])
app.include_router(webhook_router, prefix="", tags=["Webhooks"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "LumTrails Pricing Service",
        "status": "healthy",
        "version": "2.0.0",
        "timestamp": datetime.now(CET).isoformat(),
        "timezone": "Europe/Paris (CET)"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    try:
        firebase_admin.get_app()
        firebase_status = "connected"
    except Exception as e:
        firebase_status = f"error: {str(e)}"
    
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    
    return {
        "status": "healthy",
        "firebase": firebase_status,
        "project": project_id,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "timestamp": datetime.now(CET).isoformat(),
        "timezone": "Europe/Paris (CET)"
    }


@app.post("/admin/cron/renew-all-credits")
async def cron_renew_all_credits():
    """
    Cron endpoint for renewing all paid subscription credits.
    Called by Cloud Scheduler monthly.
    """
    result = await renew_all_credits()
    return JSONResponse(
        status_code=200 if result.get("success") else 500,
        content=result
    )


@app.post("/admin/renew-free-tier-credits")
async def cron_renew_free_weekly_credits():
    """
    Cron endpoint for renewing free tier weekly web and PDF scan credits.
    Called by Cloud Scheduler every Monday at 00:00 CET.
    Sets: 40 web scan credits + 2 PDF scan credits
    """
    result = await renew_free_plan_weekly_credits()
    return JSONResponse(
        status_code=200 if result.get("success") else 500,
        content=result
    )


@app.post("/admin/cron/process-deletions")
async def cron_process_deletions():
    """
    Cron endpoint for processing scheduled account deletions.
    Called by Cloud Scheduler daily at 03:00 CET.
    """
    result = await process_scheduled_account_deletions()
    return JSONResponse(
        status_code=200 if result.get("success") else 500,
        content=result
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("ENVIRONMENT") != "production" else "An unexpected error occurred",
            "timestamp": datetime.now(CET).isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8080))
    
    uvicorn.run(
        "main_new:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") != "production"
    )
