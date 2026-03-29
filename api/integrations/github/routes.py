from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import JSONResponse, RedirectResponse
import logging
import secrets
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List
import httpx
import os
import json

# Import authentication components
from auth.auth_service import get_current_user

# Import shared components
from integrations.shared.database import (
    db, secret_client, get_user_integrations_doc, 
    get_secret, store_secret, serialize_datetime_objects
)
from integrations.shared.models import GitHubConfig, GitHubConfigUpdate, OAuthCallback

logger = logging.getLogger(__name__)

# OAuth redirect URI - uses environment variable with DEV default
API_BASE_URL = os.getenv("API_BASE_URL", "")
GITHUB_OAUTH_CALLBACK_URI = f"{API_BASE_URL}/integrations/github/oauth/callback"

github_router = APIRouter()

@github_router.put("/integrations/github/config")
async def update_github_config(
    config_update: GitHubConfigUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update GitHub integration configuration"""
    try:
        user_id = current_user['uid']
        
        # Convert Pydantic model to dict, excluding None values
        config_dict = config_update.model_dump(exclude_none=True)
        logger.info(f"Received GitHub config update: {config_dict}")
        
        # Get user document from user_integrations collection
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User integrations not found")
        
        data = doc.to_dict()
        
        # Ensure GitHub integration exists
        if 'integrations' not in data or 'github' not in data['integrations']:
            raise HTTPException(status_code=404, detail="GitHub not connected")
        
        # Validate repository if provided
        if 'repository' in config_dict and config_dict['repository']:
            repository_name = config_dict['repository']
            
            try:
                # Verify repository exists and user has access
                if not await verify_github_repository(user_id, repository_name):
                    raise HTTPException(status_code=400, detail=f"Repository '{repository_name}' not found or no access")
            except Exception as e:
                logger.error(f"Error verifying repository {repository_name}: {e}")
                raise HTTPException(status_code=400, detail=f"Could not verify repository '{repository_name}'. Please check if it exists and you have access.")
        
        # Update configuration
        if 'repository' in config_dict:
            data['integrations']['github']['config']['repository'] = config_dict['repository']
        
        # WCAG specific fields go to web_scan_sections
        if 'wcag_severity_filter' in config_dict:
            if 'web_scan_sections' not in data['integrations']['github']:
                data['integrations']['github']['web_scan_sections'] = {}
            data['integrations']['github']['web_scan_sections']['wcag_severity_filter'] = config_dict['wcag_severity_filter']
        
        if 'wcag_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['github']:
                data['integrations']['github']['web_scan_sections'] = {}
            data['integrations']['github']['web_scan_sections']['wcag_grouping_option'] = config_dict['wcag_grouping_option']
        
        if 'wcag_regroup_violations' in config_dict:
            if 'web_scan_sections' not in data['integrations']['github']:
                data['integrations']['github']['web_scan_sections'] = {}
            data['integrations']['github']['web_scan_sections']['wcag_regroup_violations'] = config_dict['wcag_regroup_violations']
        
        # Handle PDF scan configuration
        if 'pdf_grouping_option' in config_dict:
            if 'pdf_scan_sections' not in data['integrations']['github']:
                data['integrations']['github']['pdf_scan_sections'] = {}
            data['integrations']['github']['pdf_scan_sections']['pdf_grouping_option'] = config_dict['pdf_grouping_option']
        
        # Handle web scan sections configuration
        if 'web_scan_sections' in config_dict:
            if 'web_scan_sections' not in data['integrations']['github']:
                data['integrations']['github']['web_scan_sections'] = {}
            
            sections = config_dict['web_scan_sections']
            # Pydantic models have attributes, dicts have keys
            
            # Update individual toggle values - check both dict keys and object attributes
            if hasattr(sections, 'wcag_enabled'):
                data['integrations']['github']['web_scan_sections']['wcag_enabled'] = sections.wcag_enabled
            elif isinstance(sections, dict) and 'wcag_enabled' in sections:
                data['integrations']['github']['web_scan_sections']['wcag_enabled'] = sections['wcag_enabled']
                
            if hasattr(sections, 'html_enabled'):
                data['integrations']['github']['web_scan_sections']['html_enabled'] = sections.html_enabled
            elif isinstance(sections, dict) and 'html_enabled' in sections:
                data['integrations']['github']['web_scan_sections']['html_enabled'] = sections['html_enabled']
                
            if hasattr(sections, 'links_enabled'):
                data['integrations']['github']['web_scan_sections']['links_enabled'] = sections.links_enabled
            elif isinstance(sections, dict) and 'links_enabled' in sections:
                data['integrations']['github']['web_scan_sections']['links_enabled'] = sections['links_enabled']
                
            if hasattr(sections, 'axtree_enabled'):
                data['integrations']['github']['web_scan_sections']['axtree_enabled'] = sections.axtree_enabled
            elif isinstance(sections, dict) and 'axtree_enabled' in sections:
                data['integrations']['github']['web_scan_sections']['axtree_enabled'] = sections['axtree_enabled']
                
            if hasattr(sections, 'layout_enabled'):
                data['integrations']['github']['web_scan_sections']['layout_enabled'] = sections.layout_enabled
            elif isinstance(sections, dict) and 'layout_enabled' in sections:
                data['integrations']['github']['web_scan_sections']['layout_enabled'] = sections['layout_enabled']
        
        # Handle module-specific grouping options
        if 'html_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['github']:
                data['integrations']['github']['web_scan_sections'] = {}
            data['integrations']['github']['web_scan_sections']['html_grouping_option'] = config_dict['html_grouping_option']
        
        if 'links_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['github']:
                data['integrations']['github']['web_scan_sections'] = {}
            data['integrations']['github']['web_scan_sections']['links_grouping_option'] = config_dict['links_grouping_option']
        
        if 'layout_grouping_option' in config_dict:
            if 'web_scan_sections' not in data['integrations']['github']:
                data['integrations']['github']['web_scan_sections'] = {}
            data['integrations']['github']['web_scan_sections']['layout_grouping_option'] = config_dict['layout_grouping_option']
        
        data['integrations']['github']['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Update in Firestore
        doc_ref.set(data)
        
        # Serialize the response data to handle datetime objects
        serialized_config = serialize_datetime_objects(data['integrations']['github'])
        
        return JSONResponse(content={
            "message": "GitHub configuration updated successfully",
            "config": serialized_config
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating GitHub config: {e}")
        raise HTTPException(status_code=500, detail="Failed to update GitHub configuration")

@github_router.put("/integrations/github/status")
async def update_github_integration_status(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update GitHub integration enabled/disabled status"""
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
        if 'github' not in data['integrations']:
            raise HTTPException(status_code=400, detail="GitHub integration not configured")
        
        # Update web_scan_enabled status in config
        is_enabled = request.get('is_enabled', False)
        if 'config' not in data['integrations']['github']:
            data['integrations']['github']['config'] = {}
        data['integrations']['github']['config']['web_scan_enabled'] = is_enabled
        data['integrations']['github']['config']['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Save to Firestore
        doc_ref.set(data)
        
        return JSONResponse(content={
            "message": f"GitHub integration {'enabled' if is_enabled else 'disabled'} successfully",
            "is_enabled": is_enabled
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating GitHub integration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update GitHub integration status")

@github_router.put("/integrations/github/pdf-status")
async def update_github_pdf_integration_status(
    request: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update GitHub PDF scan integration enabled/disabled status"""
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
        if 'github' not in data['integrations']:
            raise HTTPException(status_code=400, detail="GitHub integration not configured")
        
        # Update pdf_scan_enabled status in config
        is_enabled = request.get('is_enabled', False)
        if 'config' not in data['integrations']['github']:
            data['integrations']['github']['config'] = {}
        data['integrations']['github']['config']['pdf_scan_enabled'] = is_enabled
        data['integrations']['github']['config']['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Save to Firestore
        doc_ref.set(data)
        
        return JSONResponse(content={
            "message": f"GitHub PDF integration {'enabled' if is_enabled else 'disabled'} successfully",
            "pdf_scan_enabled": is_enabled
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating GitHub PDF integration status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update GitHub PDF integration status")

@github_router.post("/integrations/github/disconnect")
async def disconnect_github_integration(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Disconnect GitHub integration"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        user_id = current_user['uid']
        logger.info(f"Disconnecting GitHub for user: {user_id}")
        
        # Get user integrations document
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if not doc.exists:
            raise HTTPException(status_code=404, detail="User integrations not found")
        
        data = doc.to_dict()
        
        # Get the access token before deleting it, so we can revoke it with GitHub
        secret_id = f"github-access-token-{user_id}"
        access_token = None
        try:
            access_token = get_secret(secret_id)
            if access_token:
                access_token = access_token.strip()
        except Exception as e:
            logger.warning(f"Could not retrieve GitHub token for revocation {user_id}: {e}")
        
        # Revoke the OAuth token with GitHub's API first (to force re-authentication)
        if access_token:
            try:
                client_id = get_secret("github-oauth-client-id")
                client_secret = get_secret("github-oauth-client-secret")
                
                if client_id and client_secret:
                    client_id = client_id.strip()
                    client_secret = client_secret.strip()
                    
                    # GitHub OAuth grant revocation endpoint (revokes the entire app authorization)
                    # This forces the user to re-authorize the app completely
                    revoke_url = f"https://api.github.com/applications/{client_id}/grant"
                    
                    async with httpx.AsyncClient(timeout=10.0) as http_client:
                        response = await http_client.request(
                            method="DELETE",
                            url=revoke_url,
                            headers={
                                "Accept": "application/vnd.github+json",
                                "X-GitHub-Api-Version": "2022-11-28",
                                "Content-Type": "application/json"
                            },
                            json={"access_token": access_token},
                            auth=(client_id, client_secret)
                        )
                        
                        if response.status_code == 204:
                            logger.info(f"Successfully revoked GitHub OAuth token for user: {user_id}")
                        elif response.status_code == 422:
                            logger.warning(f"GitHub token revocation validation failed for user {user_id}: {response.text}")
                        else:
                            logger.warning(f"GitHub token revocation returned status {response.status_code} for user: {user_id} - {response.text}")
                else:
                    logger.warning(f"Missing GitHub OAuth credentials for token revocation")
            except Exception as e:
                logger.warning(f"Failed to revoke GitHub OAuth token for user {user_id}: {e}")
        
        # Delete stored OAuth tokens from Secret Manager
        try:
            if secret_client:
                secret_name = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT', '')}/secrets/{secret_id}"
                secret_client.delete_secret(request={"name": secret_name})
                logger.info(f"Deleted GitHub access token for user: {user_id}")
        except Exception as e:
            logger.warning(f"Could not delete GitHub token for user {user_id}: {e}")
        
        # Completely reset GitHub integration to default state
        if 'integrations' not in data:
            data['integrations'] = {}
        
        # Reset to default GitHub integration state
        data['integrations']['github'] = {
            "config": {
                "repository": None,
                "label": "accessibility",
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
                "issues_created": 0,
                "last_issue_created": None
            }
        }
        
        # Clear any OAuth states
        if 'oauth_states' in data and 'github' in data['oauth_states']:
            del data['oauth_states']['github']
        
        # Update in Firestore using set() instead of update()
        doc_ref.set(data)
        
        logger.info(f"GitHub integration fully disconnected for user: {user_id}")
        
        return JSONResponse(content={
            "message": "GitHub disconnected successfully"
        })
        
    except Exception as e:
        logger.error(f"Error disconnecting GitHub: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect GitHub")

@github_router.get("/integrations/github/oauth/authorize")
async def github_oauth_authorize(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Start GitHub OAuth flow"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        # Get GitHub OAuth credentials from Secret Manager
        client_id = get_secret("github-oauth-client-id")
        if not client_id:
            raise HTTPException(status_code=500, detail="GitHub OAuth not configured")
        
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
        
        data['oauth_states']['github'] = {
            'state': state,
            'user_id': user_id,  # Store user ID for callback lookup
            'created_at': datetime.now(timezone.utc).isoformat(),
            'expires_at': (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat()
        }
        
        doc_ref.set(data, merge=True)
        
        # Build GitHub OAuth URL - use configured redirect URI
        redirect_uri = GITHUB_OAUTH_CALLBACK_URI
        
        # Force fresh authorization by adding timestamp and login prompt
        import time
        timestamp = int(time.time())
        
        github_oauth_url = (
            f"https://github.com/login/oauth/authorize"
            f"?client_id={client_id}"
            f"&scope=repo"
            f"&state={state}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&allow_signup=false"
            f"&t={timestamp}"  # Add timestamp to prevent caching
        )
        
        logger.info(f"Starting GitHub OAuth for user {user_id} with state {state}")
        
        return JSONResponse(content={
            "oauth_url": github_oauth_url,
            "state": state
        })
        
    except Exception as e:
        logger.error(f"Error starting GitHub OAuth: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth flow: {str(e)}")

@github_router.get("/integrations/github/oauth/callback")
async def github_oauth_callback(
    code: str,
    state: str,
    request: Request
):
    """Handle GitHub OAuth callback"""
    try:
        if not db:
            raise HTTPException(status_code=503, detail="Database unavailable")
        
        logger.info(f"GitHub OAuth callback received with state: {state}")
        
        # Find the user by state in all user_integrations documents
        user_id = None
        user_doc_ref = None
        
        # Query all user integration documents to find the matching state
        users_ref = db.collection('user_integrations')
        docs = users_ref.stream()
        
        for doc in docs:
            data = doc.to_dict()
            oauth_states = data.get('oauth_states', {})
            github_state = oauth_states.get('github', {})
            
            if github_state.get('state') == state:
                # Verify state hasn't expired
                expires_at = datetime.fromisoformat(github_state.get('expires_at', ''))
                if datetime.now(timezone.utc) > expires_at:
                    raise HTTPException(status_code=400, detail="OAuth state expired")
                
                user_id = github_state.get('user_id')
                user_doc_ref = doc.reference
                break
        
        if not user_id or not user_doc_ref:
            raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
        
        # Get GitHub OAuth credentials
        client_id = get_secret("github-oauth-client-id")
        client_secret = get_secret("github-oauth-client-secret")
        
        # Strip any whitespace/newlines that might have been stored with the secrets
        if client_id:
            client_id = client_id.strip()
        if client_secret:
            client_secret = client_secret.strip()
        
        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="GitHub OAuth credentials not configured")
        
        logger.info(f"Using client_id: {client_id}")
        logger.info(f"Client secret length: {len(client_secret) if client_secret else 0}")
        
        # Exchange code for access token
        redirect_uri = GITHUB_OAUTH_CALLBACK_URI
        
        token_data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }
        logger.info(f"Token exchange data: {dict(token_data, client_secret='[REDACTED]')}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data=token_data,
                headers={
                    "Accept": "application/json",
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
        
        # Get user info from GitHub
        async with httpx.AsyncClient(timeout=30.0) as client:
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if user_response.status_code != 200:
                logger.error(f"GitHub user info failed: {user_response.text}")
                raise HTTPException(status_code=400, detail="Failed to get user info from GitHub")
            
            github_user = user_response.json()
        
        # Store the access token securely
        secret_id = f"github-access-token-{user_id}"
        if not store_secret(secret_id, access_token):
            raise HTTPException(status_code=500, detail="Failed to store access token securely")
        
        # Update user's integration status
        user_data = user_doc_ref.get().to_dict()
        
        # Initialize integrations structure if needed
        if 'integrations' not in user_data:
            user_data['integrations'] = {}
        if 'github' not in user_data['integrations']:
            user_data['integrations']['github'] = {}
        
        # Update GitHub integration
        user_data['integrations']['github'].update({
            'config': {
                'repository': None,  # User will select later
                'label': 'accessibility',
                'github_user': github_user['login'],
                'github_user_id': github_user['id'],
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
                'layout_enabled': True,
                'html_grouping_option': 'per-error-type',
                'links_grouping_option': 'per-error-type',
                'layout_grouping_option': 'per-error-type'
            },
            'pdf_scan_sections': {
                'pdf_grouping_option': 'per-page'
            },
            'stats': user_data['integrations']['github'].get('stats', {
                'issues_created': 0,
                'last_issue_created': None
            })
        })
        
        # Clean up OAuth state
        if 'oauth_states' in user_data:
            user_data['oauth_states'].pop('github', None)
        
        # Update in Firestore
        user_doc_ref.set(user_data)
        
        logger.info(f"GitHub OAuth completed for user {user_id}, GitHub user: {github_user['login']}")
        
        # Redirect to frontend with success
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/integrations?github=success&user={github_user['login']}",
            status_code=302
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in GitHub OAuth callback: {e}")
        # Redirect to frontend with error
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/integrations?github=error&message={str(e)[:100]}",
            status_code=302
        )

@github_router.get("/integrations/github/repositories")
async def get_github_repositories(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get user's GitHub repositories for selection"""
    try:
        user_id = current_user['uid']
        
        # Get access token from Secret Manager
        secret_id = f"github-access-token-{user_id}"
        access_token = get_secret(secret_id)
        
        if not access_token:
            raise HTTPException(status_code=404, detail="GitHub not connected")
        
        access_token = access_token.strip()
        
        # Fetch repositories from GitHub API
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get user's repositories
            repos_response = await client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                params={
                    "sort": "updated",
                    "direction": "desc",
                    "per_page": 100,
                    "type": "owner"  # Only repos the user owns
                }
            )
            
            if repos_response.status_code == 401:
                # Token is invalid, clear it
                logger.warning(f"Invalid GitHub token for user {user_id}, clearing connection")
                await clear_github_connection(user_id)
                raise HTTPException(status_code=401, detail="GitHub token expired, please reconnect")
            
            if repos_response.status_code != 200:
                logger.error(f"GitHub repos API failed: {repos_response.text}")
                raise HTTPException(status_code=400, detail="Failed to fetch repositories from GitHub")
            
            repositories = repos_response.json()
            
            # Format repositories for frontend
            repo_list = []
            for repo in repositories:
                repo_list.append({
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description", ""),
                    "private": repo["private"],
                    "updated_at": repo["updated_at"],
                    "html_url": repo["html_url"]
                })
            
            return JSONResponse(content={
                "repositories": repo_list,
                "total": len(repo_list)
            })
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching GitHub repositories: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch repositories")

async def clear_github_connection(user_id: str):
    """Clear GitHub connection when token is invalid"""
    try:
        # Get user document
        users_ref = db.collection('users')
        query = users_ref.where('uid', '==', user_id)
        docs = query.stream()
        
        user_doc_ref = None
        for doc in docs:
            user_doc_ref = doc.reference
            break
        
        if user_doc_ref:
            user_data = user_doc_ref.get().to_dict()
            if 'integrations' in user_data and 'github' in user_data['integrations']:
                user_data['integrations']['github'] = {
                    'connected': False,
                    'config': {},
                    'last_updated': datetime.now(timezone.utc).isoformat()
                }
                user_doc_ref.set(user_data)
        
        # Delete access token from Secret Manager
        secret_id = f"github-access-token-{user_id}"
        try:
            parent = f"projects/{os.getenv('GOOGLE_CLOUD_PROJECT', '')}"
            secret_path = f"{parent}/secrets/{secret_id}"
            secret_client.delete_secret(request={"name": secret_path})
        except Exception as e:
            logger.warning(f"Could not delete secret {secret_id}: {e}")
            
    except Exception as e:
        logger.error(f"Error clearing GitHub connection: {e}")

async def verify_github_repository(user_id: str, repository_name: str) -> bool:
    """Verify that a GitHub repository exists and user has access"""
    try:
        # Get access token
        secret_id = f"github-access-token-{user_id}"
        access_token = get_secret(secret_id)
        
        if not access_token:
            return False
        
        access_token = access_token.strip()
        
        # Check repository
        async with httpx.AsyncClient(timeout=30.0) as client:
            repo_response = await client.get(
                f"https://api.github.com/repos/{repository_name}",
                headers={
                    "Authorization": f"token {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            return repo_response.status_code == 200
            
    except Exception as e:
        logger.error(f"Error verifying repository {repository_name}: {e}")
        return False

async def create_github_issues_for_scan(user_id: str, scan_result: Dict[str, Any]):
    """Create GitHub issues from scan results"""
    try:
        # Get user's GitHub integration config
        users_ref = db.collection('users')
        query = users_ref.where('uid', '==', user_id)
        docs = query.stream()
        
        user_data = None
        for doc in docs:
            user_data = doc.to_dict()
            break
        
        if not user_data:
            logger.warning(f"User {user_id} not found for GitHub issue creation")
            return False
        
        github_config = user_data.get('integrations', {}).get('github', {})
        config = github_config.get('config', {})
        
        if not config.get('connected'):
            logger.info(f"GitHub integration not connected for user {user_id}")
            return True  # Not an error, just disabled
        
        repository = config.get('repository')
        if not repository:
            logger.info(f"No repository selected for user {user_id}")
            return True  # Not an error, just not configured
        
        # Verify repository still exists
        if not await verify_github_repository(user_id, repository):
            logger.warning(f"Repository {repository} no longer accessible, clearing config")
            await clear_repository_config(user_id)
            return False
        
        # Get access token
        secret_id = f"github-access-token-{user_id}"
        access_token = get_secret(secret_id)
        
        if not access_token:
            logger.error(f"No access token found for user {user_id}")
            return False
        
        access_token = access_token.strip()
        
        # Convert scan results to issues
        issues = convert_scan_to_github_issues(scan_result, config)
        
        if not issues:
            logger.info(f"No issues to create for scan {scan_result.get('task_id', 'unknown')}")
            return True
        
        # Create issues in GitHub
        created_count = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            for issue in issues:
                try:
                    issue_response = await client.post(
                        f"https://api.github.com/repos/{repository}/issues",
                        headers={
                            "Authorization": f"token {access_token}",
                            "Accept": "application/vnd.github.v3+json",
                            "Content-Type": "application/json"
                        },
                        json=issue
                    )
                    
                    if issue_response.status_code == 201:
                        created_count += 1
                        logger.info(f"Created GitHub issue: {issue['title']}")
                    else:
                        logger.error(f"Failed to create GitHub issue: {issue_response.text}")
                        
                except Exception as e:
                    logger.error(f"Error creating issue '{issue['title']}': {e}")
        
        # Update stats
        await update_github_stats(user_id, created_count)
        
        logger.info(f"Created {created_count} GitHub issues for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating GitHub issues for user {user_id}: {e}")
        return False

def convert_scan_to_github_issues(scan_result: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Convert scan results to GitHub issue format"""
    try:
        issues = []
        scanned_url = scan_result.get('scanned_url', 'Unknown URL')
        timestamp = scan_result.get('timestamp', 'Unknown time')
        
        # Get configuration
        severity_filter = config.get('severity_filter', ['High', 'Medium', 'Low'])
        grouping_option = config.get('grouping_option', 'per-error-type')
        label = config.get('label', 'accessibility')
        
        # Process all scan results (axe, pa11y, lighthouse)
        all_violations = []
        
        # Extract violations from different tools
        for tool_name, tool_results in scan_result.get('results', {}).items():
            if tool_name == 'axe' and 'violations' in tool_results:
                for violation in tool_results['violations']:
                    all_violations.append({
                        'tool': 'Axe-core',
                        'type': 'violation',
                        'id': violation.get('id', ''),
                        'impact': violation.get('impact', 'moderate'),
                        'description': violation.get('description', ''),
                        'help': violation.get('help', ''),
                        'helpUrl': violation.get('helpUrl', ''),
                        'nodes': violation.get('nodes', [])
                    })
            
            elif tool_name == 'pa11y' and 'issues' in tool_results:
                for issue in tool_results['issues']:
                    severity_map = {'error': 'serious', 'warning': 'moderate', 'notice': 'minor'}
                    all_violations.append({
                        'tool': 'Pa11y',
                        'type': 'issue',
                        'id': issue.get('code', ''),
                        'impact': severity_map.get(issue.get('type', 'warning'), 'moderate'),
                        'description': issue.get('message', ''),
                        'help': issue.get('message', ''),
                        'helpUrl': '',
                        'nodes': [{'target': [issue.get('selector', '')], 'html': issue.get('context', '')}]
                    })
            
            elif tool_name == 'lighthouse' and 'accessibility' in tool_results:
                for audit_id, audit in tool_results['accessibility'].get('audits', {}).items():
                    if audit.get('score', 1) < 1:  # Failed audit
                        all_violations.append({
                            'tool': 'Lighthouse',
                            'type': 'audit',
                            'id': audit_id,
                            'impact': 'moderate',  # Lighthouse doesn't provide impact levels
                            'description': audit.get('description', ''),
                            'help': audit.get('title', ''),
                            'helpUrl': audit.get('guidance', {}).get('related-techniques', [''])[0] if audit.get('guidance') else '',
                            'nodes': []
                        })
        
        # Filter by severity
        impact_priority = {'critical': 4, 'serious': 3, 'moderate': 2, 'minor': 1}
        severity_map = {'High': ['critical', 'serious'], 'Medium': ['moderate'], 'Low': ['minor']}
        
        allowed_impacts = []
        for severity in severity_filter:
            allowed_impacts.extend(severity_map.get(severity, []))
        
        filtered_violations = [v for v in all_violations if v['impact'] in allowed_impacts]
        
        if grouping_option == 'per-error-type':
            # Group by violation type
            violation_groups = {}
            for violation in filtered_violations:
                key = f"{violation['tool']}:{violation['id']}"
                if key not in violation_groups:
                    violation_groups[key] = {
                        'violation': violation,
                        'nodes': [],
                        'count': 0
                    }
                violation_groups[key]['nodes'].extend(violation['nodes'])
                violation_groups[key]['count'] += len(violation['nodes'])
            
            # Create one issue per violation type
            for group_key, group_data in violation_groups.items():
                violation = group_data['violation']
                node_count = group_data['count']
                
                # Create issue title
                title = f"🔍 {violation['tool']}: {violation['help'] or violation['description']}"
                if len(title) > 80:
                    title = title[:77] + "..."
                
                # Create issue body
                body_parts = [
                    f"**Accessibility Issue Detected**",
                    f"",
                    f"📊 **Scan Details:**",
                    f"- **URL Scanned:** {scanned_url}",
                    f"- **Detection Tool:** {violation['tool']}",
                    f"- **Scan Date:** {timestamp}",
                    f"- **Issue ID:** `{violation['id']}`",
                    f"- **Severity:** {violation['impact'].title()}",
                    f"- **Affected Elements:** {node_count}",
                    f"",
                    f"📋 **Description:**",
                    f"{violation['description'] or violation['help']}",
                    f""
                ]
                
                if violation['helpUrl']:
                    body_parts.extend([
                        f"🔗 **Reference:**",
                        f"{violation['helpUrl']}",
                        f""
                    ])
                
                if group_data['nodes']:
                    body_parts.extend([
                        f"🎯 **Affected Elements:**",
                        f""
                    ])
                    
                    for i, node in enumerate(group_data['nodes'][:10]):  # Limit to first 10
                        if node.get('target'):
                            selector = ', '.join(node['target']) if isinstance(node['target'], list) else str(node['target'])
                            body_parts.append(f"**Element {i+1}:** `{selector}`")
                            
                            if node.get('html'):
                                html_snippet = node['html'][:200] + "..." if len(node['html']) > 200 else node['html']
                                body_parts.append(f"```html\n{html_snippet}\n```")
                            body_parts.append("")
                    
                    if len(group_data['nodes']) > 10:
                        body_parts.append(f"*... and {len(group_data['nodes']) - 10} more elements*")
                        body_parts.append("")
                
                body_parts.extend([
                    f"---",
                    f"*This issue was automatically created by LumTrails accessibility scanner.*"
                ])
                
                issues.append({
                    "title": title,
                    "body": "\n".join(body_parts),
                    "labels": [label, f"severity:{violation['impact']}", f"tool:{violation['tool'].lower()}"]
                })
        
        else:  # per-element
            # Create one issue per element
            for violation in filtered_violations:
                for i, node in enumerate(violation['nodes']):
                    if i >= 20:  # Limit total issues
                        break
                    
                    selector = ', '.join(node['target']) if isinstance(node['target'], list) else str(node['target'])
                    title = f"🔍 {violation['help'] or violation['description']} - {selector}"
                    if len(title) > 80:
                        title = title[:77] + "..."
                    
                    body_parts = [
                        f"**Accessibility Issue Detected**",
                        f"",
                        f"📊 **Scan Details:**",
                        f"- **URL Scanned:** {scanned_url}",
                        f"- **Detection Tool:** {violation['tool']}",
                        f"- **Scan Date:** {timestamp}",
                        f"- **Issue ID:** `{violation['id']}`",
                        f"- **Severity:** {violation['impact'].title()}",
                        f"",
                        f"📋 **Description:**",
                        f"{violation['description'] or violation['help']}",
                        f"",
                        f"🎯 **Affected Element:**",
                        f"`{selector}`"
                    ]
                    
                    if node.get('html'):
                        html_snippet = node['html'][:300] + "..." if len(node['html']) > 300 else node['html']
                        body_parts.extend([
                            f"",
                            f"```html",
                            html_snippet,
                            f"```"
                        ])
                    
                    if violation['helpUrl']:
                        body_parts.extend([
                            f"",
                            f"🔗 **Reference:**",
                            f"{violation['helpUrl']}"
                        ])
                    
                    body_parts.extend([
                        f"",
                        f"---",
                        f"*This issue was automatically created by LumTrails accessibility scanner.*"
                    ])
                    
                    issues.append({
                        "title": title,
                        "body": "\n".join(body_parts),
                        "labels": [label, f"severity:{violation['impact']}", f"tool:{violation['tool'].lower()}"]
                    })
        
        return issues
        
    except Exception as e:
        logger.error(f"Error converting scan to GitHub issues: {e}")
        return []

async def clear_repository_config(user_id: str):
    """Clear repository configuration when repo is no longer accessible"""
    try:
        users_ref = db.collection('users')
        query = users_ref.where('uid', '==', user_id)
        docs = query.stream()
        
        for doc in docs:
            user_data = doc.to_dict()
            if 'integrations' in user_data and 'github' in user_data['integrations']:
                user_data['integrations']['github']['config']['repository'] = None
                user_data['integrations']['github']['last_updated'] = datetime.now(timezone.utc).isoformat()
                doc.reference.set(user_data)
            break
    except Exception as e:
        logger.error(f"Error clearing repository config for user {user_id}: {e}")

async def update_github_stats(user_id: str, issues_created: int):
    """Update GitHub integration statistics"""
    try:
        doc_ref = get_user_integrations_doc(user_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            if 'integrations' in data and 'github' in data['integrations']:
                stats = data['integrations']['github'].get('stats', {})
                stats['issues_created'] = stats.get('issues_created', 0) + issues_created
                stats['last_issue_created'] = datetime.now(timezone.utc).isoformat()
                data['integrations']['github']['stats'] = stats
                doc_ref.set(data)
    except Exception as e:
        logger.error(f"Error updating GitHub stats for user {user_id}: {e}")
