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

async def push_to_github(db: firestore.Client, secret_client: secretmanager.SecretManagerServiceClient, 
                        user_id: str, scan_data: Dict[str, Any], config: Dict[str, Any]) -> bool:
    """Push scan results to GitHub as issues"""
    try:
        github_config = config.get('config', {})
        
        # Check if GitHub integration is connected and enabled - both are now in config
        connected = github_config.get('connected', False)
        web_scan_enabled = github_config.get('web_scan_enabled', False)
        if not connected or not web_scan_enabled:
            logger.warning(f"GitHub integration not enabled for user {user_id} (connected: {connected}, web_scan_enabled: {web_scan_enabled})")
            if not web_scan_enabled:
                log_integration_activity(db, user_id, 'github', 'push_scan_results', 'skipped', {
                    'reason': 'integration_disabled',
                    'url': scan_data.get('url', 'Unknown')
                })
                return True  # Return True since this is intentional
            return False
        
        repository = github_config.get('repository')
        
        if not repository:
            logger.error(f"GitHub repository not configured for user {user_id}")
            return False
        
        # Get access token from Secret Manager
        secret_id = f"github-access-token-{user_id}"
        access_token = get_secret(secret_client, secret_id)
        
        if not access_token:
            logger.error(f"GitHub access token not found for user {user_id}")
            return False
        
        access_token = access_token.strip()
        
        # Extract violations from scan results - prioritize unified_results format
        all_violations = []
        
        # First, try unified_results format (this is the new consolidated multi-tool format)
        unified_results = scan_data.get('unified_results', {})
        if unified_results and unified_results.get('violations'):
            logger.info(f"Found {len(unified_results['violations'])} violations in unified format")
            for violation in unified_results['violations']:
                # Create individual violations for each target element when possible
                target_elements = violation.get('target_elements', [])
                html_context = violation.get('html_context', '')
                
                if target_elements:
                    # Create one violation entry per target element for granular issue creation
                    for target in target_elements:
                        all_violations.append({
                            'tool': ', '.join(violation.get('tools_detected', ['Unified'])),
                            'id': violation.get('rule_id', violation.get('id', '')),
                            'impact': violation.get('impact', 'moderate'),
                            'description': violation.get('description', ''),
                            'help': violation.get('title', violation.get('help', '')),
                            'helpUrl': violation.get('help_url', violation.get('helpUrl', '')),
                            'nodes': [{'target': [target], 'html': html_context}],
                            'unique_id': f"{violation.get('id', 'unknown')}-{target}-{hash(html_context[:50])}"  # Unique identifier
                        })
                elif html_context:
                    # Has context but no specific targets
                    all_violations.append({
                        'tool': ', '.join(violation.get('tools_detected', ['Unified'])),
                        'id': violation.get('rule_id', violation.get('id', '')),
                        'impact': violation.get('impact', 'moderate'),
                        'description': violation.get('description', ''),
                        'help': violation.get('title', violation.get('help', '')),
                        'helpUrl': violation.get('help_url', violation.get('helpUrl', '')),
                        'nodes': [{'target': [], 'html': html_context}],
                        'unique_id': f"{violation.get('id', 'unknown')}-context-{hash(html_context[:50])}"
                    })
                else:
                    # General violation without specific targets
                    all_violations.append({
                        'tool': ', '.join(violation.get('tools_detected', ['Unified'])),
                        'id': violation.get('rule_id', violation.get('id', '')),
                        'impact': violation.get('impact', 'moderate'),
                        'description': violation.get('description', ''),
                        'help': violation.get('title', violation.get('help', '')),
                        'helpUrl': violation.get('help_url', violation.get('helpUrl', '')),
                        'nodes': [],
                        'unique_id': f"{violation.get('id', 'unknown')}-general-{len(all_violations)}"
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
                            'nodes': violation.get('nodes', []),
                            'unique_id': f"axe-{violation.get('id', 'unknown')}-{len(all_violations)}"
                        })
                
                # Process Pa11y violations
                if 'pa11y' in results and 'issues' in results['pa11y']:
                    severity_map = {'error': 'serious', 'warning': 'moderate', 'notice': 'minor'}
                    for issue in results['pa11y']['issues']:
                        all_violations.append({
                            'tool': 'Pa11y',
                            'id': issue.get('code', ''),
                            'impact': severity_map.get(issue.get('type', 'warning'), 'moderate'),
                            'description': issue.get('message', ''),
                            'help': issue.get('message', ''),
                            'helpUrl': '',
                            'nodes': [{'target': [issue.get('selector', '')], 'html': issue.get('context', '')}],
                            'unique_id': f"pa11y-{issue.get('code', 'unknown')}-{len(all_violations)}"
                        })
                
                # Process Lighthouse violations
                if 'lighthouse' in results and 'accessibility' in results['lighthouse']:
                    for audit_id, audit in results['lighthouse']['accessibility'].get('audits', {}).items():
                        if audit.get('score', 1) < 1:  # Failed audit
                            all_violations.append({
                                'tool': 'Lighthouse',
                                'id': audit_id,
                                'impact': 'moderate',
                                'description': audit.get('description', ''),
                                'help': audit.get('title', ''),
                                'helpUrl': audit.get('guidance', {}).get('related-techniques', [''])[0] if audit.get('guidance') else '',
                                'nodes': [],
                                'unique_id': f"lighthouse-{audit_id}-{len(all_violations)}"
                            })
        
        logger.info(f"Total violations found: {len(all_violations)}")
        
        severity_filter = github_config.get('severity_filter', ['High', 'Medium', 'Low'])
        filtered_violations = filter_violations_by_severity(all_violations, severity_filter)
        
        if not filtered_violations:
            logger.info(f"No violations matching severity filter for user {user_id}")
            log_integration_activity(db, user_id, 'github', 'push_scan_results', 'success', {
                'issues_created': 0,
                'violations_processed': len(all_violations),
                'violations_filtered_out': len(all_violations),
                'url': scan_data.get('url', 'Unknown')
            })
            return True
        
        headers = {
            'Authorization': f"token {access_token}",
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        }
        
        grouping_option = github_config.get('grouping_option', 'per-error-type')
        regroup_violations = github_config.get('regroup_violations', True)
        label = github_config.get('label', 'accessibility')
        url = scan_data.get('url', 'Unknown URL')
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            issues_created = 0
            
            # If regroup_violations is False, create one issue per violation
            if not regroup_violations:
                logger.info(f"Creating individual issues for {len(filtered_violations)} violations (regrouping disabled)")
                
                for i, violation in enumerate(filtered_violations):
                    if issues_created >= 100:  # Limit to prevent spam
                        logger.warning(f"Reached issue creation limit for user {user_id}")
                        break
                    
                    rule_id = violation.get('id', 'unknown')
                    unique_id = violation.get('unique_id', f"{rule_id}-{i}")
                    
                    # Create a specific title for this individual violation
                    violation_help = violation.get('help', rule_id)
                    title = f"Accessibility: {violation_help} - {url}"
                    
                    body = f"# {violation_help}\n\n"
                    body += f"**URL:** {url}\n"
                    body += f"**Rule ID:** `{rule_id}`\n"
                    body += f"**Impact:** {violation.get('impact', 'unknown').title()}\n"
                    body += f"**Tool(s):** {violation.get('tool', 'Unknown')}\n"
                    body += f"**Unique ID:** `{unique_id}`\n\n"
                    body += f"**Description:**\n{violation.get('description', 'No description available')}\n\n"
                    
                    if violation.get('helpUrl'):
                        body += f"**Help:** {violation['helpUrl']}\n\n"
                    
                    # Show specific element information with full details
                    nodes = violation.get('nodes', [])
                    if nodes:
                        body += f"**Affected Element(s):**\n"
                        for idx, node in enumerate(nodes, 1):
                            if node.get('target') and node['target']:
                                body += f"{idx}. **Element Selector:** `{node['target'][0]}`\n"
                            if node.get('html'):
                                # Show full HTML context for individual issues
                                body += f"   **HTML Context:**\n   ```html\n   {node['html']}\n   ```\n\n"
                    
                    body += f"\n---\n*Generated by LumTrails Accessibility Scanner*"
                    
                    issue_data = {
                        'title': title,
                        'body': body,
                        'labels': [label, f"impact-{violation.get('impact', 'unknown')}"]
                    }
                    
                    response = await client.post(
                        f"https://api.github.com/repos/{repository}/issues",
                        headers=headers,
                        json=issue_data
                    )
                    
                    if response.status_code == 201:
                        issues_created += 1
                        logger.info(f"Created individual GitHub issue {issues_created}/{len(filtered_violations)} for violation {unique_id}")
                    else:
                        logger.error(f"Failed to create GitHub issue for violation {unique_id}: {response.status_code} - {response.text}")
            
            elif grouping_option == 'single-issue':
                # Create one issue with all violations
                title = f"Accessibility Issues Found - {url}"
                body = f"# Accessibility Scan Results\n\n"
                body += f"**URL:** {url}\n"
                body += f"**Scan Date:** {scan_data.get('timestamp', 'Unknown')}\n"
                body += f"**Total Violations:** {len(filtered_violations)}\n\n"
                
                # Group violations by impact
                violations_by_impact = {}
                for violation in filtered_violations:
                    impact = violation.get('impact', 'minor')
                    if impact not in violations_by_impact:
                        violations_by_impact[impact] = []
                    violations_by_impact[impact].append(violation)
                
                for impact in ['critical', 'serious', 'moderate', 'minor']:
                    if impact in violations_by_impact:
                        impact_violations = violations_by_impact[impact]
                        body += f"## {impact.title()} Issues ({len(impact_violations)})\n\n"
                        
                        # Show ALL violations, not just first 10
                        for i, violation in enumerate(impact_violations, 1):
                            body += f"### {i}. {violation.get('help', 'Unknown issue')}\n"
                            body += f"**Description:** {violation.get('description', 'No description')}\n"
                            body += f"**Rule ID:** `{violation.get('id', 'unknown')}`\n"
                            
                            if violation.get('helpUrl'):
                                body += f"**Reference:** {violation['helpUrl']}\n"
                            
                            nodes = violation.get('nodes', [])
                            if nodes:
                                body += f"**Elements affected:** {len(nodes)}\n"
                                
                                # Show detailed information for each affected element
                                for j, node in enumerate(nodes, 1):
                                    if node.get('target') and node['target']:
                                        selector = node['target'][0] if isinstance(node['target'], list) else str(node['target'])
                                        body += f"  **Element {j}:** `{selector}`\n"
                                        
                                        # Add HTML context for better understanding
                                        if node.get('html'):
                                            html_preview = node['html'][:200] + '...' if len(node['html']) > 200 else node['html']
                                            body += f"  ```html\n  {html_preview}\n  ```\n"
                            
                            body += "\n"
                
                body += f"\n---\n*Generated by LumTrails Accessibility Scanner*"
                
                issue_data = {
                    'title': title,
                    'body': body,
                    'labels': [label]
                }
                
                response = await client.post(
                    f"https://api.github.com/repos/{repository}/issues",
                    headers=headers,
                    json=issue_data
                )
                
                if response.status_code == 201:
                    issues_created = 1
                    logger.info(f"Created consolidated GitHub issue for {url}")
                else:
                    logger.error(f"Failed to create GitHub issue: {response.status_code} - {response.text}")
                    return False
            
            else:  # per-error-type (default when regrouping is enabled)
                # Group violations by rule ID
                violations_by_rule = {}
                for violation in filtered_violations:
                    rule_id = violation.get('id', 'unknown')
                    if rule_id not in violations_by_rule:
                        violations_by_rule[rule_id] = []
                    violations_by_rule[rule_id].append(violation)
                
                # Create one issue per rule type with ALL instances shown
                for rule_id, rule_violations in violations_by_rule.items():
                    if issues_created >= 20:  # Limit to prevent spam
                        logger.warning(f"Reached issue creation limit for user {user_id}")
                        break
                    
                    violation = rule_violations[0]  # Use first violation as template
                    title = f"Accessibility: {violation.get('help', rule_id)} - {url}"
                    
                    body = f"# {violation.get('help', 'Accessibility Issue')}\n\n"
                    body += f"**URL:** {url}\n"
                    body += f"**Rule ID:** `{rule_id}`\n"
                    body += f"**Impact:** {violation.get('impact', 'unknown').title()}\n"
                    body += f"**Instances:** {len(rule_violations)}\n\n"
                    body += f"**Description:**\n{violation.get('description', 'No description available')}\n\n"
                    
                    if violation.get('helpUrl'):
                        body += f"**Help:** {violation['helpUrl']}\n\n"
                    
                    # Show ALL affected elements, not just the first few
                    body += f"**Affected Elements:**\n\n"
                    for i, rule_violation in enumerate(rule_violations, 1):
                        nodes = rule_violation.get('nodes', [])
                        if nodes and nodes[0].get('target'):
                            body += f"{i}. `{nodes[0]['target'][0]}`\n"
                            # Add HTML context for better understanding
                            if nodes[0].get('html'):
                                # Truncate HTML context to keep issue readable but informative
                                html_preview = nodes[0]['html'][:150] + '...' if len(nodes[0]['html']) > 150 else nodes[0]['html']
                                body += f"   ```html\n   {html_preview}\n   ```\n"
                        else:
                            body += f"{i}. *(No specific selector available)*\n"
                        
                        body += "\n"  # Add spacing between instances
                    
                    body += f"\n---\n*Generated by LumTrails Accessibility Scanner*"
                    
                    issue_data = {
                        'title': title,
                        'body': body,
                        'labels': [label, f"impact-{violation.get('impact', 'unknown')}"]
                    }
                    
                    response = await client.post(
                        f"https://api.github.com/repos/{repository}/issues",
                        headers=headers,
                        json=issue_data
                    )
                    
                    if response.status_code == 201:
                        issues_created += 1
                        logger.info(f"Created GitHub issue for rule {rule_id} with {len(rule_violations)} instances")
                    else:
                        logger.error(f"Failed to create GitHub issue for {rule_id}: {response.status_code} - {response.text}")
            
            # Update statistics
            if issues_created > 0:
                update_integration_stats(db, user_id, 'github', {
                    'issues_created': firestore.Increment(issues_created),
                    'last_issue_created': datetime.now(timezone.utc)
                })
            
            log_integration_activity(db, user_id, 'github', 'push_scan_results', 'success', {
                'issues_created': issues_created,
                'violations_processed': len(all_violations),
                'violations_after_filtering': len(filtered_violations),
                'grouping_option': grouping_option,
                'url': url
            })
            
            return True
        
    except Exception as e:
        logger.error(f"Error pushing to GitHub for user {user_id}: {e}")
        log_integration_activity(db, user_id, 'github', 'push_scan_results', 'error', {
            'error': str(e),
            'url': scan_data.get('url', 'Unknown')
        })
        return False
