#!/usr/bin/env python3
"""
LumTrails Pricing Service - Email Notifications

Sends transactional emails via the mailing service.
"""
import os
import logging
import httpx

logger = logging.getLogger(__name__)

# Mailing service URL
MAILING_URL = os.getenv("MAILING_URL", "")


async def send_subscription_upgrade_email(
    email: str,
    name: str,
    old_tier: str,
    new_tier: str,
    interval: str,
    language: str
):
    """
    Send subscription upgrade confirmation email via mailing service.
    
    Args:
        email: User's email address
        name: User's display name
        old_tier: Previous subscription tier
        new_tier: New subscription tier
        interval: Billing interval
        language: User's preferred language
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "email": email,
                "name": name,
                "old_tier": old_tier,
                "new_tier": new_tier,
                "interval": interval,
                "language": language
            }
            
            response = await client.post(
                f"{MAILING_URL}/subscription/upgrade",
                json=payload
            )
            
            if response.status_code == 200:
                logger.info(f"Subscription upgrade email sent to {email}")
            else:
                logger.warning(f"Failed to send upgrade email to {email}: {response.status_code} - {response.text}")
                
    except Exception as e:
        logger.error(f"Error sending subscription upgrade email to {email}: {e}")
