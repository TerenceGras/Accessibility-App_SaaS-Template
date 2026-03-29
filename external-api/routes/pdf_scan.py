#!/usr/bin/env python3
"""
LumTrails External API - PDF Scan Routes

PDF accessibility scanning endpoints.
Uses the new Firebase schema with config.pdf_scan_enabled.
Credit cost: 1 credit per page in the PDF document.
"""

import logging
import httpx
import os
import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from google.cloud import firestore, tasks_v2
from firebase_admin import storage as firebase_storage
import json
import uuid
from urllib.parse import urlparse, unquote
from middleware.auth import get_current_user, check_pdf_scan_credits

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pdf-scan", tags=["PDF Scans"])

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.getenv("CLOUD_TASKS_LOCATION", "europe-west1")
INTEGRATION_QUEUE_NAME = os.getenv("INTEGRATION_QUEUE_NAME", "integration-queue")
PDF_WORKER_URL = os.getenv("PDF_WORKER_URL", "")
INTEGRATION_WORKER_URL = os.getenv("INTEGRATION_WORKER_URL", "")
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "")

# Initialize clients
db = firestore.Client()
tasks_client = tasks_v2.CloudTasksClient()
integration_queue_parent = tasks_client.queue_path(PROJECT_ID, LOCATION, INTEGRATION_QUEUE_NAME)


def count_pdf_pages(file_content: bytes) -> int:
    """
    Count the number of pages in a PDF file.
    Uses PyPDF2 if available, otherwise falls back to regex pattern matching.
    
    Args:
        file_content: Raw PDF file bytes
        
    Returns:
        Number of pages in the PDF
    """
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

# Initialize clients
db = firestore.Client()
tasks_client = tasks_v2.CloudTasksClient()
integration_queue_parent = tasks_client.queue_path(PROJECT_ID, LOCATION, INTEGRATION_QUEUE_NAME)


async def queue_integration_tasks_for_pdf(user_id: str, scan_result: Dict[str, Any]) -> bool:
    """
    Queue integration tasks for enabled platforms.
    Uses the new Firebase schema: integrations.{platform}.config.pdf_scan_enabled
    """
    try:
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
        
        logger.info(f"Queueing integration tasks for PDF scan from external API for user {user_id}")
        
        tasks_queued = 0
        
        # Queue tasks for each enabled integration
        for platform, platform_data in integrations.items():
            # New schema: config is nested under platform
            config = platform_data.get('config', {})
            is_connected = config.get('connected', False)
            is_pdf_enabled = config.get('pdf_scan_enabled', False)
            
            if is_connected and is_pdf_enabled:
                logger.info(f"Queueing {platform} integration task for PDF scan for user {user_id}")
                
                # Create task payload with datetime serialization
                def serialize_datetime_objects(obj):
                    if isinstance(obj, datetime):
                        return obj.isoformat()
                    elif hasattr(obj, '__class__') and obj.__class__.__name__ == 'Sentinel':
                        return datetime.now(timezone.utc).isoformat()
                    elif isinstance(obj, dict):
                        return {k: serialize_datetime_objects(v) for k, v in obj.items()}
                    elif isinstance(obj, list):
                        return [serialize_datetime_objects(item) for item in obj]
                    else:
                        return obj
                
                task_payload = {
                    "user_id": user_id,
                    "scan_id": scan_result.get("id", "unknown"),
                    "platform": platform,
                    "scan_type": "pdf",
                    "scan_data": serialize_datetime_objects(scan_result),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Create Cloud Task
                task_id = f"{platform}-pdf-{user_id}-{uuid.uuid4().hex[:8]}"
                task = {
                    "name": f"{integration_queue_parent}/tasks/{task_id}",
                    "http_request": {
                        "http_method": tasks_v2.HttpMethod.POST,
                        "url": f"{INTEGRATION_WORKER_URL}/process",
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(task_payload).encode(),
                        "oidc_token": {
                            "service_account_email": f"{os.environ.get('PROJECT_NUMBER', '')}-compute@developer.gserviceaccount.com",
                            "audience": INTEGRATION_WORKER_URL
                        }
                    }
                }
                
                # Queue the task
                try:
                    tasks_client.create_task(parent=integration_queue_parent, task=task)
                    tasks_queued += 1
                    logger.info(f"Queued {platform} integration task for PDF scan for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to queue {platform} integration task: {e}")
        
        logger.info(f"Queued {tasks_queued} integration tasks for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error queueing integration tasks: {e}")
        return False


class PDFPageResult(BaseModel):
    """Individual page accessibility result"""
    page_number: int
    accessibility_report: str


class PDFScanResponse(BaseModel):
    """PDF scan response with per-page results"""
    scan_id: str
    status: str
    file_name: str
    timestamp: str
    pages_analyzed: int
    credits_used: int
    credits_remaining: int
    accessibility_report: str
    page_results: Optional[List[PDFPageResult]] = None
    tool_info: dict


@router.post("", response_model=PDFScanResponse)
async def perform_pdf_scan(
    file: Optional[UploadFile] = File(None),
    pdf_url: Optional[str] = Form(None),
    user_info: dict = Depends(get_current_user)
):
    """
    Perform an AI-powered accessibility scan on a PDF document (External API - Synchronous)
    
    This endpoint performs a synchronous PDF scan and returns results immediately.
    
    **Credit Cost:** 1 credit per page in the PDF document.
    Credits are checked BEFORE scanning - if you don't have enough credits for all pages,
    the scan will not run and you'll receive a 402 error with the required credits.
    
    Accepts either:
    - file: PDF file upload
    - pdf_url: Publicly accessible URL to a PDF file
    
    Note: Provide either 'file' or 'pdf_url', not both.
    
    **Response:**
    - `accessibility_report`: Combined accessibility report for all pages
    - `page_results`: Individual accessibility reports per page
    - `pages_analyzed`: Total number of pages analyzed
    - `credits_used`: Number of credits deducted (equals pages_analyzed)
    """
    try:
        # Validate input - must provide either file or URL, but not both
        if not file and not pdf_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either 'file' or 'pdf_url' must be provided"
            )
        
        if file and pdf_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provide either 'file' or 'pdf_url', not both"
            )
        
        # Generate scan ID
        scan_id = f"api_pdf_{user_info['user_id']}_{uuid.uuid4().hex[:12]}"
        
        # Handle file upload
        if file:
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File must be a PDF"
                )
            
            logger.info(f"Starting synchronous PDF scan {scan_id} for uploaded file: {file.filename}")
            
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            file_name = file.filename
        
        # Handle URL download
        else:
            logger.info(f"Starting synchronous PDF scan {scan_id} for URL: {pdf_url}")
            
            # Download PDF from URL
            async with httpx.AsyncClient(timeout=60.0) as client:
                try:
                    response = await client.get(pdf_url)
                    response.raise_for_status()
                    
                    # Check content type
                    content_type = response.headers.get('content-type', '').lower()
                    if 'application/pdf' not in content_type and not pdf_url.lower().endswith('.pdf'):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="URL must point to a PDF file"
                        )
                    
                    file_content = response.content
                    file_size = len(file_content)
                    
                    # Validate PDF magic bytes
                    if not file_content.startswith(b'%PDF'):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Downloaded file is not a valid PDF"
                        )
                    
                    # Extract filename from URL
                    parsed_url = urlparse(pdf_url)
                    file_name = unquote(parsed_url.path.split('/')[-1])
                    if not file_name or not file_name.lower().endswith('.pdf'):
                        file_name = f"document_{scan_id}.pdf"
                    
                    logger.info(f"Downloaded PDF from URL: {file_name} ({file_size} bytes)")
                    
                except httpx.HTTPStatusError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to download PDF from URL: HTTP {e.response.status_code}"
                    )
                except httpx.RequestError as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to download PDF from URL: {str(e)}"
                    )
        
        # Count pages in PDF BEFORE scanning to check credits
        page_count = count_pdf_pages(file_content)
        logger.info(f"PDF has {page_count} pages, checking credits...")
        
        # Check if user has enough credits for all pages (1 credit per page)
        user_info = await check_pdf_scan_credits(user_info, pages_required=page_count)
        credits_required = page_count
        
        logger.info(f"User has sufficient credits. Proceeding with scan of {page_count} pages.")
        
        # Upload to Firebase Storage
        bucket = firebase_storage.bucket(FIREBASE_STORAGE_BUCKET)
        storage_path = f"api_uploads/{user_info['user_id']}/{scan_id}/{file_name}"
        blob = bucket.blob(storage_path)
        blob.upload_from_string(file_content, content_type='application/pdf')
        
        logger.info(f"Uploaded PDF to Firebase Storage: {storage_path}")
        
        # Call the PDF scan worker directly (synchronous HTTP call)
        async with httpx.AsyncClient(timeout=600.0) as client:  # 10 minute timeout for PDF processing
            worker_payload = {
                "task_id": scan_id,
                "storage_path": storage_path,
                "file_name": file_name,
                "file_size": file_size,
                "user_id": user_info['user_id'],
                "user_email": user_info['email'],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_external_api": True  # Flag to prevent callback from worker
            }
            
            logger.info(f"Calling PDF worker at {PDF_WORKER_URL}/scan")
            
            # Make synchronous HTTP call to worker
            worker_response = await client.post(
                f"{PDF_WORKER_URL}/scan",
                json=worker_payload,
                timeout=600.0  # 10 minute timeout
            )
            
            if worker_response.status_code != 200:
                logger.error(f"Worker returned error: {worker_response.status_code} - {worker_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Scan failed: {worker_response.text}"
                )
            
            scan_result = worker_response.json()
            logger.info(f"Received scan result from worker for {scan_id}")
        
        # Extract pages analyzed from result
        unified_results = scan_result.get('unified_results', {})
        pages_analyzed = unified_results.get('pages_analyzed', page_count)
        
        # Verify pages analyzed matches our count (use actual if different)
        if pages_analyzed != page_count:
            logger.warning(f"Page count mismatch: counted {page_count}, analyzed {pages_analyzed}")
            pages_analyzed = page_count  # Use our pre-counted value for billing
        
        # Store result in Firestore for record keeping
        doc_ref = db.collection('pdf_scan_results').document(scan_id)
        result_data = scan_result.copy()
        result_data['created_at'] = datetime.now(timezone.utc)
        result_data['source'] = 'external_api'
        result_data['api_key_name'] = user_info.get('key_name', 'unknown')
        result_data['credits_used'] = credits_required
        
        doc_ref.set(result_data)
        logger.info(f"Stored PDF scan result in Firestore for {scan_id}")
        
        # Deduct credits from users collection (1 credit per page)
        credits_ref = db.collection('users').document(user_info['user_id'])
        credits_ref.update({
            'pdf_scan_credits': firestore.Increment(-credits_required),
            'updated_at': datetime.now(timezone.utc)
        })
        logger.info(f"Deducted {credits_required} PDF scan credits for user {user_info['user_id']}")
        
        # Queue integration tasks if user has integrations enabled
        try:
            await queue_integration_tasks_for_pdf(user_info['user_id'], result_data)
        except Exception as e:
            logger.error(f"Error queueing integration tasks: {e}")
            # Don't fail the main operation if integration queueing fails
        
        # Extract per-page results if available
        page_results = None
        scan_results = scan_result.get('scan_results', {})
        if scan_results:
            page_results = []
            for key, value in sorted(scan_results.items()):
                # Keys are like "page_1", "page_2", etc.
                if key.startswith('page_'):
                    try:
                        page_num = int(key.split('_')[1])
                        page_results.append(PDFPageResult(
                            page_number=page_num,
                            accessibility_report=value
                        ))
                    except (ValueError, IndexError):
                        continue
        
        # Return results
        return PDFScanResponse(
            scan_id=scan_id,
            status="completed",
            file_name=file_name,
            timestamp=scan_result.get('timestamp', datetime.now(timezone.utc).isoformat()),
            pages_analyzed=pages_analyzed,
            credits_used=credits_required,
            credits_remaining=user_info['pdf_scan_credits'] - credits_required,
            accessibility_report=scan_result.get('accessibility_report', 'No analysis available'),
            page_results=page_results,
            tool_info=unified_results.get('tool_info', {
                'name': 'LumTrails-PDF-AI-Scanner',
                'version': '2.0.0'
            })
        )
        
    except HTTPException:
        # Clean up uploaded PDF on HTTP exception
        try:
            if 'storage_path' in locals() and storage_path:
                bucket = firebase_storage.bucket(FIREBASE_STORAGE_BUCKET)
                blob = bucket.blob(storage_path)
                blob.delete()
                logger.info(f"Cleaned up PDF after HTTP exception: {storage_path}")
        except Exception as cleanup_error:
            logger.warning(f"Could not clean up PDF after HTTP exception: {cleanup_error}")
        raise
    except Exception as e:
        # Clean up uploaded PDF on general exception
        try:
            if 'storage_path' in locals() and storage_path:
                bucket = firebase_storage.bucket(FIREBASE_STORAGE_BUCKET)
                blob = bucket.blob(storage_path)
                blob.delete()
                logger.info(f"Cleaned up PDF after error: {storage_path}")
        except Exception as cleanup_error:
            logger.warning(f"Could not clean up PDF after error: {cleanup_error}")
        logger.error(f"Error performing PDF scan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}"
        )
