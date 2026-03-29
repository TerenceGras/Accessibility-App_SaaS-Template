#!/usr/bin/env python3
"""
LumTrails Pricing Service - Authentication Middleware

Firebase authentication middleware for protecting pricing endpoints.
"""
import os
import logging
from typing import Dict, Any, Optional
from firebase_admin import auth, credentials, initialize_app
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# Initialize Firebase Admin SDK
try:
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    firebase_project_id = os.getenv("FIREBASE_PROJECT_ID", project_id)
    
    cred = credentials.ApplicationDefault()
    initialize_app(cred, {
        'projectId': firebase_project_id,
    })
    logger.info(f"Firebase Admin SDK initialized for project: {firebase_project_id}")
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
    raise


async def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Verify Firebase ID token and return user info
    
    Args:
        token: Firebase ID token
    
    Returns:
        Dict containing user information
    
    Raises:
        HTTPException: If token is invalid or expired
    """
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
        
        logger.info(f"Token verified for user: {user_info['email']}")
        return user_info
        
    except auth.InvalidIdTokenError:
        logger.warning("Invalid ID token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
    except auth.ExpiredIdTokenError:
        logger.warning("Expired ID token provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired"
        )
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    FastAPI dependency to get current authenticated user
    
    Args:
        credentials: HTTP Bearer credentials from request header
    
    Returns:
        Dict containing user information with user_id and email
    
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    user_info = await verify_firebase_token(token)
    
    # Return format compatible with existing code
    return {
        "user_id": user_info['uid'],
        "email": user_info['email'],
        "name": user_info.get('name'),
        "email_verified": user_info.get('email_verified', False)
    }


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    FastAPI dependency to get current user (optional authentication)
    
    Args:
        credentials: HTTP Bearer credentials from request header (optional)
    
    Returns:
        Dict containing user information or None if not authenticated
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_info = await verify_firebase_token(token)
        return {
            "user_id": user_info['uid'],
            "email": user_info['email'],
            "name": user_info.get('name'),
            "email_verified": user_info.get('email_verified', False)
        }
    except HTTPException:
        return None
