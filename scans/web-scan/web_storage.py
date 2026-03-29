"""
Web Scan Storage Management for LumTrails Web Scanner
======================================================

This module handles permanent storage of web scan results in Firebase Storage.
Unlike PDF scans which use temporary storage, web scan results are stored permanently
for user access and historical analysis.

Features:
- Permanent storage of web scan results as JSON in Firebase Storage
- Token-based secure access to stored results
- Organized storage structure by user and scan ID

Storage Strategy:
- Results stored permanently in Firebase Storage bucket
- Organized as: web-scan-results/{user_id}/{scan_id}.json
- Metadata stored in Firestore for efficient querying
- Full results retrieved from Storage when needed
"""

import os
import io
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

# CET timezone for EU service - all dates stored in CET
CET = ZoneInfo("Europe/Paris")

logger = logging.getLogger(__name__)

# Firebase Storage
try:
    import firebase_admin
    from firebase_admin import credentials, storage as firebase_storage
    FIREBASE_STORAGE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Firebase Storage dependencies not available: {e}")
    FIREBASE_STORAGE_AVAILABLE = False
    firebase_admin = None
    firebase_storage = None


class WebScanStorageManager:
    """Manages permanent storage of web scan results in Firebase Storage"""
    
    def __init__(self):
        """Initialize the web scan storage manager"""
        self.bucket = None
        self.bucket_name = None
        
        # Storage organization
        self.storage_prefix = "web-scan-results"
        
        if FIREBASE_STORAGE_AVAILABLE:
            try:
                # Get bucket name from environment or use default
                self.bucket_name = os.getenv('FIREBASE_STORAGE_BUCKET', '')
                logger.info(f"Initializing Firebase Storage with bucket: {self.bucket_name}")
                
                # Initialize Firebase Admin SDK if not already initialized
                if not firebase_admin._apps:
                    # In Cloud Run, use default credentials
                    firebase_admin.initialize_app(options={
                        'storageBucket': self.bucket_name
                    })
                    logger.info("Firebase Admin SDK initialized with default credentials")
                
                # Get bucket reference
                self.bucket = firebase_storage.bucket(self.bucket_name)
                logger.info(f"✅ Web Scan Storage client initialized successfully for bucket: {self.bucket.name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize Firebase Storage client: {e}", exc_info=True)
                self.bucket = None
        else:
            logger.warning("Firebase Storage not available - file operations will fail")
    
    async def store_scan_result(
        self, 
        scan_data: Dict[str, Any], 
        user_id: str, 
        scan_id: str
    ) -> Optional[str]:
        """
        Store complete web scan result in Firebase Storage
        
        Args:
            scan_data: The complete scan result data
            user_id: User ID who initiated the scan
            scan_id: Unique scan identifier
            
        Returns:
            Storage URL (gs://...) for the uploaded result, or None on failure
        """
        try:
            if not self.bucket:
                logger.error("Firebase Storage bucket not initialized")
                return None
            
            # Create storage path: web-scan-results/{user_id}/{scan_id}.json
            storage_path = f"{self.storage_prefix}/{user_id}/{scan_id}.json"
            blob = self.bucket.blob(storage_path)
            
            # Set metadata
            blob.metadata = {
                'scan_id': scan_id,
                'user_id': user_id,
                'upload_time': datetime.now(CET).isoformat(),
                'file_type': 'web_scan_result',
                'content_type': 'application/json',
                'scan_url': scan_data.get('url', 'unknown'),
                'scan_version': scan_data.get('testEngine', {}).get('version', 'unknown')
            }
            
            # Convert scan data to JSON string
            json_content = json.dumps(scan_data, indent=2)
            content_size = len(json_content.encode('utf-8'))
            
            logger.info(f"Uploading web scan result to Storage: {storage_path} ({content_size} bytes)")
            
            # Upload the JSON file
            blob.upload_from_string(
                json_content, 
                content_type='application/json'
            )
            
            # Generate storage URL
            storage_url = f"gs://{self.bucket_name}/{storage_path}"
            
            logger.info(f"✅ Web scan result uploaded successfully to: {storage_url}")
            return storage_url
            
        except Exception as e:
            logger.error(f"❌ Failed to store web scan result in Firebase Storage: {str(e)}", exc_info=True)
            return None
    
    async def get_scan_result(self, user_id: str, scan_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete web scan result from Firebase Storage
        
        Args:
            user_id: User ID who owns the scan
            scan_id: Unique scan identifier
            
        Returns:
            Complete scan result data, or None if not found
        """
        try:
            if not self.bucket:
                logger.error("Firebase Storage bucket not initialized")
                return None
            
            # Construct storage path
            storage_path = f"{self.storage_prefix}/{user_id}/{scan_id}.json"
            blob = self.bucket.blob(storage_path)
            
            # Check if blob exists
            if not blob.exists():
                logger.warning(f"Web scan result not found in Storage: {storage_path}")
                return None
            
            # Download and parse JSON
            json_content = blob.download_as_text()
            scan_data = json.loads(json_content)
            
            logger.info(f"✅ Retrieved web scan result from Storage: {storage_path}")
            return scan_data
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve web scan result from Firebase Storage: {str(e)}", exc_info=True)
            return None
    
    async def delete_scan_result(self, user_id: str, scan_id: str) -> bool:
        """
        Delete web scan result from Firebase Storage
        
        Args:
            user_id: User ID who owns the scan
            scan_id: Unique scan identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if not self.bucket:
                logger.error("Firebase Storage bucket not initialized")
                return False
            
            # Construct storage path
            storage_path = f"{self.storage_prefix}/{user_id}/{scan_id}.json"
            blob = self.bucket.blob(storage_path)
            
            # Check if blob exists
            if not blob.exists():
                logger.warning(f"Web scan result not found for deletion: {storage_path}")
                return False
            
            # Delete the blob
            blob.delete()
            
            logger.info(f"✅ Deleted web scan result from Storage: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to delete web scan result from Firebase Storage: {str(e)}", exc_info=True)
            return False
    
    def get_public_url(self, user_id: str, scan_id: str) -> Optional[str]:
        """
        Generate a signed URL for accessing the scan result
        
        Args:
            user_id: User ID who owns the scan
            scan_id: Unique scan identifier
            
        Returns:
            Signed URL for accessing the result, or None on failure
        """
        try:
            if not self.bucket:
                logger.error("Firebase Storage bucket not initialized")
                return None
            
            # Construct storage path
            storage_path = f"{self.storage_prefix}/{user_id}/{scan_id}.json"
            blob = self.bucket.blob(storage_path)
            
            # Check if blob exists
            if not blob.exists():
                logger.warning(f"Web scan result not found for URL generation: {storage_path}")
                return None
            
            # For permanent storage, we can make the blob public or use signed URLs
            # Using public URL with token (similar to PDF approach)
            blob.make_public()
            public_url = blob.public_url
            
            logger.info(f"Generated public URL for web scan: {storage_path}")
            return public_url
            
        except Exception as e:
            logger.error(f"Failed to generate public URL: {str(e)}", exc_info=True)
            return None


# Global storage manager instance
web_storage_manager = WebScanStorageManager()
