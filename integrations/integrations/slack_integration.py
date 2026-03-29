"""
Slack Integration Service - Web Scan v3.0.0
Supports modular web scan sections (WCAG, HTML, Links, AxTree, Layout)
Preserves PDF scan functionality
Uses Slack Block Kit for rich formatting
"""
import httpx
import logging
from typing import Dict, Any, List, Optional
from integrations.shared_utils import get_secret_async, filter_violations_by_severity
from integrations.scan_results_adapter import WebScanResultsAdapter
import re

logger = logging.getLogger(__name__)

# Slack API Limits
SLACK_TEXT_BLOCK_LIMIT = 2900  # Max ~3000 chars per text block, leaving buffer
SLACK_BLOCK_LIMIT = 50  # Max 50 blocks per message


class SlackIntegration:
    """Slack integration for posting scan results as messages"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.webhook_url = None
    
    async def _get_webhook_url(self, user_id: str) -> Optional[str]:
        """Get Slack webhook URL"""
        if not self.webhook_url:
            if not self.config.get('config', {}).get('connected'):
                logger.warning("Slack integration not connected")
                return None
            
            secret_id = f"slack-webhook-{user_id}"
            self.webhook_url = await get_secret_async(secret_id)
            
            if not self.webhook_url:
                logger.error(f"Slack webhook URL not found for user {user_id}")
        
        return self.webhook_url
    
    async def push_violations(self, violations: List[Dict[str, Any]], url: str, scan_id: str, user_id: str,
                             scan_timestamp: Optional[str] = None, accessibility_score: Optional[float] = None,
                             scan_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Push scan results to Slack"""
        try:
            # Detect scan type
            is_pdf_scan = scan_data and scan_data.get('scan_type') == 'ai_vision'
            
            # Get config object for enabled flags
            config_obj = self.config.get('config', {})
            
            # Handle PDF scans
            if is_pdf_scan:
                pdf_scan_enabled = config_obj.get('pdf_scan_enabled', False)
                if not pdf_scan_enabled:
                    logger.info(f"PDF scan integration disabled")
                    return {"success": True, "message": "PDF scan integration disabled"}
                
                return await self._push_pdf_scan_results(user_id, scan_data, scan_id, scan_timestamp)
            
            # Web scan processing
            web_scan_enabled = config_obj.get('web_scan_enabled', False)
            if not web_scan_enabled:
                logger.info(f"Slack integration disabled")
                return {"success": True, "message": "Integration disabled"}
            
            # Process modular web scan format
            logger.info("Processing modular web scan format")
            return await self._push_modular_web_scan(user_id, scan_data, scan_id, scan_timestamp, url)
        
        except Exception as e:
            logger.error(f"Error pushing to Slack: {e}")
            return {"success": False, "error": str(e)}
    
    async def _push_modular_web_scan(self, user_id: str, scan_data: Dict[str, Any], scan_id: str,
                                    scan_timestamp: str, url: str) -> Dict[str, Any]:
        """Push new modular web scan format to Slack"""
        try:
            webhook_url = await self._get_webhook_url(user_id)
            if not webhook_url:
                return {"success": False, "error": "Slack webhook URL not available"}
            
            slack_config = self.config.get('config', {})
            channel = slack_config.get('channel')
            
            # Get web scan sections configuration
            web_scan_sections = self.config.get('web_scan_sections', {})
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
            
            # Get severity filter
            severity_filter = web_scan_sections.get('wcag_severity_filter', ['High', 'Medium', 'Low'])
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                messages_sent = 0
                
                # Process WCAG Compliance (Axe-core)
                if wcag_enabled:
                    wcag_violations = WebScanResultsAdapter.extract_wcag_violations(scan_data, severity_filter)
                    if wcag_violations:
                        sent = await self._send_wcag_messages(
                            client, webhook_url, channel, wcag_violations,
                            wcag_grouping, wcag_regroup, url, scan_data
                        )
                        messages_sent += sent
                
                # Process HTML Validation
                if html_enabled:
                    html_errors = WebScanResultsAdapter.extract_html_errors(scan_data)
                    if html_errors:
                        sent = await self._send_html_messages(
                            client, webhook_url, channel, html_errors,
                            html_grouping, url, scan_data
                        )
                        messages_sent += sent
                
                # Process Link Health
                if links_enabled:
                    link_issues = WebScanResultsAdapter.extract_link_issues(scan_data)
                    if link_issues:
                        sent = await self._send_link_messages(
                            client, webhook_url, channel, link_issues,
                            links_grouping, url, scan_data
                        )
                        messages_sent += sent
                
                # Process Accessibility Tree
                if axtree_enabled:
                    axtree_data = WebScanResultsAdapter.extract_axtree_data(scan_data)
                    if axtree_data.get('has_data'):
                        sent = await self._send_axtree_message(
                            client, webhook_url, channel, axtree_data, url, scan_data
                        )
                        messages_sent += sent
                
                # Process Layout Testing
                if layout_enabled:
                    layout_issues = WebScanResultsAdapter.extract_layout_issues(scan_data)
                    if layout_issues:
                        sent = await self._send_layout_messages(
                            client, webhook_url, channel, layout_issues,
                            layout_grouping, url, scan_data
                        )
                        messages_sent += sent
                
                logger.info(f"Sent {messages_sent} Slack messages")
                return {"success": True, "messages_sent": messages_sent}
        
        except Exception as e:
            logger.error(f"Error in modular web scan processing: {e}")
            return {"success": False, "error": str(e)}
    
    async def _send_wcag_messages(self, client, webhook_url, channel, violations, grouping_option, regroup_violations, url, scan_data) -> int:
        """Send Slack messages for WCAG violations with detailed element information
        
        Grouping options:
        - 'single-issue': All violations in one message (may be truncated)
        - 'per-error-type': One message per violation or per rule type (depending on regroup_violations)
        
        regroup_violations:
        - True: Group violations by rule type (one message per rule)
        - False: One message per individual violation
        
        Truncation policy:
        - Always fit as many WHOLE violations/elements as possible
        - When truncating, add a clear message about Slack's character limit (~3,000 chars per text block)
        """
        messages_sent = 0
        
        # Slack limits
        SLACK_TEXT_BLOCK_LIMIT = 2900  # ~3000 char limit with safety margin
        SLACK_BLOCK_LIMIT = 50
        
        # Severity-based emojis
        SEVERITY_EMOJI = {
            'critical': '🚨',  # Red alarm for critical
            'serious': '⚠️',   # Warning for serious
            'moderate': '📋',  # Clipboard for moderate
            'minor': '💡'      # Light bulb for minor
        }
        
        if grouping_option == 'single-issue':
            # Create one consolidated message with all violation details
            violations_by_impact = {}
            for violation in violations:
                impact = violation.get('impact', 'minor')
                if impact not in violations_by_impact:
                    violations_by_impact[impact] = []
                violations_by_impact[impact].append(violation)
            
            blocks = []
            emoji = '🔍'
            # Use the most severe emoji for the header
            for imp in ['critical', 'serious', 'moderate', 'minor']:
                if imp in violations_by_impact:
                    emoji = SEVERITY_EMOJI.get(imp, '🔍')
                    break
            
            blocks.append({
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} WCAG Compliance Issues"}
            })
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*URL:* {url}\n*Total Violations:* {len(violations)}"}
            })
            blocks.append({"type": "divider"})
            
            was_truncated = False
            total_violations_shown = 0
            
            # Add detailed violations for each severity level
            for impact in ['critical', 'serious', 'moderate', 'minor']:
                if impact in violations_by_impact and len(blocks) < SLACK_BLOCK_LIMIT - 2:
                    impact_violations = violations_by_impact[impact]
                    emoji = SEVERITY_EMOJI.get(impact, '📋')
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*{emoji} {impact.title()} Issues ({len(impact_violations)})*"}
                    })
                    
                    # Show detailed info for each violation - fit as many whole violations as possible
                    for violation in impact_violations:
                        if len(blocks) >= SLACK_BLOCK_LIMIT - 3:  # Reserve space for truncation message
                            was_truncated = True
                            break
                            
                        help_text = violation.get('help', 'Unknown issue')
                        rule_id = violation.get('id', 'unknown')
                        description = violation.get('description', '')[:300]
                        
                        # Build violation content
                        violation_block = {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"*{help_text}*\nRule: `{rule_id}`\n{description}"}
                        }
                        
                        # Check if adding this violation would exceed limits
                        if len(blocks) + 3 >= SLACK_BLOCK_LIMIT:  # +3 for violation + elements + divider
                            was_truncated = True
                            break
                        
                        blocks.append(violation_block)
                        total_violations_shown += 1
                        
                        # Show affected elements
                        nodes = violation.get('nodes', [])
                        if nodes:
                            elements_parts = []
                            total_elements = len(nodes)
                            elements_shown = 0
                            current_length = 0
                            
                            # Fit as many whole elements as possible
                            for i, node in enumerate(nodes, 1):
                                target = node.get('target', [])
                                selector = target[0] if isinstance(target, list) and target else str(target)
                                html = node.get('html', '')[:150]
                                
                                element_entry = f"{i}. `{selector[:100]}`\n"
                                if html:
                                    element_entry += f"```{html}```\n"
                                
                                # Check if adding this element would exceed limit
                                if current_length + len(element_entry) > SLACK_TEXT_BLOCK_LIMIT - 100:
                                    break
                                
                                elements_parts.append(element_entry)
                                current_length += len(element_entry)
                                elements_shown += 1
                            
                            elements_text = f"*Affected Elements ({total_elements}):*\n" + "".join(elements_parts)
                            
                            if elements_shown < total_elements:
                                elements_text += f"\n⚠️ _...and {total_elements - elements_shown} more elements (truncated due to Slack's message limit)_"
                            
                            blocks.append({
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": elements_text[:SLACK_TEXT_BLOCK_LIMIT]}
                            })
                        
                        # Add help URL
                        if violation.get('helpUrl'):
                            blocks.append({
                                "type": "section",
                                "text": {"type": "mrkdwn", "text": f"📚 <{violation['helpUrl']}|Learn more about this rule>"}
                            })
                        
                        blocks.append({"type": "divider"})
                    
                    if was_truncated:
                        break
            
            # Add truncation warning if content was cut off
            if was_truncated:
                remaining = len(violations) - total_violations_shown
                blocks.append({
                    "type": "context",
                    "elements": [{
                        "type": "mrkdwn",
                        "text": f"⚠️ *Message truncated:* {remaining} additional violation(s) not shown due to Slack's message size limit (~3,000 characters per block, 50 blocks max). Consider using 'Multiple messages' mode for complete results."
                    }]
                })
            
            message = {"blocks": blocks[:SLACK_BLOCK_LIMIT]}
            if channel:
                message["channel"] = channel
            
            response = await client.post(webhook_url, json=message)
            if response.status_code == 200:
                messages_sent = 1
        
        elif not regroup_violations:
            # per-error-type with regroup_violations=False: Send one message per individual violation
            violation_count = 0
            for violation in violations:
                if violation_count >= 50:  # Limit to 50 individual messages to avoid spam
                    logger.info(f"Reached per-violation message limit (50)")
                    break
                
                nodes = violation.get('nodes', [])
                if not nodes:
                    continue
                
                rule_id = violation.get('id', 'unknown')
                impact = violation.get('impact', 'moderate')
                emoji = SEVERITY_EMOJI.get(impact, '📋')
                
                for node in nodes:
                    if violation_count >= 30:
                        break
                    violation_count += 1
                    
                    target = node.get('target', [])
                    selector = target[0] if isinstance(target, list) and target else str(target)
                    html = node.get('html', '')
                    
                    blocks = []
                    
                    # Header with violation info
                    blocks.append({
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"{emoji} WCAG Violation"}
                    })
                    
                    # Rule context - important for individual violations
                    blocks.append({
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Rule:*\n{violation.get('help', 'Unknown rule')[:100]}"},
                            {"type": "mrkdwn", "text": f"*Rule ID:*\n`{rule_id}`"}
                        ]
                    })
                    blocks.append({
                        "type": "section",
                        "fields": [
                            {"type": "mrkdwn", "text": f"*Impact:*\n{impact.title()}"},
                            {"type": "mrkdwn", "text": f"*URL:*\n{url[:100]}"}
                        ]
                    })
                    
                    blocks.append({"type": "divider"})
                    
                    # Affected Element
                    selector_display = selector[:150] + '...' if len(selector) > 150 else selector
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Affected Element:*\n`{selector_display}`"}
                    })
                    
                    if html:
                        html_display = html[:400] + '...' if len(html) > 400 else html
                        blocks.append({
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"*HTML:*\n```{html_display}```"}
                        })
                    
                    # Description
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Description:*\n{violation.get('description', 'No description')[:300]}"}
                    })
                    
                    # Help URL
                    if violation.get('helpUrl'):
                        blocks.append({
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"📚 <{violation['helpUrl']}|Learn more about this rule>"}
                        })
                    
                    message = {"blocks": blocks[:SLACK_BLOCK_LIMIT]}
                    if channel:
                        message["channel"] = channel
                    
                    response = await client.post(webhook_url, json=message)
                    if response.status_code == 200:
                        messages_sent += 1
        
        else:  # per-error-type with regroup_violations=True - send one message per rule type
            # Slack limits
            SLACK_TEXT_BLOCK_LIMIT = 2900
            SLACK_BLOCK_LIMIT = 50
            
            # Group violations by rule
            violations_by_rule = {}
            for violation in violations:
                rule_id = violation.get('id', 'unknown')
                if rule_id not in violations_by_rule:
                    violations_by_rule[rule_id] = []
                violations_by_rule[rule_id].append(violation)
            
            for rule_id, rule_violations in list(violations_by_rule.items()):
                violation = rule_violations[0]
                impact = violation.get('impact', 'moderate')
                emoji = SEVERITY_EMOJI.get(impact, '📋')
                
                blocks = []
                was_truncated = False
                
                # Header with severity emoji
                blocks.append({
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{emoji} {violation.get('help', 'WCAG Issue')[:140]}"}
                })
                
                # URL and Rule info
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*URL:* {url}"}
                })
                blocks.append({
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Rule ID:*\n`{rule_id}`"},
                        {"type": "mrkdwn", "text": f"*Impact:*\n{impact.title()}"}
                    ]
                })
                
                # Calculate total affected elements
                total_nodes = sum(len(v.get('nodes', [])) for v in rule_violations)
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Instances Found:* {total_nodes}"}
                })
                
                blocks.append({"type": "divider"})
                
                # Description
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Description:*\n{violation.get('description', 'No description available')[:500]}"}
                })
                
                # Affected Elements - fit as many WHOLE elements as possible
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Affected Elements:*"}
                })
                
                element_count = 0
                for v in rule_violations:
                    nodes = v.get('nodes', [])
                    for node in nodes:
                        # Check if we have room for this element + potential truncation message
                        if len(blocks) >= SLACK_BLOCK_LIMIT - 3:
                            was_truncated = True
                            break
                        
                        element_count += 1
                        
                        target = node.get('target', [])
                        selector = target[0] if isinstance(target, list) and target else str(target)
                        html = node.get('html', '')
                        
                        # Truncate individual elements for display
                        selector_display = selector[:100] + '...' if len(selector) > 100 else selector
                        html_display = html[:200] + '...' if len(html) > 200 else html
                        
                        element_text = f"*{element_count}.* `{selector_display}`"
                        if html_display:
                            element_text += f"\n```{html_display}```"
                        
                        blocks.append({
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": element_text}
                        })
                    
                    if was_truncated:
                        break
                
                # Show count of remaining elements with clear truncation message
                if total_nodes > element_count:
                    remaining = total_nodes - element_count
                    blocks.append({
                        "type": "context",
                        "elements": [{
                            "type": "mrkdwn",
                            "text": f"⚠️ *Message truncated:* {remaining} more element(s) not shown due to Slack's message size limit (~3,000 characters per block, 50 blocks max)."
                        }]
                    })
                
                # Help URL
                if violation.get('helpUrl'):
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"📚 <{violation['helpUrl']}|Learn more about this rule>"}
                    })
                
                message = {"blocks": blocks[:SLACK_BLOCK_LIMIT]}
                if channel:
                    message["channel"] = channel
                
                response = await client.post(webhook_url, json=message)
                if response.status_code == 200:
                    messages_sent += 1
        
        return messages_sent
    
    async def _send_html_messages(self, client, webhook_url, channel, html_errors, grouping_option, url, scan_data) -> int:
        """Send Slack messages for HTML validation errors
        
        Grouping options:
        - 'single-issue': All HTML errors in one message
        - 'per-error-type': One message per HTML error
        """
        messages_sent = 0
        errors = [e for e in html_errors if e.get('type') == 'error']
        warnings = [e for e in html_errors if e.get('type') == 'warning']
        
        if grouping_option == 'single-issue':
            blocks = []
            blocks.append({
                "type": "header",
                "text": {"type": "plain_text", "text": "🔧 HTML Validation Issues"}
            })
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*URL:* {url}\n*Errors:* {len(errors)}\n*Warnings:* {len(warnings)}"}
            })
            blocks.append({"type": "divider"})
            
            errors_shown = 0
            was_truncated = False
            
            if errors:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "*Errors:*"}
                })
                for error in errors:
                    if len(blocks) >= SLACK_BLOCK_LIMIT - 1:  # Reserve 1 for truncation message
                        was_truncated = True
                        break
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"• {error.get('message', 'Unknown')[:200]}\n  Line {error.get('line', '?')}, Column {error.get('column', '?')}"}
                    })
                    errors_shown += 1
                
                # Add truncation warning if we didn't show all errors
                remaining = len(errors) - errors_shown
                if remaining > 0 or was_truncated:
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"⚠️ *Message truncated:* {remaining} more error(s) not shown due to Slack's message size limit (~3,000 characters per block, 50 blocks max)."}
                    })
            
            message = {"blocks": blocks[:SLACK_BLOCK_LIMIT]}
            if channel:
                message["channel"] = channel
            
            response = await client.post(webhook_url, json=message)
            if response.status_code == 200:
                messages_sent = 1
        
        else:  # per-error-type - one message per HTML error
            for error in errors[:5]:
                blocks = []
                blocks.append({
                    "type": "header",
                    "text": {"type": "plain_text", "text": "🔧 HTML Validation Error"}
                })
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*URL:* {url}"}
                })
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Message:* {error.get('message', 'Unknown error')[:500]}"}
                })
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Location:* Line {error.get('line', '?')}, Column {error.get('column', '?')}"}
                })
                
                message = {"blocks": blocks[:SLACK_BLOCK_LIMIT]}
                if channel:
                    message["channel"] = channel
                
                response = await client.post(webhook_url, json=message)
                if response.status_code == 200:
                    messages_sent += 1
        
        return messages_sent
    
    async def _send_link_messages(self, client, webhook_url, channel, link_issues, grouping_option, url, scan_data) -> int:
        """Send Slack messages for broken links
        
        Grouping options:
        - 'single-issue': All broken links in one message
        - 'per-error-type': One message per broken link
        """
        messages_sent = 0
        
        if grouping_option == 'single-issue':
            blocks = []
            blocks.append({
                "type": "header",
                "text": {"type": "plain_text", "text": "🔗 Link Issues Detected"}
            })
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*URL:* {url}\n*Total Issues:* {len(link_issues)}"}
            })
            blocks.append({"type": "divider"})
            
            links_shown = 0
            was_truncated = False
            
            for link in link_issues:
                if len(blocks) >= SLACK_BLOCK_LIMIT - 1:  # Reserve 1 for truncation message
                    was_truncated = True
                    break
                
                state = link.get('state', 'invalid')
                state_emoji = "🔴" if state == 'invalid' else "🟠" if state == 'timeout' else "🟡"
                state_label = "Broken" if state == 'invalid' else "Timeout" if state == 'timeout' else "Unreachable"
                error_reason = link.get('error_reason', '')
                
                text = f"{state_emoji} <{link.get('url', 'Unknown')}|{link.get('url', 'Unknown')[:80]}>\n  *Status:* {state_label}"
                if error_reason:
                    text += f"\n  *Reason:* {error_reason[:100]}"
                
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": text}
                })
                links_shown += 1
            
            # Add truncation warning if we didn't show all links
            remaining = len(link_issues) - links_shown
            if remaining > 0 or was_truncated:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"⚠️ *Message truncated:* {remaining} more link issue(s) not shown due to Slack's message size limit."}
                })
            
            message = {"blocks": blocks[:SLACK_BLOCK_LIMIT]}
            if channel:
                message["channel"] = channel
            
            response = await client.post(webhook_url, json=message)
            if response.status_code == 200:
                messages_sent = 1
        
        else:  # per-error-type - one message per broken link
            for link in link_issues[:10]:
                state = link.get('state', 'invalid')
                state_emoji = "🔴" if state == 'invalid' else "🟠" if state == 'timeout' else "🟡"
                state_label = "Broken" if state == 'invalid' else "Timeout" if state == 'timeout' else "Unreachable"
                error_reason = link.get('error_reason', '')
                
                blocks = []
                blocks.append({
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{state_emoji} Link Issue: {state_label}"}
                })
                
                fields = [
                    {"type": "mrkdwn", "text": f"*Page:*\n{url}"},
                    {"type": "mrkdwn", "text": f"*Status:*\n{state_label}"}
                ]
                blocks.append({
                    "type": "section",
                    "fields": fields
                })
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*URL:*\n<{link.get('url', 'Unknown')}|{link.get('url', 'Unknown')[:200]}>"}
                })
                
                if error_reason:
                    blocks.append({
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Reason:* {error_reason}"}
                    })
                
                message = {"blocks": blocks[:SLACK_BLOCK_LIMIT]}
                if channel:
                    message["channel"] = channel
                
                response = await client.post(webhook_url, json=message)
                if response.status_code == 200:
                    messages_sent += 1
        
        return messages_sent
    
    async def _send_axtree_message(self, client, webhook_url, channel, axtree_data, url, scan_data) -> int:
        """Send Slack message for accessibility tree with full content"""
        import json
        
        blocks = []
        blocks.append({
            "type": "header",
            "text": {"type": "plain_text", "text": "🌳 Accessibility Tree"}
        })
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*URL:* {url}\n*Total Nodes:* {axtree_data.get('node_count', 0)}"}
        })
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "This tree represents how assistive technologies interpret your page structure."}
        })
        blocks.append({"type": "divider"})
        
        # Get the full tree content
        tree_content = axtree_data.get('tree', axtree_data.get('content', None))
        
        if tree_content:
            # Convert to string if it's a dict/list
            if isinstance(tree_content, (dict, list)):
                tree_str = json.dumps(tree_content, indent=2)
            else:
                tree_str = str(tree_content)
            
            # Slack has a limit of ~3000 chars per text block
            if len(tree_str) > SLACK_TEXT_BLOCK_LIMIT:
                # Truncate and indicate there's more
                tree_str = tree_str[:SLACK_TEXT_BLOCK_LIMIT] + "\n\n⚠️ Tree truncated due to Slack's message size limit (~3,000 characters per block)."
            
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Accessibility Tree Structure:*"}
            })
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"```{tree_str}```"}
            })
        else:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": "_No tree content available_"}
            })
        
        message = {"blocks": blocks[:SLACK_BLOCK_LIMIT]}
        if channel:
            message["channel"] = channel
        
        response = await client.post(webhook_url, json=message)
        return 1 if response.status_code == 200 else 0
    
    async def _send_layout_messages(self, client, webhook_url, channel, layout_issues, grouping_option, url, scan_data) -> int:
        """Send Slack messages for layout testing issues
        
        Grouping options:
        - 'single-issue': All layout issues in one message
        - 'per-error-type': One message per layout issue
        """
        messages_sent = 0
        
        if grouping_option == 'single-issue':
            blocks = []
            blocks.append({
                "type": "header",
                "text": {"type": "plain_text", "text": "📐 Layout Testing Issues"}
            })
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*URL:* {url}\n*Total Issues:* {len(layout_issues)}"}
            })
            blocks.append({"type": "divider"})
            
            issues_shown = 0
            was_truncated = False
            
            for issue in layout_issues:
                if len(blocks) >= SLACK_BLOCK_LIMIT - 1:  # Reserve 1 for truncation message
                    was_truncated = True
                    break
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"• {issue.get('message', 'Layout issue')[:200]}\n  Object: `{issue.get('object', 'Unknown')}`"}
                })
                issues_shown += 1
            
            # Add truncation warning if we didn't show all issues
            remaining = len(layout_issues) - issues_shown
            if remaining > 0 or was_truncated:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"⚠️ *Message truncated:* {remaining} more layout issue(s) not shown due to Slack's message size limit (~3,000 characters per block, 50 blocks max)."}
                })
            
            message = {"blocks": blocks[:SLACK_BLOCK_LIMIT]}
            if channel:
                message["channel"] = channel
            
            response = await client.post(webhook_url, json=message)
            if response.status_code == 200:
                messages_sent = 1
        
        else:  # per-error-type - one message per layout issue
            for issue in layout_issues[:5]:
                blocks = []
                blocks.append({
                    "type": "header",
                    "text": {"type": "plain_text", "text": "📐 Layout Issue"}
                })
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*URL:* {url}"}
                })
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*Message:* {issue.get('message', 'Layout issue')[:500]}"}
                })
                blocks.append({
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Object:*\n`{issue.get('object', 'Unknown')}`"},
                        {"type": "mrkdwn", "text": f"*Spec:*\n`{issue.get('spec', 'Unknown')}`"}
                    ]
                })
                
                message = {"blocks": blocks[:SLACK_BLOCK_LIMIT]}
                if channel:
                    message["channel"] = channel
                
                response = await client.post(webhook_url, json=message)
                if response.status_code == 200:
                    messages_sent += 1
        
        return messages_sent
    
    async def _push_pdf_scan_results(self, user_id: str, scan_data: Dict[str, Any], scan_id: str, scan_timestamp: str) -> Dict[str, Any]:
        """Push PDF scan results to Slack based on grouping configuration"""
        try:
            webhook_url = await self._get_webhook_url(user_id)
            if not webhook_url:
                return {"success": False, "error": "Slack webhook URL not available"}
            
            slack_config = self.config.get('config', {})
            pdf_scan_sections = self.config.get('pdf_scan_sections', {})
            pdf_grouping_option = pdf_scan_sections.get('pdf_grouping_option', 'per-page')
            channel = slack_config.get('channel')
            
            # Extract PDF scan data
            file_name = scan_data.get('file_name', 'Unknown PDF')
            accessibility_report = scan_data.get('accessibility_report', 'No analysis available')
            pages_analyzed = scan_data.get('unified_results', {}).get('pages_analyzed', 0)
            
            messages = []
            
            if pdf_grouping_option == 'single-issue':
                messages.append(self._create_pdf_comprehensive_message(
                    file_name, accessibility_report, pages_analyzed, scan_id, scan_timestamp
                ))
            else:  # per-page grouping
                page_analyses = self._parse_pdf_report_by_page(accessibility_report)
                
                if not page_analyses:
                    logger.warning(f"Could not parse PDF report into pages, falling back to single message")
                    messages.append(self._create_pdf_comprehensive_message(
                        file_name, accessibility_report, pages_analyzed, scan_id, scan_timestamp
                    ))
                else:
                    for page_num, page_analysis in page_analyses.items():
                        messages.append(self._create_pdf_page_message(
                            file_name, page_num, pages_analyzed, page_analysis, scan_id, scan_timestamp
                        ))
            
            # Send messages to Slack
            sent_count = 0
            failed_messages = []
            
            async with httpx.AsyncClient() as client:
                for i, message in enumerate(messages):
                    if channel:
                        message['channel'] = channel
                    
                    if not self._validate_slack_message(message):
                        logger.error(f"PDF message {i+1} failed validation, skipping")
                        failed_messages.append(f"Message {i+1}: Invalid format")
                        continue
                    
                    response = await client.post(webhook_url, json=message)
                    
                    if response.status_code == 200:
                        sent_count += 1
                    else:
                        error_msg = f"Message {i+1} failed: {response.status_code} - {response.text}"
                        logger.error(f"Slack webhook failed for PDF: {error_msg}")
                        failed_messages.append(error_msg)
                        continue
            
            if failed_messages:
                return {
                    "success": sent_count > 0,
                    "message": f"Sent {sent_count} PDF scan messages, {len(failed_messages)} failed",
                    "messages_sent": sent_count,
                    "failures": failed_messages
                }
            else:
                return {
                    "success": True,
                    "message": f"Successfully sent {sent_count} PDF scan messages to Slack",
                    "messages_sent": sent_count
                }
        
        except Exception as e:
            logger.error(f"Error pushing PDF scan to Slack: {e}")
            return {"success": False, "error": str(e)}
    
    def _create_pdf_comprehensive_message(self, file_name: str, accessibility_report: str, pages_analyzed: int, scan_id: str, scan_timestamp: Optional[str]) -> Dict[str, Any]:
        """Create a single comprehensive Slack message for entire PDF report"""
        blocks = []
        
        header_text = f"📄 *PDF Accessibility Analysis*\n"
        header_text += f"*File:* {self._escape_markdown(file_name)}\n"
        header_text += f"*Pages Analyzed:* {pages_analyzed}"
        
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": header_text}
        })
        blocks.append({"type": "divider"})
        
        report_sections = self._split_long_text(accessibility_report, 2900)
        
        for section in report_sections[:10]:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": self._escape_markdown(section)}
            })
        
        if len(report_sections) > 10:
            remaining = len(report_sections) - 10
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"_Message truncated: {remaining} more section(s) not shown due to Slack's message size limit (~3,000 characters per block, 50 blocks max)._"}
            })
        
        metadata_text = f"*Scan ID:* {scan_id}"
        if scan_timestamp:
            metadata_text += f" • *Time:* {scan_timestamp}"
        
        blocks.extend([
            {"type": "divider"},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": metadata_text}]}
        ])
        
        return {"text": f"PDF Accessibility Analysis: {file_name}", "blocks": blocks}
    
    def _create_pdf_page_message(self, file_name: str, page_num: int, total_pages: int, page_analysis: str, scan_id: str, scan_timestamp: Optional[str]) -> Dict[str, Any]:
        """Create a Slack message for a single PDF page analysis"""
        blocks = []
        
        header_text = f"📄 *PDF Accessibility - Page {page_num}*\n"
        header_text += f"*File:* {self._escape_markdown(file_name)}\n"
        header_text += f"*Page:* {page_num} of {total_pages}"
        
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": header_text}
        })
        blocks.append({"type": "divider"})
        
        analysis_sections = self._split_long_text(page_analysis, 2900)
        
        for section in analysis_sections[:8]:
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": self._escape_markdown(section)}
            })
        
        if len(analysis_sections) > 8:
            remaining = len(analysis_sections) - 8
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"_Message truncated: {remaining} more section(s) not shown due to Slack's message size limit (~3,000 characters per block, 50 blocks max)._"}
            })
        
        metadata_text = f"*Scan ID:* {scan_id}"
        if scan_timestamp:
            metadata_text += f" • *Time:* {scan_timestamp}"
        
        blocks.extend([
            {"type": "divider"},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": metadata_text}]}
        ])
        
        return {"text": f"PDF Page {page_num} Accessibility Analysis: {file_name}", "blocks": blocks}
    
    def _parse_pdf_report_by_page(self, accessibility_report: str) -> Dict[int, str]:
        """Parse PDF accessibility report to extract individual page analyses"""
        try:
            page_analyses = {}
            
            page_pattern = r'PAGE (\d+) ANALYSIS\s*[-]+\s*Source: [^\n]+\s*(.*?)(?=PAGE \d+ ANALYSIS|ANALYSIS SUMMARY|$)'
            matches = re.findall(page_pattern, accessibility_report, re.DOTALL)
            
            for page_num_str, page_content in matches:
                page_num = int(page_num_str)
                cleaned_content = page_content.strip()
                cleaned_content = re.sub(r'\n={20,}\n', '\n\n', cleaned_content)
                page_analyses[page_num] = cleaned_content
            
            logger.info(f"Parsed {len(page_analyses)} pages from PDF report for Slack")
            return page_analyses
        
        except Exception as e:
            logger.error(f"Error parsing PDF report by page: {e}")
            return {}
    
    def _split_long_text(self, text: str, max_length: int) -> List[str]:
        """Split long text into chunks that fit Slack's limits"""
        if len(text) <= max_length:
            return [text]
        
        sections = []
        current_section = ""
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            if len(current_section) + len(para) + 2 <= max_length:
                if current_section:
                    current_section += "\n\n"
                current_section += para
            else:
                if current_section:
                    sections.append(current_section)
                
                if len(para) > max_length:
                    words = para.split()
                    current_section = ""
                    for word in words:
                        if len(current_section) + len(word) + 1 <= max_length:
                            if current_section:
                                current_section += " "
                            current_section += word
                        else:
                            if current_section:
                                sections.append(current_section)
                            current_section = word
                else:
                    current_section = para
        
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _escape_markdown(self, text: str) -> str:
        """Escape special characters for Slack markdown"""
        if not text:
            return ""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text
    
    def _validate_slack_message(self, message: Dict[str, Any]) -> bool:
        """Validate Slack message structure to prevent API errors"""
        try:
            if not isinstance(message, dict):
                return False
            
            blocks = message.get('blocks', [])
            if blocks:
                if len(blocks) > 50:
                    logger.warning(f"Message has {len(blocks)} blocks, exceeds Slack limit of 50")
                    return False
                
                for block in blocks:
                    if not isinstance(block, dict):
                        return False
                    if 'type' not in block:
                        return False
                    
                    if block.get('type') == 'section' and 'text' in block:
                        text_obj = block['text']
                        if isinstance(text_obj, dict) and 'text' in text_obj:
                            text_content = text_obj['text']
                            if len(text_content) > 3000:
                                logger.warning(f"Text block exceeds 3000 characters: {len(text_content)}")
                                return False
            
            main_text = message.get('text', '')
            if len(main_text) > 3000:
                logger.warning(f"Main text exceeds 3000 characters: {len(main_text)}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating Slack message: {e}")
            return False
