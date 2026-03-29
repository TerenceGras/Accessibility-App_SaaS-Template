from fastapi import FastAPI, HTTPException, Request, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, List, Optional, Any
import asyncio
import logging
import httpx
import os
import tempfile
import uuid
import time
import json
from pathlib import Path
from contextlib import asynccontextmanager

# Google Auth for service-to-service authentication
import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
import google.auth.transport.requests

# CET timezone for EU service - all dates stored in CET
CET = ZoneInfo("Europe/Paris")

# Import custom modules with error handling
try:
    from gpt_scanner import run_gpt_vision_scan, run_gpt_vision_scan_with_content
    SCANNER_AVAILABLE = True
except ImportError as e:
    logging.warning(f"GPT Scanner not available: {e}")
    SCANNER_AVAILABLE = False
    run_gpt_vision_scan = None
    run_gpt_vision_scan_with_content = None

try:
    from pdf_storage import storage_manager
    STORAGE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"PDF Storage not available: {e}")
    STORAGE_AVAILABLE = False
    storage_manager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"PDF Scanner Worker starting up on port {PORT}")
    logger.info(f"OpenAI API Key configured: {'Yes' if OPENAI_API_KEY else 'No'}")
    logger.info(f"API URL: {API_URL}")
    logger.info(f"Scanner Available: {SCANNER_AVAILABLE}")
    logger.info(f"Storage Available: {STORAGE_AVAILABLE}")
    logger.info("Startup complete")
    yield
    # Shutdown
    logger.info("PDF Scanner Worker shutting down")

# Initialize FastAPI app
app = FastAPI(
    title="LumTrails PDF AI Accessibility Scanner Worker",
    description="PDF accessibility scanner worker with GPT-5 Vision AI integration",
    version="2.0.0",
    lifespan=lifespan
)

# Configuration
PORT = int(os.getenv("PORT", 8080))
API_URL = os.getenv("API_URL", "")

# OpenAI API configuration - Secret Manager entry: openai-api-key-pdf-scanner
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OpenAI API key not found. PDF scanning will use placeholder results.")

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


# =============================================================================
# OIDC Token for Service-to-Service Authentication
# =============================================================================

def get_oidc_token(audience: str) -> str:
    """
    Get an OIDC identity token for authenticating to another Cloud Run service.
    Uses the default service account's identity.
    """
    try:
        # Get credentials from the default service account
        credentials, project = google.auth.default()
        
        # Create a new request for fetching the token
        auth_req = google.auth.transport.requests.Request()
        
        # Fetch an ID token for the target audience (the API URL)
        token = google_id_token.fetch_id_token(auth_req, audience)
        
        logger.info(f"Successfully fetched OIDC token for audience: {audience}")
        return token
    except Exception as e:
        logger.error(f"Failed to fetch OIDC token: {e}")
        raise


# CORS middleware - Restrict to internal services in production
if ENVIRONMENT == "production":
    cors_origins = [
        os.getenv("MAIN_API_URL", ""),
        os.getenv("EXTERNAL_API_URL", ""),
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

# Security middleware - Allow Cloud Run internal traffic
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]
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

# Pydantic models
class PDFScanRequest(BaseModel):
    file_name: str
    file_size: int
    scan_type: str = "full"  # "full", "compliance", "vision"

class CloudTaskPayload(BaseModel):
    task_id: str
    storage_path: str  # Firebase Storage path to the PDF file
    file_name: str
    file_size: int
    user_id: str
    user_email: str
    created_at: str
    is_external_api: Optional[bool] = False  # Flag to prevent callback when called from external API
    credits_reserved: Optional[bool] = False
    credits_required: Optional[int] = None
    language: Optional[str] = "en"  # Language code for the analysis prompt (en, fr, de, es, it, pt)

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str

class TestEngine(BaseModel):
    name: str
    version: str
    tools: List[str] = []

class PDFAccessibilityIssue(BaseModel):
    id: str
    severity: str  # "critical", "serious", "moderate", "minor"
    category: str  # "structure", "navigation", "images", "forms", "color_contrast", "language"
    title: str
    description: str
    recommendation: str
    page_number: Optional[int] = None
    element_context: Optional[str] = None
    wcag_guidelines: List[str] = []
    tool_detected: str  # "veracpdf", "pdfminer", "gpt5"

class UnifiedPDFScanResponse(BaseModel):
    file_name: str
    file_size: int
    timestamp: str
    testEngine: TestEngine
    scan_type: str
    violations: List[PDFAccessibilityIssue]
    warnings: List[PDFAccessibilityIssue]
    notices: List[PDFAccessibilityIssue]
    passes: List[PDFAccessibilityIssue]
    unified_results: Dict[str, Any]
    scanDuration: int

# Utility functions
def is_valid_pdf(file_path: str) -> bool:
    """Validate PDF file format"""
    try:
        with open(file_path, 'rb') as f:
            header = f.read(8)
            return header.startswith(b'%PDF-')
    except Exception:
        return False

async def process_pdf_file(file_path: str, language: str = "en") -> Dict[str, Any]:
    """Process PDF file using GPT-5 Vision for AI-powered accessibility analysis"""
    results = {}
    
    try:
        # Run GPT-5 Vision scan for comprehensive AI accessibility analysis
        logger.info(f"Running GPT-5 Vision accessibility scan (language: {language})")
        gpt_results = await run_gpt_vision_scan(file_path, language=language)
        results['gpt5'] = gpt_results
        logger.info(f"GPT-5 Vision scan completed: {len(gpt_results.get('violations', []))} issues found")
        
        return results
        
    except Exception as e:
        logger.error(f"PDF processing failed: {str(e)}", exc_info=True)
        return {
            'error': str(e),
            'gpt5': {'error': str(e), 'violations': []}
        }

# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(CET).isoformat(),
        service="pdf-ai-accessibility-scanner"
    )

@app.post("/scan")
async def scan_pdf_worker(payload: CloudTaskPayload):
    """Process PDF scan request from Cloud Tasks using AI-powered analysis with Firebase Storage"""
    start_time = time.time()
    task_id = payload.task_id
    
    logger.info(f"Processing PDF scan task {task_id} for: {payload.file_name}")
    
    # Security: Validate storage path to prevent path traversal attacks
    expected_prefix = f"temp-pdfs/{task_id}/"
    if not payload.storage_path.startswith(expected_prefix):
        logger.error(f"Invalid storage path: {payload.storage_path} (expected prefix: {expected_prefix})")
        raise HTTPException(
            status_code=400,
            detail="Invalid storage path"
        )
    
    try:
        # Use the new storage-based GPT scanning which handles Firebase Storage internally
        if not SCANNER_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="PDF scanning service not available - missing dependencies"
            )
        
        # Get language from payload (defaults to English)
        language = payload.language or "en"
        scan_results = await run_gpt_vision_scan(payload.storage_path, payload.file_name, task_id, language)
        
        # Calculate scan duration
        scan_duration = int((time.time() - start_time) * 1000)
        logger.info(f"PDF scan completed in {scan_duration}ms")
        
        # Check if scan returned an error status (e.g., OpenAI API key issues)
        scan_status = scan_results.get('status', 'completed')
        if scan_status == 'error':
            error_message = scan_results.get('error', 'Unknown scan error')
            logger.error(f"PDF scan returned error status: {error_message}")
            
            # Raise an exception to trigger the error handling path (which refunds credits)
            raise Exception(f"PDF scan failed: {error_message}")
        
        # Create unified result from GPT-5 results with free-text format
        logger.info(f"Creating unified result with GPT-5 scan results in free-text format")
        try:
            # scan_results now contains free-text accessibility report instead of structured violations
            unified_result = {
                # For PDF scans with free-text, these traditional arrays are empty or minimal
                'violations': [],
                'passes': [],
                'incomplete': [],
                'inapplicable': [],
                'warnings': [],
                'notices': [],
                'unified_results': {
                    'analysis_type': scan_results.get('analysis_type', 'ai_vision_free_text'),
                    'accessibility_report': scan_results.get('accessibility_report', 'No analysis available'),
                    'pages_analyzed': scan_results.get('pages_analyzed', 0),
                    'tool_info': scan_results.get('tool_info', {}),
                    'is_free_text': True  # Flag to indicate this is free-text format
                },
                'accessibility_report': scan_results.get('accessibility_report', 'No analysis available'),
                'analysis_type': 'ai_vision_free_text',
                'file_name': payload.file_name,
                'file_size': payload.file_size,
                'scan_type': 'ai_vision',
                'timestamp': datetime.now(CET).isoformat(),
                'testEngine': {
                    'name': 'LumTrails-PDF-AI-Scanner',
                    'version': '2.0.0',
                    'tools': ['GPT-5-Vision']
                },
                'scanDuration': scan_duration,
                'status': 'completed',
                'user_id': payload.user_id,
                'user_email': payload.user_email,
                'id': task_id,
                'credits_reserved': payload.credits_reserved,
                'credits_required': payload.credits_required
            }
            logger.info(f"Unified result created successfully with free-text format")
        except Exception as mapping_error:
            logger.error(f"Failed to create unified result: {str(mapping_error)}", exc_info=True)
            # Create a minimal result structure to avoid complete failure
            unified_result = {
                'violations': [],
                'passes': [],
                'incomplete': [],
                'inapplicable': [],
                'warnings': [],
                'notices': [],
                'unified_results': {'error': f'AI analysis failed: {str(mapping_error)}'},
                'accessibility_report': f'Analysis failed: {str(mapping_error)}',
                'analysis_type': 'ai_vision_free_text',
                'file_name': payload.file_name,
                'file_size': payload.file_size,
                'scan_type': 'ai_vision',
                'timestamp': datetime.now(CET).isoformat(),
                'testEngine': {
                    'name': 'LumTrails-PDF-AI-Scanner',
                    'version': '2.0.0',
                    'tools': ['GPT-5-Vision']
                },
                'scanDuration': scan_duration,
                'status': 'completed_with_errors',
                'user_id': payload.user_id,
                'user_email': payload.user_email,
                'id': task_id,
                'credits_reserved': payload.credits_reserved,
                'credits_required': payload.credits_required
            }
        
        # Set timestamp
        unified_result['timestamp'] = datetime.now(CET).isoformat()
        
        logger.info(f"Unified PDF scan result created with free-text accessibility report")
        
        # Store result in database (skip if called from external API)
        if not payload.is_external_api:
            try:
                logger.info(f"Sending unified PDF scan result to API with user_id: {payload.user_id}, user_email: {payload.user_email}")
                
                # Get OIDC token for service-to-service authentication
                try:
                    oidc_token = get_oidc_token(API_URL)
                    auth_headers = {"Authorization": f"Bearer {oidc_token}"}
                except Exception as token_error:
                    logger.error(f"Failed to get OIDC token: {token_error}")
                    auth_headers = {}
                
                async with httpx.AsyncClient() as client:
                    store_response = await client.post(
                        f"{API_URL}/pdf-scan/store-result",
                        json=unified_result,
                        headers=auth_headers,
                        timeout=30
                    )
                    
                if store_response.status_code == 200:
                    logger.info(f"Stored unified PDF scan result in database for {payload.file_name}")
                else:
                    logger.warning(f"Failed to store PDF scan result: {store_response.text}")
                    
            except Exception as e:
                logger.error(f"Error storing PDF scan result: {str(e)}")
        else:
            logger.info("Skipping API callback - called from external API")
        
        # Note: Cleanup is handled automatically by the GPT scanner's storage manager
        logger.info("PDF scan completed - temporary files cleaned up by storage manager")
        
        return unified_result
                
    except asyncio.TimeoutError:
        logger.error(f"Timeout error for PDF {payload.file_name}")
        
        # Notify API of failure so credits can be refunded
        if not payload.is_external_api:
            try:
                # Get OIDC token for service-to-service authentication
                try:
                    oidc_token = get_oidc_token(API_URL)
                    auth_headers = {"Authorization": f"Bearer {oidc_token}"}
                except Exception:
                    auth_headers = {}
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await client.post(
                        f"{API_URL}/pdf-scan/store-result",
                        json={
                            "id": payload.task_id,
                            "file_name": payload.file_name,
                            "file_size": payload.file_size,
                            "timestamp": datetime.now(CET).isoformat(),
                            "status": "failed",
                            "user_id": payload.user_id,
                            "user_email": payload.user_email,
                            "error_message": "PDF scan timed out - the file took too long to process",
                            "credits_reserved": payload.credits_reserved,
                            "credits_required": payload.credits_required
                        },
                        headers=auth_headers
                    )
            except Exception as callback_error:
                logger.error(f"Failed to notify API of scan failure: {str(callback_error)}")
        
        raise HTTPException(
            status_code=408, 
            detail="PDF scan timed out - the file took too long to process"
        )
    except Exception as error:
        logger.error(f"PDF scan error for {payload.file_name}: {str(error)}", exc_info=True)
        
        # Note: Cleanup is handled automatically by the GPT scanner's storage manager
        logger.info("PDF scan failed - temporary files cleaned up by storage manager")
        
        # Notify API of failure so credits can be refunded
        if not payload.is_external_api:
            try:
                # Get OIDC token for service-to-service authentication
                try:
                    oidc_token = get_oidc_token(API_URL)
                    auth_headers = {"Authorization": f"Bearer {oidc_token}"}
                except Exception:
                    auth_headers = {}
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    await client.post(
                        f"{API_URL}/pdf-scan/store-result",
                        json={
                            "id": payload.task_id,
                            "file_name": payload.file_name,
                            "file_size": payload.file_size,
                            "timestamp": datetime.now(CET).isoformat(),
                            "status": "failed",
                            "user_id": payload.user_id,
                            "user_email": payload.user_email,
                            "error_message": str(error),
                            "credits_reserved": payload.credits_reserved,
                            "credits_required": payload.credits_required
                        },
                        headers=auth_headers
                    )
            except Exception as callback_error:
                logger.error(f"Failed to notify API of scan failure: {str(callback_error)}")
        
        # Determine appropriate error response
        error_message = str(error).lower()
        if 'timeout' in error_message:
            raise HTTPException(
                status_code=408,
                detail="PDF scan timed out - the file took too long to process"
            )
        elif 'corrupt' in error_message or 'invalid' in error_message:
            raise HTTPException(
                status_code=400,
                detail="PDF file appears to be corrupted or invalid"
            )
        elif 'permission' in error_message or 'password' in error_message:
            raise HTTPException(
                status_code=403,
                detail="PDF file is password protected or permission denied"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error during PDF scan: {str(error)}"
            )

@app.get("/debug")
async def debug_test():
    """Debug endpoint to test basic functionality"""
    try:
        from mapping import create_unified_pdf_scan_result
        from veracpdf_scanner import run_veracpdf_scan
        from pdfminer_scanner import run_pdfminer_scan
        from gpt_scanner import run_gpt_vision_scan
        
        logger.info("Debug: All imports successful")
        
        # Test placeholder results
        test_result = create_unified_pdf_scan_result(
            veracpdf_results={'valid': True, 'tool': 'test'},
            pdfminer_results={'text_issues': [], 'tool': 'test'},
            gpt_results={'issues': [], 'status': 'test'},
            file_name="test.pdf",
            file_size=1000,
            scan_type="full",
            scan_duration=100,
            task_id="test-123",
            user_id="test-user",
            user_email="test@example.com"
        )
        
        return {
            "status": "debug_success",
            "imports_ok": True,
            "mapping_test": "success",
            "test_result_keys": list(test_result.keys())
        }
        
    except Exception as e:
        logger.error(f"Debug test failed: {str(e)}", exc_info=True)
        return {
            "status": "debug_failed",
            "error": str(e),
            "traceback": str(e.__class__.__name__)
        }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "LumTrails PDF Accessibility Scanner Worker v1.0"}

if __name__ == "__main__":
    import uvicorn
    print(f"Starting PDF Scanner Worker on port {PORT}")
    logger.info(f"Starting PDF Scanner Worker on port {PORT}")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
