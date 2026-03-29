from google.cloud import firestore, secretmanager
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any
from ..shared.utils import (
    update_integration_stats, 
    log_integration_activity, 
    filter_violations_by_severity
)

logger = logging.getLogger(__name__)

async def push_to_notion(db: firestore.Client, secret_client: secretmanager.SecretManagerServiceClient,
                        user_id: str, scan_data: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Push scan results to Notion as database entries or pages"""
    try:
        notion_config = config.get('config', {})
        
        # Check if Notion integration is connected and enabled - both are now in config
        connected = notion_config.get('connected', False)
        web_scan_enabled = notion_config.get('web_scan_enabled', False)
        if not connected or not web_scan_enabled:
            logger.warning(f"Notion integration not connected or not enabled for user {user_id}")
            return False
        database_id = notion_config.get('database')
        access_token = notion_config.get('access_token')
        
        if not database_id or not access_token:
            logger.error(f"Notion configuration incomplete for user {user_id}")
            return False
        
        # Filter violations by severity
        all_violations = scan_data.get('violations', [])
        severity_filter = notion_config.get('severity_filter', ['High', 'Medium', 'Low'])
        filtered_violations = filter_violations_by_severity(all_violations, severity_filter)
        
        headers = {
            'Authorization': f"Bearer {access_token}",
            'Notion-Version': '2022-06-28',
            'Content-Type': 'application/json'
        }
        
        url = scan_data.get('url', 'Unknown URL')
        timestamp = scan_data.get('timestamp', datetime.now(timezone.utc).isoformat())
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            pages_created = 0
            
            if notion_config.get('create_new_page_per_scan', False):
                # Create a new page for this scan
                page_title = f"Accessibility Scan - {url} - {timestamp[:10]}"
                
                # Create rich content
                children = [
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
                                {"type": "text", "text": {"content": f"URL: {url}\n"}},
                                {"type": "text", "text": {"content": f"Scan Date: {timestamp}\n"}},
                                {"type": "text", "text": {"content": f"Total Violations: {len(filtered_violations)}"}}
                            ]
                        }
                    }
                ]
                
                # Add violations by impact
                violations_by_impact = {}
                for violation in filtered_violations:
                    impact = violation.get('impact', 'minor')
                    if impact not in violations_by_impact:
                        violations_by_impact[impact] = []
                    violations_by_impact[impact].append(violation)
                
                for impact in ['critical', 'serious', 'moderate', 'minor']:
                    if impact in violations_by_impact:
                        impact_violations = violations_by_impact[impact]
                        children.append({
                            "object": "block",
                            "type": "heading_2",
                            "heading_2": {
                                "rich_text": [{"type": "text", "text": {"content": f"{impact.title()} Issues ({len(impact_violations)})"}}]
                            }
                        })
                        
                        for violation in impact_violations[:10]:  # Limit to prevent page bloat
                            children.append({
                                "object": "block",
                                "type": "bulleted_list_item",
                                "bulleted_list_item": {
                                    "rich_text": [{"type": "text", "text": {"content": violation.get('help', 'Unknown issue')}}]
                                }
                            })
                
                page_data = {
                    "parent": {"database_id": database_id},
                    "properties": {
                        "Name": {
                            "title": [{"type": "text", "text": {"content": page_title}}]
                        }
                    },
                    "children": children
                }
                
                response = await client.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json=page_data
                )
                
                if response.status_code == 200:
                    pages_created = 1
                    logger.info(f"Created Notion page for {url}")
                else:
                    logger.error(f"Failed to create Notion page: {response.status_code} - {response.text}")
                    return False
            
            else:
                # Add entries to database
                for violation in filtered_violations[:50]:  # Limit to prevent overwhelming database
                    entry_data = {
                        "parent": {"database_id": database_id},
                        "properties": {
                            "Name": {
                                "title": [{"type": "text", "text": {"content": violation.get('help', 'Accessibility Issue')}}]
                            },
                            "URL": {
                                "url": url
                            },
                            "Impact": {
                                "select": {"name": violation.get('impact', 'minor').title()}
                            },
                            "Rule ID": {
                                "rich_text": [{"type": "text", "text": {"content": violation.get('id', 'unknown')}}]
                            },
                            "Date": {
                                "date": {"start": timestamp[:10]}
                            }
                        }
                    }
                    
                    response = await client.post(
                        "https://api.notion.com/v1/pages",
                        headers=headers,
                        json=entry_data
                    )
                    
                    if response.status_code == 200:
                        pages_created += 1
                    else:
                        logger.warning(f"Failed to create Notion entry: {response.status_code}")
            
            # Update statistics
            if pages_created > 0:
                update_integration_stats(db, user_id, 'notion', {
                    'pages_created': firestore.Increment(pages_created),
                    'last_page_created': datetime.now(timezone.utc)
                })
            
            log_integration_activity(db, user_id, 'notion', 'push_scan_results', 'success', {
                'pages_created': pages_created,
                'violations_processed': len(filtered_violations),
                'url': url
            })
            
            return True
        
    except Exception as e:
        logger.error(f"Error pushing to Notion for user {user_id}: {e}")
        log_integration_activity(db, user_id, 'notion', 'push_scan_results', 'error', {
            'error': str(e),
            'url': scan_data.get('url', 'Unknown')
        })
        return False
