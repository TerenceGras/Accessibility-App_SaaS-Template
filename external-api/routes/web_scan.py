#!/usr/bin/env python3
"""
LumTrails External API - Web Scan Routes

Web accessibility scanning endpoints.
Uses the v3.0.0 unified_results format and new Firebase schema.
Credit cost: 1 credit per active module (max 5 credits for all modules)
"""

import logging
import httpx
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl
from google.cloud import firestore, tasks_v2
from typing import Dict, List, Optional, Any
import json
import uuid
from middleware.auth import get_current_user, check_web_scan_credits, calculate_web_scan_credits

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/web-scan", tags=["Web Scans"])

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.getenv("CLOUD_TASKS_LOCATION", "europe-west1")
INTEGRATION_QUEUE_NAME = os.getenv("INTEGRATION_QUEUE_NAME", "integration-queue")
WORKER_URL = os.getenv("WORKER_URL", "")
INTEGRATION_WORKER_URL = os.getenv("INTEGRATION_WORKER_URL", "")

# Initialize clients
db = firestore.Client()
tasks_client = tasks_v2.CloudTasksClient()
integration_queue_parent = tasks_client.queue_path(PROJECT_ID, LOCATION, INTEGRATION_QUEUE_NAME)

# Available scan modules
AVAILABLE_MODULES = ["axe", "nu", "axTree", "galen", "links"]


class WebScanRequest(BaseModel):
    url: HttpUrl
    modules: Optional[List[str]] = None  # If None, runs all modules (costs 5 credits)


class ScanSummary(BaseModel):
    """Summary statistics from the scan"""
    total_violations: int = 0
    total_passes: int = 0
    total_html_errors: int = 0
    total_broken_links: int = 0


class WebScanResponse(BaseModel):
    """
    Web scan response using v3.0.0 unified_results format.
    All scan data is contained within unified_results.
    """
    scan_id: str
    status: str
    url: str
    timestamp: str
    scan_format_version: str = "3.0.0"
    modules_executed: List[str]
    scan_duration_ms: int
    credits_used: int
    credits_remaining: int
    summary: ScanSummary
    unified_results: Dict[str, Any]


async def queue_integration_tasks_for_api(user_id: str, scan_result: Dict[str, Any], scan_type: str = "web") -> bool:
    """
    Queue integration tasks for enabled platforms.
    Uses the new Firebase schema: integrations.{platform}.config.web_scan_enabled
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
        
        logger.info(f"Queueing integration tasks for {scan_type} scan from external API for user {user_id}")
        
        tasks_queued = 0
        
        # Queue tasks for each enabled integration
        for platform, platform_data in integrations.items():
            # New schema: config is nested under platform
            config = platform_data.get('config', {})
            is_connected = config.get('connected', False)
            is_web_enabled = config.get('web_scan_enabled', False)
            
            if is_connected and is_web_enabled:
                logger.info(f"Queueing {platform} integration task for {scan_type} scan for user {user_id}")
                
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
                    "scan_type": scan_type,
                    "scan_data": serialize_datetime_objects(scan_result),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                # Create Cloud Task
                task_id = f"{platform}-{user_id}-{uuid.uuid4().hex[:8]}"
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
                    logger.info(f"Queued {platform} integration task for user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to queue {platform} integration task: {e}")
        
        logger.info(f"Queued {tasks_queued} integration tasks for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error queueing integration tasks: {e}")
        return False


def fix_axe_targets(data: Any) -> Any:
    """Fix Firestore compatibility for axe-core target selectors"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key == 'target' and isinstance(value, list):
                simplified_targets = []
                for target_item in value:
                    if isinstance(target_item, list):
                        if len(target_item) == 2 and isinstance(target_item[1], int):
                            simplified_targets.append(f"{target_item[0]}:nth-child({target_item[1]})")
                        else:
                            simplified_targets.append(" ".join(str(x) for x in target_item))
                    else:
                        simplified_targets.append(str(target_item))
                result[key] = simplified_targets
            else:
                result[key] = fix_axe_targets(value)
        return result
    elif isinstance(data, list):
        return [fix_axe_targets(item) for item in data]
    else:
        return data


def extract_summary_from_unified_results(unified_results: Dict[str, Any]) -> ScanSummary:
    """Extract summary statistics from unified_results"""
    axe_data = unified_results.get('axe', {})
    nu_data = unified_results.get('nu', {})
    links_data = unified_results.get('links', {})
    
    # Count actual violation nodes, not categories
    total_violations = sum(
        len(v.get("nodes", [])) 
        for v in axe_data.get("violations", [])
    )
    
    total_passes = sum(
        len(p.get("nodes", [])) 
        for p in axe_data.get("passes", [])
    )
    
    total_html_errors = len([
        m for m in nu_data.get("messages", []) 
        if m.get("type") == "error"
    ])
    
    total_broken_links = len([
        l for l in links_data.get("links", []) 
        if l.get("state") == "broken"
    ])
    
    return ScanSummary(
        total_violations=total_violations,
        total_passes=total_passes,
        total_html_errors=total_html_errors,
        total_broken_links=total_broken_links
    )


@router.post("", response_model=WebScanResponse)
async def perform_web_scan(
    request: WebScanRequest,
    user_info: dict = Depends(get_current_user)
):
    """
    Perform an accessibility scan on a website URL (External API - Synchronous)
    
    This endpoint performs a synchronous web scan and returns results immediately
    in the v3.0.0 unified_results format.
    
    **Credit Cost:** 1 credit per active module (max 5 credits for all modules)
    - axe: WCAG compliance testing
    - nu: HTML validation
    - axTree: Accessibility tree analysis
    - galen: Responsive layout testing
    - links: Link health check
    
    **Response Format (v3.0.0):**
    - `unified_results.axe`: WCAG compliance violations from axe-core
    - `unified_results.nu`: HTML validation errors from Nu HTML Checker
    - `unified_results.axTree`: Accessibility tree snapshot
    - `unified_results.galen`: Responsive layout testing results
    - `unified_results.links`: Link health check results
    - `unified_results.meta`: Page metadata (viewport, title, final URL)
    """
    # Validate and set modules (default to all if not specified)
    modules_to_run = request.modules if request.modules else AVAILABLE_MODULES
    # Filter to only valid modules
    modules_to_run = [m for m in modules_to_run if m in AVAILABLE_MODULES]
    if not modules_to_run:
        modules_to_run = AVAILABLE_MODULES
    
    # Check credits based on number of modules (1 credit per module)
    user_info = await check_web_scan_credits(user_info, modules=modules_to_run)
    credits_required = user_info.get('credits_required', len(modules_to_run))
    
    try:
        # Generate scan ID
        scan_id = f"api_web_{user_info['user_id']}_{uuid.uuid4().hex[:12]}"
        
        logger.info(f"Starting synchronous web scan {scan_id} for URL: {request.url}")
        logger.info(f"Modules to run: {modules_to_run} (credits required: {credits_required})")
        
        # Call the web scan worker directly (synchronous HTTP call)
        async with httpx.AsyncClient(timeout=300.0) as client:
            worker_payload = {
                "task_id": scan_id,
                "url": str(request.url),
                "modules": modules_to_run,
                "user_id": user_info['user_id'],
                "user_email": user_info['email'],
                "created_at": datetime.now(timezone.utc).isoformat(),
                "is_external_api": True  # Flag to prevent integration queueing from worker
            }
            
            logger.info(f"Calling worker at {WORKER_URL}/sync-scan")
            
            # Make synchronous HTTP call to worker's sync-scan endpoint
            # This returns full results immediately instead of async acknowledgment
            worker_response = await client.post(
                f"{WORKER_URL}/sync-scan",
                json=worker_payload,
                timeout=300.0
            )
            
            if worker_response.status_code != 200:
                logger.error(f"Worker returned error: {worker_response.status_code} - {worker_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Scan failed: {worker_response.text}"
                )
            
            scan_result = worker_response.json()
            logger.info(f"Received scan result from worker for {scan_id}")
            
            # Debug: Log the structure of what we received
            logger.info(f"Worker response keys: {list(scan_result.keys())}")
        
        # Extract unified_results from the worker response
        unified_results = scan_result.get('unified_results', {})
        
        # Debug: Log unified_results structure
        logger.info(f"unified_results keys: {list(unified_results.keys())}")
        logger.info(f"modules_executed from unified_results: {unified_results.get('modules_executed', [])}")
        logger.info(f"scan_duration_ms from unified_results: {unified_results.get('scan_duration_ms', 0)}")
        
        # Store result in Firestore for record keeping
        # Store the entire scan_result with the id field renamed to match scan_id
        doc_ref = db.collection('web_scan_results').document(scan_id)
        result_data = scan_result.copy()
        result_data['id'] = scan_id  # Update id to match our scan_id
        result_data['created_at'] = datetime.now(timezone.utc)
        result_data['source'] = 'external_api'
        
        # Extract and store summary for MyScansPage display
        summary = extract_summary_from_unified_results(unified_results)
        result_data['summary'] = {
            'total_violations': summary.total_violations,
            'total_passes': summary.total_passes,
            'total_html_errors': summary.total_html_errors,
            'total_broken_links': summary.total_broken_links
        }
        
        # Fix Firestore compatibility for axe-core target selectors
        result_data = fix_axe_targets(result_data)
        doc_ref.set(result_data)
        logger.info(f"Stored scan result in Firestore for {scan_id}")
        
        # Deduct credits from users collection (1 credit per module)
        credits_ref = db.collection('users').document(user_info['user_id'])
        credits_ref.update({
            'web_scan_credits': firestore.Increment(-credits_required),
            'updated_at': datetime.now(timezone.utc)
        })
        logger.info(f"Deducted {credits_required} web scan credits for user {user_info['user_id']}")
        
        # Queue integration tasks if user has integrations enabled
        try:
            await queue_integration_tasks_for_api(user_info['user_id'], result_data, scan_type="web")
        except Exception as e:
            logger.error(f"Error queueing integration tasks: {e}")
            # Don't fail the main operation if integration queueing fails
        
        # Extract summary statistics from unified_results
        summary = extract_summary_from_unified_results(unified_results)
        
        # Return results in v3.0.0 format
        # Note: scan_format_version, modules_executed, and scan_duration_ms are INSIDE unified_results
        return WebScanResponse(
            scan_id=scan_id,
            status="completed",
            url=str(request.url),
            timestamp=scan_result.get('timestamp', datetime.now(timezone.utc).isoformat()),
            scan_format_version=unified_results.get('scan_format_version', '3.0.0'),
            modules_executed=unified_results.get('modules_executed', modules_to_run),
            scan_duration_ms=unified_results.get('scan_duration_ms', 0),
            credits_used=credits_required,
            credits_remaining=user_info['web_scan_credits'] - credits_required,
            summary=summary,
            unified_results=unified_results
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error performing web scan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}"
        )
