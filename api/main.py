from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, Depends, File, UploadFile, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, HttpUrl, Field
from google.cloud import tasks_v2, firestore
from google.auth import default
import httpx
import os
import logging
import json
import uuid
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional, List
import asyncio
import firebase_admin
from firebase_admin import credentials, storage as firebase_storage

# OpenTelemetry for distributed tracing
try:
    from opentelemetry import trace
    from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    TRACING_ENABLED = True
except ImportError:
    TRACING_ENABLED = False

# CET timezone for EU service - all dates stored in CET
CET = ZoneInfo("Europe/Paris")

# Import authentication components
from auth.auth_routes import auth_router
from auth.auth_service import get_current_user, get_optional_user

# Import integration routes
from integrations.integration_routes import integration_router

# Import API key routes
from api_key_routes import router as api_key_router

# Security: Import for OIDC token verification (Cloud Scheduler/Cloud Tasks)
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from google.auth import default as google_auth_default
from google.auth.transport.requests import Request as GoogleAuthRequest

# Project configuration for OIDC verification
PROJECT_NUMBER = os.getenv("PROJECT_NUMBER", "")
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
ALLOWED_SERVICE_ACCOUNTS = [
    f"{PROJECT_NUMBER}-compute@developer.gserviceaccount.com",
    f"{PROJECT_ID}@appspot.gserviceaccount.com",
]


async def verify_cloud_service_token(request: Request) -> dict:
    """
    Verify OIDC token from Cloud Scheduler or Cloud Tasks.
    Returns the verified claims if valid, raises HTTPException if not.
    """
    authorization = request.headers.get("Authorization", "")
    
    # Check for Bearer token
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=403, detail="Missing or invalid authorization header")
    
    token = authorization[7:]
    
    try:
        # Verify the OIDC token
        claims = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            audience=None  # We'll verify the service account email instead
        )
        
        # Verify the token is from an allowed service account
        email = claims.get("email", "")
        if email not in ALLOWED_SERVICE_ACCOUNTS:
            logger.warning(f"Unauthorized service account attempted access: {email}")
            raise HTTPException(status_code=403, detail="Unauthorized service account")
        
        logger.info(f"Verified OIDC token from service account: {email}")
        return claims
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OIDC token verification failed: {e}")
        raise HTTPException(status_code=403, detail="Invalid or expired token")


async def get_service_auth_token(audience: str) -> str:
    """
    Get an ID token for authenticated service-to-service calls.
    Uses the default service account credentials to generate a token.
    """
    try:
        credentials, _ = google_auth_default()
        # Refresh credentials to get a valid token
        auth_request = GoogleAuthRequest()
        credentials.refresh(auth_request)
        
        # For ID token, we need to use the IAM API or fetch_id_token
        from google.oauth2 import service_account
        from google.auth import compute_engine
        
        # If running on Cloud Run, use compute engine credentials
        if hasattr(credentials, 'token'):
            # Get ID token using the service account
            import google.auth.transport.requests
            import google.oauth2.id_token
            
            id_token_creds = google.oauth2.id_token.fetch_id_token(
                google.auth.transport.requests.Request(),
                audience
            )
            return id_token_creds
        else:
            # Fallback for local development
            logger.warning("Running without proper GCP credentials for service auth")
            return None
    except Exception as e:
        logger.error(f"Failed to get service auth token: {e}")
        return None


# Contact Form Request Model
class ContactFormRequest(BaseModel):
    """Request model for contact form submissions"""
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)


def log_credit_usage(user_id: str, credit_type: str, amount: int, reason: str, scan_id: str = None):
    """Log credit usage to credit_usage_daily_summary collection (aggregated by day).
    
    This replaces the old per-transaction credit_usage_history approach with a more
    efficient daily aggregation. Each user has one document per day containing
    totals for that day.
    
    Daily summary documents are retained for 30 days (via TTL/cleanup job).
    """
    try:
        if not db:
            logger.error("Firestore client not initialized")
            return False
        
        # Create document ID from user_id and date
        today = datetime.now(CET).strftime('%Y-%m-%d')
        summary_id = f"{user_id}_{today}"
        
        summary_ref = db.collection('credit_usage_daily_summary').document(summary_id)
        
        @firestore.transactional
        def update_summary(transaction, ref):
            doc = ref.get(transaction=transaction)
            now = datetime.now(CET)
            
            if doc.exists:
                # Update existing daily summary
                update = {
                    'last_updated': now,
                    'scan_count': firestore.Increment(1)
                }
                if credit_type == "web_scan":
                    update['total_web_credits_used'] = firestore.Increment(amount)
                else:
                    update['total_pdf_credits_used'] = firestore.Increment(amount)
                transaction.update(ref, update)
            else:
                # Create new daily summary document
                transaction.set(ref, {
                    'user_id': user_id,
                    'date': today,
                    'total_web_credits_used': amount if credit_type == "web_scan" else 0,
                    'total_pdf_credits_used': amount if credit_type == "pdf_scan" else 0,
                    'scan_count': 1,
                    'created_at': now,
                    'last_updated': now,
                    # TTL field for automatic cleanup (30 days from now)
                    'expires_at': now + timedelta(days=30)
                })
        
        transaction = db.transaction()
        update_summary(transaction, summary_ref)
        
        logger.info(f"Logged credit usage to daily summary for user {user_id}: {credit_type} - {amount}")
        return True
    except Exception as e:
        logger.error(f"Error logging credit usage: {e}")
        return False


def reserve_credits(user_id: str, credit_type: str, amount: int, scan_id: str) -> tuple[bool, str]:
    """
    Reserve credits atomically using Firestore transaction.
    This prevents concurrent scans from using the same credits.
    
    Returns: (success: bool, error_message: str)
    """
    try:
        if not db:
            return False, "Database unavailable"
        
        credit_field = "web_scan_credits" if credit_type == "web_scan" else "pdf_scan_credits"
        reserved_field = f"reserved_{credit_type}_credits"
        
        @firestore.transactional
        def reserve_in_transaction(transaction, user_ref):
            user_doc = user_ref.get(transaction=transaction)
            
            if not user_doc.exists:
                return False, "User not found"
            
            user_data = user_doc.to_dict()
            current_credits = user_data.get(credit_field, 0)
            reserved_credits = user_data.get(reserved_field, 0)
            
            # Available credits = actual credits - already reserved
            available_credits = current_credits - reserved_credits
            
            if available_credits < amount:
                return False, f"Insufficient credits. Need {amount}, have {available_credits} available ({current_credits} total - {reserved_credits} reserved)"
            
            # Reserve the credits by adding to reserved count
            transaction.update(user_ref, {
                reserved_field: firestore.Increment(amount),
                'updated_at': datetime.now(CET)
            })
            
            # Log the reservation
            reservation_ref = db.collection('credit_reservations').document(scan_id)
            now = datetime.now(CET)
            transaction.set(reservation_ref, {
                "user_id": user_id,
                "scan_id": scan_id,
                "credit_type": credit_type,
                "amount": amount,
                "status": "reserved",
                "created_at": now,
                "expires_at": now + timedelta(hours=2)  # TTL: auto-delete abandoned reservations
            })
            
            return True, ""
        
        user_ref = db.collection('users').document(user_id)
        transaction = db.transaction()
        success, error = reserve_in_transaction(transaction, user_ref)
        
        if success:
            logger.info(f"Reserved {amount} {credit_type} credits for user {user_id}, scan {scan_id}")
        else:
            logger.warning(f"Failed to reserve credits for user {user_id}: {error}")
        
        return success, error
        
    except Exception as e:
        logger.error(f"Error reserving credits: {e}")
        return False, str(e)


def finalize_credits(user_id: str, credit_type: str, amount: int, scan_id: str, success: bool, reason: str = None):
    """
    Finalize credit reservation after scan completes.
    If success=True: deduct credits and release reservation
    If success=False: refund credits (just release reservation)
    """
    try:
        if not db:
            logger.error("Database unavailable for credit finalization")
            return False
        
        credit_field = "web_scan_credits" if credit_type == "web_scan" else "pdf_scan_credits"
        reserved_field = f"reserved_{credit_type}_credits"
        
        @firestore.transactional
        def finalize_in_transaction(transaction, user_ref, reservation_ref):
            user_doc = user_ref.get(transaction=transaction)
            reservation_doc = reservation_ref.get(transaction=transaction)
            
            if not user_doc.exists:
                logger.error(f"User {user_id} not found during credit finalization")
                return False
            
            # Check if reservation exists and is still pending
            if reservation_doc.exists:
                reservation_data = reservation_doc.to_dict()
                if reservation_data.get('status') != 'reserved':
                    logger.warning(f"Reservation {scan_id} already finalized: {reservation_data.get('status')}")
                    return True  # Already processed
            
            user_data = user_doc.to_dict()
            reserved_credits = user_data.get(reserved_field, 0)
            current_credits = user_data.get(credit_field, 0)
            
            if success:
                # Deduct credits and release reservation
                new_credits = max(0, current_credits - amount)  # Never go below 0
                new_reserved = max(0, reserved_credits - amount)
                
                transaction.update(user_ref, {
                    credit_field: new_credits,
                    reserved_field: new_reserved,
                    'updated_at': datetime.now(CET)
                })
                
                # Update reservation status
                if reservation_doc.exists:
                    transaction.update(reservation_ref, {
                        "status": "completed",
                        "completed_at": datetime.now(CET)
                    })
                
                logger.info(f"Finalized credit deduction for user {user_id}: {amount} {credit_type} credits deducted")
            else:
                # Just release the reservation (refund)
                new_reserved = max(0, reserved_credits - amount)
                
                transaction.update(user_ref, {
                    reserved_field: new_reserved,
                    'updated_at': datetime.now(CET)
                })
                
                # Update reservation status
                if reservation_doc.exists:
                    transaction.update(reservation_ref, {
                        "status": "refunded",
                        "refund_reason": reason or "Scan failed",
                        "completed_at": datetime.now(CET)
                    })
                
                logger.info(f"Released credit reservation for user {user_id}: {amount} {credit_type} credits refunded")
            
            return True
        
        user_ref = db.collection('users').document(user_id)
        reservation_ref = db.collection('credit_reservations').document(scan_id)
        transaction = db.transaction()
        result = finalize_in_transaction(transaction, user_ref, reservation_ref)
        
        # Log credit usage history if successful deduction
        if success and result:
            log_credit_usage(user_id, credit_type, amount, reason or f"{credit_type} completed successfully", scan_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Error finalizing credits: {e}")
        return False


def queue_integration_tasks(user_id: str, scan_result: Dict[str, Any]) -> bool:
    """Queue integration tasks for enabled platforms"""
    try:
        logger.info(f"DEBUG queue_integration_tasks: user_id='{user_id}', type={type(user_id)}")
        if not tasks_client or not db:
            logger.error("Cloud Tasks or Firestore client not initialized")
            return False
        
        # Get user's integration settings
        doc_ref = db.collection('user_integrations').document(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.info(f"No integrations configured for user {user_id}")
            return True
        
        integrations_data = doc.to_dict()
        integrations = integrations_data.get('integrations', {})
        
        # Detect if this is a PDF scan
        is_pdf_scan = scan_result.get('scan_type') == 'ai_vision' or scan_result.get('analysis_type') == 'ai_vision_free_text'
        scan_type_str = "PDF" if is_pdf_scan else "web"
        
        logger.info(f"Queueing integration tasks for {scan_type_str} scan for user {user_id}")
        
        tasks_queued = 0
        
        # Queue tasks for each enabled integration
        for platform, platform_config in integrations.items():
            # Get the config object that contains connected, web_scan_enabled, pdf_scan_enabled
            config = platform_config.get('config', {})
            
            # Check basic connection and web scan enabled status
            is_connected = config.get('connected', False)
            is_web_enabled = config.get('web_scan_enabled', False)
            
            # For PDF scans, also check if PDF scans are enabled
            if is_pdf_scan:
                is_pdf_enabled = config.get('pdf_scan_enabled', False)
                should_queue = is_connected and is_pdf_enabled
                logger.info(f"{platform}: connected={is_connected}, pdf_scan_enabled={is_pdf_enabled}, should_queue={should_queue}")
            else:
                should_queue = is_connected and is_web_enabled
                logger.info(f"{platform}: connected={is_connected}, web_scan_enabled={is_web_enabled}, should_queue={should_queue}")
            
            if should_queue:
                logger.info(f"Queueing {platform} integration task for {scan_type_str} scan for user {user_id}")
                
                # Create task payload with datetime and Sentinel serialization
                def serialize_datetime_objects(obj):
                    """Recursively convert datetime objects and Firestore Sentinels to ISO format strings"""
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'Sentinel':
                        # Firestore Sentinel (like SERVER_TIMESTAMP) - replace with current time
                        return datetime.now(CET).isoformat()
                    elif isinstance(obj, dict):
                        return {k: serialize_datetime_objects(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [serialize_datetime_objects(item) for item in obj]
                    else:
                        return obj
                
                task_payload = {
                    "user_id": user_id,
                    "scan_id": scan_result.get("task_id", "unknown"),
                    "platform": platform,
                    "scan_data": serialize_datetime_objects(scan_result),
                    "timestamp": datetime.now(CET).isoformat()
                }
                
                # Create Cloud Task
                task_id = f"{platform}-{user_id}-{uuid.uuid4().hex[:8]}"
                # Remove hyphens from task_id for Cloud Tasks name
                task_name = task_id.replace("-", "_")
                
                task = {
                    "name": f"{integration_parent}/tasks/{task_name}",
                    "http_request": {
                        "http_method": tasks_v2.HttpMethod.POST,
                        "url": f"{INTEGRATION_WORKER_URL}/push-integrations",
                        "headers": {
                            "Content-Type": "application/json"
                        },
                        "body": json.dumps(task_payload).encode("utf-8"),
                        "oidc_token": {
                            "service_account_email": f"{os.environ.get('PROJECT_NUMBER', '')}-compute@developer.gserviceaccount.com",
                            "audience": INTEGRATION_WORKER_URL
                        }
                    }
                }
                
                # Queue the task
                response = tasks_client.create_task(parent=integration_parent, task=task)
                logger.info(f"Queued {platform} integration task: {response.name}")
                tasks_queued += 1
        
        if tasks_queued > 0:
            logger.info(f"Queued {tasks_queued} integration tasks for user {user_id}")
        else:
            logger.info(f"No enabled integrations found for user {user_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error queueing integration tasks for user {user_id}: {e}")
        return False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenTelemetry tracing
if TRACING_ENABLED:
    try:
        tracer_provider = TracerProvider()
        cloud_trace_exporter = CloudTraceSpanExporter()
        tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
        trace.set_tracer_provider(tracer_provider)
        logger.info("OpenTelemetry tracing initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize OpenTelemetry tracing: {e}")
        TRACING_ENABLED = False

# Initialize FastAPI app
app = FastAPI(
    title="LumTrails Main API",
    description="Main API server for LumTrails accessibility scanner",
    version="1.0.0"
)

# Instrument FastAPI with OpenTelemetry
if TRACING_ENABLED:
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning(f"Failed to instrument FastAPI: {e}")

# Configuration
PORT = int(os.getenv("PORT", 8000))
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
MAILING_URL = os.getenv("MAILING_URL", "")

# Google Cloud configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.getenv("CLOUD_TASKS_LOCATION", "europe-west1")
QUEUE_NAME = os.getenv("CLOUD_TASKS_QUEUE", "web-scan-queue")
PDF_QUEUE_NAME = os.getenv("PDF_SCAN_QUEUE", "pdf-scan-queue")
INTEGRATION_QUEUE_NAME = os.getenv("INTEGRATION_QUEUE_NAME", "integration-queue")
WORKER_URL = os.getenv("WORKER_URL", "")
PDF_WORKER_URL = os.getenv("PDF_WORKER_URL", "")
INTEGRATION_WORKER_URL = os.getenv("INTEGRATION_WORKER_URL", "")

# Initialize Cloud Tasks client
try:
    tasks_client = tasks_v2.CloudTasksClient()
    parent = tasks_client.queue_path(PROJECT_ID, LOCATION, QUEUE_NAME)
    pdf_parent = tasks_client.queue_path(PROJECT_ID, LOCATION, PDF_QUEUE_NAME)
    integration_parent = tasks_client.queue_path(PROJECT_ID, LOCATION, INTEGRATION_QUEUE_NAME)
    logger.info(f"Cloud Tasks initialized for queues: {parent}, {pdf_parent}, {integration_parent}")
except Exception as e:
    logger.error(f"Failed to initialize Cloud Tasks client: {e}")
    tasks_client = None
    parent = None
    pdf_parent = None
    integration_parent = None

# Initialize Firestore client
try:
    db = firestore.Client(project=PROJECT_ID)
    logger.info("Firestore client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firestore client: {e}")
    db = None

# Initialize Firebase Storage for PDF storage
try:
    from google.cloud import secretmanager
    import json
    
    # Firebase Storage bucket name (without gs:// prefix)
    storage_bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET', '')
    logger.info(f"Initializing Firebase Storage with bucket: {storage_bucket_name}")
    
    # Initialize Firebase Admin SDK if not already initialized
    if not firebase_admin._apps:
        logger.info("Initializing Firebase Admin SDK...")
        
        # Try to fetch service account key from Secret Manager
        try:
            logger.info("Fetching service account key from Secret Manager...")
            secret_client = secretmanager.SecretManagerServiceClient()
            secret_name = f"projects/{PROJECT_ID}/secrets/firebase-storage-private-key/versions/latest"
            response = secret_client.access_secret_version(request={"name": secret_name})
            secret_data = response.payload.data.decode('UTF-8')
            service_account_info = json.loads(secret_data)
            
            logger.info("Successfully loaded service account key from Secret Manager")
            cred = credentials.Certificate(service_account_info)
            firebase_admin.initialize_app(cred, {
                'storageBucket': storage_bucket_name
            })
            logger.info(f"Firebase Admin SDK initialized with service account credentials from Secret Manager")
        except Exception as secret_error:
            logger.warning(f"Could not load service account key from Secret Manager: {secret_error}")
            logger.info("Falling back to default Cloud Run service account credentials")
            firebase_admin.initialize_app(options={
                'storageBucket': storage_bucket_name
            })
            logger.info(f"Firebase Admin SDK initialized with default credentials")
    else:
        logger.info("Firebase Admin SDK already initialized")
    
    # Get bucket reference - explicitly specify the bucket name
    logger.info(f"Getting Firebase Storage bucket reference for: {storage_bucket_name}")
    storage_bucket = firebase_storage.bucket(storage_bucket_name)
    logger.info(f"✅ Firebase Storage client initialized successfully for bucket: {storage_bucket.name}")
except Exception as e:
    logger.error(f"❌ Failed to initialize Firebase Storage client: {e}", exc_info=True)
    storage_bucket = None

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware - Use environment-based configuration
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
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
    allow_headers=["Content-Type", "Authorization"],
)

# Security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Request size limit middleware (default 50MB, PDF endpoint handles 5GB separately)
MAX_REQUEST_SIZE = 50 * 1024 * 1024  # 50MB default

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Skip size check for PDF upload endpoint (handled separately with 5GB limit)
        if request.url.path == "/pdf-scan/scan":
            return await call_next(request)
        
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > MAX_REQUEST_SIZE:
            return Response("Request too large", status_code=413)
        return await call_next(request)

app.add_middleware(RequestSizeLimitMiddleware)

# Include authentication routes
app.include_router(auth_router, prefix="/auth")

# Include integration routes
app.include_router(integration_router, prefix="")

# Include API key management routes
app.include_router(api_key_router, prefix="")

# Helper function to store PDFs in Firebase Storage
async def store_pdf_in_firebase_storage(file_content: bytes, file_name: str, task_id: str) -> str:
    """Store PDF temporarily in Firebase Storage and return the storage path"""
    try:
        if not storage_bucket:
            raise Exception("Firebase Storage bucket not initialized")
        
        # Create unique storage path
        storage_path = f"temp-pdfs/{task_id}/{file_name}"
        blob = storage_bucket.blob(storage_path)
        
        # Set metadata for cleanup
        now = datetime.now(CET)
        blob.metadata = {
            'task_id': task_id,
            'original_filename': file_name,
            'upload_time': now.isoformat(),
            'file_type': 'pdf',
            'cleanup_after': (now + timedelta(hours=2)).isoformat()
        }
        
        # Upload the PDF file
        blob.upload_from_string(file_content, content_type='application/pdf')
        
        logger.info(f"PDF uploaded to Firebase Storage: {storage_path}")
        return storage_path
        
    except Exception as e:
        logger.error(f"Failed to store PDF in Firebase Storage: {str(e)}")
        raise

# Available scan modules for web scans (1 credit per module)
AVAILABLE_WEB_MODULES = ["axe", "nu", "axTree", "galen", "links"]


def calculate_web_scan_credits(modules: Optional[List[str]] = None) -> int:
    """
    Calculate the number of credits required for a web scan based on active modules.
    Web scans cost 1 credit per module (max 5 credits for all modules).
    
    Args:
        modules: List of module IDs to run. If None, all modules will be run.
    
    Returns:
        Number of credits required (1 per module)
    """
    if modules is None:
        return len(AVAILABLE_WEB_MODULES)
    
    # Filter to only valid modules
    valid_modules = [m for m in modules if m in AVAILABLE_WEB_MODULES]
    
    # If no valid modules specified, use all modules
    if not valid_modules:
        return len(AVAILABLE_WEB_MODULES)
    
    return len(valid_modules)


# Pydantic models
class ScanRequest(BaseModel):
    url: str
    modules: Optional[List[str]] = Field(
        default=None,
        description="List of scan modules to run (axe, nu, axTree, galen, links). If None, all modules run. Cost: 1 credit per module."
    )

class PDFScanRequest(BaseModel):
    file_name: str
    file_size: int

class ScanTaskResponse(BaseModel):
    task_id: str
    status: str
    url: str
    created_at: str

class PDFScanTaskResponse(BaseModel):
    task_id: str
    status: str
    file_name: str
    created_at: str

class TaskStatus(BaseModel):
    task_id: str
    status: str
    url: str
    created_at: str
    result: Dict[str, Any] = None

class ScanResult(BaseModel):
    id: str  # Task/scan ID
    url: str
    timestamp: Optional[str] = None
    testEngine: Dict[str, Any]
    violations: List[Dict[str, Any]] = []
    passes: List[Dict[str, Any]] = []
    incomplete: List[Dict[str, Any]] = []
    inapplicable: List[Dict[str, Any]] = []
    unified_results: Optional[Dict[str, Any]] = None  # New unified format from multi-tool scanner
    scanDuration: int
    status: str = "completed"
    user_id: str  # User who initiated the scan (required)
    user_email: str  # User email for display purposes (required)

class PDFScanResult(BaseModel):
    id: str  # Task/scan ID
    file_name: str
    file_size: int
    scan_type: Optional[str] = None  # Optional for failed scans
    timestamp: Optional[str] = None
    testEngine: Optional[Dict[str, Any]] = None  # Optional for failed scans
    violations: List[Dict[str, Any]] = []
    warnings: List[Dict[str, Any]] = []  # Additional for PDF scans
    notices: List[Dict[str, Any]] = []   # Additional for PDF scans
    passes: List[Dict[str, Any]] = []
    incomplete: List[Dict[str, Any]] = []
    inapplicable: List[Dict[str, Any]] = []
    unified_results: Optional[Dict[str, Any]] = None
    accessibility_report: Optional[str] = None  # Free-text AI analysis report
    analysis_type: Optional[str] = None  # e.g., 'ai_vision_free_text'
    scanDuration: Optional[int] = None  # Optional for failed scans
    status: str = "completed"
    user_id: str
    user_email: str
    error_message: Optional[str] = None  # Error message for failed scans
    credits_reserved: Optional[bool] = False
    credits_required: Optional[int] = None

class HealthService(BaseModel):
    api: str
    cloud_tasks: str
    firestore: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: HealthService

class UserPreferences(BaseModel):
    web_scan_modules: List[str] = Field(
        default=['axe', 'nu', 'axTree', 'galen', 'links'],
        description="List of enabled scan modules"
    )

# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now(CET)
    logger.info(f"{start_time.isoformat()} - {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = (datetime.now(CET) - start_time).total_seconds()
    logger.info(f"Request processed in {process_time:.3f}s")
    
    return response

# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with actual dependency verification"""
    try:
        # Check Cloud Tasks - verify we can reach the service
        cloud_tasks_status = "unknown"
        if tasks_client:
            try:
                # Just verify client exists and is configured
                cloud_tasks_status = "healthy"
            except Exception:
                cloud_tasks_status = "unhealthy"
        else:
            cloud_tasks_status = "unhealthy"
            
        # Check Firestore - actually try a read operation
        firestore_status = "unknown"
        if db:
            try:
                # Quick read to verify connectivity (read a single doc limit 1)
                list(db.collection('users').limit(1).stream())
                firestore_status = "healthy"
            except Exception as e:
                logger.warning(f"Firestore health check failed: {e}")
                firestore_status = "unhealthy"
        else:
            firestore_status = "unhealthy"
        
        # Check Firebase Storage
        storage_status = "unknown"
        if storage_bucket:
            try:
                # Verify bucket exists (doesn't incur read costs)
                if storage_bucket.exists():
                    storage_status = "healthy"
                else:
                    storage_status = "unhealthy"
            except Exception as e:
                logger.warning(f"Storage health check failed: {e}")
                storage_status = "unhealthy"
        else:
            storage_status = "unavailable"
        
        # Determine overall status
        all_healthy = all(s == "healthy" for s in [cloud_tasks_status, firestore_status])
        overall_status = "healthy" if all_healthy else "degraded"
        
        # If critical services are down, mark as unhealthy
        if firestore_status == "unhealthy":
            overall_status = "unhealthy"
            
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(CET).isoformat(),
            services=HealthService(
                api="healthy",
                cloud_tasks=cloud_tasks_status,
                firestore=firestore_status
            )
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(CET).isoformat(),
            services=HealthService(
                api="healthy",
                cloud_tasks="unknown",
                firestore="unknown"
            )
        )


# =============================================================================
# Contact Form Endpoint (Public - proxies to authenticated mailing service)
# =============================================================================

@app.post("/contact")
@limiter.limit("5/minute")
async def submit_contact_form(request: Request, contact_data: ContactFormRequest):
    """
    Submit a contact form message.
    
    This endpoint is public (no auth required) but proxies to the internal
    mailing service using authenticated service-to-service communication.
    Rate limited to prevent abuse.
    """
    try:
        logger.info(f"Contact form submission from: {contact_data.email}")
        
        # Get ID token for authenticated call to mailing service
        id_token = await get_service_auth_token(MAILING_URL)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authentication header if we got a token
        if id_token:
            headers["Authorization"] = f"Bearer {id_token}"
        else:
            logger.warning("No service auth token available for mailing service call")
        
        # Call the mailing service
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{MAILING_URL}/contact",
                json={
                    "name": contact_data.name,
                    "email": contact_data.email,
                    "subject": contact_data.subject,
                    "message": contact_data.message
                },
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"Contact form submitted successfully for: {contact_data.email}")
                return {"success": True, "message": "Message sent successfully"}
            else:
                logger.error(f"Mailing service error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to send message. Please try again later."
                )
                
    except httpx.TimeoutException:
        logger.error("Mailing service timeout")
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable. Please try again later."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Contact form error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred. Please try again later."
        )


@app.post("/web-scan/scan", response_model=ScanTaskResponse)
@limiter.limit("20/15minutes")
async def scan_website(
    request: Request, 
    scan_request: ScanRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)  # Require authentication
):
    """
    Create a scan task in Cloud Tasks queue (requires authentication).
    
    Credit cost: 1 credit per active module (max 5 credits for all modules).
    Credits are deducted AFTER scan completes successfully.
    """
    url = scan_request.url
    user_id = current_user['uid']
    user_email = current_user['email']
    
    logger.info(f"Authenticated user - uid: {user_id}, email: {user_email}")
    
    # Validate input
    if not url or not isinstance(url, str):
        raise HTTPException(
            status_code=400,
            detail="URL is required and must be a string"
        )
    
    # Calculate required credits based on modules (1 credit per module)
    modules_to_run = scan_request.modules if scan_request.modules else AVAILABLE_WEB_MODULES
    # Filter to only valid modules
    modules_to_run = [m for m in modules_to_run if m in AVAILABLE_WEB_MODULES]
    if not modules_to_run:
        modules_to_run = AVAILABLE_WEB_MODULES
    
    credits_required = len(modules_to_run)
    
    logger.info(f"Creating scan task for user {user_email} ({user_id}): {url}")
    logger.info(f"Modules to run: {modules_to_run} (credits required: {credits_required})")
    
    try:
        if not tasks_client or not parent:
            logger.error(f"Cloud Tasks not initialized: tasks_client={tasks_client is not None}, parent={parent is not None}")
            raise HTTPException(
                status_code=503,
                detail="Cloud Tasks service is unavailable"
            )
        
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Generate unique task ID first (needed for reservation)
        task_id = str(uuid.uuid4())
        
        # Reserve credits atomically BEFORE creating the scan task
        # This prevents concurrent scans from using the same credits
        success, error_message = reserve_credits(user_id, "web_scan", credits_required, task_id)
        
        if not success:
            # Get current credit info for error message
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            web_scan_credits = user_data.get('web_scan_credits', 0)
            reserved_credits = user_data.get('reserved_web_scan_credits', 0)
            available_credits = web_scan_credits - reserved_credits
            
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": f"Insufficient web scan credits. You need {credits_required} credits ({len(modules_to_run)} modules × 1 credit each).",
                    "credits_required": credits_required,
                    "credits_available": available_credits,
                    "credits_total": web_scan_credits,
                    "credits_reserved": reserved_credits,
                    "modules_requested": modules_to_run
                }
            )
        
        # Create task payload with user information and credit info
        task_payload = {
            "task_id": task_id,
            "url": url,
            "user_id": user_id,
            "user_email": user_email,
            "modules": modules_to_run,
            "credits_required": credits_required,
            "credits_reserved": True,  # Flag indicating credits are already reserved
            "created_at": datetime.now(CET).isoformat()
        }
        
        try:
            # Create Cloud Task
            task_name = task_id.replace("-", "_")
            
            task = {
                "name": f"{parent}/tasks/{task_name}",
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": f"{WORKER_URL}/scan",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": json.dumps(task_payload).encode(),
                    "oidc_token": {
                        "service_account_email": f"{os.environ.get('PROJECT_NUMBER', '')}-compute@developer.gserviceaccount.com",
                        "audience": WORKER_URL
                    }
                }
            }
            
            # Submit task to queue
            response = tasks_client.create_task(parent=parent, task=task)
            
            logger.info(f"Task created: {response.name} - Credits reserved, will be finalized upon completion")
            
            return ScanTaskResponse(
                task_id=task_id,
                status="queued",
                url=url,
                created_at=task_payload["created_at"]
            )
        except Exception as task_error:
            # If task creation fails, refund the reserved credits
            logger.error(f"Task creation failed, refunding credits: {task_error}")
            finalize_credits(user_id, "web_scan", credits_required, task_id, success=False, reason="Task creation failed")
            raise
            
    except Exception as e:
        logger.error(f"Failed to create scan task", exc_info=True)
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception str: {str(e)}")
        logger.error(f"Exception repr: {repr(e)}")
        error_msg = str(e) if str(e) else repr(e)
        if "NOT_FOUND" in error_msg:
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable. Please try again later."
            )
        # Log full error internally but return generic message to client
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Please try again later."
        )

# Deprecated: sync scan endpoint removed - use /web-scan/scan instead

@app.get("/web-scan/status/{task_id}")
async def get_scan_status(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_user)
):
    """Get the status of a scan task. Verifies user ownership if authenticated."""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Check if result exists in Firestore
        doc_ref = db.collection('web_scan_results').document(task_id)
        doc = doc_ref.get()
        
        if doc.exists:
            result = doc.to_dict()
            
            # Verify ownership if user is authenticated
            if current_user and result.get("user_id") and result.get("user_id") != current_user.get("uid"):
                raise HTTPException(status_code=403, detail="Access denied - you don't own this scan")
            
            return JSONResponse(content={
                "task_id": task_id,
                "status": result.get("status", "completed"),
                "url": result.get("url"),
                "created_at": result.get("timestamp"),
                "result": result
            })
        else:
            return JSONResponse(content={
                "task_id": task_id,
                "status": "processing",
                "message": "Task is being processed by the worker"
            })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task status")

@app.get("/web-scan/result/{task_id}")
async def get_scan_result(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_user)
):
    """Get scan result - returns metadata for pending scans, full results for completed scans. Verifies user ownership if authenticated."""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Get metadata from Firestore
        doc_ref = db.collection('web_scan_results').document(task_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Scan result not found")
        
        metadata = doc.to_dict()
        
        # Verify ownership if user is authenticated
        if current_user and metadata.get("user_id") and metadata.get("user_id") != current_user.get("uid"):
            raise HTTPException(status_code=403, detail="Access denied - you don't own this scan")
        
        # If scan is completed and has storage_url, fetch full results from Storage
        if metadata.get('status') == 'completed' and metadata.get('storage_path'):
            if not storage_bucket:
                logger.error("Storage bucket not available, returning metadata only")
            else:
                try:
                    storage_path = metadata.get('storage_path')
                    logger.info(f"Fetching full scan results from Storage: {storage_path}")
                    
                    blob = storage_bucket.blob(storage_path)
                    
                    if blob.exists():
                        # Download and parse JSON
                        json_content = blob.download_as_text()
                        full_results = json.loads(json_content)
                        
                        logger.info(f"✅ Retrieved full scan results from Storage for task {task_id}")
                        return JSONResponse(content=full_results)
                    else:
                        logger.warning(f"Storage blob not found: {storage_path}, returning metadata")
                        
                except Exception as storage_error:
                    logger.error(f"Error fetching from Storage: {storage_error}", exc_info=True)
                    # Fall through to return metadata
        
        # Convert datetime objects to ISO format strings recursively
        def convert_datetime_objects(obj):
            if isinstance(obj, dict):
                return {k: convert_datetime_objects(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime_objects(item) for item in obj]
            elif hasattr(obj, 'isoformat'):  # datetime objects
                return obj.isoformat()
            else:
                return obj
        
        metadata = convert_datetime_objects(metadata)
        
        return JSONResponse(content=metadata)
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error getting scan result: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get scan result")


@app.get("/web-scan/result/{task_id}/full")
async def get_full_scan_result(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Fetch full scan results from Firebase Storage (requires authentication)"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        if not storage_bucket:
            raise HTTPException(status_code=503, detail="Storage service unavailable")
        
        # Get metadata from Firestore to verify ownership
        doc_ref = db.collection('web_scan_results').document(task_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        metadata = doc.to_dict()
        
        # Verify user owns this scan
        if metadata.get("user_id") != current_user["uid"]:
            raise HTTPException(status_code=403, detail="Unauthorized - you don't own this scan")
        
        # Get storage path from metadata
        storage_path = metadata.get("storage_path")
        if not storage_path:
            # Fallback: construct path from user_id and task_id
            user_id = metadata.get("user_id")
            storage_path = f"web-scan-results/{user_id}/{task_id}.json"
            logger.info(f"Storage path not in metadata, using constructed path: {storage_path}")
        
        logger.info(f"Fetching full scan result from Storage: {storage_path}")
        
        # Fetch full results from Firebase Storage
        try:
            blob = storage_bucket.blob(storage_path)
            
            if not blob.exists():
                logger.error(f"Storage blob not found: {storage_path}")
                raise HTTPException(status_code=404, detail="Scan results not found in storage")
            
            # Download and parse JSON
            json_content = blob.download_as_text()
            full_results = json.loads(json_content)
            
            logger.info(f"✅ Retrieved full scan results from Storage for task {task_id}")
            
            # Return full results
            return JSONResponse(content=full_results)
            
        except Exception as storage_error:
            logger.error(f"Error fetching from Storage: {storage_error}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to fetch scan results from storage")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching full scan results: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch scan results")

@app.post("/web-scan/store-result")
async def store_scan_result(
    result: Dict[str, Any],
    request: Request,
    claims: dict = Depends(verify_cloud_service_token)
):
    """
    Store web scan metadata in Firestore (full results already in Firebase Storage).
    Called by worker services - requires OIDC token from authorized service account.
    Credits are deducted here AFTER scan completes successfully.
    Credit cost: 1 per module executed.
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        task_id = result.get("id")
        user_id = result.get("user_id")
        
        if not task_id or not user_id:
            raise HTTPException(status_code=400, detail="Missing required fields: id or user_id")
        
        logger.info(f"Storing web scan metadata for task {task_id} with URL: {result.get('url')}")
        logger.info(f"User info: user_id={user_id}, user_email={result.get('user_email')}")
        logger.info(f"Storage URL: {result.get('storage_url')}")
        
        # Determine credits to deduct based on modules executed
        # First check if credits_required was passed from the task
        credits_to_deduct = result.get('credits_required')
        
        # If not, calculate from modules executed
        if credits_to_deduct is None:
            modules_executed = result.get('unified_results', {}).get('modules_executed', [])
            if modules_executed:
                credits_to_deduct = len(modules_executed)
            else:
                # Default: count from modules in task or use 5 (all modules)
                modules_from_task = result.get('modules', AVAILABLE_WEB_MODULES)
                credits_to_deduct = len(modules_from_task) if modules_from_task else 5
        
        logger.info(f"Credits to deduct: {credits_to_deduct}")
        
        # Store metadata in Firestore (renamed collection for clarity)
        doc_ref = db.collection('web_scan_results').document(task_id)
        
        # Ensure proper timestamp format
        if not result.get('timestamp'):
            result['timestamp'] = datetime.now(CET).isoformat()
        
        if not result.get('created_at'):
            result['created_at'] = datetime.now(CET).isoformat()
        
        # Add credits info to stored result
        result['credits_deducted'] = credits_to_deduct
        
        # Store the metadata
        doc_ref.set(result)
        
        logger.info(f"Web scan metadata stored successfully for task {task_id}")
        
        # Finalize credits (deduct if successful, refund if failed)
        credits_reserved = result.get('credits_reserved', False)
        scan_status = result.get('status')
        
        if user_id:
            if credits_reserved:
                # Credits were reserved at scan initiation, now finalize them
                if scan_status == 'completed':
                    finalize_credits(
                        user_id=user_id,
                        credit_type="web_scan",
                        amount=credits_to_deduct,
                        scan_id=task_id,
                        success=True,
                        reason=f"Web scan completed successfully ({credits_to_deduct} modules)"
                    )
                    logger.info(f"Finalized {credits_to_deduct} web scan credits for user {user_id}")
                elif scan_status == 'failed':
                    finalize_credits(
                        user_id=user_id,
                        credit_type="web_scan",
                        amount=credits_to_deduct,
                        scan_id=task_id,
                        success=False,
                        reason=f"Web scan failed: {result.get('error', 'Unknown error')}"
                    )
                    logger.info(f"Refunded {credits_to_deduct} web scan credits for user {user_id} (scan failed)")
            else:
                # Legacy path: credits not reserved, deduct directly (for backward compatibility)
                if scan_status == 'completed':
                    try:
                        user_ref = db.collection('users').document(user_id)
                        user_doc = user_ref.get()
                        if user_doc.exists:
                            current_credits = user_doc.to_dict().get('web_scan_credits', 0)
                            new_credits = max(0, current_credits - credits_to_deduct)  # Never go below 0
                            user_ref.update({
                                'web_scan_credits': new_credits,
                                'updated_at': datetime.now(CET)
                            })
                            logger.info(f"Deducted {credits_to_deduct} web scan credits for user {user_id} (legacy path)")
                            
                            # Log credit usage
                            log_credit_usage(
                                user_id=user_id,
                                credit_type="web_scan",
                                amount=credits_to_deduct,
                                reason=f"Web scan completed successfully ({credits_to_deduct} modules)",
                                scan_id=task_id
                            )
                    except Exception as e:
                        logger.error(f"Error deducting/logging credit usage: {e}")
        
        # Trigger integration tasks if user has integrations enabled
        if user_id and result.get('status') == 'completed':
            try:
                # Fetch full scan data from Storage for integrations
                storage_path = result.get('storage_path')
                if storage_path and storage_bucket:
                    logger.info(f"Fetching full scan data from Storage for integrations: {storage_path}")
                    try:
                        blob = storage_bucket.blob(storage_path)
                        if blob.exists():
                            full_scan_data = json.loads(blob.download_as_text())
                            
                            # Queue integration tasks with full scan data
                            background_task = asyncio.create_task(
                                asyncio.to_thread(queue_integration_tasks, user_id, full_scan_data)
                            )
                            logger.info(f"Started integration task queuing for user {user_id} with full scan data")
                        else:
                            logger.warning(f"Storage blob not found: {storage_path}, queuing with metadata only")
                            background_task = asyncio.create_task(
                                asyncio.to_thread(queue_integration_tasks, user_id, result)
                            )
                    except Exception as storage_error:
                        logger.error(f"Error fetching full scan data from Storage for integrations: {storage_error}")
                        # Fall back to metadata only if storage fetch fails
                        background_task = asyncio.create_task(
                            asyncio.to_thread(queue_integration_tasks, user_id, result)
                        )
                        logger.warning(f"Queued integration tasks with metadata only for user {user_id}")
                else:
                    logger.warning(f"No storage_path or storage_bucket unavailable for scan {task_id}, queuing with metadata only")
                    background_task = asyncio.create_task(
                        asyncio.to_thread(queue_integration_tasks, user_id, result)
                    )
            except Exception as e:
                logger.error(f"Error starting integration task queuing for user {user_id}: {e}")
        
        return {"status": "success", "task_id": task_id}
        
    except Exception as e:
        logger.error(f"Error storing web scan metadata: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/web-scan/recent-results")
async def get_recent_results(limit: int = 10):
    """Get recent scan results metadata"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Query recent results from new collection
        results = []
        docs = db.collection('web_scan_results').order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit).stream()
        
        for doc in docs:
            data = doc.to_dict()
            summary = data.get("summary", {})
            results.append({
                "task_id": doc.id,
                "url": data.get("url"),
                "timestamp": data.get("timestamp"),
                "violations_count": summary.get("total_violations", 0),
                "status": data.get("status", "completed")
            })
        
        return JSONResponse(content={"results": results})
    except Exception as e:
        logger.error(f"Error getting recent results: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent results")

@app.post("/cleanup")
async def cleanup_old_scans():
    """
    DEPRECATED: Web scans now use permanent Firebase Storage. This endpoint is kept for backward compatibility.
    Only cleans up old PDF scan results older than 30 minutes.
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Calculate cutoff time (30 minutes ago)
        cutoff_time = datetime.now(CET) - timedelta(minutes=30)
        
        logger.info(f"Starting cleanup of PDF scan results older than {cutoff_time.isoformat()}")
        logger.info("Note: Web scans now use permanent storage and are not cleaned up automatically")
        
        # Only clean up PDF scan results (web scans are permanent)
        old_scans_query = db.collection('pdf_scan_results').where('created_at', '<', cutoff_time)
        old_scans = old_scans_query.stream()
        
        deleted_count = 0
        
        # Delete old scans in batches
        batch = db.batch()
        batch_size = 0
        max_batch_size = 500  # Firestore limit
        
        for scan_doc in old_scans:
            batch.delete(scan_doc.reference)
            batch_size += 1
            
            # Commit batch when it reaches max size
            if batch_size >= max_batch_size:
                batch.commit()
                deleted_count += batch_size
                logger.info(f"Deleted batch of {batch_size} PDF scan results")
                batch = db.batch()
                batch_size = 0
        
        # Commit remaining items in batch
        if batch_size > 0:
            batch.commit()
            deleted_count += batch_size
            logger.info(f"Deleted final batch of {batch_size} PDF scan results")
        
        logger.info(f"Cleanup completed. Deleted {deleted_count} old PDF scan results.")
        return JSONResponse(content={
            "message": "Cleanup successful (PDF scans only - web scans use permanent storage)", 
            "deleted_count": deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Cleanup failed")


@app.post("/admin/cleanup-expired-scans")
async def cleanup_expired_scans_endpoint(
    request: Request,
    claims: dict = Depends(verify_cloud_service_token)
):
    """
    Admin endpoint to clean up scan results older than 24 months.
    
    Called by Cloud Scheduler daily at 03:00 CET.
    Requires OIDC token from authorized service account.
    
    This enforces the Privacy Policy retention period:
    - Scan results are stored for a maximum of 24 months
    - Users are notified before their scans are deleted
    """
    try:
        from cronjob import cleanup_expired_scans
        
        deleted_count = cleanup_expired_scans()
        
        logger.info(f"Expired scan cleanup completed. Deleted {deleted_count} scans older than 24 months.")
        return JSONResponse(content={
            "message": "Expired scan cleanup successful",
            "deleted_count": deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error during expired scan cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Expired scan cleanup failed")


@app.post("/admin/delete-user-data/{user_id}")
async def delete_user_data_endpoint(
    user_id: str,
    request: Request,
    claims: dict = Depends(verify_cloud_service_token)
):
    """
    Admin endpoint to delete all data associated with a user account.
    
    Called when a user requests account deletion (GDPR compliance).
    Requires OIDC token from authorized service account.
    
    This removes:
    - User profile
    - All scan results
    - Integration configurations
    - API keys
    - Usage history
    - Storage files
    """
    try:
        from cronjob import delete_user_data
        
        if not user_id or len(user_id) < 5:
            raise HTTPException(status_code=400, detail="Invalid user ID")
        
        summary = delete_user_data(user_id)
        
        logger.info(f"User data deletion completed for {user_id}")
        return JSONResponse(content={
            "message": f"User data deletion successful for {user_id}",
            "deleted_summary": summary
        })
        
    except Exception as e:
        logger.error(f"Error during user data deletion for {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="User data deletion failed")


@app.post("/admin/cleanup-old-scans")
async def cleanup_old_scans_admin(
    request: Request,
    claims: dict = Depends(verify_cloud_service_token)
):
    """
    Admin endpoint to clean up temporary PDF scan results (older than 30 minutes).
    
    Called by Cloud Scheduler every 30 minutes.
    Requires OIDC token from authorized service account.
    Web scans use permanent storage and are NOT cleaned up by this endpoint.
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Calculate cutoff time (30 minutes ago)
        cutoff_time = datetime.now(CET) - timedelta(minutes=30)
        
        logger.info(f"Starting cleanup of PDF scan results older than {cutoff_time.isoformat()}")
        
        # Only clean up PDF scan results (web scans are permanent)
        old_scans_query = db.collection('pdf_scan_results').where('created_at', '<', cutoff_time)
        old_scans = old_scans_query.stream()
        
        deleted_count = 0
        batch = db.batch()
        batch_size = 0
        max_batch_size = 500
        
        for scan_doc in old_scans:
            batch.delete(scan_doc.reference)
            batch_size += 1
            
            if batch_size >= max_batch_size:
                batch.commit()
                deleted_count += batch_size
                batch = db.batch()
                batch_size = 0
        
        if batch_size > 0:
            batch.commit()
            deleted_count += batch_size
        
        logger.info(f"Cleanup completed. Deleted {deleted_count} old PDF scan results.")
        return JSONResponse(content={
            "message": "PDF scan cleanup successful",
            "deleted_count": deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error during scan cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Scan cleanup failed")


@app.post("/admin/expire-api-keys")
async def expire_api_keys_admin(
    request: Request,
    claims: dict = Depends(verify_cloud_service_token)
):
    """
    Admin endpoint to mark expired API keys as revoked.
    
    Called by Cloud Scheduler every hour.
    Requires OIDC token from authorized service account.
    Finds API keys where expires_at < now and revoked=false, then marks them as revoked.
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        now = datetime.now(CET)
        
        # Query for non-revoked keys that have expired
        expired_keys_query = db.collection('api_keys')\
            .where('revoked', '==', False)\
            .where('expires_at', '<', now)
        
        expired_keys = expired_keys_query.stream()
        
        revoked_count = 0
        batch = db.batch()
        batch_size = 0
        max_batch_size = 500
        
        for key_doc in expired_keys:
            batch.update(key_doc.reference, {
                'revoked': True,
                'revoked_at': now,
                'revoked_reason': 'expired'
            })
            batch_size += 1
            
            if batch_size >= max_batch_size:
                batch.commit()
                revoked_count += batch_size
                batch = db.batch()
                batch_size = 0
        
        if batch_size > 0:
            batch.commit()
            revoked_count += batch_size
        
        logger.info(f"Expired API key cleanup completed. Revoked {revoked_count} expired keys.")
        return JSONResponse(content={
            "message": "API key expiration cleanup successful",
            "revoked_count": revoked_count
        })
        
    except Exception as e:
        logger.error(f"Error during API key expiration: {str(e)}")
        raise HTTPException(status_code=500, detail="API key expiration failed")


@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse(content={"message": "LumTrails Main API"})

# 404 handler - preserve HTTPException details
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    # If it's an HTTPException with a detail, use that detail
    if hasattr(exc, 'detail') and exc.detail:
        return JSONResponse(content={"detail": exc.detail}, status_code=404)
    return JSONResponse(content={"error": "Endpoint not found"}, status_code=404)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {str(exc)}")
    return JSONResponse(content={"error": "Internal server error"}, status_code=500)

# User-specific scan endpoints

@app.get("/web-scan/my-scans")
async def get_user_scans(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get scan results METADATA for the authenticated user (list view only).
    
    Returns only Firestore metadata for the list view. For full scan details,
    use the /web-scan/result/{task_id}/full endpoint.
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        user_id = current_user['uid']
        logger.info(f"Getting scans for user: {user_id}")
        
        # Query scans for this user with Firestore-side pagination
        query = db.collection('web_scan_results')\
            .where('user_id', '==', user_id)\
            .order_by('created_at', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .offset(offset)
        
        scans = []
        for doc in query.stream():
            scan_data = doc.to_dict()
            
            # Convert datetime objects to ISO format strings
            def convert_datetime_objects(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_datetime_objects(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime_objects(item) for item in obj]
                else:
                    return obj
            
            scan_data = convert_datetime_objects(scan_data)
            
            # Get summary from metadata
            summary = scan_data.get("summary", {})
            
            # Return ONLY metadata - NO Storage fetch for list view
            scans.append({
                "id": doc.id,
                "url": scan_data.get("url"),
                "timestamp": scan_data.get("timestamp"),
                "created_at": scan_data.get("created_at"),
                "violations_count": summary.get("total_violations", 0),
                "passes_count": summary.get("total_passes", 0),
                "html_errors_count": summary.get("total_html_errors", 0),
                "broken_links_count": summary.get("total_broken_links", 0),
                "scan_duration": scan_data.get("scan_duration_ms"),
                "status": scan_data.get("status", "completed"),
                "modules_executed": scan_data.get("modules_executed", []),
                "summary": summary
                # NO full_result - use /web-scan/result/{task_id}/full for details
            })
        
        return JSONResponse(content={
            "scans": scans,
            "user_id": user_id,
            "total": len(scans),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.error(f"Error getting user scans: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user scans")

@app.delete("/web-scan/my-scans/{scan_id}")
async def delete_user_scan(
    scan_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a specific scan result for the authenticated user"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        user_id = current_user['uid']
        logger.info(f"Deleting scan {scan_id} for user: {user_id}")
        
        # Get the scan document from web_scan_results collection
        doc_ref = db.collection('web_scan_results').document(scan_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        # Verify the scan belongs to the user
        scan_data = doc.to_dict()
        if scan_data.get('user_id') != user_id:
            logger.warning(f"User {user_id} attempted to delete scan {scan_id} belonging to {scan_data.get('user_id')}")
            raise HTTPException(status_code=403, detail="You don't have permission to delete this scan")
        
        # Delete the scan metadata from Firestore
        doc_ref.delete()
        
        # Also delete the full scan results from Firebase Storage if storage_path exists
        if storage_bucket and scan_data.get('storage_path'):
            try:
                storage_path = scan_data.get('storage_path')
                blob = storage_bucket.blob(storage_path)
                if blob.exists():
                    blob.delete()
                    logger.info(f"Deleted Storage file: {storage_path}")
            except Exception as storage_error:
                logger.error(f"Error deleting Storage file: {storage_error}")
                # Continue anyway - metadata is deleted
        
        logger.info(f"Successfully deleted scan {scan_id} for user {user_id}")
        
        return JSONResponse(content={
            "message": "Scan deleted successfully",
            "scan_id": scan_id
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete scan")

# PDF Scan endpoints

def count_pdf_pages(file_content: bytes) -> int:
    """
    Count the number of pages in a PDF file.
    Uses PyPDF2 if available, otherwise falls back to regex pattern matching.
    
    Args:
        file_content: Raw PDF file bytes
        
    Returns:
        Number of pages in the PDF
    """
    import io
    try:
        # Try using PyPDF2 first (most reliable)
        try:
            from PyPDF2 import PdfReader
            pdf_reader = PdfReader(io.BytesIO(file_content))
            page_count = len(pdf_reader.pages)
            logger.info(f"PDF page count (PyPDF2): {page_count}")
            return page_count
        except ImportError:
            logger.warning("PyPDF2 not available, falling back to pattern matching")
        
        # Fallback: count /Page objects in PDF (less reliable but works without extra deps)
        import re
        # Look for /Type /Page patterns (each page has this)
        page_pattern = rb'/Type\s*/Page[^s]'
        matches = re.findall(page_pattern, file_content)
        page_count = len(matches)
        
        # If that didn't work, try counting /Count entries in page tree
        if page_count == 0:
            count_pattern = rb'/Count\s+(\d+)'
            counts = re.findall(count_pattern, file_content)
            if counts:
                page_count = max(int(c) for c in counts)
        
        # Minimum 1 page
        page_count = max(1, page_count)
        logger.info(f"PDF page count (regex): {page_count}")
        return page_count
        
    except Exception as e:
        logger.error(f"Error counting PDF pages: {e}")
        # Default to 1 page if we can't count
        return 1


@app.post("/pdf-scan/scan", response_model=PDFScanTaskResponse)
@limiter.limit("10/15minutes")
async def scan_pdf(
    request: Request,
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a PDF scan task in Cloud Tasks queue using AI-powered analysis (requires authentication).
    
    Credit cost: 1 credit per page in the PDF document.
    Credits are checked BEFORE scanning - if you don't have enough credits for all pages,
    the scan will not run and you'll receive a 402 error with the required credits.
    """
    user_id = current_user['uid']
    user_email = current_user['email']
    
    logger.info(f"Authenticated user - uid: {user_id}, email: {user_email}")
    
    # Validate file
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed"
        )
    
    logger.info(f"Creating PDF scan task for user {user_email} ({user_id}): {file.filename}")
    
    try:
        if not tasks_client or not pdf_parent:
            raise HTTPException(
                status_code=503,
                detail="Cloud Tasks service is unavailable"
            )
        
        if not storage_bucket:
            raise HTTPException(
                status_code=503,
                detail="Firebase Storage service is unavailable"
            )
        
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Read file content
        content = await file.read()
        
        # Check file size after reading
        if len(content) > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(
                status_code=400,
                detail="File size exceeds 50MB limit"
            )
        
        # Count pages in PDF BEFORE queueing to check credits
        page_count = count_pdf_pages(content)
        credits_required = page_count
        
        logger.info(f"PDF has {page_count} pages, checking credits (required: {credits_required})...")
        
        # Reserve credits atomically BEFORE creating the scan task
        success, error_message = reserve_credits(user_id, "pdf_scan", credits_required, task_id)
        
        if not success:
            # Get current credit info for error message
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            pdf_scan_credits = user_data.get('pdf_scan_credits', 0)
            reserved_credits = user_data.get('reserved_pdf_scan_credits', 0)
            available_credits = pdf_scan_credits - reserved_credits
            
            raise HTTPException(
                status_code=402,
                detail={
                    "error": "insufficient_credits",
                    "message": f"Insufficient PDF scan credits. You need {credits_required} credits ({page_count} pages × 1 credit each).",
                    "credits_required": credits_required,
                    "credits_available": available_credits,
                    "credits_total": pdf_scan_credits,
                    "credits_reserved": reserved_credits,
                    "page_count": page_count
                }
            )
        
        logger.info(f"Reserved {credits_required} PDF scan credits. Proceeding with scan.")
        
        try:
            # Get user's preferred language for the scan
            user_ref = db.collection('users').document(user_id)
            user_doc = user_ref.get()
            user_data = user_doc.to_dict() if user_doc.exists else {}
            user_language = user_data.get('preferredLanguage', 'en')
            logger.info(f"User preferred language: {user_language}")
            
            # Store PDF in Firebase Storage first
            logger.info(f"Storing PDF in Firebase Storage for task {task_id}")
            storage_path = await store_pdf_in_firebase_storage(content, file.filename, task_id)
            
            # Create task payload with storage path and credit info
            task_payload = {
                "task_id": task_id,
                "storage_path": storage_path,
                "file_name": file.filename,
                "file_size": len(content),
                "page_count": page_count,
                "credits_required": credits_required,
                "credits_reserved": True,  # Flag indicating credits are already reserved
                "user_id": user_id,
                "user_email": user_email,
                "created_at": datetime.now(CET).isoformat(),
                "language": user_language  # Pass user's preferred language to the scanner
            }
            
            # Create Cloud Task
            task_name = task_id.replace("-", "_")
            
            task = {
                "name": f"{pdf_parent}/tasks/{task_name}",
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": f"{PDF_WORKER_URL}/scan",
                    "headers": {
                        "Content-Type": "application/json"
                    },
                    "body": json.dumps(task_payload).encode(),
                    "oidc_token": {
                        "service_account_email": f"{os.environ.get('PROJECT_NUMBER', '')}-compute@developer.gserviceaccount.com",
                        "audience": PDF_WORKER_URL
                    }
                }
            }
            
            # Submit task to queue
            response = tasks_client.create_task(parent=pdf_parent, task=task)
            
            logger.info(f"PDF scan task created: {response.name} - Credits reserved, will be finalized upon completion")
            
            return PDFScanTaskResponse(
                task_id=task_id,
                status="queued",
                file_name=file.filename,
                created_at=task_payload["created_at"]
            )
        except Exception as task_error:
            # If task creation or storage fails, refund the reserved credits
            logger.error(f"PDF task creation failed, refunding credits: {task_error}")
            finalize_credits(user_id, "pdf_scan", credits_required, task_id, success=False, reason="Task creation failed")
            # Clean up uploaded PDF if it exists
            try:
                if 'storage_path' in locals() and storage_path and storage_bucket:
                    blob = storage_bucket.blob(storage_path)
                    blob.delete()
                    logger.info(f"Cleaned up PDF after task creation failure: {storage_path}")
            except Exception as cleanup_error:
                logger.warning(f"Could not clean up PDF after task failure: {cleanup_error}")
            raise
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Failed to create PDF scan task: {str(e)}", exc_info=True)
        # Clean up uploaded PDF if it exists
        try:
            if 'storage_path' in locals() and storage_path and storage_bucket:
                blob = storage_bucket.blob(storage_path)
                blob.delete()
                logger.info(f"Cleaned up PDF after error: {storage_path}")
        except Exception as cleanup_error:
            logger.warning(f"Could not clean up PDF after error: {cleanup_error}")
        if "NOT_FOUND" in str(e):
            raise HTTPException(
                status_code=503,
                detail="Service temporarily unavailable. Please try again later."
            )
        # Log full error internally but return generic message to client
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Please try again later."
        )

@app.get("/pdf-scan/status/{task_id}")
async def get_pdf_scan_status(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_user)
):
    """Get the status of a PDF scan task. Verifies user ownership if authenticated."""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Check if result exists in Firestore
        doc_ref = db.collection('pdf_scan_results').document(task_id)
        doc = doc_ref.get()
        
        if doc.exists:
            result = doc.to_dict()
            
            # Verify ownership if user is authenticated
            if current_user and result.get("user_id") and result.get("user_id") != current_user.get("uid"):
                raise HTTPException(status_code=403, detail="Access denied - you don't own this scan")
            
            return JSONResponse(content={
                "task_id": task_id,
                "status": result.get("status", "completed"),
                "file_name": result.get("file_name"),
                "scan_type": result.get("scan_type"),
                "created_at": result.get("timestamp"),
                "result": result
            })
        else:
            return JSONResponse(content={
                "task_id": task_id,
                "status": "processing",
                "message": "PDF scan task is being processed by the worker"
            })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF scan status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get PDF scan status")

@app.get("/pdf-scan/result/{task_id}")
async def get_pdf_scan_result(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_optional_user)
):
    """Get the result of a completed PDF scan task. Verifies user ownership if authenticated."""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Get result from Firestore
        doc_ref = db.collection('pdf_scan_results').document(task_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="PDF scan result not found")
        
        result = doc.to_dict()
        
        # Verify ownership if user is authenticated
        if current_user and result.get("user_id") and result.get("user_id") != current_user.get("uid"):
            raise HTTPException(status_code=403, detail="Access denied - you don't own this scan")
        
        # Convert datetime objects to ISO format strings recursively
        def convert_datetime_objects(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, dict):
                return {key: convert_datetime_objects(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_datetime_objects(item) for item in obj]
            else:
                return obj
        
        result = convert_datetime_objects(result)
        
        return JSONResponse(content=result)
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        logger.error(f"Error getting PDF scan result: {e}")
        raise HTTPException(status_code=500, detail="Failed to get PDF scan result")

@app.post("/pdf-scan/store-result")
async def store_pdf_scan_result(
    result: PDFScanResult,
    request: Request,
    claims: dict = Depends(verify_cloud_service_token)
):
    """
    Store PDF scan result from worker (called by worker service).
    Called by worker services - requires OIDC token from authorized service account.
    Credits are deducted here AFTER scan completes successfully.
    Credit cost: 1 per page scanned.
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Convert result to dictionary for storage
        result_dict = result.dict()
        
        # Add server timestamp
        result_dict['created_at'] = firestore.SERVER_TIMESTAMP
        result_dict['stored_at'] = datetime.now(CET)
        
        # Determine credits to deduct
        # First check if credits_required was passed from the task payload
        credits_to_deduct = result_dict.get('credits_required')
        
        # If not, use pages_processed count or page_count
        if credits_to_deduct is None:
            if hasattr(result, 'pages_processed') and result.pages_processed:
                credits_to_deduct = len(result.pages_processed)
            elif result_dict.get('page_count'):
                credits_to_deduct = result_dict.get('page_count')
            else:
                # Fall back to unified_results.pages_analyzed
                credits_to_deduct = result_dict.get('unified_results', {}).get('pages_analyzed', 1)
        
        # Store credits info in result
        result_dict['credits_deducted'] = credits_to_deduct
        
        # Store in Firestore
        doc_ref = db.collection('pdf_scan_results').document(result.id)
        doc_ref.set(result_dict)
        
        logger.info(f"Stored PDF scan result for task {result.id} (credits to deduct: {credits_to_deduct})")
        
        # Finalize credits (deduct if successful, refund if failed)
        credits_reserved = result_dict.get('credits_reserved', False)
        scan_status = result_dict.get('status', 'completed')
        
        if result.user_id:
            if credits_reserved:
                # Credits were reserved at scan initiation, now finalize them
                # Only deduct credits on clean completion - refund if errors occurred
                if scan_status == 'completed':
                    finalize_credits(
                        user_id=result.user_id,
                        credit_type="pdf_scan",
                        amount=credits_to_deduct,
                        scan_id=result.id,
                        success=True,
                        reason=f"PDF scan completed successfully ({credits_to_deduct} pages)"
                    )
                    logger.info(f"Finalized {credits_to_deduct} PDF scan credits for user {result.user_id}")
                elif scan_status == 'failed' or scan_status == 'completed_with_errors':
                    # Refund credits for failed scans or scans that completed with errors
                    # (AI-based scans can't guarantee results, so refund on errors)
                    finalize_credits(
                        user_id=result.user_id,
                        credit_type="pdf_scan",
                        amount=credits_to_deduct,
                        scan_id=result.id,
                        success=False,
                        reason=f"PDF scan {'failed' if scan_status == 'failed' else 'completed with errors'}: {result_dict.get('error_message', 'Unknown error')}"
                    )
                    logger.info(f"Refunded {credits_to_deduct} PDF scan credits for user {result.user_id} (scan {scan_status})")
            else:
                # Legacy path: credits not reserved, deduct directly (for backward compatibility)
                try:
                    user_ref = db.collection('users').document(result.user_id)
                    user_doc = user_ref.get()
                    if user_doc.exists:
                        current_credits = user_doc.to_dict().get('pdf_scan_credits', 0)
                        new_credits = max(0, current_credits - credits_to_deduct)  # Never go below 0
                        user_ref.update({
                            'pdf_scan_credits': new_credits,
                            'updated_at': datetime.now(CET)
                        })
                        logger.info(f"Deducted {credits_to_deduct} PDF scan credits for user {result.user_id} (legacy path)")
                        
                        # Log credit usage
                        log_credit_usage(
                            user_id=result.user_id,
                            credit_type="pdf_scan",
                            amount=credits_to_deduct,
                            reason=f"PDF scan completed successfully ({credits_to_deduct} pages)",
                            scan_id=result.id
                        )
                except Exception as e:
                    logger.error(f"Error deducting/logging PDF credit usage: {e}")
        
        # Queue integration tasks if user has enabled integrations
        try:
            integration_success = queue_integration_tasks(result.user_id, result_dict)
            if integration_success:
                logger.info(f"Queued integration tasks for PDF scan {result.id}")
        except Exception as e:
            logger.warning(f"Failed to queue integration tasks for PDF scan {result.id}: {e}")
        
        return JSONResponse(content={"message": "PDF scan result stored successfully"})
        
    except Exception as e:
        logger.error(f"Error storing PDF scan result for task {result.id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to store PDF scan result")

@app.get("/pdf-scan/my-scans")
async def get_user_pdf_scans(
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = 50,
    offset: int = 0
):
    """Get PDF scan results METADATA for the authenticated user (list view only).
    
    Returns only summary metadata for the list view. For full scan details,
    use the /pdf-scan/result/{task_id} endpoint.
    """
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        user_id = current_user['uid']
        logger.info(f"Getting PDF scans for user: {user_id}")
        
        # Query PDF scans for this user with Firestore-side pagination
        query = db.collection('pdf_scan_results')\
            .where('user_id', '==', user_id)\
            .order_by('created_at', direction=firestore.Query.DESCENDING)\
            .limit(limit)\
            .offset(offset)
        
        scans = []
        for doc in query.stream():
            scan_data = doc.to_dict()
            
            # Convert datetime objects to ISO format strings
            def convert_datetime_objects(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {key: convert_datetime_objects(value) for key, value in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime_objects(item) for item in obj]
                else:
                    return obj
            
            scan_data = convert_datetime_objects(scan_data)
            
            # Return ONLY metadata - NO full result for list view
            scans.append({
                "id": doc.id,
                "file_name": scan_data.get("file_name"),
                "file_size": scan_data.get("file_size"),
                "scan_type": scan_data.get("scan_type"),
                "timestamp": scan_data.get("timestamp"),
                "created_at": scan_data.get("created_at"),
                "violations_count": len(scan_data.get("violations", [])) if isinstance(scan_data.get("violations"), list) else scan_data.get("summary", {}).get("violations_count", 0),
                "warnings_count": len(scan_data.get("warnings", [])) if isinstance(scan_data.get("warnings"), list) else scan_data.get("summary", {}).get("warnings_count", 0),
                "notices_count": len(scan_data.get("notices", [])) if isinstance(scan_data.get("notices"), list) else scan_data.get("summary", {}).get("notices_count", 0),
                "passes_count": len(scan_data.get("passes", [])) if isinstance(scan_data.get("passes"), list) else scan_data.get("summary", {}).get("passes_count", 0),
                "scan_duration": scan_data.get("scanDuration"),
                "accessibility_score": scan_data.get("accessibility_score"),
                "status": scan_data.get("status", "completed")
                # NO full_result - use /pdf-scan/result/{task_id} for details
            })
        
        return JSONResponse(content={
            "scans": scans,
            "user_id": user_id,
            "total": len(scans),
            "limit": limit,
            "offset": offset
        })
        
    except Exception as e:
        logger.error(f"Error getting user PDF scans: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user PDF scans")

@app.delete("/pdf-scan/my-scans/{scan_id}")
async def delete_user_pdf_scan(
    scan_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a specific PDF scan result for the authenticated user"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        user_id = current_user['uid']
        logger.info(f"Deleting PDF scan {scan_id} for user: {user_id}")
        
        # Get the scan document
        doc_ref = db.collection('pdf_scan_results').document(scan_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="PDF scan not found")
        
        # Verify the scan belongs to the user
        scan_data = doc.to_dict()
        if scan_data.get('user_id') != user_id:
            logger.warning(f"User {user_id} attempted to delete PDF scan {scan_id} belonging to {scan_data.get('user_id')}")
            raise HTTPException(status_code=403, detail="You don't have permission to delete this scan")
        
        # Delete the scan
        doc_ref.delete()
        logger.info(f"Successfully deleted PDF scan {scan_id} for user {user_id}")
        
        return JSONResponse(content={
            "message": "PDF scan deleted successfully",
            "scan_id": scan_id
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting PDF scan {scan_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete PDF scan")

@app.get("/user/preferences")
async def get_user_preferences(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's scan preferences (requires authentication)"""
    user_id = current_user['uid']
    
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        user_ref = db.collection('users').document(user_id)
        user_doc = user_ref.get()
        
        if not user_doc.exists:
            # Return default preferences if user document doesn't exist yet
            return {
                "web_scan_modules": ['axe', 'nu', 'axTree', 'galen', 'links']
            }
        
        user_data = user_doc.to_dict()
        preferences = user_data.get('scan_preferences', {})
        
        return {
            "web_scan_modules": preferences.get('web_scan_modules', ['axe', 'nu', 'axTree', 'galen', 'links'])
        }
        
    except Exception as e:
        logger.error(f"Failed to get user preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to get user preferences"
        )

@app.put("/user/preferences")
async def update_user_preferences(
    preferences: UserPreferences,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update user's scan preferences (requires authentication)"""
    user_id = current_user['uid']
    
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Validate that at least one module is selected
        if not preferences.web_scan_modules or len(preferences.web_scan_modules) == 0:
            raise HTTPException(
                status_code=400,
                detail="At least one scan module must be selected"
            )
        
        # Limit array size to prevent abuse
        if len(preferences.web_scan_modules) > 10:
            raise HTTPException(
                status_code=400,
                detail="Too many modules selected (maximum 10)"
            )
        
        # Validate module names
        valid_modules = {'axe', 'nu', 'axTree', 'galen', 'links'}
        invalid_modules = set(preferences.web_scan_modules) - valid_modules
        if invalid_modules:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid modules: {', '.join(invalid_modules)}"
            )
        
        user_ref = db.collection('users').document(user_id)
        user_ref.set({
            'scan_preferences': {
                'web_scan_modules': preferences.web_scan_modules
            },
            'updated_at': datetime.now(CET)
        }, merge=True)
        
        logger.info(f"Updated scan preferences for user {user_id}: {preferences.web_scan_modules}")
        
        return {
            "success": True,
            "web_scan_modules": preferences.web_scan_modules
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to update user preferences"
        )
