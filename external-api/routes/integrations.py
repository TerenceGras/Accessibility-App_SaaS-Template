#!/usr/bin/env python3
"""
LumTrails External API - Integration Routes

Configure and manage integrations (GitHub, Notion, Slack).
Uses the new Firebase schema with web_scan_sections and pdf_scan_sections.
"""

import logging
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List
from google.cloud import firestore
from middleware.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["Integrations"])

# Initialize Firestore
db = firestore.Client()


# ============================================================================
# Shared Models
# ============================================================================

class WebScanSectionsConfig(BaseModel):
    """Web scan sections configuration for all platforms"""
    # Module enable toggles
    wcag_enabled: Optional[bool] = None
    html_enabled: Optional[bool] = None
    links_enabled: Optional[bool] = None
    axtree_enabled: Optional[bool] = None
    layout_enabled: Optional[bool] = None
    
    # WCAG/Axe-core specific settings
    wcag_grouping_option: Optional[str] = None  # "per-error-type" | "single-issue"
    wcag_regroup_violations: Optional[bool] = None
    wcag_severity_filter: Optional[List[str]] = None  # ["High", "Medium", "Low"]
    
    # Other module grouping options
    html_grouping_option: Optional[str] = None  # "per-error-type" | "single-issue"
    links_grouping_option: Optional[str] = None  # "per-error-type" | "single-issue"
    layout_grouping_option: Optional[str] = None  # "per-error-type" | "single-issue"


class PdfScanSectionsConfig(BaseModel):
    """PDF scan sections configuration for all platforms"""
    pdf_grouping_option: Optional[str] = None  # "per-page" | "single-issue"


def validate_grouping_option(option: str, valid_options: set, field_name: str):
    """Validate grouping option against valid values"""
    if option not in valid_options:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid {field_name}. Use: {', '.join(valid_options)}"
        )


def validate_severity_filter(severity_filter: List[str]):
    """Validate severity filter values"""
    valid_severities = {'High', 'Medium', 'Low'}
    if not all(s in valid_severities for s in severity_filter):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid severity filter. Use: High, Medium, Low"
        )


def apply_web_scan_sections_update(current_sections: dict, update: WebScanSectionsConfig) -> dict:
    """Apply web scan sections update to current config"""
    sections = current_sections.copy()
    
    # Module enable toggles
    if update.wcag_enabled is not None:
        sections['wcag_enabled'] = update.wcag_enabled
    if update.html_enabled is not None:
        sections['html_enabled'] = update.html_enabled
    if update.links_enabled is not None:
        sections['links_enabled'] = update.links_enabled
    if update.axtree_enabled is not None:
        sections['axtree_enabled'] = update.axtree_enabled
    if update.layout_enabled is not None:
        sections['layout_enabled'] = update.layout_enabled
    
    # WCAG specific settings
    if update.wcag_grouping_option is not None:
        validate_grouping_option(update.wcag_grouping_option, {'per-error-type', 'single-issue'}, 'wcag_grouping_option')
        sections['wcag_grouping_option'] = update.wcag_grouping_option
    if update.wcag_regroup_violations is not None:
        sections['wcag_regroup_violations'] = update.wcag_regroup_violations
    if update.wcag_severity_filter is not None:
        validate_severity_filter(update.wcag_severity_filter)
        sections['wcag_severity_filter'] = update.wcag_severity_filter
    
    # Other module grouping options
    if update.html_grouping_option is not None:
        validate_grouping_option(update.html_grouping_option, {'per-error-type', 'single-issue'}, 'html_grouping_option')
        sections['html_grouping_option'] = update.html_grouping_option
    if update.links_grouping_option is not None:
        validate_grouping_option(update.links_grouping_option, {'per-error-type', 'single-issue'}, 'links_grouping_option')
        sections['links_grouping_option'] = update.links_grouping_option
    if update.layout_grouping_option is not None:
        validate_grouping_option(update.layout_grouping_option, {'per-error-type', 'single-issue'}, 'layout_grouping_option')
        sections['layout_grouping_option'] = update.layout_grouping_option
    
    return sections


def apply_pdf_scan_sections_update(current_sections: dict, update: PdfScanSectionsConfig) -> dict:
    """Apply PDF scan sections update to current config"""
    sections = current_sections.copy()
    
    if update.pdf_grouping_option is not None:
        validate_grouping_option(update.pdf_grouping_option, {'per-page', 'single-issue'}, 'pdf_grouping_option')
        sections['pdf_grouping_option'] = update.pdf_grouping_option
    
    return sections


# ============================================================================
# GitHub Integration
# ============================================================================

class GitHubHealthResponse(BaseModel):
    connected: bool
    account: Optional[dict] = None
    repository: Optional[str] = None
    web_scan_enabled: Optional[bool] = None
    pdf_scan_enabled: Optional[bool] = None
    message: Optional[str] = None


class GitHubConfigRequest(BaseModel):
    # Config section
    repository: Optional[str] = None
    label: Optional[str] = None
    web_scan_enabled: Optional[bool] = None
    pdf_scan_enabled: Optional[bool] = None
    
    # Web scan sections
    web_scan_sections: Optional[WebScanSectionsConfig] = None
    
    # PDF scan sections
    pdf_scan_sections: Optional[PdfScanSectionsConfig] = None


class GitHubConfigResponse(BaseModel):
    success: bool
    message: str
    config: dict


@router.get("/github/health", response_model=GitHubHealthResponse)
async def github_health(user_info: dict = Depends(get_current_user)):
    """Check GitHub integration connection status"""
    try:
        doc = db.collection('user_integrations').document(user_info['user_id']).get()
        
        if not doc.exists:
            return GitHubHealthResponse(
                connected=False,
                message="GitHub integration is not connected. Please connect via the web interface."
            )
        
        integrations = doc.to_dict().get('integrations', {})
        github_data = integrations.get('github', {})
        config = github_data.get('config', {})
        
        if not config.get('connected', False):
            return GitHubHealthResponse(
                connected=False,
                message="GitHub integration is not connected. Please connect via the web interface."
            )
        
        account_info = {
            "username": config.get('github_user', 'Unknown'),
            "id": config.get('github_user_id', 0)
        }
        
        return GitHubHealthResponse(
            connected=True,
            account=account_info,
            repository=config.get('repository'),
            web_scan_enabled=config.get('web_scan_enabled', False),
            pdf_scan_enabled=config.get('pdf_scan_enabled', False)
        )
        
    except Exception as e:
        logger.error(f"Error checking GitHub health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check GitHub integration status"
        )


@router.put("/github/config", response_model=GitHubConfigResponse)
async def configure_github(
    request: GitHubConfigRequest,
    user_info: dict = Depends(get_current_user)
):
    """Update GitHub integration configuration"""
    try:
        doc_ref = db.collection('user_integrations').document(user_info['user_id'])
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GitHub integration not connected. Please connect via the web interface."
            )
        
        integrations = doc.to_dict().get('integrations', {})
        github_data = integrations.get('github', {})
        config = github_data.get('config', {})
        
        if not config.get('connected', False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="GitHub integration not connected. Please connect via the web interface."
            )
        
        # Update config section
        if request.repository is not None:
            if not re.match(r'^[\w\-\.]+/[\w\-\.]+$', request.repository):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid repository format. Use 'owner/repo'"
                )
            config['repository'] = request.repository
        
        if request.label is not None:
            config['label'] = request.label
        
        if request.web_scan_enabled is not None:
            config['web_scan_enabled'] = request.web_scan_enabled
        
        if request.pdf_scan_enabled is not None:
            config['pdf_scan_enabled'] = request.pdf_scan_enabled
        
        config['last_updated'] = datetime.now(timezone.utc).isoformat()
        github_data['config'] = config
        
        # Update web_scan_sections
        if request.web_scan_sections is not None:
            current_sections = github_data.get('web_scan_sections', {})
            github_data['web_scan_sections'] = apply_web_scan_sections_update(current_sections, request.web_scan_sections)
        
        # Update pdf_scan_sections
        if request.pdf_scan_sections is not None:
            current_sections = github_data.get('pdf_scan_sections', {})
            github_data['pdf_scan_sections'] = apply_pdf_scan_sections_update(current_sections, request.pdf_scan_sections)
        
        # Save to Firestore
        integrations['github'] = github_data
        doc_ref.update({'integrations': integrations})
        
        logger.info(f"Updated GitHub config for user {user_info['user_id']}")
        
        return GitHubConfigResponse(
            success=True,
            message="GitHub integration configuration updated successfully",
            config={
                "config": config,
                "web_scan_sections": github_data.get('web_scan_sections', {}),
                "pdf_scan_sections": github_data.get('pdf_scan_sections', {})
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring GitHub: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update GitHub configuration"
        )


# ============================================================================
# Notion Integration
# ============================================================================

class NotionHealthResponse(BaseModel):
    connected: bool
    workspace: Optional[dict] = None
    parent_page_id: Optional[str] = None
    web_scan_enabled: Optional[bool] = None
    pdf_scan_enabled: Optional[bool] = None
    message: Optional[str] = None


class NotionConfigRequest(BaseModel):
    # Config section
    page_url: Optional[str] = None
    web_scan_enabled: Optional[bool] = None
    pdf_scan_enabled: Optional[bool] = None
    
    # Web scan sections
    web_scan_sections: Optional[WebScanSectionsConfig] = None
    
    # PDF scan sections
    pdf_scan_sections: Optional[PdfScanSectionsConfig] = None


class NotionConfigResponse(BaseModel):
    success: bool
    message: str
    config: dict


def extract_notion_page_id(page_url: str) -> str:
    """Extract page ID from Notion URL"""
    # Notion URLs: https://www.notion.so/Page-Title-abc123def456
    match = re.search(r'([a-f0-9]{32})', page_url)
    if match:
        return match.group(1)
    
    # Alternative format with dashes: abc123de-f456-...
    match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', page_url)
    if match:
        return match.group(1).replace('-', '')
    
    raise ValueError("Could not extract page ID from Notion URL")


@router.get("/notion/health", response_model=NotionHealthResponse)
async def notion_health(user_info: dict = Depends(get_current_user)):
    """Check Notion integration connection status"""
    try:
        doc = db.collection('user_integrations').document(user_info['user_id']).get()
        
        if not doc.exists:
            return NotionHealthResponse(
                connected=False,
                message="Notion integration is not connected. Please connect via the web interface."
            )
        
        integrations = doc.to_dict().get('integrations', {})
        notion_data = integrations.get('notion', {})
        config = notion_data.get('config', {})
        
        if not config.get('connected', False):
            return NotionHealthResponse(
                connected=False,
                message="Notion integration is not connected. Please connect via the web interface."
            )
        
        workspace_info = {
            "name": config.get('notion_user', 'My Workspace'),
            "id": config.get('notion_user_id', 'unknown')
        }
        
        return NotionHealthResponse(
            connected=True,
            workspace=workspace_info,
            parent_page_id=config.get('parent_page_id'),
            web_scan_enabled=config.get('web_scan_enabled', False),
            pdf_scan_enabled=config.get('pdf_scan_enabled', False)
        )
        
    except Exception as e:
        logger.error(f"Error checking Notion health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check Notion integration status"
        )


@router.put("/notion/config", response_model=NotionConfigResponse)
async def configure_notion(
    request: NotionConfigRequest,
    user_info: dict = Depends(get_current_user)
):
    """Update Notion integration configuration"""
    try:
        doc_ref = db.collection('user_integrations').document(user_info['user_id'])
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notion integration not connected. Please connect via the web interface."
            )
        
        integrations = doc.to_dict().get('integrations', {})
        notion_data = integrations.get('notion', {})
        config = notion_data.get('config', {})
        
        if not config.get('connected', False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notion integration not connected. Please connect via the web interface."
            )
        
        # Update config section
        if request.page_url is not None:
            try:
                parent_page_id = extract_notion_page_id(request.page_url)
                config['page_url'] = request.page_url
                config['parent_page_id'] = parent_page_id
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e)
                )
        
        if request.web_scan_enabled is not None:
            config['web_scan_enabled'] = request.web_scan_enabled
        
        if request.pdf_scan_enabled is not None:
            config['pdf_scan_enabled'] = request.pdf_scan_enabled
        
        config['last_updated'] = datetime.now(timezone.utc).isoformat()
        notion_data['config'] = config
        
        # Update web_scan_sections
        if request.web_scan_sections is not None:
            current_sections = notion_data.get('web_scan_sections', {})
            notion_data['web_scan_sections'] = apply_web_scan_sections_update(current_sections, request.web_scan_sections)
        
        # Update pdf_scan_sections
        if request.pdf_scan_sections is not None:
            current_sections = notion_data.get('pdf_scan_sections', {})
            notion_data['pdf_scan_sections'] = apply_pdf_scan_sections_update(current_sections, request.pdf_scan_sections)
        
        # Save to Firestore
        integrations['notion'] = notion_data
        doc_ref.update({'integrations': integrations})
        
        logger.info(f"Updated Notion config for user {user_info['user_id']}")
        
        return NotionConfigResponse(
            success=True,
            message="Notion integration configuration updated successfully",
            config={
                "config": config,
                "web_scan_sections": notion_data.get('web_scan_sections', {}),
                "pdf_scan_sections": notion_data.get('pdf_scan_sections', {})
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring Notion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Notion configuration"
        )


# ============================================================================
# Slack Integration
# ============================================================================

class SlackHealthResponse(BaseModel):
    connected: bool
    channel: Optional[str] = None
    web_scan_enabled: Optional[bool] = None
    pdf_scan_enabled: Optional[bool] = None
    message: Optional[str] = None


class SlackConfigRequest(BaseModel):
    # Config section
    channel: Optional[str] = None
    webhook_url: Optional[str] = None
    web_scan_enabled: Optional[bool] = None
    pdf_scan_enabled: Optional[bool] = None
    
    # Web scan sections
    web_scan_sections: Optional[WebScanSectionsConfig] = None
    
    # PDF scan sections
    pdf_scan_sections: Optional[PdfScanSectionsConfig] = None


class SlackConfigResponse(BaseModel):
    success: bool
    message: str
    config: dict


@router.get("/slack/health", response_model=SlackHealthResponse)
async def slack_health(user_info: dict = Depends(get_current_user)):
    """Check Slack integration connection status"""
    try:
        doc = db.collection('user_integrations').document(user_info['user_id']).get()
        
        if not doc.exists:
            return SlackHealthResponse(
                connected=False,
                message="Slack integration is not connected. Please connect via the web interface."
            )
        
        integrations = doc.to_dict().get('integrations', {})
        slack_data = integrations.get('slack', {})
        config = slack_data.get('config', {})
        
        if not config.get('connected', False):
            return SlackHealthResponse(
                connected=False,
                message="Slack integration is not connected. Please connect via the web interface."
            )
        
        return SlackHealthResponse(
            connected=True,
            channel=config.get('channel'),
            web_scan_enabled=config.get('web_scan_enabled', False),
            pdf_scan_enabled=config.get('pdf_scan_enabled', False)
        )
        
    except Exception as e:
        logger.error(f"Error checking Slack health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check Slack integration status"
        )


@router.put("/slack/config", response_model=SlackConfigResponse)
async def configure_slack(
    request: SlackConfigRequest,
    user_info: dict = Depends(get_current_user)
):
    """Update Slack integration configuration"""
    try:
        doc_ref = db.collection('user_integrations').document(user_info['user_id'])
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slack integration not connected. Please connect via the web interface."
            )
        
        integrations = doc.to_dict().get('integrations', {})
        slack_data = integrations.get('slack', {})
        config = slack_data.get('config', {})
        
        if not config.get('connected', False):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Slack integration not connected. Please connect via the web interface."
            )
        
        # Update config section
        if request.channel is not None:
            config['channel'] = request.channel
        
        if request.webhook_url is not None:
            if not request.webhook_url.startswith('https://hooks.slack.com/'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid Slack webhook URL"
                )
            # Store webhook as secret reference
            config['webhook_secret_id'] = request.webhook_url
        
        if request.web_scan_enabled is not None:
            config['web_scan_enabled'] = request.web_scan_enabled
        
        if request.pdf_scan_enabled is not None:
            config['pdf_scan_enabled'] = request.pdf_scan_enabled
        
        config['last_updated'] = datetime.now(timezone.utc).isoformat()
        slack_data['config'] = config
        
        # Update web_scan_sections
        if request.web_scan_sections is not None:
            current_sections = slack_data.get('web_scan_sections', {})
            slack_data['web_scan_sections'] = apply_web_scan_sections_update(current_sections, request.web_scan_sections)
        
        # Update pdf_scan_sections
        if request.pdf_scan_sections is not None:
            current_sections = slack_data.get('pdf_scan_sections', {})
            slack_data['pdf_scan_sections'] = apply_pdf_scan_sections_update(current_sections, request.pdf_scan_sections)
        
        # Save to Firestore
        integrations['slack'] = slack_data
        doc_ref.update({'integrations': integrations})
        
        logger.info(f"Updated Slack config for user {user_info['user_id']}")
        
        # Return config without webhook URL for security
        response_config = {
            "config": {k: v for k, v in config.items() if k != 'webhook_secret_id'},
            "web_scan_sections": slack_data.get('web_scan_sections', {}),
            "pdf_scan_sections": slack_data.get('pdf_scan_sections', {})
        }
        
        return SlackConfigResponse(
            success=True,
            message="Slack integration configuration updated successfully",
            config=response_config
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error configuring Slack: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Slack configuration"
        )
