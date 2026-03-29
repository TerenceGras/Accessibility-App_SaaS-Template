import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import HTTPException

from ..base.auth import get_user_integrations_doc, get_secret, store_secret

logger = logging.getLogger(__name__)

async def test_slack_webhook(webhook_url: str, channel: str = None) -> bool:
    """Test if a Slack webhook URL is valid by sending a test message"""
    try:
        test_payload = {
            "text": "🎉 LumTrails integration test successful! Your accessibility scan notifications are now connected.",
            "username": "LumTrails",
            "channel": channel if channel else None
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=test_payload)
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"Error testing Slack webhook: {e}")
        return False

async def connect_slack_webhook(user_id: str, webhook_url: str, channel: str = None) -> Dict[str, Any]:
    """Connect Slack webhook for a user"""
    try:
        # Test webhook URL
        if not await test_slack_webhook(webhook_url, channel):
            raise HTTPException(status_code=400, detail="Invalid webhook URL or Slack rejected the request")
        
        # Store webhook URL securely
        secret_id = f"slack-webhook-{user_id}"
        if not store_secret(secret_id, webhook_url):
            raise HTTPException(status_code=500, detail="Failed to store webhook securely")
        
        # Get user integrations document
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        data = doc.to_dict() if doc.exists else {"integrations": {}}
        
        # Update Slack integration
        if 'integrations' not in data:
            data['integrations'] = {}
        if 'slack' not in data['integrations']:
            data['integrations']['slack'] = {}
        
        data['integrations']['slack'].update({
            'connected': True,
            'config': {
                'channel': channel,
                'webhook_secret_id': secret_id  # Store secret reference, not the URL
            },
            'web_scan_sections': {
                'wcag_enabled': True,
                'html_enabled': True,
                'links_enabled': True,
                'axtree_enabled': False,
                'layout_enabled': True,
                'html_grouping_option': 'per-error-type',
                'links_grouping_option': 'per-error-type',
                'layout_grouping_option': 'per-error-type'
            },
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'stats': data['integrations']['slack'].get('stats', {
                'messages_posted': 0,
                'last_message_posted': None
            })
        })
        
        # Update in Firestore
        doc_ref.set(data)
        
        return {
            "message": "Slack webhook connected successfully",
            "test_sent": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting Slack webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect Slack webhook")

async def send_slack_notification(user_id: str, message: str) -> bool:
    """Send a notification to user's connected Slack webhook"""
    try:
        # Get user integrations
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.warning(f"No integrations found for user {user_id}")
            return False
        
        data = doc.to_dict()
        slack_config = data.get('integrations', {}).get('slack', {})
        config = slack_config.get('config', {})
        
        if not config.get('connected'):
            logger.info(f"Slack not connected for user {user_id}")
            return False
        
        # Get webhook URL from secrets
        webhook_secret_id = config.get('webhook_secret_id')
        if not webhook_secret_id:
            logger.error(f"No webhook secret ID found for user {user_id}")
            return False
        
        webhook_url = get_secret(webhook_secret_id)
        if not webhook_url:
            logger.error(f"Could not retrieve webhook URL for user {user_id}")
            return False
        
        # Send message
        channel = config.get('channel')
        payload = {
            "text": message,
            "username": "LumTrails",
            "channel": channel if channel else None
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_url, json=payload)
            
            if response.status_code == 200:
                # Update stats
                slack_config['stats']['messages_posted'] += 1
                slack_config['stats']['last_message_posted'] = datetime.now(timezone.utc).isoformat()
                data['integrations']['slack'] = slack_config
                doc_ref.set(data)
                return True
            else:
                logger.error(f"Slack webhook returned status {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"Error sending Slack notification: {e}")
        return False
