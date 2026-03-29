from google.cloud import firestore, secretmanager
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any
from ..shared.utils import (
    get_secret, 
    update_integration_stats, 
    log_integration_activity,
    filter_violations_by_severity
)

logger = logging.getLogger(__name__)

async def push_to_slack(db: firestore.Client, secret_client: secretmanager.SecretManagerServiceClient,
                       user_id: str, scan_data: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Push scan results to Slack via webhook"""
    try:
        slack_config = config.get('config', {})
        
        # Check if Slack integration is connected and enabled - both are now in config
        connected = slack_config.get('connected', False)
        web_scan_enabled = slack_config.get('web_scan_enabled', False)
        if not connected or not web_scan_enabled:
            logger.warning(f"Slack integration not enabled for user {user_id} (connected: {connected}, web_scan_enabled: {web_scan_enabled})")
            if not web_scan_enabled:
                log_integration_activity(db, user_id, 'slack', 'push_scan_results', 'skipped', {
                    'reason': 'integration_disabled',
                    'url': scan_data.get('url', 'Unknown')
                })
                return True  # Return True since this is intentional
            return False
        
        webhook_secret_id = slack_config.get('webhook_secret_id')
        
        if not webhook_secret_id:
            logger.error(f"Slack webhook not configured for user {user_id}")
            return False
        
        webhook_url = get_secret(secret_client, webhook_secret_id)
        if not webhook_url:
            logger.error(f"Failed to retrieve Slack webhook for user {user_id}")
            return False
        
        # Extract violations from scan results - prioritize unified_results format
        all_violations = []
        
        # First, try unified_results format (this is the new consolidated multi-tool format)
        unified_results = scan_data.get('unified_results', {})
        if unified_results and unified_results.get('violations'):
            logger.info("Using unified_results format for Slack")
            violations_in_unified = unified_results.get('violations', [])
            logger.info(f"Found {len(violations_in_unified)} violations in unified format")
            for violation in violations_in_unified:
                all_violations.append({
                    'tool': violation.get('tool', 'Unknown'),
                    'id': violation.get('id', ''),
                    'impact': violation.get('impact', 'moderate'),
                    'description': violation.get('description', ''),
                    'help': violation.get('help', ''),
                    'helpUrl': violation.get('helpUrl', ''),
                    'nodes': violation.get('nodes', []),
                    'unique_id': violation.get('unique_id', f"unified-{violation.get('id', 'unknown')}")
                })
        
        # Fallback to legacy format if unified_results not available
        elif scan_data.get('violations', []):
            logger.info("Using legacy violations format")
            violations_in_root = scan_data.get('violations', [])
            logger.info(f"Found {len(violations_in_root)} violations in legacy format")
            for i, violation in enumerate(violations_in_root):
                all_violations.append({
                    'tool': violation.get('tool', 'Unknown'),
                    'id': violation.get('id', ''),
                    'impact': violation.get('impact', 'moderate'),
                    'description': violation.get('description', ''),
                    'help': violation.get('help', ''),
                    'helpUrl': violation.get('helpUrl', ''),
                    'nodes': violation.get('nodes', []),
                    'unique_id': f"legacy-{violation.get('id', 'unknown')}-{i}"
                })
        
        # Final fallback: Extract from different tools in the scan results (old structure)
        else:
            logger.info("Falling back to results structure")
            results = scan_data.get('results', {})
            if results:
                # Process Axe violations
                if 'axe' in results and 'violations' in results['axe']:
                    for violation in results['axe']['violations']:
                        all_violations.append({
                            'tool': 'Axe-core',
                            'id': violation.get('id', ''),
                            'impact': violation.get('impact', 'moderate'),
                            'description': violation.get('description', ''),
                            'help': violation.get('help', ''),
                            'helpUrl': violation.get('helpUrl', ''),
                            'nodes': violation.get('nodes', [])
                        })
                
                # Process Pa11y violations  
                if 'pa11y' in results and 'violations' in results['pa11y']:
                    for violation in results['pa11y']['violations']:
                        all_violations.append({
                            'tool': 'Pa11y',
                            'id': violation.get('code', ''),
                            'impact': 'moderate',  # Pa11y doesn't provide impact levels
                            'description': violation.get('message', ''),
                            'help': violation.get('message', ''),
                            'helpUrl': '',
                            'nodes': []
                        })
        
        if not all_violations:
            logger.info(f"No violations found for Slack notification for user {user_id}")
            # Send success message for clean scans if trigger allows
            notification_trigger = slack_config.get('notification_trigger', 'all-scans')
            if notification_trigger == 'all-scans':
                url = scan_data.get('url', 'Unknown URL')
                timestamp = scan_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                success_payload = {
                    "text": f"✅ *Accessibility Scan Passed*",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": f"✅ *Accessibility Scan Passed*\n*URL:* {url}\n*Time:* {timestamp}\n*Result:* No accessibility issues found!"
                            }
                        }
                    ],
                    "username": "LumTrails"
                }
                
                # Add channel if specified
                if slack_config.get('channel'):
                    success_payload['channel'] = slack_config['channel']
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(webhook_url, json=success_payload)
                    
                    if response.status_code == 200:
                        # Update statistics
                        update_integration_stats(db, user_id, 'slack', {
                            'messages_posted': firestore.Increment(1),
                            'last_message_posted': datetime.now(timezone.utc)
                        })
                        
                        log_integration_activity(db, user_id, 'slack', 'push_scan_results', 'success', {
                            'violations_count': 0,
                            'url': url,
                            'message_type': 'success'
                        })
                        
                        logger.info(f"Sent Slack success notification for {url}")
                        return True
                    else:
                        logger.error(f"Failed to send Slack success message: {response.status_code} - {response.text}")
                        return False
            return True
        
        # Apply severity filter
        severity_filter = slack_config.get('severity_filter', ['High', 'Medium', 'Low'])
        filtered_violations = []
        for violation in all_violations:
            violation_severity = violation.get('impact', 'moderate').title()
            if violation_severity in severity_filter:
                filtered_violations.append(violation)
        
        if not filtered_violations:
            logger.info(f"No violations meet severity filter {severity_filter}")
            return True
        
        # Check notification trigger
        notification_trigger = slack_config.get('notification_trigger', 'all-scans')
        if notification_trigger == 'failed-only' and len(filtered_violations) == 0:
            logger.info(f"No violations found, skipping Slack notification for user {user_id}")
            return True
        
        # TODO: Implement weekly digest logic if needed
        if notification_trigger == 'weekly-digest':
            logger.info(f"Weekly digest not implemented yet for user {user_id}")
            return True
        
        url = scan_data.get('url', 'Unknown URL')
        timestamp = scan_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        violations_count = len(filtered_violations)
        
        # Create Slack messages based on configuration
        message_grouping = slack_config.get('message_grouping', 'per-error-type')
        regroup_violations = slack_config.get('regroup_violations', False)
        
        messages = create_slack_messages(
            filtered_violations, url, scan_data.get('scan_id', 'unknown'), 
            timestamp, message_grouping, regroup_violations
        )
        
        # Send messages to Slack
        sent_count = 0
        async with httpx.AsyncClient(timeout=30.0) as client:
            for message in messages:
                # Add channel if specified
                if slack_config.get('channel'):
                    message['channel'] = slack_config['channel']
                
                # Add LumTrails branding
                message['username'] = 'LumTrails'
                message['icon_emoji'] = ':mag:'
                
                response = await client.post(webhook_url, json=message)
                
                if response.status_code == 200:
                    sent_count += 1
                else:
                    logger.error(f"Failed to send Slack message: {response.status_code} - {response.text}")
                    return False
        
        # Update statistics
        update_integration_stats(db, user_id, 'slack', {
            'messages_posted': firestore.Increment(sent_count),
            'last_message_posted': datetime.now(timezone.utc)
        })
        
        log_integration_activity(db, user_id, 'slack', 'push_scan_results', 'success', {
            'violations_count': violations_count,
            'messages_sent': sent_count,
            'url': url
        })
        
        logger.info(f"Sent {sent_count} Slack messages for {url}")
        return True
    
    except Exception as e:
        logger.error(f"Error pushing to Slack for user {user_id}: {e}")
        log_integration_activity(db, user_id, 'slack', 'push_scan_results', 'error', {
            'error': str(e),
            'url': scan_data.get('url', 'Unknown')
        })
        return False

def create_slack_messages(violations, url, scan_id, scan_timestamp, message_grouping, regroup_violations):
    """Create Slack message payloads based on configuration"""
    
    if message_grouping == 'single-issue':
        # Single comprehensive message
        return [create_comprehensive_message(violations, url, scan_id, scan_timestamp)]
    else:
        # Per error type (default)
        if regroup_violations:
            return create_grouped_messages(violations, url, scan_id, scan_timestamp)
        else:
            return create_individual_messages(violations, url, scan_id, scan_timestamp)

def create_comprehensive_message(violations, url, scan_id, scan_timestamp):
    """Create a single comprehensive Slack message"""
    # Count violations by severity
    severity_counts = {}
    for violation in violations:
        severity = violation.get('impact', 'unknown').title()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    # Create severity summary
    severity_text = ", ".join([f"{count} {severity}" for severity, count in severity_counts.items()])
    
    # Emoji mapping for severity
    severity_emoji = {
        'critical': '🚨',
        'serious': '⚠️',
        'moderate': '⚡',
        'minor': '💡',
        'unknown': '❓'
    }
    
    # Main message text
    main_text = f"🔍 *Accessibility Scan Results*\n"
    main_text += f"*URL:* {url}\n"
    main_text += f"*Found:* {len(violations)} accessibility issues ({severity_text})"
    
    # Create blocks for rich formatting
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": main_text
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Add top violations (limit to first 5 to avoid message size limits)
    top_violations = violations[:5]
    for violation in top_violations:
        impact = violation.get('impact', 'unknown')
        emoji = severity_emoji.get(impact.lower(), '❓')
        
        violation_text = f"{emoji} *{violation.get('description', 'Unknown issue')}*\n"
        violation_text += f"Rule: `{violation.get('id', 'unknown')}`\n"
        violation_text += f"Impact: {impact.title()}"
        
        if violation.get('helpUrl'):
            violation_text += f"\n<{violation['helpUrl']}|Learn more>"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": violation_text
            }
        })
    
    if len(violations) > 5:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"_...and {len(violations) - 5} more issues_"
            }
        })
    
    # Add metadata
    metadata_text = f"*Scan ID:* {scan_id}"
    if scan_timestamp:
        metadata_text += f"\n*Scan Time:* {scan_timestamp}"
    
    blocks.extend([
        {
            "type": "divider"
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": metadata_text
                }
            ]
        }
    ])
    
    return {
        "text": f"Accessibility scan found {len(violations)} issues on {url}",
        "blocks": blocks
    }

def create_grouped_messages(violations, url, scan_id, scan_timestamp):
    """Create grouped messages by violation type"""
    # Group violations by rule ID
    violation_groups = {}
    for violation in violations:
        rule_id = violation.get('id', 'unknown')
        if rule_id not in violation_groups:
            violation_groups[rule_id] = []
        violation_groups[rule_id].append(violation)
    
    messages = []
    for rule_id, rule_violations in violation_groups.items():
        # Take the first violation as representative
        representative = rule_violations[0]
        
        main_text = f"🔍 *Accessibility Issue Found*\n"
        main_text += f"*URL:* {url}\n"
        main_text += f"*Rule:* {rule_id}\n"
        main_text += f"*Impact:* {representative.get('impact', 'unknown').title()}\n"
        main_text += f"*Instances:* {len(rule_violations)}"
        
        if representative.get('helpUrl'):
            main_text += f"\n*Reference:* <{representative['helpUrl']}|Learn more>"
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": main_text
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:* {representative.get('description', 'No description available')}"
                }
            }
        ]
        
        # Add metadata for each message
        metadata_text = f"*Scan ID:* {scan_id}"
        if scan_timestamp:
            metadata_text += f" • *Time:* {scan_timestamp}"
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": metadata_text
                }
            ]
        })
        
        messages.append({
            "text": f"Accessibility issue: {rule_id} found on {url}",
            "blocks": blocks
        })
    
    return messages

def create_individual_messages(violations, url, scan_id, scan_timestamp):
    """Create individual messages for each violation"""
    messages = []
    
    for violation in violations[:10]:  # Limit to 10 messages to avoid spam
        main_text = f"🔍 *Accessibility Issue Found*\n"
        main_text += f"*URL:* {url}\n"
        main_text += f"*Rule:* {violation.get('id', 'unknown')}\n"
        main_text += f"*Impact:* {violation.get('impact', 'unknown').title()}\n"
        main_text += f"*Description:* {violation.get('description', 'No description available')}"
        
        if violation.get('helpUrl'):
            main_text += f"\n*Reference:* <{violation['helpUrl']}|Learn more>"
        
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": main_text
                }
            }
        ]
        
        # Add metadata
        metadata_text = f"*Scan ID:* {scan_id}"
        if scan_timestamp:
            metadata_text += f" • *Time:* {scan_timestamp}"
        
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": metadata_text
                }
            ]
        })
        
        messages.append({
            "text": f"Accessibility issue: {violation.get('id', 'unknown')} found on {url}",
            "blocks": blocks
        })
    
    if len(violations) > 10:
        # Add summary message for remaining violations
        summary_text = f"📊 *Additional Issues Summary*\n"
        summary_text += f"*URL:* {url}\n"
        summary_text += f"*Additional Issues:* {len(violations) - 10} more accessibility issues were found but not shown individually to avoid message spam."
        
        messages.append({
            "text": f"{len(violations) - 10} additional accessibility issues found",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": summary_text
                    }
                }
            ]
        })
    
    return messages
