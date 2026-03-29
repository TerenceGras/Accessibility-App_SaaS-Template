#!/usr/bin/env python3
"""
LumTrails Pricing Service - Slack Notifications

Sends notifications to Slack channels for subscription events.
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

# Slack webhook URL for subscription events (set via environment variable)
SLACK_SUBSCRIPTION_WEBHOOK = os.getenv("SLACK_SUBSCRIPTION_WEBHOOK", "")

# Production detection via ENVIRONMENT env var
def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("ENVIRONMENT", "development") == "production"


async def notify_subscription_created(
    email: str,
    user_id: str,
    plan: str,
    interval: str
):
    """
    Send Slack notification when a subscription is created.
    Only sends in production environment.
    """
    if not is_production():
        logger.debug(f"Skipping Slack notification for subscription created (not production): {email}")
        return
    
    try:
        now = datetime.now(CET)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S CET")
        
        plan_emoji = "⭐" if plan == "business" else "✨"
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{plan_emoji} New Subscription!",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Email:*\n{email}"},
                        {"type": "mrkdwn", "text": f"*Plan:*\n{plan.capitalize()} ({interval})"}
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"User ID: `{user_id}` | Time: {timestamp}"}
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(SLACK_SUBSCRIPTION_WEBHOOK, json=message)
            
            if response.status_code == 200:
                logger.info(f"Slack notification sent for subscription created: {email}")
            else:
                logger.warning(f"Failed to send Slack notification: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Error sending Slack notification for subscription created {email}: {e}")


async def notify_subscription_updated(
    email: str,
    user_id: str,
    old_status: str,
    new_status: str,
    plan: str,
    interval: str
):
    """
    Send Slack notification when a subscription is updated.
    Only sends in production environment.
    """
    if not is_production():
        logger.debug(f"Skipping Slack notification for subscription updated (not production): {email}")
        return
    
    try:
        now = datetime.now(CET)
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S CET")
        
        if new_status == "active" and old_status in ["incomplete", "incomplete_expired", "past_due"]:
            emoji = "✅"
            title = "Subscription Activated!"
        elif new_status == "past_due":
            emoji = "⚠️"
            title = "Subscription Past Due"
        elif new_status == "canceled":
            emoji = "❌"
            title = "Subscription Canceled"
        else:
            emoji = "🔄"
            title = "Subscription Updated"
        
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} {title}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Email:*\n{email}"},
                        {"type": "mrkdwn", "text": f"*Plan:*\n{plan.capitalize()} ({interval})"}
                    ]
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Status Change:*\n`{old_status}` → `{new_status}`"}
                    ]
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"User ID: `{user_id}` | Time: {timestamp}"}
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(SLACK_SUBSCRIPTION_WEBHOOK, json=message)
            
            if response.status_code == 200:
                logger.info(f"Slack notification sent for subscription updated: {email}")
            else:
                logger.warning(f"Failed to send Slack notification: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Error sending Slack notification for subscription updated {email}: {e}")


async def notify_subscription_deleted(
    email: str,
    user_id: str,
    plan: str
):
    """
    Send Slack notification when a subscription is deleted/canceled.
    Only sends in production environment.
    """
    if not is_production():
        logger.debug(f"Skipping Slack notification for subscription deleted (not production): {email}")
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
                        "text": "📉 Subscription Canceled",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Email:*\n{email}"},
                        {"type": "mrkdwn", "text": f"*Previous Plan:*\n{plan.capitalize()}"}
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "User has been downgraded to Free tier."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": f"User ID: `{user_id}` | Time: {timestamp}"}
                    ]
                }
            ]
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(SLACK_SUBSCRIPTION_WEBHOOK, json=message)
            
            if response.status_code == 200:
                logger.info(f"Slack notification sent for subscription deleted: {email}")
            else:
                logger.warning(f"Failed to send Slack notification: {response.status_code}")
                
    except Exception as e:
        logger.error(f"Error sending Slack notification for subscription deleted {email}: {e}")
