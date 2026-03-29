from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
import logging
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import httpx
import os
import re

# Import authentication components
from auth.auth_service import get_current_user

# Import shared components
from integrations.shared.database import (
    db, secret_client, get_user_integrations_doc, 
    get_secret, store_secret, serialize_datetime_objects
)
from integrations.shared.models import NotionConfig, NotionConfigUpdate, OAuthCallback

logger = logging.getLogger(__name__)

# OAuth redirect URI - uses environment variable with DEV default
API_BASE_URL = os.getenv("API_BASE_URL", "")
NOTION_OAUTH_CALLBACK_URI = f"{API_BASE_URL}/integrations/notion/oauth/callback"

notion_router = APIRouter()

@notion_router.put("/integrations/notion/config")
async def update_notion_config(
    config_update: NotionConfigUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update Notion integration configuration"""
    try:
        user_id = current_user['uid']
        
        # Convert Pydantic model to dict, excluding None values
        config_dict = config_update.model_dump(exclude_none=True)
        logger.info(f"Received Notion config update: {config_dict}")
        
        # Get user document from user_integrations collection
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User integrations not found")
        
        data = doc.to_dict()
        
        # Ensure Notion integration exists
        if 'integrations' not in data or 'notion' not in data['integrations']:
            raise HTTPException(status_code=404, detail="Notion not connected")
        
        # Validate page_url and extract page_id if provided
        if 'page_url' in config_dict and config_dict['page_url']:
            page_url = config_dict['page_url']
            
            try:
                # Extract page ID from URL and verify access
                page_id = extract_page_id_from_url(page_url)
                if not await verify_notion_page_access(user_id, page_id):
                    raise HTTPException(status_code=400, detail=f"Page '{page_url}' not found or no access")
                
                # Store both URL and extracted page ID
                config_dict['parent_page_id'] = page_id
            except Exception as e:
                logger.error(f"Error verifying page {page_url}: {e}")
                raise HTTPException(status_code=400, detail=f"Could not verify page '{page_url}'. Please check if it exists and you have access.")
        
        # Update configuration
        if 'page_url' in config_dict:
            data['integrations']['notion']['config']['page_url'] = config_dict['page_url']
        
        if 'parent_page_id' in config_dict:
            data['integrations']['notion']['config']['parent_page_id'] = config_dict['parent_page_id']
        
        # WCAG specific fields go to web_scan_sections
        if 'wcag_severity_filter' in config_dict:
            if 'web_scan_sections' not in data['integrations']['notion']:
                data['integrations']['notion']['web_scan_sections'] = {}
            data['integrations']['notion']['web_scan_sections']['wcag_severity_filter'] = config_dict['wcag_severity_filter']
        
        if 'wcag_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['notion']:
                data['integrations']['notion']['web_scan_sections'] = {}
            data['integrations']['notion']['web_scan_sections']['wcag_grouping_option'] = config_dict['wcag_grouping_option']
        
        if 'wcag_regroup_violations' in config_dict:
            if 'web_scan_sections' not in data['integrations']['notion']:
                data['integrations']['notion']['web_scan_sections'] = {}
            data['integrations']['notion']['web_scan_sections']['wcag_regroup_violations'] = config_dict['wcag_regroup_violations']
        
        # Handle PDF scan configuration
        if 'pdf_grouping_option' in config_dict:
            if 'pdf_scan_sections' not in data['integrations']['notion']:
                data['integrations']['notion']['pdf_scan_sections'] = {}
            data['integrations']['notion']['pdf_scan_sections']['pdf_grouping_option'] = config_dict['pdf_grouping_option']
        
        # Handle web scan sections configuration
        if 'web_scan_sections' in config_dict:
            if 'web_scan_sections' not in data['integrations']['notion']:
                data['integrations']['notion']['web_scan_sections'] = {}
            
            sections = config_dict['web_scan_sections']
            # Pydantic models have attributes, dicts have keys
            
            # Update individual toggle values - check both dict keys and object attributes
            if hasattr(sections, 'wcag_enabled'):
                data['integrations']['notion']['web_scan_sections']['wcag_enabled'] = sections.wcag_enabled
            elif isinstance(sections, dict) and 'wcag_enabled' in sections:
                data['integrations']['notion']['web_scan_sections']['wcag_enabled'] = sections['wcag_enabled']
                
            if hasattr(sections, 'html_enabled'):
                data['integrations']['notion']['web_scan_sections']['html_enabled'] = sections.html_enabled
            elif isinstance(sections, dict) and 'html_enabled' in sections:
                data['integrations']['notion']['web_scan_sections']['html_enabled'] = sections['html_enabled']
                
            if hasattr(sections, 'links_enabled'):
                data['integrations']['notion']['web_scan_sections']['links_enabled'] = sections.links_enabled
            elif isinstance(sections, dict) and 'links_enabled' in sections:
                data['integrations']['notion']['web_scan_sections']['links_enabled'] = sections['links_enabled']
                
            if hasattr(sections, 'axtree_enabled'):
                data['integrations']['notion']['web_scan_sections']['axtree_enabled'] = sections.axtree_enabled
            elif isinstance(sections, dict) and 'axtree_enabled' in sections:
                data['integrations']['notion']['web_scan_sections']['axtree_enabled'] = sections['axtree_enabled']
                
            if hasattr(sections, 'layout_enabled'):
                data['integrations']['notion']['web_scan_sections']['layout_enabled'] = sections.layout_enabled
            elif isinstance(sections, dict) and 'layout_enabled' in sections:
                data['integrations']['notion']['web_scan_sections']['layout_enabled'] = sections['layout_enabled']
        
        # Handle module-specific grouping options
        if 'html_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['notion']:
                data['integrations']['notion']['web_scan_sections'] = {}
            data['integrations']['notion']['web_scan_sections']['html_grouping_option'] = config_dict['html_grouping_option']
        
        if 'links_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['notion']:
                data['integrations']['notion']['web_scan_sections'] = {}
            data['integrations']['notion']['web_scan_sections']['links_grouping_option'] = config_dict['links_grouping_option']
        
        if 'layout_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['notion']:
                data['integrations']['notion']['web_scan_sections'] = {}
            data['integrations']['notion']['web_scan_sections']['layout_grouping_option'] = config_dict['layout_grouping_option']
        
        data['integrations']['notion']['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Update in Firestore
        doc_ref.set(data)
        
        # Serialize the response data to handle datetime objects
        serialized_config = serialize_datetime_objects(data['integrations']['notion'])
        
        return JSONResponse(content={
            "message": "Notion configuration updated successfully",
            "config": serialized_config
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Notion config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Notion configuration")

@notion_router.put("/integrations/notion/status")
async def update_notion_integration_status(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update Notion integration enabled/disabled status"""
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
        if 'notion' not in data['integrations']:
            raise HTTPException(status_code=400, detail="Notion integration not configured")
        
        # Update web_scan_enabled status in config
        is_enabled = request.get('is_enabled', False)
        if 'config' not in data['integrations']['notion']:
            data['integrations']['notion']['config'] = {}
        data['integrations']['notion']['config']['web_scan_enabled'] = is_enabled
        data['integrations']['notion']['config']['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Save to Firestore
        doc_ref.set(data)
        
        return JSONResponse(content={
            "message": f"Notion integration {'enabled' if is_enabled else 'disabled'} successfully",
            "is_enabled": is_enabled
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Notion integration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Notion integration status")

@notion_router.put("/integrations/notion/pdf-status")
async def update_notion_pdf_integration_status(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update Notion PDF scan integration enabled/disabled status"""
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
        if 'notion' not in data['integrations']:
            raise HTTPException(status_code=400, detail="Notion integration not configured")
        
        # Update pdf_scan_enabled status in config
        is_enabled = request.get('is_enabled', False)
        if 'config' not in data['integrations']['notion']:
            data['integrations']['notion']['config'] = {}
        data['integrations']['notion']['config']['pdf_scan_enabled'] = is_enabled
        data['integrations']['notion']['config']['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Save to Firestore
        doc_ref.set(data)
        
        return JSONResponse(content={
            "message": f"Notion PDF integration {'enabled' if is_enabled else 'disabled'} successfully",
            "pdf_scan_enabled": is_enabled
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating Notion PDF integration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update Notion PDF integration status")

@notion_router.post("/integrations/notion/disconnect")
async def disconnect_notion_integration(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Disconnect Notion integration"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        user_id = current_user['uid']
        logger.info(f"Disconnecting Notion for user: {user_id}")
        
        # Get user integrations document
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User integrations not found")
        
        data = doc.to_dict()
        
        # Delete stored OAuth tokens from Secret Manager first
        secret_id = f"notion-access-token-{user_id}"
        try:
            secret_path = f"projects/{db._project}/secrets/{secret_id}"
            if secret_client:
                secret_client.delete_secret(request={"name": secret_path})
                logger.info(f"Deleted Notion access token for user: {user_id}")
        except Exception as e:
            logger.warning(f"Could not delete Notion token for user {user_id}: {e}")
        
        # Completely reset Notion integration to default state
        if 'integrations' not in data:
            data['integrations'] = {}
        
        # Reset to default Notion integration state
        data['integrations']['notion'] = {
            "config": {
                "parent_page_id": None,
                "page_url": None,
                "connected": False,
                "web_scan_enabled": False,
                "pdf_scan_enabled": False,
                "last_updated": datetime.now(timezone.utc).isoformat()
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
        }
        
        # Clear any OAuth states
        if 'oauth_states' in data and 'notion' in data['oauth_states']:
            del data['oauth_states']['notion']
        
        # Update in Firestore using set() instead of update()
        doc_ref.set(data)
        
        logger.info(f"Notion integration fully disconnected for user: {user_id}")
        
        return JSONResponse(content={
            "message": "Notion disconnected successfully"
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting Notion: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Notion")

@notion_router.get("/integrations/notion/oauth/authorize")
async def notion_oauth_authorize(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Start Notion OAuth flow"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Get Notion OAuth credentials from Secret Manager
        client_id = get_secret("notion-oauth-client-id")
        if not client_id:
            raise HTTPException(status_code=500, detail="Notion OAuth not configured")
        
        # Generate a random state for security
        state = secrets.token_urlsafe(32)
        
        # Store state in user's integration document temporarily
        user_id = current_user['uid']
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
        else:
            data = {"integrations": {}}
        
        # Store OAuth state with expiration (10 minutes)
        if 'oauth_states' not in data:
            data['oauth_states'] = {}
        
        data['oauth_states']['notion'] = {
            'state': state,
            'user_id': user_id,  # Store user ID for callback lookup
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        }
        
        doc_ref.set(data, merge=True)
        
        # Build Notion OAuth URL
        redirect_uri = NOTION_OAUTH_CALLBACK_URI
        
        notion_oauth_url = (
            f"https://api.notion.com/v1/oauth/authorize"
            f"?client_id={client_id}"
            f"&response_type=code"
            f"&owner=user"
            f"&state={state}"
            f"&redirect_uri={redirect_uri}"
        )
        
        logger.info(f"Starting Notion OAuth for user {user_id} with state {state}")
        
        return JSONResponse(content={
            "oauth_url": notion_oauth_url,
            "state": state
        })
        
    except Exception as e:
        logger.error(f"Error starting Notion OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")

@notion_router.get("/integrations/notion/oauth/callback")
async def notion_oauth_callback(
    code: str,
    state: str,
    request: Request
):
    """Handle Notion OAuth callback"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        logger.info(f"Notion OAuth callback received with state: {state}")
        
        # Find the user by state in all user_integrations documents
        user_id = None
        user_doc_ref = None
        
        # Query all user integration documents to find the matching state
        users_ref = db.collection('user_integrations')
        docs = users_ref.stream()
        
        for doc in docs:
            data = doc.to_dict()
            oauth_states = data.get('oauth_states', {})
            notion_state = oauth_states.get('notion', {})
            
            if notion_state.get('state') == state:
                # Verify state hasn't expired
                expires_at = datetime.fromisoformat(notion_state.get('expires_at', ''))
                if datetime.now(timezone.utc) > expires_at:
                    raise HTTPException(status_code=400, detail="OAuth state expired")
                
                user_id = notion_state.get('user_id')
                user_doc_ref = doc.reference
                break
        
        if not user_id or not user_doc_ref:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        
        # Get Notion OAuth credentials
        client_id = get_secret("notion-oauth-client-id")
        client_secret = get_secret("notion-oauth-client-secret")
        
        # Strip any whitespace/newlines that might have been stored with the secrets
        if client_id:
            client_id = client_id.strip()
        if client_secret:
            client_secret = client_secret.strip()
        
        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="Notion OAuth credentials not configured")
        
        logger.info(f"Using client_id: {client_id}")
        logger.info(f"Client secret length: {len(client_secret) if client_secret else 0}")
        
        # Exchange code for access token
        redirect_uri = NOTION_OAUTH_CALLBACK_URI
        
        # Encode credentials for Basic auth (Notion uses Basic auth for token exchange)
        import base64
        auth_string = f"{client_id}:{client_secret}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri
        }
        logger.info(f"Token exchange data: {token_data}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                "https://api.notion.com/v1/oauth/token",
                data=token_data,
                headers={
                    "Authorization": f"Basic {auth_b64}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Token exchange failed: {token_response.text}")
                raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                logger.error(f"No access token in response: {token_data}")
                raise HTTPException(status_code=400, detail="No access token received")
        
        # Get user info from Notion
        async with httpx.AsyncClient(timeout=30.0) as client:
            user_response = await client.get(
                "https://api.notion.com/v1/users/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Notion-Version": "2022-06-28"
                }
            )
            
            if user_response.status_code != 200:
                logger.error(f"Notion user info failed: {user_response.text}")
                raise HTTPException(status_code=400, detail="Failed to get user info from Notion")
            
            notion_user = user_response.json()
        
        # Store the access token securely
        secret_id = f"notion-access-token-{user_id}"
        if not store_secret(secret_id, access_token):
            raise HTTPException(status_code=500, detail="Failed to store access token securely")
        
        # Update user's integration status
        user_data = user_doc_ref.get().to_dict()
        
        # Initialize integrations structure if needed
        if 'integrations' not in user_data:
            user_data['integrations'] = {}
        if 'notion' not in user_data['integrations']:
            user_data['integrations']['notion'] = {}
        
        # Update Notion integration
        user_data['integrations']['notion'].update({
            'config': {
                'page_url': None,  # User will set later
                'parent_page_id': None,
                'notion_user': notion_user.get('name', 'Unknown'),
                'notion_user_id': notion_user.get('id'),
                'connected': True,
                'web_scan_enabled': True,
                'pdf_scan_enabled': False,
                'last_updated': datetime.now(timezone.utc).isoformat()
            },
            'web_scan_sections': {
                'wcag_enabled': True,
                'wcag_severity_filter': ['High', 'Medium', 'Low'],
                'wcag_grouping_option': 'per-error-type',
                'wcag_regroup_violations': True,
                'html_enabled': True,
                'links_enabled': True,
                'axtree_enabled': False,
                'layout_enabled': True,
                'html_grouping_option': 'per-error-type',
                'links_grouping_option': 'per-error-type',
                'layout_grouping_option': 'per-error-type'
            },
            'pdf_scan_sections': {
                'pdf_grouping_option': 'per-page'
            },
            'stats': user_data['integrations']['notion'].get('stats', {
                'pages_created': 0,
                'last_page_created': None
            })
        })
        
        # Clean up OAuth state
        if 'oauth_states' in user_data:
            user_data['oauth_states'].pop('notion', None)
        
        # Update in Firestore
        user_doc_ref.set(user_data)
        
        logger.info(f"Notion OAuth completed for user {user_id}, Notion user: {notion_user.get('name', 'Unknown')}")
        
        # Redirect to frontend with success
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/integrations?notion=success&user={notion_user.get('name', 'User')}",
            status_code=302
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Notion OAuth callback: {e}")
        # Redirect to frontend with error
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/integrations?notion=error&message={str(e)[:100]}",
            status_code=302
        )

def extract_page_id_from_url(page_url: str) -> str:
    """Extract page ID from Notion page URL"""
    try:
        # Notion page URLs typically look like:
        # https://www.notion.so/workspace/Page-Title-32_character_page_id
        # or https://notion.so/Page-Title-32_character_page_id
        
        # Extract the last 32 character string (page ID)
        # Remove any query parameters first
        clean_url = page_url.split('?')[0]
        
        # Extract page ID using regex - look for 32 character hex string
        page_id_match = re.search(r'([a-f0-9]{32})', clean_url.replace('-', ''))
        if page_id_match:
            page_id = page_id_match.group(1)
            # Format with dashes: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
            formatted_id = f"{page_id[:8]}-{page_id[8:12]}-{page_id[12:16]}-{page_id[16:20]}-{page_id[20:]}"
            return formatted_id
        
        raise ValueError("Could not extract page ID from URL")
    except Exception as e:
        logger.error(f"Error extracting page ID from URL {page_url}: {e}")
        raise ValueError(f"Invalid Notion page URL: {e}")

async def verify_notion_page_access(user_id: str, page_id: str) -> bool:
    """Verify user has access to the specified Notion page"""
    try:
        # Get user's access token
        secret_id = f"notion-access-token-{user_id}"
        access_token = get_secret(secret_id)
        
        if not access_token:
            return False
        
        # Try to retrieve the page
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"https://api.notion.com/v1/pages/{page_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Notion-Version": "2022-06-28"
                }
            )
            
            return response.status_code == 200
            
    except Exception as e:
        logger.error(f"Error verifying Notion page {page_id}: {e}")
        return False

async def clear_notion_connection(user_id: str):
    """Clear Notion connection when token is invalid"""
    try:
        # Get user document
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            user_data = doc.to_dict()
            if 'integrations' in user_data and 'notion' in user_data['integrations']:
                user_data['integrations']['notion'] = {
                    'connected': False,
                    'config': {},
                    'last_updated': datetime.now(timezone.utc).isoformat()
                }
                doc_ref.set(user_data)
        
        # Delete access token from Secret Manager
        secret_id = f"notion-access-token-{user_id}"
        try:
            parent = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT', '')}"
            secret_path = f"{parent}/secrets/{secret_id}"
            secret_client.delete_secret(request={"name": secret_path})
        except Exception as e:
            logger.warning(f"Could not delete secret {secret_id}: {e}")
            
    except Exception as e:
        logger.error(f"Error clearing Notion connection: {e}")

async def create_notion_pages_for_scan(user_id: str, scan_result: Dict[str, Any]):
    """Create Notion pages from scan results"""
    try:
        # Get user integrations
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            logger.error(f"No user integrations found for {user_id}")
            return False
        
        data = doc.to_dict()
        notion_config = data.get('integrations', {}).get('notion', {})
        config = notion_config.get('config', {})
        
        if not config.get('connected') or not config.get('web_scan_enabled'):
            logger.info(f"Notion integration not enabled for user {user_id}")
            return False
        parent_page_id = config.get('parent_page_id')
        
        if not parent_page_id:
            logger.error(f"No parent page configured for user {user_id}")
            return False
        
        # Get access token
        secret_id = f"notion-access-token-{user_id}"
        access_token = get_secret(secret_id)
        
        if not access_token:
            logger.error(f"No access token found for user {user_id}")
            return False
        
        # Convert scan results to Notion page format using Slack formatting as base
        pages_data = convert_scan_to_notion_pages(scan_result, config, parent_page_id)
        
        created_count = 0
        async with httpx.AsyncClient(timeout=60.0) as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Notion-Version": "2022-06-28",
                "Content-Type": "application/json"
            }
            
            for page_data in pages_data:
                try:
                    page_response = await client.post(
                        "https://api.notion.com/v1/pages",
                        headers=headers,
                        json=page_data
                    )
                    
                    if page_response.status_code == 200:
                        created_count += 1
                        logger.info(f"Created Notion page: {page_data['properties']['title']['title'][0]['text']['content']}")
                    else:
                        logger.error(f"Failed to create Notion page: {page_response.text}")
                        
                except Exception as e:
                    logger.error(f"Error creating page: {e}")
        
        # Update stats
        await update_notion_stats(user_id, created_count)
        
        logger.info(f"Created {created_count} Notion pages for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating Notion pages for user {user_id}: {e}")
        return False

def convert_scan_to_notion_pages(scan_result: Dict[str, Any], config: Dict[str, Any], parent_page_id: str) -> List[Dict[str, Any]]:
    """Convert scan results to Notion page format"""
    pages = []
    violations = scan_result.get('violations', [])
    url = scan_result.get('url', 'Unknown URL')
    timestamp = scan_result.get('timestamp', datetime.now(timezone.utc).isoformat())
    
    # Apply severity filter
    severity_filter = config.get('severity_filter', ['Critical', 'High', 'Medium', 'Low'])
    filtered_violations = [v for v in violations if v.get('impact', '').title() in severity_filter]
    
    grouping_option = config.get('grouping_option', 'per-scan')
    regroup_violations = config.get('regroup_violations', True)
    
    if grouping_option == 'per-scan' or not regroup_violations:
        # Create one page with all violations
        page_data = create_comprehensive_scan_page(
            filtered_violations, url, scan_result.get('id', 'scan'), 
            timestamp, parent_page_id, scan_result.get('accessibility_score')
        )
        pages.append(page_data)
    else:
        # Group by error type and create separate pages
        if regroup_violations:
            # Group by rule ID
            violation_groups = {}
            for violation in filtered_violations:
                rule_id = violation.get('id', 'unknown')
                if rule_id not in violation_groups:
                    violation_groups[rule_id] = []
                violation_groups[rule_id].append(violation)
            
            for rule_id, rule_violations in violation_groups.items():
                page_data = create_error_type_page(
                    rule_violations, url, scan_result.get('id', 'scan'),
                    timestamp, parent_page_id
                )
                pages.append(page_data)
        else:
            # Create individual pages for each violation
            for violation in filtered_violations:
                page_data = create_individual_violation_page(
                    violation, url, scan_result.get('id', 'scan'),
                    timestamp, parent_page_id
                )
                pages.append(page_data)
    
    return pages

def create_comprehensive_scan_page(violations: List[Dict[str, Any]], url: str, 
                                 scan_id: str, scan_timestamp: str, parent_page_id: str, 
                                 accessibility_score: float = None) -> Dict[str, Any]:
    """Create a comprehensive page with all violations from a scan"""
    
    timestamp_str = scan_timestamp[:10] if scan_timestamp else datetime.now().strftime('%Y-%m-%d')
    
    # Page title
    title = f"Accessibility Scan - {url} - {timestamp_str}"
    
    # Build page content blocks
    children = []
    
    # Add accessibility score at the top for comprehensive scan pages
    if accessibility_score is not None:
        children.extend([
            {
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"Accessibility Score: "}},
                        {"type": "text", "text": {"content": f"{accessibility_score:.1f}%"}, "annotations": {"bold": True}}
                    ],
                    "icon": {"emoji": "🎯"},
                    "color": "green" if accessibility_score >= 80 else "yellow" if accessibility_score >= 60 else "red"
                }
            },
            {
                "object": "block",
                "type": "divider",
                "divider": {}
            }
        ])
    
    # Add basic info
    children.extend([
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": "Accessibility Scan Results"}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"URL: "}},
                    {"type": "text", "text": {"content": url}, "annotations": {"bold": True}},
                    {"type": "text", "text": {"content": f"\nScan Date: {timestamp_str}\nTotal Issues: {len(violations)}"}}
                ]
            }
        }
    ])
    
    # Add violations by severity (similar to Slack formatting)
    severity_counts = {}
    for violation in violations:
        impact = violation.get('impact', 'unknown')
        severity_map = {
            'critical': 'Critical',
            'serious': 'High', 
            'moderate': 'Medium',
            'minor': 'Low',
            'unknown': 'Unknown'
        }
        severity = severity_map.get(impact.lower(), impact.title())
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    if severity_counts:
        severity_text = ", ".join([f"{count} {severity}" for severity, count in severity_counts.items()])
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "Severity Breakdown: "}},
                    {"type": "text", "text": {"content": severity_text}, "annotations": {"bold": True}}
                ]
            }
        })
    
    # Add detailed violations
    children.append({
        "object": "block",
        "type": "heading_2",
        "heading_2": {
            "rich_text": [{"type": "text", "text": {"content": "Detailed Issues"}}]
        }
    })
    
    for i, violation in enumerate(violations, 1):
        impact_emoji = get_severity_emoji(violation.get('impact', 'unknown'))
        
        children.extend([
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": f"{impact_emoji} {i}. {violation.get('help', 'Accessibility Issue')}"}}]
                }
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"type": "text", "text": {"content": f"Rule ID: "}},
                        {"type": "text", "text": {"content": violation.get('id', 'unknown')}, "annotations": {"code": True}},
                        {"type": "text", "text": {"content": f" | Impact: "}},
                        {"type": "text", "text": {"content": violation.get('impact', 'unknown').title()}, "annotations": {"bold": True}}
                    ]
                }
            }
        ])
        
        if violation.get('description'):
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": violation['description']}}]
                }
            })
    
    return {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        },
        "children": children
    }

def create_error_type_page(violations: List[Dict[str, Any]], url: str, 
                          scan_id: str, scan_timestamp: str, parent_page_id: str) -> Dict[str, Any]:
    """Create a page for a specific error type"""
    
    rule_id = violations[0].get('id', 'unknown') if violations else 'unknown'
    rule_help = violations[0].get('help', 'Accessibility Issue') if violations else 'Accessibility Issue'
    
    title = f"{rule_help} - {url}"
    
    children = [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": rule_help}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"Rule ID: "}},
                    {"type": "text", "text": {"content": rule_id}, "annotations": {"code": True}},
                    {"type": "text", "text": {"content": f"\nURL: {url}\nOccurrences: {len(violations)}"}}
                ]
            }
        }
    ]
    
    # Add each violation instance
    for i, violation in enumerate(violations, 1):
        children.append({
            "object": "block",
            "type": "heading_3",
            "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": f"Instance {i}"}}]
            }
        })
        
        if violation.get('description'):
            children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": violation['description']}}]
                }
            })
    
    return {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        },
        "children": children
    }

def create_individual_violation_page(violation: Dict[str, Any], url: str, 
                                   scan_id: str, scan_timestamp: str, parent_page_id: str) -> Dict[str, Any]:
    """Create a page for an individual violation"""
    
    title = f"{violation.get('help', 'Accessibility Issue')} - {url}"
    
    children = [
        {
            "object": "block",
            "type": "heading_1",
            "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": violation.get('help', 'Accessibility Issue')}}]
            }
        },
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": f"Rule ID: "}},
                    {"type": "text", "text": {"content": violation.get('id', 'unknown')}, "annotations": {"code": True}},
                    {"type": "text", "text": {"content": f"\nURL: {url}\nImpact: "}},
                    {"type": "text", "text": {"content": violation.get('impact', 'unknown').title()}, "annotations": {"bold": True}}
                ]
            }
        }
    ]
    
    if violation.get('description'):
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": violation['description']}}]
            }
        })
    
    return {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {
                "title": [{"type": "text", "text": {"content": title}}]
            }
        },
        "children": children
    }

def get_severity_emoji(impact: str) -> str:
    """Get emoji for severity level"""
    severity_emojis = {
        'critical': '🔴',
        'serious': '🟡', 
        'moderate': '🟠',
        'minor': '🔵',
        'unknown': '⚪'
    }
    return severity_emojis.get(impact.lower(), '⚪')

async def update_notion_stats(user_id: str, pages_created: int):
    """Update Notion integration statistics"""
    try:
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            if 'integrations' in data and 'notion' in data['integrations']:
                stats = data['integrations']['notion'].get('stats', {})
                stats['pages_created'] = stats.get('pages_created', 0) + pages_created
                stats['last_page_created'] = datetime.now(timezone.utc).isoformat()
                
                data['integrations']['notion']['stats'] = stats
                doc_ref.set(data)
                
    except Exception as e:
        logger.error(f"Error updating Notion stats: {e}")
