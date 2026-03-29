from google.cloud import firestore
from google.cloud import secretmanager
import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Initialize clients
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "")

try:
    db = firestore.Client(project=PROJECT_ID)
    secret_client = secretmanager.SecretManagerServiceClient()
    logger.info("Integration services initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize integration services: {e}")
    db = None
    secret_client = None

def serialize_datetime_objects(obj):
    """Recursively convert datetime objects to ISO format strings for JSON serialization"""
    if hasattr(obj, 'timestamp'):  # Firestore DatetimeWithNanoseconds
        return obj.isoformat()
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime_objects(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime_objects(item) for item in obj]
    else:
        return obj

def get_user_integrations_doc(user_id: str):
    """Get the Firestore document reference for user integrations"""
    return db.collection('user_integrations').document(user_id)

def get_secret(secret_id: str) -> str:
    """Get secret from Google Secret Manager"""
    try:
        name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/latest"
        response = secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        logger.error(f"Failed to get secret {secret_id}: {e}")
        return None

def store_secret(secret_id: str, secret_value: str) -> bool:
    """Store secret in Google Secret Manager"""
    try:
        parent = f"projects/{PROJECT_ID}"
        
        # Try to create secret first (may already exist)
        try:
            secret_client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}},
                }
            )
        except Exception:
            pass  # Secret may already exist
        
        # Add secret version
        secret_path = f"{parent}/secrets/{secret_id}"
        secret_client.add_secret_version(
            request={
                "parent": secret_path,
                "payload": {"data": secret_value.encode("UTF-8")},
            }
        )
        return True
    except Exception as e:
        logger.error(f"Failed to store secret {secret_id}: {e}")
        return False
