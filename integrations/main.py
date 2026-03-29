"""
LumTrails Integration Worker - Modular Version
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import os

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
from pydantic import BaseModel, Field
from google.cloud import firestore

# Import the platform modules
from integrations.github_integration import GitHubIntegration
from integrations.slack_integration import SlackIntegration
from integrations.notion_integration import NotionIntegration
from integrations.shared_utils import get_user_integration_config, update_integration_stats_async

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LumTrails Integration Worker")

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# CORS - Restrict to internal services in production
if ENVIRONMENT == "production":
    cors_origins = [
        os.getenv("MAIN_API_URL", ""),
    ]
else:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Initialize clients
try:
    db = firestore.Client(project=PROJECT_ID)
    logger.info("Integration worker services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    db = None

# Request models
class IntegrationTask(BaseModel):
    user_id: str = Field(..., description="User ID")
    scan_id: str = Field(..., description="Scan ID")
    platform: str = Field(..., description="Integration platform")
    scan_data: Dict[str, Any] = Field(..., description="Scan data")
    timestamp: str = Field(..., description="Task timestamp")

async def _handle_integration_task(task: IntegrationTask):
    """
    Shared handler for integration tasks (used by both /push-integrations and /process)
    """
    try:
        logger.info(f"Processing integration push for user {task.user_id}, platform {task.platform}")
        
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Get user's integration configuration
        integration_config = get_user_integration_config(task.user_id, task.platform)
        
        if not integration_config:
            logger.warning(f"No integration config found for user {task.user_id}, platform {task.platform}")
            return JSONResponse(content={"message": "Integration not configured"})
        
        # Extract violations from scan_data for platforms that need pre-processing
        violations = []
        url = task.scan_data.get('url', 'Unknown URL')
        scan_timestamp = task.timestamp
        accessibility_score = None
        
        # Extract accessibility score if available
        if 'unified_results' in task.scan_data and task.scan_data['unified_results'].get('summary'):
            accessibility_score = task.scan_data['unified_results']['summary'].get('accessibility_score')
        
        # Only extract violations for platforms other than GitHub (GitHub handles its own extraction)
        if task.platform != 'github':
            # Extract violations based on scan_data structure - DON'T split by target elements for Slack/Notion
            if 'unified_results' in task.scan_data and task.scan_data['unified_results'].get('violations'):
                # New unified format - keep violations grouped, don't split by target elements
                for violation in task.scan_data['unified_results']['violations']:
                    target_elements = violation.get('target_elements', [])
                    html_context = violation.get('html_context', '')
                    
                    # Keep violation as a single entity with all targets, don't split
                    violations.append({
                        'id': violation.get('rule_id', violation.get('id', '')),
                        'impact': violation.get('impact', 'moderate'),
                        'description': violation.get('description', ''),
                        'help': violation.get('title', violation.get('help', '')),
                        'helpUrl': violation.get('help_url', violation.get('helpUrl', '')),
                        'target': target_elements,  # Keep all targets together
                        'html': html_context,
                        'failureSummary': violation.get('description', ''),
                        # Include nodes format for compatibility with existing Slack code
                        'nodes': [{'target': [target], 'html': html_context} for target in target_elements] if target_elements else [{'target': [], 'html': html_context}]
                    })
            elif 'violations' in task.scan_data:
                # Direct violations array
                violations = task.scan_data['violations']
            else:
                # Legacy format - extract from results
                results = task.scan_data.get('results', {})
                if 'axe' in results and 'violations' in results['axe']:
                    for violation in results['axe']['violations']:
                        violations.append(violation)
        
        # Route to appropriate integration handler
        success = False
        if task.platform == 'github':
            github_integration = GitHubIntegration(integration_config)
            result = await github_integration.push_violations(task.user_id, task.scan_data)
            success = result.get('success', False)
        elif task.platform == 'slack':
            slack_integration = SlackIntegration(integration_config)
            result = await slack_integration.push_violations(violations, url, task.scan_id, task.user_id, scan_timestamp, accessibility_score, task.scan_data)
            success = result.get('success', False)
        elif task.platform == 'notion':
            notion_integration = NotionIntegration(integration_config)
            result = await notion_integration.push_violations(violations, url, task.scan_id, task.user_id, scan_timestamp, accessibility_score, task.scan_data)
            success = result.get('success', False)
        else:
            logger.error(f"Unknown platform: {task.platform}")
            raise HTTPException(status_code=400, detail="Unknown platform")
        
        if success:
            return JSONResponse(content={"message": f"Successfully pushed to {task.platform}"})
        else:
            # Return 200 OK even for "soft" failures to prevent Cloud Tasks retries
            # Only use 500 for genuine system errors that should be retried
            return JSONResponse(content={"message": f"Push to {task.platform} completed with issues", "success": False})
        
    except HTTPException:
        # Re-raise HTTP exceptions as they have appropriate status codes
        raise
    except Exception as e:
        logger.error(f"Error processing integration push: {e}")
        # Return 200 OK for application errors to prevent retries - log the error instead
        return JSONResponse(content={"error": "Failed to process integration push", "details": str(e)}, status_code=200)

@app.post("/push-integrations")
async def process_integration_push(task: IntegrationTask):
    """
    Process integration push task from Cloud Tasks (Frontend API)
    """
    return await _handle_integration_task(task)

@app.post("/process")
async def process_integration_task(task: IntegrationTask):
    """
    Process integration push task from Cloud Tasks (External API)
    
    This endpoint provides compatibility for the External API which calls /process
    instead of /push-integrations. Both endpoints handle the same task processing.
    """
    return await _handle_integration_task(task)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db_status = "ok" if db else "unavailable"
        
        return JSONResponse(content={
            "status": "healthy",
            "service": "integration-worker",
            "database": db_status
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(content={
            "status": "unhealthy",
            "error": str(e)
        }, status_code=503)

@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(content={
        "message": "LumTrails Integration Worker",
        "version": "1.0.0"
    })

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(content={"error": "Internal server error"}, status_code=500)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)