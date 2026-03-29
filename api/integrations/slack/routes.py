from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timezone
from typing import Dict, Any
import httpx

# Import authentication components
from auth.auth_service import get_current_user

# Import shared components
from integrations.shared.database import (
    db, secret_client, get_user_integrations_doc, store_secret, serialize_datetime_objects
)
from integrations.shared.models import SlackWebhookConfig, SlackConfigUpdate

logger = logging.getLogger(__name__)

slack_router = APIRouter()

@slack_router.put("/integrations/slack/config")
async def update_slack_config(
    config_update: SlackConfigUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update Slack integration configuration"""
    try:
        user_id = current_user['uid']
        
        # Convert Pydantic model to dict, excluding None values
        config_dict = config_update.model_dump(exclude_none=True)
        logger.info(f"Received Slack config update: {config_dict}")
        
        # Get user document from user_integrations collection
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User integrations not found")
        
        data = doc.to_dict()
        
        # Ensure Slack integration exists
        if 'integrations' not in data or 'slack' not in data['integrations']:
            raise HTTPException(status_code=404, detail="Slack not connected")
        
        # Update configuration - WCAG specific fields go to web_scan_sections
        if 'wcag_severity_filter' in config_dict:
            if 'web_scan_sections' not in data['integrations']['slack']:
                data['integrations']['slack']['web_scan_sections'] = {}
            data['integrations']['slack']['web_scan_sections']['wcag_severity_filter'] = config_dict['wcag_severity_filter']
        
        if 'wcag_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['slack']:
                data['integrations']['slack']['web_scan_sections'] = {}
            data['integrations']['slack']['web_scan_sections']['wcag_grouping_option'] = config_dict['wcag_grouping_option']
        
        if 'wcag_regroup_violations' in config_dict:
            if 'web_scan_sections' not in data['integrations']['slack']:
                data['integrations']['slack']['web_scan_sections'] = {}
            data['integrations']['slack']['web_scan_sections']['wcag_regroup_violations'] = config_dict['wcag_regroup_violations']
        
        if 'webhook_url' in config_dict:
            data['integrations']['slack']['config']['webhook_url'] = config_dict['webhook_url']
        
        if 'channel' in config_dict:
            data['integrations']['slack']['config']['channel'] = config_dict['channel']
        
        # Handle PDF scan configuration
        if 'pdf_grouping_option' in config_dict:
            if 'pdf_scan_sections' not in data['integrations']['slack']:
                data['integrations']['slack']['pdf_scan_sections'] = {}
            data['integrations']['slack']['pdf_scan_sections']['pdf_grouping_option'] = config_dict['pdf_grouping_option']
        
        # Handle web scan sections configuration
        if 'web_scan_sections' in config_dict:
            if 'web_scan_sections' not in data['integrations']['slack']:
                data['integrations']['slack']['web_scan_sections'] = {}
            
            sections = config_dict['web_scan_sections']
            # Pydantic models have attributes, dicts have keys
            
            # Update individual toggle values - check both dict keys and object attributes
            if hasattr(sections, 'wcag_enabled'):
                data['integrations']['slack']['web_scan_sections']['wcag_enabled'] = sections.wcag_enabled
            elif isinstance(sections, dict) and 'wcag_enabled' in sections:
                data['integrations']['slack']['web_scan_sections']['wcag_enabled'] = sections['wcag_enabled']
                
            if hasattr(sections, 'html_enabled'):
                data['integrations']['slack']['web_scan_sections']['html_enabled'] = sections.html_enabled
            elif isinstance(sections, dict) and 'html_enabled' in sections:
                data['integrations']['slack']['web_scan_sections']['html_enabled'] = sections['html_enabled']
                
            if hasattr(sections, 'links_enabled'):
                data['integrations']['slack']['web_scan_sections']['links_enabled'] = sections.links_enabled
            elif isinstance(sections, dict) and 'links_enabled' in sections:
                data['integrations']['slack']['web_scan_sections']['links_enabled'] = sections['links_enabled']
                
            if hasattr(sections, 'axtree_enabled'):
                data['integrations']['slack']['web_scan_sections']['axtree_enabled'] = sections.axtree_enabled
            elif isinstance(sections, dict) and 'axtree_enabled' in sections:
                data['integrations']['slack']['web_scan_sections']['axtree_enabled'] = sections['axtree_enabled']
                
            if hasattr(sections, 'layout_enabled'):
                data['integrations']['slack']['web_scan_sections']['layout_enabled'] = sections.layout_enabled
            elif isinstance(sections, dict) and 'layout_enabled' in sections:
                data['integrations']['slack']['web_scan_sections']['layout_enabled'] = sections['layout_enabled']
        
        # Handle module-specific grouping options
        if 'html_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['slack']:
                data['integrations']['slack']['web_scan_sections'] = {}
            data['integrations']['slack']['web_scan_sections']['html_grouping_option'] = config_dict['html_grouping_option']
        
        if 'links_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['slack']:
                data['integrations']['slack']['web_scan_sections'] = {}
            data['integrations']['slack']['web_scan_sections']['links_grouping_option'] = config_dict['links_grouping_option']
        
        if 'layout_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['slack']:
                data['integrations']['slack']['web_scan_sections'] = {}
            data['integrations']['slack']['web_scan_sections']['layout_grouping_option'] = config_dict['layout_grouping_option']
        
        data['integrations']['slack']['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Update in Firestore
        doc_ref.set(data)
        
        # Serialize the response data to handle datetime objects
        serialized_config = serialize_datetime_objects(data['integrations']['slack'])
        
        return JSONResponse(content={
            "message": "Slack configuration updated successfully",
            "config": serialized_config
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Slack config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Slack configuration")

@slack_router.put("/integrations/slack/status")
async def update_slack_integration_status(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update Slack integration enabled/disabled status"""
    try:
        user_id = current_user["uid"]
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User integrations not found")
        
        data = doc.to_dict()
        
        # Ensure integrations structure exists
        if 'integrations' not in data:
            data['integrations'] = {}
        if 'slack' not in data['integrations']:
            raise HTTPException(status_code=400, detail="Slack integration not configured")
        
        # Update web_scan_enabled status in config
        is_enabled = request.get('is_enabled', False)
        if 'config' not in data['integrations']['slack']:
            data['integrations']['slack']['config'] = {}
        data['integrations']['slack']['config']['web_scan_enabled'] = is_enabled
        data['integrations']['slack']['config']['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Save to Firestore
        doc_ref.set(data)
        
        return JSONResponse(content={
            "message": f"Slack integration {'enabled' if is_enabled else 'disabled'} successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Slack integration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Slack integration status")

@slack_router.put("/integrations/slack/pdf-status")
async def update_slack_pdf_integration_status(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update Slack PDF scan integration enabled/disabled status"""
    try:
        user_id = current_user["uid"]
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User integrations not found")
        
        data = doc.to_dict()
        
        # Ensure integrations structure exists
        if 'integrations' not in data:
            data['integrations'] = {}
        if 'slack' not in data['integrations']:
            raise HTTPException(status_code=400, detail="Slack integration not configured")
        
        # Update pdf_scan_enabled status in config
        is_enabled = request.get('is_enabled', False)
        if 'config' not in data['integrations']['slack']:
            data['integrations']['slack']['config'] = {}
        data['integrations']['slack']['config']['pdf_scan_enabled'] = is_enabled
        data['integrations']['slack']['config']['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Save to Firestore
        doc_ref.set(data)
        
        return JSONResponse(content={
            "message": f"Slack PDF integration {'enabled' if is_enabled else 'disabled'} successfully",
            "pdf_scan_enabled": is_enabled
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Slack PDF integration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Slack PDF integration status")

@slack_router.post("/integrations/slack/webhook")
async def connect_slack_webhook(
    webhook_config: SlackWebhookConfig,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Connect Slack via webhook URL"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        user_id = current_user['uid']
        logger.info(f"Connecting Slack webhook for user: {user_id}")
        
        # Test webhook URL
        test_payload = {
            "text": "🎉 LumTrails integration test successful! Your accessibility scan notifications are now connected.",
            "username": "LumTrails",
            "channel": webhook_config.channel if webhook_config.channel else None
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(webhook_config.webhook_url, json=test_payload)
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid webhook URL or Slack rejected the request")
        
        # Store webhook URL securely
        secret_id = f"slack-webhook-{user_id}"
        if not store_secret(secret_id, webhook_config.webhook_url):
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
            'config': {
                'channel': webhook_config.channel,
                'webhook_secret_id': secret_id,  # Store secret reference, not the URL
                'connected': True,
                'web_scan_enabled': True,
                'pdf_scan_enabled': False,
                'last_updated': datetime.now(timezone.utc).isoformat()
            },
            'web_scan_sections': {
                'wcag_enabled': True,
                'wcag_severity_filter': ['High', 'Medium', 'Low'],
                'wcag_grouping_option': 'per-error-type',
                'wcag_regroup_violations': False,
                'html_enabled': True,
                'links_enabled': True,
                'axtree_enabled': False,
                'layout_enabled': True
            },
            'pdf_scan_sections': {
                'pdf_grouping_option': 'per-page'
            },
            'stats': data['integrations']['slack'].get('stats', {
                'messages_posted': 0,
                'last_message_posted': None
            })
        })
        
        # Update in Firestore
        doc_ref.set(data)
        
        return JSONResponse(content={
            "message": "Slack webhook connected successfully",
            "test_sent": True
        })
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=400, detail="Webhook URL timeout")
    except httpx.RequestError:
        raise HTTPException(status_code=400, detail="Invalid webhook URL")
    except Exception as e:
        logger.error(f"Error connecting Slack webhook: {e}")
        raise HTTPException(status_code=500, detail="Failed to connect Slack webhook")

@slack_router.post("/integrations/slack/disconnect")
async def disconnect_slack_integration(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Disconnect Slack integration"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        user_id = current_user['uid']
        logger.info(f"Disconnecting Slack for user: {user_id}")
        
        # Get user integrations document
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User integrations not found")
        
        data = doc.to_dict()
        
        # Delete stored webhook URL from Secret Manager first
        secret_id = f"slack-webhook-{user_id}"
        try:
            secret_path = f"projects/{db._project}/secrets/{secret_id}"
            if secret_client:
                secret_client.delete_secret(request={"name": secret_path})
                logger.info(f"Deleted Slack webhook for user: {user_id}")
        except Exception as e:
            logger.warning(f"Could not delete Slack webhook for user {user_id}: {e}")
        
        # Completely reset Slack integration to default state
        if 'integrations' not in data:
            data['integrations'] = {}
        
        # Reset to default Slack integration state
        data['integrations']['slack'] = {
            "config": {
                "channel": None,
                "connected": False,
                "web_scan_enabled": False,
                "pdf_scan_enabled": False,
                "last_updated": datetime.now(timezone.utc).isoformat()
            },
            "web_scan_sections": {
                "wcag_enabled": True,
                "wcag_severity_filter": ["High", "Medium", "Low"],
                "wcag_grouping_option": "per-error-type",
                "wcag_regroup_violations": False,
                "html_enabled": True,
                "links_enabled": True,
                "axtree_enabled": False,
                "layout_enabled": True
            },
            "pdf_scan_sections": {
                "pdf_grouping_option": "per-page"
            },
            "stats": {
                "messages_posted": 0,
                "last_message_posted": None
            }
        }
        
        # Clear any OAuth states (in case Slack OAuth is added later)
        if 'oauth_states' in data and 'slack' in data['oauth_states']:
            del data['oauth_states']['slack']
        
        # Update in Firestore using set() instead of update()
        doc_ref.set(data)
        
        logger.info(f"Slack integration fully disconnected for user: {user_id}")
        
        return JSONResponse(content={
            "message": "Slack disconnected successfully"
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting Slack: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Slack")
