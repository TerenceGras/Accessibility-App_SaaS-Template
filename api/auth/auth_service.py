#!/usr/bin/env python3
"""
LumTrails Authentication Service

Firebase Auth integration for B2B SaaS authentication.
Handles user authentication, token verification, and user management.

Usage:
    from api.auth.auth_service import AuthService
    
    auth = AuthService()
    user = await auth.verify_token(token)

Environment Variables:
    GOOGLE_CLOUD_PROJECT: Google Cloud Project ID
    FIREBASE_PROJECT_ID: Firebase Project ID (usually same as GOOGLE_CLOUD_PROJECT)
    DEV_WHITELIST_EMAILS: Comma-separated list of whitelisted emails for DEV environment
"""

import os
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from firebase_admin import auth, credentials, initialize_app
from google.auth import default
from google.cloud import firestore
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import Slack notification utility
from utils.slack_notifications import notify_new_user_signup

# DEV environment email whitelist
# In production, this is empty (all authenticated users allowed)
# In DEV, only whitelisted emails can access the system
DEV_WHITELIST_EMAILS: List[str] = [
    email.strip().lower() 
    for email in os.getenv("DEV_WHITELIST_EMAILS", "").split(",") 
    if email.strip()
]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def is_email_whitelisted(email: str) -> bool:
    """
    Check if an email is whitelisted for DEV environment access.
    In production (empty whitelist), all emails are allowed.
    """
    if not DEV_WHITELIST_EMAILS:
        # No whitelist configured = production mode, allow all
        return True
    
    return email.lower() in DEV_WHITELIST_EMAILS


class AuthService:
    """Firebase Authentication Service"""
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
        self.firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", self.project_id)
        self._initialize_firebase()
        # Initialize Firestore client for user document creation
        self.db = firestore.Client(project=self.project_id)
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK with Application Default Credentials"""
        try:
            # Use Application Default Credentials (works in Cloud Run)
            cred = credentials.ApplicationDefault()
            initialize_app(cred, {
                'projectId': self.firebase_project_id,
            })
            logger.info(f"Firebase Admin SDK initialized for project: {self.firebase_project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            raise e
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify Firebase ID token and return user info"""
        try:
            # Verify the ID token
            decoded_token = auth.verify_id_token(token)
            
            # Extract user information
            user_info = {
                'uid': decoded_token.get('uid'),
                'email': decoded_token.get('email'),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name'),
                'picture': decoded_token.get('picture'),
                'firebase_claims': decoded_token
            }
            
            # DEV environment: Check email whitelist
            user_email = user_info.get('email', '')
            if not is_email_whitelisted(user_email):
                logger.warning(f"Unauthorized email attempted access in DEV: {user_email}")
                raise HTTPException(
                    status_code=403, 
                    detail="Access restricted to authorized accounts in DEV environment"
                )
            
            # Create user document in Firestore if it doesn't exist (first authentication)
            await self._ensure_user_document(user_info)
            
            # Check Firestore for custom email_verified status (set by our verification flow)
            # This overrides Firebase Auth's email_verified if our custom verification is complete
            user_info = await self._check_email_verification_status(user_info)
            
            logger.info(f"Token verified for user: {user_info['email']}")
            return user_info
            
        except auth.InvalidIdTokenError:
            logger.warning(f"Invalid ID token provided")
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        except auth.ExpiredIdTokenError:
            logger.warning(f"Expired ID token provided")
            raise HTTPException(status_code=401, detail="Authentication token has expired")
        except HTTPException:
            # Re-raise HTTPExceptions (like 403 from whitelist check) as-is
            raise
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def _ensure_user_document(self, user_info: Dict[str, Any]):
        """Create user document in Firestore if it doesn't exist"""
        try:
            user_id = user_info['uid']
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if not user_doc.exists:
                # Create new user document with default FREE tier credits
                # Free users get: 40 web scan credits + 2 PDF scan credits (renewed weekly on Monday 00:00 CET)
                user_data = {
                    'user_id': user_id,
                    'email': user_info['email'],
                    'plan': 'free',
                    'web_scan_credits': 40,  # Free tier: 40 web scan credits per week
                    'pdf_scan_credits': 2,   # Free tier: 2 PDF scan credits per week
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'updated_at': firestore.SERVER_TIMESTAMP
                }
                user_ref.set(user_data)
                logger.info(f"Created Firestore user document for: {user_info['email']} with free tier credits (40 web, 2 PDF)")
                
                # Send Slack notification for new user signup (production only)
                await notify_new_user_signup(user_info['email'], user_id)
            
        except Exception as e:
            logger.error(f"Error ensuring user document for {user_info.get('email')}: {e}")
            # Don't fail authentication if user document creation fails
            pass
    
    async def _check_email_verification_status(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check Firestore for custom email_verified status.
        
        Our verification flow (via mailing service) sets email_verified in Firestore,
        which should take precedence over Firebase Auth's built-in email_verified.
        
        Google OAuth users automatically have email_verified=True from Firebase.
        Email/password users need to go through our verification flow.
        """
        try:
            # If already verified via Firebase Auth (e.g., Google OAuth), keep it
            if user_info.get('email_verified'):
                return user_info
            
            # Check Firestore for our custom verification status
            user_id = user_info['uid']
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                # If our custom verification flow marked email as verified, update user_info
                if user_data.get('email_verified') is True:
                    user_info['email_verified'] = True
                    logger.info(f"Email verified status loaded from Firestore for: {user_info['email']}")
            
            return user_info
            
        except Exception as e:
            logger.error(f"Error checking email verification status for {user_info.get('email')}: {e}")
            # Return original user_info if check fails
            return user_info
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user information by email"""
        try:
            user = auth.get_user_by_email(email)
            return {
                'uid': user.uid,
                'email': user.email,
                'email_verified': user.email_verified,
                'display_name': user.display_name,
                'photo_url': user.photo_url,
                'disabled': user.disabled,
                'created_at': user.user_metadata.creation_timestamp.isoformat() if user.user_metadata.creation_timestamp else None
            }
        except auth.UserNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def create_custom_token(self, uid: str, additional_claims: Optional[Dict] = None) -> str:
        """Create a custom token for a user"""
        try:
            custom_token = auth.create_custom_token(uid, additional_claims)
            return custom_token.decode('utf-8')
        except Exception as e:
            logger.error(f"Error creating custom token for {uid}: {e}")
            raise HTTPException(status_code=500, detail="Failed to create authentication token")
    
    async def revoke_refresh_tokens(self, uid: str):
        """Revoke all refresh tokens for a user (sign out everywhere)"""
        try:
            auth.revoke_refresh_tokens(uid)
            logger.info(f"Revoked refresh tokens for user: {uid}")
        except Exception as e:
            logger.error(f"Error revoking tokens for {uid}: {e}")
            raise HTTPException(status_code=500, detail="Failed to revoke user sessions")

# Global auth service instance
auth_service = AuthService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """FastAPI dependency to get current authenticated user"""
    token = credentials.credentials
    return await auth_service.verify_token(token)

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)) -> Optional[Dict[str, Any]]:
    """FastAPI dependency to get current user (optional authentication)"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        return await auth_service.verify_token(token)
    except HTTPException:
        return None
