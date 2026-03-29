#!/usr/bin/env python3
"""
LumTrails External API - General Routes

Health checks, API key validation, and account information.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["General"])


class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str


class ValidityResponse(BaseModel):
    key_name: str
    expires_at: str | None
    time_remaining: str
    is_unlimited: bool


class CreditsInfo(BaseModel):
    web_scan_credits: int
    pdf_scan_credits: int


class AccountResponse(BaseModel):
    user_id: str
    email: str
    credits: CreditsInfo


@router.get("/health", response_model=HealthResponse)
async def health_check(user_info: dict = Depends(get_current_user)):
    """
    Health check endpoint - validates API key and returns system status
    """
    return HealthResponse(
        status="healthy",
        message="API is operational",
        timestamp=datetime.now(timezone.utc).isoformat()
    )


@router.get("/validity", response_model=ValidityResponse)
async def check_validity(user_info: dict = Depends(get_current_user)):
    """
    Check remaining validity time for the API key
    """
    expires_at = user_info.get('expires_at')
    is_unlimited = expires_at is None
    
    if is_unlimited:
        time_remaining = "no limit set"
    else:
        # Calculate time remaining
        now = datetime.now(timezone.utc)
        delta = expires_at - now
        
        days = delta.days
        hours = delta.seconds // 3600
        
        if days > 0:
            time_remaining = f"{days} days, {hours} hours"
        else:
            minutes = (delta.seconds % 3600) // 60
            time_remaining = f"{hours} hours, {minutes} minutes"
    
    return ValidityResponse(
        key_name=user_info['key_name'],
        expires_at=expires_at.isoformat() if expires_at else None,
        time_remaining=time_remaining,
        is_unlimited=is_unlimited
    )


@router.get("/account", response_model=AccountResponse)
async def get_account_info(user_info: dict = Depends(get_current_user)):
    """
    Get account information including available credits
    """
    return AccountResponse(
        user_id=user_info['user_id'],
        email=user_info['email'],
        credits=CreditsInfo(
            web_scan_credits=user_info.get('web_scan_credits', 0),
            pdf_scan_credits=user_info.get('pdf_scan_credits', 0)
        )
    )
