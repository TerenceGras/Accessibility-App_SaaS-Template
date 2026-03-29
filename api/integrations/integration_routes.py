from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timezone
from typing import Dict, Any

# Import authentication components
from auth.auth_service import get_current_user

# Import shared components
from integrations.shared.database import (
    db, get_user_integrations_doc, serialize_datetime_objects
)
from integrations.shared.models import IntegrationConfig

# Import integration routers
from integrations.github.routes import github_router
from integrations.slack.routes import slack_router
from integrations.notion.routes import notion_router

logger = logging.getLogger(__name__)

integration_router = APIRouter()

# Include all sub-routers
integration_router.include_router(github_router)
integration_router.include_router(slack_router)
integration_router.include_router(notion_router)

@integration_router.get("/integrations")
async def get_user_integrations(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get all integrations for the authenticated user"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        user_id = current_user['uid']
        logger.info(f"Getting integrations for user: {user_id}")
        
        # Get user integrations document
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            integrations_data = doc.to_dict()
            
            # Serialize datetime objects
            integrations_data = serialize_datetime_objects(integrations_data)
            
            # Remove sensitive data from response
            for platform in ['github', 'notion', 'slack']:
                if platform in integrations_data.get('integrations', {}):
                    config = integrations_data['integrations'][platform].get('config', {})
                    # Remove tokens and webhook URLs from response
                    config.pop('access_token', None)
                    config.pop('refresh_token', None)
                    config.pop('webhook_url', None)
            
            return JSONResponse(content=integrations_data)
        else:
            # Return default integrations structure
            default_integrations = {
                "integrations": {
                    "github": {
                        "config": {
                            "repository": None,
                            "label": "accessibility",
                            "connected": False,
                            "web_scan_enabled": False,
                            "pdf_scan_enabled": False,
                            "last_updated": None
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
                            "issues_created": 0,
                            "last_issue_created": None
                        }
                    },
                    "notion": {
                        "config": {
                            "parent_page_id": None,
                            "page_url": None,
                            "connected": False,
                            "web_scan_enabled": False,
                            "pdf_scan_enabled": False,
                            "last_updated": None
                        },
                        "web_scan_sections": {
                            "wcag_enabled": True,
                            "wcag_severity_filter": ["High", "Medium", "Low"],
                            "wcag_grouping_option": "per-error-type",
                            "wcag_regroup_violations": True,
                            "html_enabled": True,
                            "links_enabled": True,
                            "axtree_enabled": False,
                            "layout_enabled": True
                        },
                        "pdf_scan_sections": {
                            "pdf_grouping_option": "per-page"
                        },
                        "stats": {
                            "pages_created": 0,
                            "last_page_created": None
                        }
                    },
                    "slack": {
                        "config": {
                            "channel": None,
                            "connected": False,
                            "web_scan_enabled": False,
                            "pdf_scan_enabled": False,
                            "last_updated": None
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
                }
            }
            
            # Create the document with default values
            doc_ref.set(default_integrations)
            return JSONResponse(content=default_integrations)
        
    except Exception as e:
        logger.error(f"Error getting user integrations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user integrations")

@integration_router.put("/integrations/{platform}/config")
async def update_integration_config(
    platform: str,
    config_update: IntegrationConfig,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update configuration for a specific integration platform (except GitHub, which has its own endpoint)"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        if platform not in ['notion', 'slack']:
            raise HTTPException(status_code=400, detail="Invalid platform. Use /integrations/github/config for GitHub.")
        
        user_id = current_user['uid']
        logger.info(f"Updating {platform} config for user: {user_id}")
        
        # Get user integrations document
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User integrations not found")
        
        data = doc.to_dict()
        
        # Update the configuration
        if 'integrations' not in data:
            data['integrations'] = {}
        if platform not in data['integrations']:
            data['integrations'][platform] = {}
        if 'config' not in data['integrations'][platform]:
            data['integrations'][platform]['config'] = {}
        
        # Merge new config with existing
        data['integrations'][platform]['config'].update(config_update.config)
        data['integrations'][platform]['last_updated'] = datetime.now(timezone.utc)
        
        # Update in Firestore
        doc_ref.update(data)
        
        return JSONResponse(content={"message": f"{platform.capitalize()} configuration updated successfully"})
        
    except Exception as e:
        logger.error(f"Error updating {platform} config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update {platform} configuration")
