#!/usr/bin/env python3
"""
LumTrails Authentication Routes

FastAPI routes for Firebase Auth integration.
Handles login, logout, user profile, and protected endpoints.

Usage:
    Include in main FastAPI app:
    from api.auth.auth_routes import auth_router
    app.include_router(auth_router, prefix="/auth")
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from .auth_service import auth_service, get_current_user, get_optional_user

# Configure logging
logger = logging.getLogger(__name__)

# Create router
auth_router = APIRouter(tags=["authentication"])

# Pydantic models
class UserProfile(BaseModel):
    uid: str
    email: str
    email_verified: bool
    name: Optional[str] = None
    picture: Optional[str] = None
    created_at: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[UserProfile] = None

class TokenRequest(BaseModel):
    token: str

class SignOutRequest(BaseModel):
    uid: str

# Routes
@auth_router.post("/verify-token", response_model=AuthResponse)
async def verify_token(token_request: TokenRequest):
    """Verify Firebase ID token and return user information"""
    try:
        user_info = await auth_service.verify_token(token_request.token)
        
        user_profile = UserProfile(
            uid=user_info['uid'],
            email=user_info['email'],
            email_verified=user_info['email_verified'],
            name=user_info.get('name'),
            picture=user_info.get('picture')
        )
        
        return AuthResponse(
            success=True,
            message="Token verified successfully",
            user=user_profile
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )

@auth_router.get("/profile", response_model=AuthResponse)
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user profile (protected route)"""
    try:
        # Get additional user information from Firebase
        user_data = await auth_service.get_user_by_email(current_user['email'])
        
        user_profile = UserProfile(
            uid=current_user['uid'],
            email=current_user['email'],
            email_verified=current_user['email_verified'],
            name=current_user.get('name') or (user_data.get('display_name') if user_data else None),
            picture=current_user.get('picture') or (user_data.get('photo_url') if user_data else None),
            created_at=user_data.get('created_at') if user_data else None
        )
        
        return AuthResponse(
            success=True,
            message="Profile retrieved successfully",
            user=user_profile
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@auth_router.post("/signout", response_model=AuthResponse)
async def sign_out_user(
    signout_request: SignOutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Sign out user by revoking all refresh tokens"""
    try:
        # Ensure user can only sign out themselves
        if current_user['uid'] != signout_request.uid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot sign out another user"
            )
        
        await auth_service.revoke_refresh_tokens(signout_request.uid)
        
        return AuthResponse(
            success=True,
            message="User signed out successfully"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Sign out error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sign out user"
        )

@auth_router.get("/status")
async def auth_status(current_user: Optional[Dict[str, Any]] = Depends(get_optional_user)):
    """Check authentication status (public route)"""
    if current_user:
        return JSONResponse(content={
            "authenticated": True,
            "user": {
                "uid": current_user['uid'],
                "email": current_user['email'],
                "email_verified": current_user['email_verified']
            }
        })
    else:
        return JSONResponse(content={
            "authenticated": False,
            "user": None
        })

@auth_router.get("/health")
async def auth_health():
    """Authentication service health check"""
    try:
        # Test Firebase connection by trying to get a non-existent user
        # This will fail gracefully and indicate if Firebase is reachable
        await auth_service.get_user_by_email("test@nonexistent.com")
        
        return JSONResponse(content={
            "status": "healthy",
            "service": "firebase-auth",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "service": "firebase-auth", 
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
