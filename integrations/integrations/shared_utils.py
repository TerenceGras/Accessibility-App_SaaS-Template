"""
Shared utilities for all integrations
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import os
from google.cloud import firestore, secretmanager

logger = logging.getLogger(__name__)

# Initialize clients
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")
db = firestore.Client(project=PROJECT_ID)
secret_client = secretmanager.SecretManagerServiceClient()

def get_user_integration_config(user_id: str, platform: str) -> Optional[Dict[str, Any]]:
    """Get user's integration configuration for a specific platform"""
    try:
        doc_ref = db.collection('user_integrations').document(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            return None
        
        data = doc.to_dict()
        return data.get('integrations', {}).get(platform, {})
    except Exception as e:
        logger.error(f"Failed to get integration config: {e}")
        return None

async def get_user_integration_config_async(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user's integration configuration from Firestore (async version for main.py)"""
    try:
        doc_ref = db.collection('user_integrations').document(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.warning(f"User integration document not found: {user_id}")
            return None
        
        data = doc.to_dict()
        integrations = data.get('integrations', {})
        
        logger.info(f"Retrieved integration config for user {user_id}: {list(integrations.keys())}")
        return integrations
        
    except Exception as e:
        logger.error(f"Error fetching user integration config: {e}")
        return None

async def update_integration_stats(user_id: str, platform: str, success: bool):
    """Update integration statistics in Firestore"""
    try:
        doc_ref = db.collection('user_integrations').document(user_id)
        
        # Update stats based on success
        stat_updates = {
            'last_sync': datetime.now(timezone.utc)
        }
        
        if success:
            stat_updates['last_success'] = datetime.now(timezone.utc)
        
        # Update the document
        update_data = {}
        for key, value in stat_updates.items():
            update_data[f"integrations.{platform}.stats.{key}"] = value
        
        doc_ref.update(update_data)
        logger.info(f"Updated {platform} stats for user {user_id}: success={success}")
        
    except Exception as e:
        logger.error(f"Error updating integration stats: {e}")

def filter_violations_by_severity(violations: List[Dict[str, Any]], severity_filter: List[str]) -> List[Dict[str, Any]]:
    """Filter violations based on severity settings"""
    if not severity_filter:
        return violations
    
    # Map impact levels to severity
    impact_to_severity = {
        'critical': 'High',
        'serious': 'High', 
        'moderate': 'Medium',
        'minor': 'Low'
    }
    
    filtered = []
    for violation in violations:
        impact = violation.get('impact', 'minor')
        severity = impact_to_severity.get(impact, 'Low')
        if severity in severity_filter:
            filtered.append(violation)
    
    return filtered

def get_secret(secret_name: str) -> Optional[str]:
    """Retrieve a secret from Google Secret Manager (synchronous)"""
    try:
        secret_path = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = secret_client.access_secret_version(request={"name": secret_path})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_name}: {e}")
        return None

async def get_secret_async(secret_name: str) -> Optional[str]:
    """Retrieve a secret from Google Secret Manager (async)"""
    try:
        secret_path = f"projects/{PROJECT_ID}/secrets/{secret_name}/versions/latest"
        response = secret_client.access_secret_version(request={"name": secret_path})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Error accessing secret {secret_name}: {e}")
        return None

async def update_integration_stats_async(user_id: str, platform: str, success: bool):
    """Update integration statistics in Firestore (async version for main.py)"""
    try:
        doc_ref = db.collection('user_integrations').document(user_id)
        
        # Update stats based on success
        stat_updates = {
            'last_sync': datetime.now(timezone.utc)
        }
        
        if success:
            stat_updates['last_success'] = datetime.now(timezone.utc)
        
        # Update the document
        update_data = {}
        for key, value in stat_updates.items():
            update_data[f"integrations.{platform}.stats.{key}"] = value
        
        doc_ref.update(update_data)
        logger.info(f"Updated {platform} stats for user {user_id}: success={success}")
        
    except Exception as e:
        logger.error(f"Error updating integration stats: {e}")

def update_integration_stats(user_id: str, platform: str, stat_updates: Dict[str, Any]):
    """Update integration statistics"""
    try:
        doc_ref = db.collection('user_integrations').document(user_id)
        
        # Update stats
        update_data = {}
        for key, value in stat_updates.items():
            update_data[f"integrations.{platform}.stats.{key}"] = value
        
        update_data[f"integrations.{platform}.last_sync"] = datetime.now(timezone.utc)
        
        doc_ref.update(update_data)
        logger.info(f"Updated {platform} stats for user {user_id}: {stat_updates}")
    except Exception as e:
        logger.error(f"Failed to update integration stats: {e}")

def log_integration_activity(user_id: str, platform: str, action: str, status: str, details: Dict[str, Any] = None):
    """Log integration activity for debugging and monitoring"""
    try:
        log_ref = db.collection('integration_logs').document()
        log_data = {
            'user_id': user_id,
            'platform': platform,
            'action': action,
            'status': status,
            'timestamp': datetime.now(timezone.utc),
            'details': details or {}
        }
        
        log_ref.set(log_data)
        logger.info(f"Logged {platform} {action} for user {user_id}: {status}")
    except Exception as e:
        logger.error(f"Failed to log integration activity: {e}")
