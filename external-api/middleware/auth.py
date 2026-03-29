#!/usr/bin/env python3
"""
LumTrails External API - Authentication Middleware

Middleware for validating API keys and extracting user information.
Credit deduction logic for web scans (per module) and PDF scans (per page).
"""

import logging
from typing import Optional, List
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from services.api_key_service import api_key_service

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Available scan modules for web scans
AVAILABLE_WEB_MODULES = ["axe", "nu", "axTree", "galen", "links"]


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> dict:
    """
    Dependency to get current authenticated user from API key
    
    Raises:
        HTTPException: If API key is invalid or expired
    
    Returns:
        User information dictionary
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key"
        )
    
    api_key = credentials.credentials
    
    # Validate API key
    user_info = await api_key_service.validate_api_key(api_key)
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key"
        )
    
    logger.info(f"Authenticated user: {user_info['email']} (key: {user_info['key_name']})")
    
    return user_info


def calculate_web_scan_credits(modules: Optional[List[str]] = None) -> int:
    """
    Calculate the number of credits required for a web scan based on active modules.
    
    Args:
        modules: List of module IDs to run. If None, all modules will be run.
    
    Returns:
        Number of credits required (1 per module)
    """
    if modules is None:
        # All modules by default
        return len(AVAILABLE_WEB_MODULES)
    
    # Filter to only valid modules
    valid_modules = [m for m in modules if m in AVAILABLE_WEB_MODULES]
    
    # If no valid modules specified, use all modules
    if not valid_modules:
        return len(AVAILABLE_WEB_MODULES)
    
    return len(valid_modules)


async def check_web_scan_credits(user_info: dict, modules: Optional[List[str]] = None) -> dict:
    """
    Check if user has enough web scan credits for the requested modules.
    
    Web scans cost 1 credit per active module (max 5 credits for all modules).
    
    Args:
        user_info: User information from get_current_user
        modules: List of modules to run (if None, all 5 modules)
    
    Raises:
        HTTPException: If insufficient credits
    
    Returns:
        User information with credits_required added
    """
    required = calculate_web_scan_credits(modules)
    available = user_info.get('web_scan_credits', 0)
    
    if available < required:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "insufficient_credits",
                "message": f"Insufficient web scan credits. Required: {required} (1 per module), Available: {available}",
                "credits_required": required,
                "credits_available": available,
                "modules_requested": modules if modules else AVAILABLE_WEB_MODULES
            }
        )
    
    # Add credits_required to user_info for later deduction
    user_info['credits_required'] = required
    return user_info


async def check_pdf_scan_credits(user_info: dict, pages_required: int) -> dict:
    """
    Check if user has enough PDF scan credits for the number of pages.
    
    PDF scans cost 1 credit per page.
    
    Args:
        user_info: User information from get_current_user
        pages_required: Number of pages in the PDF document
    
    Raises:
        HTTPException: If insufficient credits
    
    Returns:
        User information with credits_required added
    """
    available = user_info.get('pdf_scan_credits', 0)
    
    if available < pages_required:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "error": "insufficient_credits",
                "message": f"Insufficient PDF scan credits. Required: {pages_required} (1 per page), Available: {available}",
                "credits_required": pages_required,
                "credits_available": available
            }
        )
    
    # Add credits_required to user_info for later deduction
    user_info['credits_required'] = pages_required
    return user_info
