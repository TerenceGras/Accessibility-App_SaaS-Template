#!/usr/bin/env python3
"""
LumTrails External API - Main Application

REST API for programmatic access to LumTrails scanning services.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import firebase_admin
from firebase_admin import credentials

# Import routes
from routes.general import router as general_router
from routes.web_scan import router as web_scan_router
from routes.pdf_scan import router as pdf_scan_router
from routes.integrations import router as integrations_router

# Import services
from services.api_key_service import api_key_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Configuration
PORT = int(os.getenv("PORT", 8080))
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", PROJECT_ID)

# Initialize Firebase Admin SDK
try:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': FIREBASE_PROJECT_ID,
        'storageBucket': f'{FIREBASE_PROJECT_ID}.firebasestorage.app'
    })
    logger.info(f"Firebase Admin SDK initialized for project: {FIREBASE_PROJECT_ID}")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
    raise


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting LumTrails External API")
    
    # Cleanup expired API keys on startup
    try:
        cleaned = await api_key_service.cleanup_expired_keys()
        logger.info(f"Cleaned up {cleaned} expired API keys on startup")
    except Exception as e:
        logger.error(f"Error cleaning up expired keys: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down LumTrails External API")


# Initialize FastAPI app
app = FastAPI(
    title="LumTrails External API",
    description="REST API for programmatic access to LumTrails accessibility scanning services",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://lumtrails.com")

# CORS middleware - Use environment-based configuration
if ENVIRONMENT == "production":
    cors_origins = [FRONTEND_URL]
else:
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost",
        FRONTEND_URL
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

# Security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Request size limit middleware (50MB default, PDF endpoint handles 5GB separately)
MAX_REQUEST_SIZE = 50 * 1024 * 1024  # 50MB default

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Skip size check for PDF upload endpoint (handled separately with 5GB limit)
        if request.url.path in ["/pdf-scan", "/pdf-scan/"]:
            return await call_next(request)
        
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return JSONResponse(content={"error": "Request too large"}, status_code=413)
        return await call_next(request)

app.add_middleware(RequestSizeLimitMiddleware)


# Global error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail if isinstance(exc.detail, str) else exc.detail.get("error", "error"),
            "message": exc.detail if isinstance(exc.detail, str) else exc.detail.get("message", str(exc.detail)),
            "details": exc.detail if isinstance(exc.detail, dict) else {}
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_error",
            "message": "An unexpected error occurred",
            "details": {}
        }
    )


# Include routers
app.include_router(general_router)
app.include_router(web_scan_router)
app.include_router(pdf_scan_router)
app.include_router(integrations_router)


# Root endpoint
@app.get("/")
@limiter.limit("10/minute")
async def root(request: Request):
    """API root endpoint"""
    return {
        "service": "LumTrails External API",
        "version": "1.0.0",
        "status": "operational",
        "documentation": {
            "interactive": "/docs",
            "redoc": "/redoc",
            "blueprint": "https://github.com/yourusername/lumtrails/blob/main/API_BLUEPRINT.md"
        }
    }


# Health check (no auth required)
@app.get("/ping")
async def ping():
    """Simple health check without authentication"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        log_level="info"
    )
