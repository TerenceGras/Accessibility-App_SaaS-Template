from google.cloud import firestore, secretmanager
import logging
from typing import Dict, Any
from datetime import datetime, timezone
import os

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

# Initialize clients (shared across module)
try:
    db = firestore.Client(project=PROJECT_ID)
    secret_client = secretmanager.SecretManagerServiceClient()
    logger.info("Shared utilities initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize shared utilities: {e}")
    db = None
    secret_client = None

def get_secret(secret_id: str) -> str:
    """Get secret from Google Secret Manager"""
    try:
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to get secret {secret_id}: {e}")
        return None

async def get_user_integration_config(user_id: str) -> Dict[str, Any]:
    """Get user's complete integration configuration"""
    try:
        doc_ref = db.collection('user_integrations').document(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.info(f"No integration config found for user {user_id}")
            return None
        
        data = doc.to_dict()
        integrations = data.get('integrations', {})
        logger.info(f"Retrieved integration config for user {user_id}: {list(integrations.keys())}")
        return integrations
    except Exception as e:
        logger.error(f"Failed to get integration config: {e}")
        return None

async def update_integration_stats(user_id: str, platform: str, success: bool):
    """Update integration statistics"""
    try:
        doc_ref = db.collection('user_integrations').document(user_id)
        
        # Update stats
        update_data = {
            f"integrations.{platform}.last_sync": datetime.now(timezone.utc),
            f"integrations.{platform}.stats.last_success": success
        }
        
        if success:
            update_data[f"integrations.{platform}.stats.success_count"] = firestore.Increment(1)
        else:
            update_data[f"integrations.{platform}.stats.failure_count"] = firestore.Increment(1)
        
        doc_ref.update(update_data)
        logger.info(f"Updated {platform} stats for user {user_id}: success={success}")
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

def filter_violations_by_severity(violations, severity_filter):
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
