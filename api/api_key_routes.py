#!/usr/bin/env python3
"""
LumTrails Main API - API Key Management Routes

Routes for managing API keys through the web interface.
"""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth.auth_service import get_current_user
from services.api_key_service import api_key_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


class CreateAPIKeyRequest(BaseModel):
    key_name: str
    validity_period: str  # '1day', '1week', '1month', '6months', '1year', 'unlimited'


class CreateAPIKeyResponse(BaseModel):
    key_id: str
    api_key: str  # Only returned once!
    key_name: str
    created_at: str
    expires_at: str | None
    validity_period: str


class APIKeyInfo(BaseModel):
    key_id: str
    key_name: str
    created_at: str
    expires_at: str | None
    validity_period: str
    last_used: str | None
    request_count: int


class ListAPIKeysResponse(BaseModel):
    keys: List[APIKeyInfo]


class RevokeAPIKeyResponse(BaseModel):
    success: bool
    message: str


@router.post("/create", response_model=CreateAPIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    user_info: dict = Depends(get_current_user)
):
    """
    Create a new API key
    
    Requires authentication via Firebase token.
    """
    try:
        result = await api_key_service.create_api_key(
            user_id=user_info['uid'],
            key_name=request.key_name,
            validity_period=request.validity_period
        )
        
        return CreateAPIKeyResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to create API key")


@router.get("/list", response_model=ListAPIKeysResponse)
async def list_api_keys(user_info: dict = Depends(get_current_user)):
    """
    List all API keys for the authenticated user
    
    Does not include the actual API key values.
    """
    try:
        keys = await api_key_service.list_user_keys(user_info['uid'])
        
        return ListAPIKeysResponse(
            keys=[APIKeyInfo(**key) for key in keys]
        )
        
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        raise HTTPException(status_code=500, detail="Failed to list API keys")


@router.delete("/{key_id}", response_model=RevokeAPIKeyResponse)
async def revoke_api_key(
    key_id: str,
    user_info: dict = Depends(get_current_user)
):
    """
    Revoke an API key
    
    The key will be immediately invalidated and cannot be used again.
    """
    try:
        await api_key_service.revoke_api_key(
            user_id=user_info['uid'],
            key_id=key_id
        )
        
        return RevokeAPIKeyResponse(
            success=True,
            message="API key revoked successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        raise HTTPException(status_code=500, detail="Failed to revoke API key")
