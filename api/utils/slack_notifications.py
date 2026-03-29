#!/usr/bin/env python3
"""
Slack Notification Utility for LumTrails

Sends notifications to Slack channels for key events:
- New user signups
- Subscription changes

ONLY ACTIVE IN PRODUCTION (ENVIRONMENT=production)
"""

import os
import logging
import httpx
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

# CET timezone for EU service
CET = ZoneInfo("Europe/Paris")

# Slack webhook URLs (only used in production, set via environment variable)
SLACK_NEW_USER_WEBHOOK = os.getenv("SLACK_NEW_USER_WEBHOOK", "")


def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("ENVIRONMENT", "development") == "production"


async def notify_new_user_signup(email: str, user_id: str):
    """
    Send Slack notification when a new user signs up.
    Only sends in production environment.
    
    Args:
        email: The new user's email address
        user_id: The Firebase user ID
    """
    if not is_production():
        logger.debug(f"Skipping Slack notification for new user (not production): {email}")
        return
    
    try:
        now = datetime.now(CET)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S CET")
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🎉 New User Signup!",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Email:*\n{email}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:*\n{timestamp}"
                        }
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"User ID: `{user_id}`"
                        }
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(SLACK_NEW_USER_WEBHOOK, json=message)
            
            if response.status_code == 200:
                logger.info(f"Slack notification sent for new user: {email}")
            else:
                logger.warning(f"Failed to send Slack notification: {response.status_code}")
                
    except Exception as e:
        # Don't fail user signup if Slack notification fails
        logger.error(f"Error sending Slack notification for new user {email}: {e}")
