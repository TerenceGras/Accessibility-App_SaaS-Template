#!/usr/bin/env python3
"""
LumTrails External API - API Key Service

Handles API key generation, validation, and management.
"""

import os
import secrets
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from google.cloud import firestore
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for managing API keys"""
    
    def __init__(self):
        """Initialize Firestore client"""
        self.db = firestore.Client()
        self.api_keys_collection = 'api_keys'
        self.users_collection = 'users'
    
    def generate_api_key(self) -> str:
        """Generate a secure random API key"""
        # Generate 32-byte random key and encode as hex (64 characters)
        return secrets.token_urlsafe(32)
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def calculate_expiry_date(self, validity_period: str) -> Optional[datetime]:
        """
        Calculate expiry date based on validity period
        
        Args:
            validity_period: One of '1day', '1week', '1month', '6months', '1year', 'unlimited'
        
        Returns:
            Expiry datetime or None for unlimited
        """
        now = datetime.now(timezone.utc)
        
        period_map = {
            '1day': timedelta(days=1),
            '1week': timedelta(weeks=1),
            '1month': timedelta(days=30),
            '6months': timedelta(days=180),
            '1year': timedelta(days=365),
            'unlimited': None
        }
        
        delta = period_map.get(validity_period)
        if delta is None and validity_period != 'unlimited':
            raise ValueError(f"Invalid validity period: {validity_period}")
        
        return now + delta if delta else None
    
    async def create_api_key(
        self,
        user_id: str,
        key_name: str,
        validity_period: str
    ) -> Dict[str, Any]:
        """
        Create a new API key for a user
        
        Args:
            user_id: Firebase user ID
            key_name: User-friendly name for the key (alphanumeric only)
            validity_period: Validity period string
        
        Returns:
            Dictionary with key details including the plain API key
        """
        try:
            # Validate key name (alphanumeric only, no caps)
            if not key_name.replace('_', '').replace('-', '').isalnum():
                raise ValueError("Key name must be alphanumeric (underscores and hyphens allowed)")
            
            if key_name.upper() != key_name.lower() and key_name != key_name.lower():
                raise ValueError("Key name must be lowercase")
            
            # Check if key name already exists for this user
            existing_keys = self.db.collection(self.api_keys_collection)\
                .where('user_id', '==', user_id)\
                .where('key_name', '==', key_name)\
                .where('revoked', '==', False)\
                .limit(1)\
                .stream()
            
            if any(existing_keys):
                raise ValueError(f"An active API key with name '{key_name}' already exists")
            
            # Generate API key
            api_key = self.generate_api_key()
            api_key_hash = self.hash_api_key(api_key)
            
            # Calculate expiry
            expires_at = self.calculate_expiry_date(validity_period)
            
            # Create key document
            now = datetime.now(timezone.utc)
            key_doc = {
                'user_id': user_id,
                'key_name': key_name,
                'key_hash': api_key_hash,
                'created_at': now,
                'expires_at': expires_at,
                'validity_period': validity_period,
                'revoked': False,
                'last_used': None,
                'request_count': 0
            }
            
            # Store in Firestore
            doc_ref = self.db.collection(self.api_keys_collection).document()
            doc_ref.set(key_doc)
            
            logger.info(f"Created API key '{key_name}' for user {user_id}")
            
            return {
                'key_id': doc_ref.id,
                'api_key': api_key,  # Only returned once!
                'key_name': key_name,
                'created_at': now.isoformat(),
                'expires_at': expires_at.isoformat() if expires_at else None,
                'validity_period': validity_period
            }
            
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            raise HTTPException(status_code=500, detail="Failed to create API key")
    
    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return associated user info
        
        Args:
            api_key: The API key to validate
        
        Returns:
            User and key info if valid, None otherwise
        """
        try:
            api_key_hash = self.hash_api_key(api_key)
            
            # Find key in database
            keys = self.db.collection(self.api_keys_collection)\
                .where('key_hash', '==', api_key_hash)\
                .where('revoked', '==', False)\
                .limit(1)\
                .stream()
            
            key_doc = None
            key_id = None
            for doc in keys:
                key_doc = doc.to_dict()
                key_id = doc.id
                break
            
            if not key_doc:
                logger.warning(f"Invalid or revoked API key")
                return None
            
            # Check expiry
            if key_doc['expires_at']:
                if datetime.now(timezone.utc) > key_doc['expires_at']:
                    logger.warning(f"Expired API key: {key_doc['key_name']}")
                    return None
            
            # Update last used and request count
            self.db.collection(self.api_keys_collection).document(key_id).update({
                'last_used': datetime.now(timezone.utc),
                'request_count': firestore.Increment(1)
            })
            
            # Get user credits info
            credits_doc = self.db.collection(self.users_collection).document(key_doc['user_id']).get()
            
            if not credits_doc.exists:
                logger.warning(f"User credits not found for user: {key_doc['user_id']} - creating with 0 credits")
                # Create credits document with 0 credits
                self.db.collection(self.users_collection).document(key_doc['user_id']).set({
                    'user_id': key_doc['user_id'],
                    'web_scan_credits': 0,
                    'pdf_scan_credits': 0,
                    'created_at': datetime.now(timezone.utc),
                    'updated_at': datetime.now(timezone.utc)
                })
                credits_data = {
                    'web_scan_credits': 0,
                    'pdf_scan_credits': 0
                }
            else:
                credits_data = credits_doc.to_dict()
            
            return {
                'user_id': key_doc['user_id'],
                'email': credits_data.get('email', 'unknown'),
                'key_name': key_doc['key_name'],
                'key_id': key_id,
                'expires_at': key_doc['expires_at'],
                'validity_period': key_doc['validity_period'],
                'web_scan_credits': credits_data.get('web_scan_credits', 0),
                'pdf_scan_credits': credits_data.get('pdf_scan_credits', 0)
            }
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return None
    
    async def revoke_api_key(self, user_id: str, key_id: str) -> bool:
        """
        Revoke an API key
        
        Args:
            user_id: User ID (for authorization)
            key_id: Key document ID to revoke
        
        Returns:
            True if revoked successfully
        """
        try:
            # Get key document
            key_ref = self.db.collection(self.api_keys_collection).document(key_id)
            key_doc = key_ref.get()
            
            if not key_doc.exists:
                raise HTTPException(status_code=404, detail="API key not found")
            
            key_data = key_doc.to_dict()
            
            # Verify ownership
            if key_data['user_id'] != user_id:
                raise HTTPException(status_code=403, detail="Unauthorized")
            
            # Revoke the key
            key_ref.update({
                'revoked': True,
                'revoked_at': datetime.now(timezone.utc)
            })
            
            logger.info(f"Revoked API key {key_id} for user {user_id}")
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error revoking API key: {e}")
            raise HTTPException(status_code=500, detail="Failed to revoke API key")
    
    async def list_user_keys(self, user_id: str) -> list:
        """
        List all API keys for a user
        
        Args:
            user_id: Firebase user ID
        
        Returns:
            List of API key info (without the actual keys)
        """
        try:
            keys = self.db.collection(self.api_keys_collection)\
                .where('user_id', '==', user_id)\
                .where('revoked', '==', False)\
                .stream()
            
            result = []
            for doc in keys:
                key_data = doc.to_dict()
                
                # Check if expired
                is_expired = False
                if key_data.get('expires_at'):
                    is_expired = datetime.now(timezone.utc) > key_data['expires_at']
                
                if not is_expired:
                    result.append({
                        'key_id': doc.id,
                        'key_name': key_data['key_name'],
                        'created_at': key_data['created_at'].isoformat() if key_data.get('created_at') else None,
                        'expires_at': key_data['expires_at'].isoformat() if key_data.get('expires_at') else None,
                        'validity_period': key_data['validity_period'],
                        'last_used': key_data.get('last_used').isoformat() if key_data.get('last_used') else None,
                        'request_count': key_data.get('request_count', 0)
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing API keys: {e}")
            raise HTTPException(status_code=500, detail="Failed to list API keys")
    
    async def cleanup_expired_keys(self) -> int:
        """
        Clean up expired API keys (mark as revoked)
        
        Returns:
            Number of keys cleaned up
        """
        try:
            now = datetime.now(timezone.utc)
            
            # Find expired keys
            expired_keys = self.db.collection(self.api_keys_collection)\
                .where('revoked', '==', False)\
                .where('expires_at', '<=', now)\
                .stream()
            
            count = 0
            for doc in expired_keys:
                doc.reference.update({
                    'revoked': True,
                    'revoked_at': now
                })
                count += 1
            
            if count > 0:
                logger.info(f"Cleaned up {count} expired API keys")
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired keys: {e}")
            return 0


# Singleton instance
api_key_service = APIKeyService()
