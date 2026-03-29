"""
GitHub Integration Service - Refactored for Web Scan v3.0.0
Supports modular web scan sections (WCAG, HTML, Links, AxTree, Layout)
Preserves PDF scan functionality unchanged

Character limits:
- GitHub issue body: 65,536 characters max
"""
import httpx
import logging
from typing import Dict, Any, List
from integrations.shared_utils import get_secret, filter_violations_by_severity
from integrations.scan_results_adapter import WebScanResultsAdapter
import re

logger = logging.getLogger(__name__)

# GitHub API Limits
GITHUB_ISSUE_BODY_LIMIT = 65000  # Leave some buffer from the 65,536 limit
GITHUB_TRUNCATION_THRESHOLD = 60000  # Start truncating when approaching the limit


class GitHubIntegration:
    """GitHub integration for pushing scan results as issues"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def push_violations(self, user_id: str, scan_data: Dict[str, Any], github_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Push scan results to GitHub repository
        
        Args:
            user_id: The user ID
            scan_data: The scan data to push
            github_config: Optional config override, defaults to self.config
        """
        # Use provided config or fall back to instance config
        if github_config is None:
            github_config = self.config
        
        try:
            # Get repository from config.repository or top-level repository
            repository = github_config.get('config', {}).get('repository') or github_config.get('repository')
            if not repository:
                logger.error(f"GitHub repository not configured for user {user_id}")
                return {"success": False}
            
            # Get access token from Secret Manager
            secret_id = f"github-access-token-{user_id}"
            access_token = get_secret(secret_id)
            
            if not access_token:
                logger.error(f"GitHub access token not found for user {user_id}")
                return {"success": False}
            
            access_token = access_token.strip()
            
            # Detect scan type
            is_pdf_scan = scan_data.get('scan_type') == 'ai_vision'
            
            # Get config object for enabled flags
            config_obj = github_config.get('config', {})
            
            # Handle PDF scans separately
            if is_pdf_scan:
                pdf_scan_enabled = config_obj.get('pdf_scan_enabled', False)
                if not pdf_scan_enabled:
                    logger.info(f"PDF scan integration disabled for user {user_id}")
                    return {"success": True, "message": "PDF scan integration disabled"}
                
                return await self._push_pdf_scan_results(user_id, scan_data, github_config)
            
            # Web scan processing
            web_scan_enabled = config_obj.get('web_scan_enabled', False)
            if not web_scan_enabled:
                logger.info(f"GitHub integration disabled for user {user_id}")
                return {"success": True, "message": "Integration disabled"}
            
            # Process modular web scan format
            logger.info("Processing modular web scan format")
            return await self._push_modular_web_scan(user_id, scan_data, github_config)
        
        except Exception as e:
            logger.error(f"Error pushing to GitHub for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _push_modular_web_scan(self, user_id: str, scan_data: Dict[str, Any], github_config: Dict[str, Any]) -> Dict[str, Any]:
        """Push new modular web scan format to GitHub"""
        try:
            # Get repository from config.repository or top-level repository
            repository = github_config.get('config', {}).get('repository') or github_config.get('repository')
            access_token = get_secret(f"github-access-token-{user_id}").strip()
            
            headers = {
                'Authorization': f"token {access_token}",
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }
            
            # Get web scan sections configuration
            web_scan_sections = github_config.get('web_scan_sections', {})
            wcag_enabled = web_scan_sections.get('wcag_enabled', True)
            html_enabled = web_scan_sections.get('html_enabled', True)
            links_enabled = web_scan_sections.get('links_enabled', True)
            axtree_enabled = web_scan_sections.get('axtree_enabled', False)
            layout_enabled = web_scan_sections.get('layout_enabled', True)
            
            # Get grouping options - consistent naming: per-error-type or single-issue
            wcag_grouping = web_scan_sections.get('wcag_grouping_option', 'per-error-type')
            wcag_regroup = web_scan_sections.get('wcag_regroup_violations', False)
            html_grouping = web_scan_sections.get('html_grouping_option', 'per-error-type')
            links_grouping = web_scan_sections.get('links_grouping_option', 'per-error-type')
            layout_grouping = web_scan_sections.get('layout_grouping_option', 'per-error-type')
            
            # Get severity filter and label
            config_section = github_config.get('config', {})
            severity_filter = web_scan_sections.get('wcag_severity_filter', ['High', 'Medium', 'Low'])
            label = config_section.get('label', github_config.get('label', 'accessibility'))
            url = scan_data.get('url', 'Unknown URL')
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                issues_created = 0
                
                # Process WCAG Compliance (Axe-core)
                if wcag_enabled:
                    wcag_violations = WebScanResultsAdapter.extract_wcag_violations(scan_data, severity_filter)
                    if wcag_violations:
                        created = await self._create_wcag_issues(
                            client, headers, repository, wcag_violations, 
                            wcag_grouping, wcag_regroup, label, url, scan_data
                        )
                        issues_created += created
                
                # Process HTML Validation
                if html_enabled:
                    html_errors = WebScanResultsAdapter.extract_html_errors(scan_data)
                    if html_errors:
                        created = await self._create_html_issues(
                            client, headers, repository, html_errors,
                            html_grouping, label, url, scan_data
                        )
                        issues_created += created
                
                # Process Link Health
                if links_enabled:
                    link_issues = WebScanResultsAdapter.extract_link_issues(scan_data)
                    if link_issues:
                        created = await self._create_link_issues(
                            client, headers, repository, link_issues,
                            links_grouping, label, url, scan_data
                        )
                        issues_created += created
                
                # Process Accessibility Tree
                if axtree_enabled:
                    axtree_data = WebScanResultsAdapter.extract_axtree_data(scan_data)
                    if axtree_data.get('has_data'):
                        created = await self._create_axtree_issue(
                            client, headers, repository, axtree_data,
                            label, url, scan_data
                        )
                        issues_created += created
                
                # Process Layout Testing
                if layout_enabled:
                    layout_issues = WebScanResultsAdapter.extract_layout_issues(scan_data)
                    if layout_issues:
                        created = await self._create_layout_issues(
                            client, headers, repository, layout_issues,
                            layout_grouping, label, url, scan_data
                        )
                        issues_created += created
                
                logger.info(f"Created {issues_created} GitHub issues for user {user_id}")
                return {"success": True, "issues_created": issues_created}
        
        except Exception as e:
            logger.error(f"Error in modular web scan processing: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_wcag_issues(self, client, headers, repository, violations, grouping_option, regroup_violations, label, url, scan_data) -> int:
        """Create GitHub issues for WCAG violations with detailed element information
        
        Grouping options:
        - 'single-issue': All violations in one issue (may be truncated at 65k chars)
        - 'per-error-type': One issue per violation or per rule type (depending on regroup_violations)
        
        regroup_violations:
        - True: Group violations by rule type (one issue per rule)
        - False: One issue per individual violation
        """
        issues_created = 0
        
        # Severity-based emojis
        SEVERITY_EMOJI = {
            'critical': '🚨',  # Red alarm for critical
            'serious': '⚠️',   # Warning for serious
            'moderate': '📋',  # Clipboard for moderate
            'minor': '💡'      # Light bulb for minor
        }
        
        if grouping_option == 'single-issue':
            # Create one consolidated issue
            title = f"🔍 WCAG Compliance Issues - {url}"
            body = f"# WCAG Accessibility Compliance Report\n\n"
            body += f"**URL:** {url}\n"
            body += f"**Scan Date:** {scan_data.get('timestamp', 'Unknown')}\n"
            body += f"**Total Violations:** {len(violations)}\n\n"
            
            # Group by impact
            violations_by_impact = {}
            for violation in violations:
                impact = violation.get('impact', 'minor')
                if impact not in violations_by_impact:
                    violations_by_impact[impact] = []
                violations_by_impact[impact].append(violation)
            
            for impact in ['critical', 'serious', 'moderate', 'minor']:
                if impact in violations_by_impact:
                    impact_violations = violations_by_impact[impact]
                    emoji = SEVERITY_EMOJI.get(impact, '📋')
                    body += f"## {emoji} {impact.title()} Issues ({len(impact_violations)})\n\n"
                    
                    for i, violation in enumerate(impact_violations, 1):
                        body += f"### {i}. {violation.get('help', 'Unknown issue')}\n\n"
                        body += f"**Rule ID:** `{violation.get('id', 'unknown')}`\n"
                        body += f"**Impact:** {impact.title()}\n"
                        body += f"**Description:** {violation.get('description', 'No description')}\n\n"
                        
                        # Affected elements with full details
                        nodes = violation.get('nodes', [])
                        if nodes:
                            body += f"**Affected Elements ({len(nodes)}):**\n\n"
                            for j, node in enumerate(nodes, 1):  # ALL elements - no limit
                                target = node.get('target', [])
                                selector = target[0] if isinstance(target, list) and target else str(target)
                                html = node.get('html', '')
                                
                                body += f"{j}. `{selector[:150]}`\n"
                                if html:
                                    html_preview = html[:300] + '...' if len(html) > 300 else html
                                    body += f"```html\n{html_preview}\n```\n"
                                
                                # Check if approaching limit
                                if len(body) > GITHUB_TRUNCATION_THRESHOLD:
                                    body += f"\n⚠️ _Message truncated: {len(nodes) - j} more element(s) not shown due to GitHub's issue body limit (~65,000 characters)._\n"
                                    break
                        
                        if violation.get('helpUrl'):
                            body += f"\n📚 **Learn more:** [{violation.get('id', 'Rule details')}]({violation['helpUrl']})\n"
                        
                        body += "\n---\n\n"
                        
                        # Check if approaching limit
                        if len(body) > GITHUB_TRUNCATION_THRESHOLD:
                            body += f"\n⚠️ _Message truncated due to GitHub's issue body limit (~65,000 characters)._\n"
                            break
                    
                    if len(body) > GITHUB_TRUNCATION_THRESHOLD:
                        break
            
            body += f"\n*Generated by LumTrails Web Scanner - WCAG Module*"
            
            issue_data = {
                'title': title,
                'body': body[:GITHUB_ISSUE_BODY_LIMIT],  # GitHub body limit
                'labels': [label, 'wcag', 'web-scan']
            }
            
            response = await client.post(
                f"https://api.github.com/repos/{repository}/issues",
                headers=headers,
                json=issue_data
            )
            
            if response.status_code == 201:
                issues_created = 1
                logger.info(f"Created consolidated WCAG issue")
        
        elif not regroup_violations:
            # per-error-type with regroup_violations=False: One issue per individual violation
            violation_count = 0
            for violation in violations:
                nodes = violation.get('nodes', [])
                if not nodes:
                    continue
                
                rule_id = violation.get('id', 'unknown')
                impact = violation.get('impact', 'moderate')
                emoji = SEVERITY_EMOJI.get(impact, '📋')
                
                for node in nodes:
                    if violation_count >= 50:  # Limit to 50 issues to avoid spam
                        logger.info(f"Reached per-violation issue limit (50)")
                        break
                    violation_count += 1
                    
                    target = node.get('target', [])
                    selector = target[0] if isinstance(target, list) and target else str(target)
                    html = node.get('html', '')
                    
                    title = f"{emoji} WCAG: {violation.get('help', rule_id)[:60]} - Element #{violation_count}"
                    
                    body = f"# {emoji} WCAG Violation\n\n"
                    body += f"## Rule Information\n\n"
                    body += f"**Rule:** {violation.get('help', 'Unknown rule')}\n"
                    body += f"**Rule ID:** `{rule_id}`\n"
                    body += f"**Impact:** {impact.title()}\n"
                    body += f"**URL:** {url}\n\n"
                    
                    body += f"## Description\n\n{violation.get('description', 'No description')}\n\n"
                    
                    body += f"## Affected Element\n\n"
                    body += f"**Selector:** `{selector}`\n\n"
                    
                    if html:
                        body += f"**HTML:**\n```html\n{html}\n```\n\n"
                    
                    if violation.get('helpUrl'):
                        body += f"## 📚 Learn More\n\n"
                        body += f"[{rule_id} - Axe Documentation]({violation['helpUrl']})\n\n"
                    
                    body += f"---\n*Generated by LumTrails Web Scanner - WCAG Module*"
                    
                    issue_data = {
                        'title': title,
                        'body': body[:GITHUB_ISSUE_BODY_LIMIT],
                        'labels': [label, 'wcag', 'web-scan', f"impact-{impact}"]
                    }
                    
                    response = await client.post(
                        f"https://api.github.com/repos/{repository}/issues",
                        headers=headers,
                        json=issue_data
                    )
                    
                    if response.status_code == 201:
                        issues_created += 1
                
                if violation_count >= 50:
                    break
        
        else:  # per-error-type with regroup_violations=True - one issue per rule type
            # Group by rule ID
            violations_by_rule = {}
            for violation in violations:
                rule_id = violation.get('id', 'unknown')
                if rule_id not in violations_by_rule:
                    violations_by_rule[rule_id] = []
                violations_by_rule[rule_id].append(violation)
            
            # Create one issue per rule type - no arbitrary limit
            for rule_id, rule_violations in violations_by_rule.items():
                violation = rule_violations[0]
                impact = violation.get('impact', 'moderate')
                emoji = SEVERITY_EMOJI.get(impact, '📋')
                
                title = f"{emoji} WCAG: {violation.get('help', rule_id)[:80]} - {url[:50]}"
                
                body = f"# {emoji} {violation.get('help', 'WCAG Violation')}\n\n"
                body += f"**URL:** {url}\n"
                body += f"**Rule ID:** `{rule_id}`\n"
                body += f"**Impact:** {impact.title()}\n"
                body += f"**Instances Found:** {len(rule_violations)}\n\n"
                body += f"## Description\n\n{violation.get('description', 'No description')}\n\n"
                
                # Count total affected elements
                total_nodes = sum(len(v.get('nodes', [])) for v in rule_violations)
                body += f"## Affected Elements ({total_nodes})\n\n"
                
                element_count = 0
                truncated = False
                for rule_violation in rule_violations:
                    nodes = rule_violation.get('nodes', [])
                    for node in nodes:
                        element_count += 1
                        
                        target = node.get('target', [])
                        selector = target[0] if isinstance(target, list) and target else str(target)
                        html = node.get('html', '')
                        
                        body += f"### Element {element_count}\n\n"
                        body += f"**Selector:** `{selector[:200]}`\n\n"
                        if html:
                            html_preview = html[:400] + '...' if len(html) > 400 else html
                            body += f"**HTML:**\n```html\n{html_preview}\n```\n\n"
                        
                        # Check if approaching GitHub limit
                        if len(body) > GITHUB_TRUNCATION_THRESHOLD:
                            body += f"\n⚠️ _Message truncated: {total_nodes - element_count} more element(s) not shown due to GitHub's issue body limit (~65,000 characters)._\n\n"
                            truncated = True
                            break
                    
                    if truncated:
                        break
                
                if violation.get('helpUrl'):
                    body += f"## 📚 Learn More\n\n"
                    body += f"Read more about this accessibility rule: [{violation.get('id', 'Rule details')}]({violation['helpUrl']})\n\n"
                
                body += f"---\n*Generated by LumTrails Web Scanner - WCAG Module*"
                
                issue_data = {
                    'title': title,
                    'body': body[:GITHUB_ISSUE_BODY_LIMIT],
                    'labels': [label, 'wcag', 'web-scan', f"impact-{impact}"]
                }
                
                response = await client.post(
                    f"https://api.github.com/repos/{repository}/issues",
                    headers=headers,
                    json=issue_data
                )
                
                if response.status_code == 201:
                    issues_created += 1
        
        return issues_created
    
    async def _create_html_issues(self, client, headers, repository, html_errors, grouping_option, label, url, scan_data) -> int:
        """Create GitHub issues for HTML validation errors"""
        issues_created = 0
        
        if grouping_option == 'single-issue':
            # Create one consolidated issue
            errors = [e for e in html_errors if e.get('type') == 'error']
            warnings = [e for e in html_errors if e.get('type') == 'warning']
            
            title = f"HTML Validation Issues - {url}"
            body = f"# HTML Validation Report\n\n"
            body += f"**URL:** {url}\n"
            body += f"**Scan Date:** {scan_data.get('timestamp', 'Unknown')}\n"
            body += f"**Errors:** {len(errors)}\n"
            body += f"**Warnings:** {len(warnings)}\n\n"
            
            if errors:
                body += f"## Errors ({len(errors)})\n\n"
                for i, error in enumerate(errors, 1):
                    body += f"### {i}. {error.get('message', 'Unknown error')}\n"
                    body += f"**Location:** Line {error.get('line', '?')}, Column {error.get('column', '?')}\n"
                    if error.get('extract'):
                        body += f"**Code Extract:**\n```html\n{error['extract']}\n```\n\n"
            
            if warnings:
                body += f"## Warnings ({len(warnings)})\n\n"
                for i, warning in enumerate(warnings, 1):
                    body += f"### {i}. {warning.get('message', 'Unknown warning')}\n"
                    body += f"**Location:** Line {warning.get('line', '?')}, Column {warning.get('column', '?')}\n"
                    if warning.get('extract'):
                        body += f"**Code Extract:**\n```html\n{warning['extract']}\n```\n\n"
            
            body += f"\n---\n*Generated by LumTrails Web Scanner - HTML Validation Module*"
            
            issue_data = {
                'title': title,
                'body': body,
                'labels': [label, 'html-validation', 'web-scan']
            }
            
            response = await client.post(
                f"https://api.github.com/repos/{repository}/issues",
                headers=headers,
                json=issue_data
            )
            
            if response.status_code == 201:
                issues_created = 1
        
        else:  # per-error-type
            # Create separate issues for errors and warnings
            errors = [e for e in html_errors if e.get('type') == 'error']
            warnings = [e for e in html_errors if e.get('type') == 'warning']
            
            if errors:
                for i, error in enumerate(errors[:10], 1):  # Limit to 10
                    title = f"HTML Error: {error.get('message', 'Unknown')[:80]} - {url}"
                    
                    body = f"# HTML Validation Error\n\n"
                    body += f"**URL:** {url}\n"
                    body += f"**Message:** {error.get('message', 'Unknown error')}\n"
                    body += f"**Location:** Line {error.get('line', '?')}, Column {error.get('column', '?')}\n\n"
                    
                    if error.get('extract'):
                        body += f"**Code Extract:**\n```html\n{error['extract']}\n```\n\n"
                    
                    body += f"---\n*Generated by LumTrails Web Scanner - HTML Validation Module*"
                    
                    issue_data = {
                        'title': title,
                        'body': body,
                        'labels': [label, 'html-validation', 'html-error', 'web-scan']
                    }
                    
                    response = await client.post(
                        f"https://api.github.com/repos/{repository}/issues",
                        headers=headers,
                        json=issue_data
                    )
                    
                    if response.status_code == 201:
                        issues_created += 1
            
            if warnings and issues_created < 20:
                # Create one consolidated warning issue
                title = f"HTML Validation Warnings - {url}"
                body = f"# HTML Validation Warnings\n\n"
                body += f"**URL:** {url}\n"
                body += f"**Total Warnings:** {len(warnings)}\n\n"
                
                for i, warning in enumerate(warnings, 1):
                    body += f"### {i}. {warning.get('message', 'Unknown')}\n"
                    body += f"**Location:** Line {warning.get('line', '?')}, Column {warning.get('column', '?')}\n\n"
                
                body += f"---\n*Generated by LumTrails Web Scanner - HTML Validation Module*"
                
                issue_data = {
                    'title': title,
                    'body': body,
                    'labels': [label, 'html-validation', 'html-warning', 'web-scan']
                }
                
                response = await client.post(
                    f"https://api.github.com/repos/{repository}/issues",
                    headers=headers,
                    json=issue_data
                )
                
                if response.status_code == 201:
                    issues_created += 1
        
        return issues_created
    
    async def _create_link_issues(self, client, headers, repository, link_issues, grouping_option, label, url, scan_data) -> int:
        """Create GitHub issues for link problems"""
        issues_created = 0
        
        if grouping_option == 'single-issue':
            # Create one consolidated issue
            title = f"Link Issues Report - {url}"
            body = f"# Link Health Check Report\n\n"
            body += f"**URL:** {url}\n"
            body += f"**Scan Date:** {scan_data.get('timestamp', 'Unknown')}\n"
            body += f"**Total Issues:** {len(link_issues)}\n\n"
            
            for i, link in enumerate(link_issues, 1):
                state = link.get('state', 'invalid')
                state_emoji = "🔴" if state == 'invalid' else "🟠" if state == 'timeout' else "🟡"
                state_label = "Broken" if state == 'invalid' else "Timeout" if state == 'timeout' else "Unreachable"
                error_reason = link.get('error_reason', '')
                
                body += f"### {i}. {state_emoji} {link.get('url', 'Unknown URL')}\n"
                body += f"**Status:** {state_label}\n"
                if error_reason:
                    body += f"**Reason:** {error_reason}\n"
                body += "\n"
            
            body += f"---\n*Generated by LumTrails Web Scanner - Link Health Module*"
            
            issue_data = {
                'title': title,
                'body': body,
                'labels': [label, 'link-issues', 'web-scan']
            }
            
            response = await client.post(
                f"https://api.github.com/repos/{repository}/issues",
                headers=headers,
                json=issue_data
            )
            
            if response.status_code == 201:
                issues_created = 1
        
        else:  # per-error-type
            # Create one issue per link issue (limited to 15)
            for link in link_issues[:15]:
                state = link.get('state', 'invalid')
                state_emoji = "🔴" if state == 'invalid' else "🟠" if state == 'timeout' else "🟡"
                state_label = "Broken" if state == 'invalid' else "Timeout" if state == 'timeout' else "Unreachable"
                error_reason = link.get('error_reason', '')
                
                title = f"{state_emoji} Link {state_label}: {link.get('url', 'Unknown')[:60]} - {url}"
                
                body = f"# Link Issue Detected\n\n"
                body += f"**Link URL:** {link.get('url', 'Unknown')}\n"
                body += f"**Status:** {state_label}\n"
                if error_reason:
                    body += f"**Reason:** {error_reason}\n"
                body += f"**Source URL:** {url}\n\n"
                body += f"---\n*Generated by LumTrails Web Scanner - Link Health Module*"
                
                issue_data = {
                    'title': title,
                    'body': body,
                    'labels': [label, 'link-issues', 'web-scan']
                }
                
                response = await client.post(
                    f"https://api.github.com/repos/{repository}/issues",
                    headers=headers,
                    json=issue_data
                )
                
                if response.status_code == 201:
                    issues_created += 1
        
        return issues_created
    
    async def _create_axtree_issue(self, client, headers, repository, axtree_data, label, url, scan_data) -> int:
        """Create GitHub issue for accessibility tree data with full tree content"""
        import json
        
        issues_created = 0
        
        title = f"🌳 Accessibility Tree Analysis - {url}"
        body = f"# Accessibility Tree Report\n\n"
        body += f"**URL:** {url}\n"
        body += f"**Scan Date:** {scan_data.get('timestamp', 'Unknown')}\n"
        body += f"**Total Nodes:** {axtree_data.get('node_count', 0)}\n\n"
        
        body += f"## About Accessibility Trees\n\n"
        body += f"The accessibility tree represents how assistive technologies (like screen readers) interpret the page structure. "
        body += f"It's derived from the DOM but filtered to show only semantically meaningful elements.\n\n"
        
        # Get the full tree content
        tree_content = axtree_data.get('tree', axtree_data.get('content', None))
        
        if tree_content:
            body += f"## Full Accessibility Tree Structure\n\n"
            
            # Convert to string if it's a dict/list
            if isinstance(tree_content, (dict, list)):
                tree_str = json.dumps(tree_content, indent=2)
            else:
                tree_str = str(tree_content)
            
            # GitHub has a body limit of ~65000 chars, reserve some for other content
            MAX_TREE_LENGTH = 55000
            
            if len(tree_str) > MAX_TREE_LENGTH:
                body += f"```json\n{tree_str[:MAX_TREE_LENGTH]}\n```\n\n"
                body += f"⚠️ _Tree content truncated due to GitHub's issue body limit (~65,000 characters). Full tree has {len(tree_str)} characters._\n\n"
            else:
                body += f"```json\n{tree_str}\n```\n\n"
        else:
            body += f"_No tree content available_\n\n"
        
        body += f"---\n*Generated by LumTrails Web Scanner - Accessibility Tree Module*"
        
        issue_data = {
            'title': title,
            'body': body[:GITHUB_ISSUE_BODY_LIMIT],
            'labels': [label, 'axtree', 'web-scan']
        }
        
        response = await client.post(
            f"https://api.github.com/repos/{repository}/issues",
            headers=headers,
            json=issue_data
        )
        
        if response.status_code == 201:
            issues_created = 1
        
        return issues_created
    
    async def _create_layout_issues(self, client, headers, repository, layout_issues, grouping_option, label, url, scan_data) -> int:
        """Create GitHub issues for layout testing problems"""
        issues_created = 0
        
        if grouping_option == 'single-issue':
            # Create one consolidated issue
            title = f"Layout Testing Issues - {url}"
            body = f"# Layout Testing Report\n\n"
            body += f"**URL:** {url}\n"
            body += f"**Scan Date:** {scan_data.get('timestamp', 'Unknown')}\n"
            body += f"**Total Issues:** {len(layout_issues)}\n\n"
            
            for i, issue in enumerate(layout_issues, 1):
                body += f"### {i}. {issue.get('message', 'Layout issue')}\n"
                body += f"**Object:** {issue.get('object', 'Unknown')}\n"
                body += f"**Spec:** {issue.get('spec', 'Unknown spec')}\n"
                
                area = issue.get('area', {})
                if area:
                    body += f"**Area:** {area}\n"
                body += "\n"
            
            body += f"---\n*Generated by LumTrails Web Scanner - Layout Testing Module*"
            
            issue_data = {
                'title': title,
                'body': body,
                'labels': [label, 'layout-testing', 'web-scan']
            }
            
            response = await client.post(
                f"https://api.github.com/repos/{repository}/issues",
                headers=headers,
                json=issue_data
            )
            
            if response.status_code == 201:
                issues_created = 1
        
        else:  # per-error-type
            # Create one issue per layout problem (limited to 10)
            for issue in layout_issues[:10]:
                title = f"Layout: {issue.get('message', 'Unknown')[:80]} - {url}"
                
                body = f"# Layout Testing Issue\n\n"
                body += f"**URL:** {url}\n"
                body += f"**Message:** {issue.get('message', 'Layout issue detected')}\n"
                body += f"**Object:** {issue.get('object', 'Unknown')}\n"
                body += f"**Spec:** {issue.get('spec', 'Unknown spec')}\n\n"
                
                area = issue.get('area', {})
                if area:
                    body += f"**Area Details:**\n```json\n{area}\n```\n\n"
                
                body += f"---\n*Generated by LumTrails Web Scanner - Layout Testing Module*"
                
                issue_data = {
                    'title': title,
                    'body': body,
                    'labels': [label, 'layout-testing', 'web-scan']
                }
                
                response = await client.post(
                    f"https://api.github.com/repos/{repository}/issues",
                    headers=headers,
                    json=issue_data
                )
                
                if response.status_code == 201:
                    issues_created += 1
        
        return issues_created
    
    async def _push_pdf_scan_results(self, user_id: str, scan_data: Dict[str, Any], github_config: Dict[str, Any]) -> Dict[str, Any]:
        """Push PDF scan results to GitHub"""
        try:
            # Get repository from config.repository or top-level repository
            repository = github_config.get('config', {}).get('repository') or github_config.get('repository')
            if not repository:
                logger.error(f"GitHub repository not configured for user {user_id}")
                return {"success": False}
            
            # Get access token from Secret Manager
            secret_id = f"github-access-token-{user_id}"
            access_token = get_secret(secret_id)
            
            if not access_token:
                logger.error(f"GitHub access token not found for user {user_id}")
                return {"success": False}
            
            access_token = access_token.strip()
            
            headers = {
                'Authorization': f"token {access_token}",
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            }
            
            # Get PDF scan grouping option - default to "per-page" for consistency across platforms
            config_obj = github_config.get('config', {})
            pdf_scan_sections = github_config.get('pdf_scan_sections', {})
            pdf_grouping_option = pdf_scan_sections.get('pdf_grouping_option', 'per-page')
            label = config_obj.get('label', 'accessibility')
            
            # Extract PDF scan data
            file_name = scan_data.get('file_name', 'Unknown PDF')
            accessibility_report = scan_data.get('accessibility_report', 'No analysis available')
            pages_analyzed = scan_data.get('unified_results', {}).get('pages_analyzed', 0)
            scan_timestamp = scan_data.get('timestamp', 'Unknown')
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                issues_created = 0
                
                if pdf_grouping_option == 'single-issue':
                    # Create one issue with the entire PDF accessibility report
                    title = f"PDF Accessibility Analysis - {file_name}"
                    
                    body = f"# PDF Accessibility Report\n\n"
                    body += f"**File:** {file_name}\n"
                    body += f"**Pages Analyzed:** {pages_analyzed}\n"
                    body += f"**Scan Date:** {scan_timestamp}\n\n"
                    body += f"---\n\n"
                    body += f"{accessibility_report}\n\n"
                    body += f"---\n\n*Generated by LumTrails PDF AI Accessibility Scanner*"
                    
                    # Truncate if body exceeds GitHub's issue body limit
                    if len(body) > GITHUB_TRUNCATION_THRESHOLD:
                        truncation_notice = f"\n\n---\n\n_Message truncated due to GitHub's issue body limit (~65,000 characters). Full report available in LumTrails._"
                        # Calculate how much we can keep
                        max_content_length = GITHUB_ISSUE_BODY_LIMIT - len(truncation_notice) - 100
                        body = body[:max_content_length] + truncation_notice
                        logger.warning(f"PDF report truncated for GitHub issue (original: {len(accessibility_report)} chars)")
                    
                    issue_data = {
                        'title': title,
                        'body': body[:GITHUB_ISSUE_BODY_LIMIT],  # Final safety truncation
                        'labels': [label, 'pdf-scan']
                    }
                    
                    response = await client.post(
                        f"https://api.github.com/repos/{repository}/issues",
                        headers=headers,
                        json=issue_data
                    )
                    
                    if response.status_code == 201:
                        issues_created = 1
                        logger.info(f"Created GitHub issue for PDF scan: {file_name}")
                    else:
                        logger.error(f"Failed to create GitHub issue for PDF: {response.status_code} - {response.text}")
                        return {"success": False}
                
                else:  # per-page grouping
                    # Parse the accessibility report to extract individual page analyses
                    page_analyses = self._parse_pdf_report_by_page(accessibility_report)
                    
                    if not page_analyses:
                        logger.warning(f"Could not parse PDF report into pages, falling back to single issue")
                        # Fall back to single issue
                        return await self._push_pdf_scan_results(
                            user_id, 
                            scan_data, 
                            {**github_config, 'pdf_scan_sections': {'pdf_grouping_option': 'single-issue'}}
                        )
                    
                    # Create one issue per page
                    for page_num, page_analysis in page_analyses.items():
                        if issues_created >= 20:  # Limit to prevent spam
                            logger.warning(f"Reached issue creation limit for PDF scan")
                            break
                        
                        title = f"PDF Accessibility - {file_name} - Page {page_num}"
                        
                        body = f"# PDF Accessibility Report - Page {page_num}\n\n"
                        body += f"**File:** {file_name}\n"
                        body += f"**Page:** {page_num} of {pages_analyzed}\n"
                        body += f"**Scan Date:** {scan_timestamp}\n\n"
                        body += f"---\n\n"
                        body += f"{page_analysis}\n\n"
                        body += f"---\n\n*Generated by LumTrails PDF AI Accessibility Scanner*"
                        
                        # Truncate if body exceeds GitHub's issue body limit
                        if len(body) > GITHUB_TRUNCATION_THRESHOLD:
                            truncation_notice = f"\n\n---\n\n_Message truncated due to GitHub's issue body limit (~65,000 characters)._"
                            max_content_length = GITHUB_ISSUE_BODY_LIMIT - len(truncation_notice) - 100
                            body = body[:max_content_length] + truncation_notice
                        
                        issue_data = {
                            'title': title,
                            'body': body[:GITHUB_ISSUE_BODY_LIMIT],  # Final safety truncation
                            'labels': [label, 'pdf-scan', f'page-{page_num}']
                        }
                        
                        response = await client.post(
                            f"https://api.github.com/repos/{repository}/issues",
                            headers=headers,
                            json=issue_data
                        )
                        
                        if response.status_code == 201:
                            issues_created += 1
                            logger.info(f"Created GitHub issue for PDF page {page_num}")
                        else:
                            logger.error(f"Failed to create GitHub issue for page {page_num}: {response.status_code}")
                
                logger.info(f"Created {issues_created} GitHub issues for PDF scan")
                return {"success": True, "issues_created": issues_created}
        
        except Exception as e:
            logger.error(f"Error pushing PDF scan to GitHub: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_pdf_report_by_page(self, accessibility_report: str) -> Dict[int, str]:
        """Parse PDF accessibility report to extract individual page analyses - UNCHANGED"""
        try:
            page_analyses = {}
            
            # Split report by PAGE markers
            page_pattern = r'PAGE (\d+) ANALYSIS\s*[-]+\s*Source: [^\n]+\s*(.*?)(?=PAGE \d+ ANALYSIS|ANALYSIS SUMMARY|$)'
            matches = re.findall(page_pattern, accessibility_report, re.DOTALL)
            
            for page_num_str, page_content in matches:
                page_num = int(page_num_str)
                # Clean up the content
                cleaned_content = page_content.strip()
                # Remove excessive equal signs separators
                cleaned_content = re.sub(r'\n={20,}\n', '\n\n', cleaned_content)
                page_analyses[page_num] = cleaned_content
            
            logger.info(f"Parsed {len(page_analyses)} pages from PDF report")
            return page_analyses
        
        except Exception as e:
            logger.error(f"Error parsing PDF report by page: {e}")
            return {}
