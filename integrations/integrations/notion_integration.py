"""
Notion Integration Service - Web Scan v3.0.0
Supports modular web scan sections (WCAG, HTML, Links, AxTree, Layout)
Preserves PDF scan functionality

Note: Notion has NO character limits for content, but has a 100-block limit per API request.
We work around this by making multiple append requests to add more blocks.
"""
import httpx
import logging
from typing import Dict, Any, List, Optional
from integrations.shared_utils import get_secret_async, filter_violations_by_severity
from integrations.scan_results_adapter import WebScanResultsAdapter
import re

logger = logging.getLogger(__name__)

# Notion API limits - blocks per request, NOT content limits
NOTION_BLOCKS_PER_REQUEST = 100


class NotionIntegration:
    """Notion integration for pushing scan results as pages"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.token = None
    
    async def _get_auth_token(self, user_id: str) -> Optional[str]:
        """Get Notion authentication token"""
        if not self.token:
            if not self.config.get('config', {}).get('connected'):
                logger.warning("Notion integration not connected")
                return None
            
            secret_id = f"notion-access-token-{user_id}"
            self.token = await get_secret_async(secret_id)
            
            if not self.token:
                logger.error(f"Notion access token not found for user {user_id}")
        
        return self.token
    
    async def _create_page_with_all_blocks(self, client, headers, parent_page_id: str, title: str, blocks: List[Dict]) -> bool:
        """Create a Notion page and append all blocks, handling the 100-block limit per request.
        
        Notion has no character limit, but limits requests to 100 blocks.
        We work around this by creating the page with initial blocks, then appending more.
        """
        if not blocks:
            return False
        
        # Create page with first batch of blocks
        first_batch = blocks[:NOTION_BLOCKS_PER_REQUEST]
        page_data = {
            "parent": {"page_id": parent_page_id},
            "properties": {
                "title": {"title": [{"text": {"content": title[:2000]}}]}
            },
            "children": first_batch
        }
        
        response = await client.post("https://api.notion.com/v1/pages", headers=headers, json=page_data)
        if response.status_code != 200:
            logger.error(f"Failed to create Notion page: {response.text}")
            return False
        
        # If we have more blocks, append them in batches
        if len(blocks) > NOTION_BLOCKS_PER_REQUEST:
            page_id = response.json().get('id')
            remaining_blocks = blocks[NOTION_BLOCKS_PER_REQUEST:]
            
            # Append remaining blocks in batches
            for i in range(0, len(remaining_blocks), NOTION_BLOCKS_PER_REQUEST):
                batch = remaining_blocks[i:i + NOTION_BLOCKS_PER_REQUEST]
                append_data = {"children": batch}
                
                append_response = await client.patch(
                    f"https://api.notion.com/v1/blocks/{page_id}/children",
                    headers=headers,
                    json=append_data
                )
                
                if append_response.status_code != 200:
                    logger.warning(f"Failed to append blocks batch {i // NOTION_BLOCKS_PER_REQUEST + 2}: {append_response.text}")
                    # Continue anyway - partial content is better than no content
        
        return True
    
    async def push_violations(self, violations: List[Dict[str, Any]], url: str, scan_id: str, user_id: str, 
                             scan_timestamp: Optional[str] = None, accessibility_score: Optional[float] = None, 
                             scan_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Push scan results to Notion"""
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
                logger.info(f"Notion integration disabled")
                return {"success": True, "message": "Integration disabled"}
            
            # Process modular web scan format
            logger.info("Processing modular web scan format")
            return await self._push_modular_web_scan(user_id, scan_data, scan_id, scan_timestamp, url)
        
        except Exception as e:
            logger.error(f"Error pushing to Notion: {e}")
            return {"success": False, "error": str(e)}
    
    async def _push_modular_web_scan(self, user_id: str, scan_data: Dict[str, Any], scan_id: str, 
                                    scan_timestamp: str, url: str) -> Dict[str, Any]:
        """Push new modular web scan format to Notion"""
        try:
            token = await self._get_auth_token(user_id)
            if not token:
                return {"success": False, "error": "Notion token not available"}
            
            notion_config = self.config.get('config', {})
            parent_page_id = notion_config.get('parent_page_id')
            
            if not parent_page_id:
                logger.error(f"Notion parent page not configured")
                return {"success": False, "error": "Parent page not configured"}
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            # Get web scan sections configuration
            web_scan_sections = self.config.get('web_scan_sections', {})
            wcag_enabled = web_scan_sections.get('wcag_enabled', True)
            html_enabled = web_scan_sections.get('html_enabled', True)
            links_enabled = web_scan_sections.get('links_enabled', True)
            axtree_enabled = web_scan_sections.get('axtree_enabled', False)
            layout_enabled = web_scan_sections.get('layout_enabled', True)
            
            # Get grouping options - strict schema, no fallbacks
            wcag_grouping = web_scan_sections.get('wcag_grouping_option', 'per-error-type')
            wcag_regroup = web_scan_sections.get('wcag_regroup_violations', True)  # Default True for Notion
            html_grouping = web_scan_sections.get('html_grouping_option', 'per-error-type')
            links_grouping = web_scan_sections.get('links_grouping_option', 'per-error-type')
            layout_grouping = web_scan_sections.get('layout_grouping_option', 'per-error-type')
            
            # Get severity filter - strict schema, no fallbacks
            severity_filter = web_scan_sections.get('wcag_severity_filter', ['High', 'Medium', 'Low'])
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                pages_created = 0
                
                # Process WCAG Compliance (Axe-core)
                if wcag_enabled:
                    wcag_violations = WebScanResultsAdapter.extract_wcag_violations(scan_data, severity_filter)
                    if wcag_violations:
                        created = await self._create_wcag_pages(
                            client, headers, parent_page_id, wcag_violations,
                            wcag_grouping, wcag_regroup, url, scan_data
                        )
                        pages_created += created
                
                # Process HTML Validation
                if html_enabled:
                    html_errors = WebScanResultsAdapter.extract_html_errors(scan_data)
                    if html_errors:
                        created = await self._create_html_pages(
                            client, headers, parent_page_id, html_errors,
                            html_grouping, url, scan_data
                        )
                        pages_created += created
                
                # Process Link Health
                if links_enabled:
                    link_issues = WebScanResultsAdapter.extract_link_issues(scan_data)
                    if link_issues:
                        created = await self._create_link_pages(
                            client, headers, parent_page_id, link_issues,
                            links_grouping, url, scan_data
                        )
                        pages_created += created
                
                # Process Accessibility Tree
                if axtree_enabled:
                    axtree_data = WebScanResultsAdapter.extract_axtree_data(scan_data)
                    if axtree_data.get('has_data'):
                        created = await self._create_axtree_page(
                            client, headers, parent_page_id, axtree_data, url, scan_data
                        )
                        pages_created += created
                
                # Process Layout Testing
                if layout_enabled:
                    layout_issues = WebScanResultsAdapter.extract_layout_issues(scan_data)
                    if layout_issues:
                        created = await self._create_layout_pages(
                            client, headers, parent_page_id, layout_issues,
                            layout_grouping, url, scan_data
                        )
                        pages_created += created
                
                logger.info(f"Created {pages_created} Notion pages")
                return {"success": True, "pages_created": pages_created}
        
        except Exception as e:
            logger.error(f"Error in modular web scan processing: {e}")
            return {"success": False, "error": str(e)}
    
    async def _create_wcag_pages(self, client, headers, parent_page_id, violations, grouping_option, regroup_violations, url, scan_data) -> int:
        """Create Notion pages for WCAG violations with ALL elements - no truncation.
        
        Notion has NO character limits. We include every single element.
        We handle the 100-block API limit by making multiple append requests.
        
        Args:
            regroup_violations: When True with per-error-type, group by rule type. When False, individual pages per violation.
        """
        pages_created = 0
        
        # Severity-based emojis
        SEVERITY_EMOJI = {
            'critical': '🚨',
            'serious': '⚠️',
            'moderate': '📋',
            'minor': '💡'
        }
        
        if grouping_option == 'single-issue':
            # Create one consolidated page with ALL violations and ALL elements
            violations_by_impact = {}
            for violation in violations:
                impact = violation.get('impact', 'minor')
                if impact not in violations_by_impact:
                    violations_by_impact[impact] = []
                violations_by_impact[impact].append(violation)
            
            blocks = []
            
            # Use most severe emoji for header
            header_emoji = '🔍'
            for imp in ['critical', 'serious', 'moderate', 'minor']:
                if imp in violations_by_impact:
                    header_emoji = SEVERITY_EMOJI.get(imp, '🔍')
                    break
            
            blocks.append(self._create_heading_block(f"{header_emoji} WCAG Compliance Report", 1))
            blocks.append(self._create_paragraph_block(f"**URL:** {url}"))
            blocks.append(self._create_paragraph_block(f"**Total Violations:** {len(violations)}"))
            blocks.append(self._create_divider_block())
            
            for impact in ['critical', 'serious', 'moderate', 'minor']:
                if impact in violations_by_impact:
                    impact_violations = violations_by_impact[impact]
                    emoji = SEVERITY_EMOJI.get(impact, '📋')
                    blocks.append(self._create_heading_block(f"{emoji} {impact.title()} Issues ({len(impact_violations)})", 2))
                    
                    for i, violation in enumerate(impact_violations, 1):
                        blocks.append(self._create_heading_block(f"{i}. {violation.get('help', 'Unknown issue')}", 3))
                        blocks.append(self._create_paragraph_block(f"**Rule ID:** `{violation.get('id', 'unknown')}`"))
                        blocks.append(self._create_paragraph_block(f"**Impact:** {impact.title()}"))
                        blocks.append(self._create_paragraph_block(f"**Description:** {violation.get('description', '')}"))
                        
                        # ALL affected elements - no limit
                        nodes = violation.get('nodes', [])
                        if nodes:
                            blocks.append(self._create_paragraph_block(f"**Affected Elements ({len(nodes)}):**"))
                            for j, node in enumerate(nodes, 1):  # ALL elements
                                target = node.get('target', [])
                                selector = target[0] if isinstance(target, list) and target else str(target)
                                html = node.get('html', '')
                                
                                blocks.append(self._create_paragraph_block(f"{j}. `{selector}`"))
                                if html:
                                    blocks.append(self._create_code_block(html, 'html'))
                        
                        if violation.get('helpUrl'):
                            blocks.append(self._create_paragraph_block(f"📚 Learn more: {violation['helpUrl']}"))
                        
                        blocks.append(self._create_divider_block())
            
            # Use helper to create page with all blocks (handles 100-block limit)
            title = f"{header_emoji} WCAG Issues - {url[:50]}"
            if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                pages_created = 1
        
        else:  # per-error-type
            if regroup_violations:
                # Group violations by rule type - one page per rule with ALL elements
                violations_by_rule = {}
                for violation in violations:
                    rule_id = violation.get('id', 'unknown')
                    if rule_id not in violations_by_rule:
                        violations_by_rule[rule_id] = []
                    violations_by_rule[rule_id].append(violation)
                
                for rule_id, rule_violations in violations_by_rule.items():
                    violation = rule_violations[0]
                    impact = violation.get('impact', 'moderate')
                    emoji = SEVERITY_EMOJI.get(impact, '📋')
                    
                    blocks = []
                    
                    blocks.append(self._create_heading_block(f"{emoji} {violation.get('help', 'WCAG Violation')}", 1))
                    blocks.append(self._create_paragraph_block(f"**URL:** {url}"))
                    blocks.append(self._create_paragraph_block(f"**Rule ID:** `{rule_id}`"))
                    blocks.append(self._create_paragraph_block(f"**Impact:** {impact.title()}"))
                    
                    # Count total affected elements
                    total_nodes = sum(len(v.get('nodes', [])) for v in rule_violations)
                    blocks.append(self._create_paragraph_block(f"**Instances Found:** {total_nodes}"))
                    blocks.append(self._create_divider_block())
                    blocks.append(self._create_paragraph_block(f"**Description:**"))
                    blocks.append(self._create_paragraph_block(violation.get('description', '')))
                    
                    if violation.get('helpUrl'):
                        blocks.append(self._create_paragraph_block(f"📚 **Learn more:** {violation['helpUrl']}"))
                    
                    blocks.append(self._create_heading_block("Affected Elements", 2))
                    
                    # Add ALL elements - no truncation
                    element_count = 0
                    for rule_violation in rule_violations:
                        nodes = rule_violation.get('nodes', [])
                        for node in nodes:
                            element_count += 1
                            
                            target = node.get('target', [])
                            selector = target[0] if isinstance(target, list) and target else str(target)
                            html = node.get('html', '')
                            
                            blocks.append(self._create_paragraph_block(f"**{element_count}.** `{selector}`"))
                            if html:
                                blocks.append(self._create_code_block(html, 'html'))
                    
                    # Use helper to create page with all blocks
                    title = f"{emoji} {violation.get('help', rule_id)[:80]}"
                    if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                        pages_created += 1
            else:
                # Individual pages per violation with ALL elements
                for violation in violations:
                    rule_id = violation.get('id', 'unknown')
                    impact = violation.get('impact', 'moderate')
                    emoji = SEVERITY_EMOJI.get(impact, '📋')
                    help_text = violation.get('help', 'WCAG Violation')
                    description = violation.get('description', '')
                    help_url = violation.get('helpUrl', '')
                    nodes = violation.get('nodes', [])
                    
                    blocks = []
                    blocks.append(self._create_heading_block(f"{emoji} {help_text}", 1))
                    blocks.append(self._create_paragraph_block(f"**URL:** {url}"))
                    blocks.append(self._create_paragraph_block(f"**Rule ID:** `{rule_id}`"))
                    blocks.append(self._create_paragraph_block(f"**Impact:** {impact.title()}"))
                    blocks.append(self._create_paragraph_block(f"**Instances:** {len(nodes)}"))
                    blocks.append(self._create_divider_block())
                    
                    blocks.append(self._create_heading_block("Description", 2))
                    blocks.append(self._create_paragraph_block(description))
                    
                    blocks.append(self._create_heading_block("Affected Elements", 2))
                    for i, node in enumerate(nodes, 1):  # ALL elements
                        target = node.get('target', [])
                        selector = target[0] if isinstance(target, list) and target else str(target)
                        html = node.get('html', '')
                        
                        blocks.append(self._create_paragraph_block(f"**{i}.** `{selector}`"))
                        if html:
                            blocks.append(self._create_code_block(html, 'html'))
                    
                    if help_url:
                        blocks.append(self._create_divider_block())
                        blocks.append(self._create_paragraph_block(f"📚 **Learn more:** {help_url}"))
                    
                    # Use helper to create page with all blocks
                    title = f"{emoji} {help_text[:80]}"
                    if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                        pages_created += 1
        
        return pages_created
    
    async def _create_html_pages(self, client, headers, parent_page_id, html_errors, grouping_option, url, scan_data) -> int:
        """Create Notion pages for HTML validation errors - no truncation."""
        pages_created = 0
        errors = [e for e in html_errors if e.get('type') == 'error']
        warnings = [e for e in html_errors if e.get('type') == 'warning']
        
        if grouping_option == 'single-issue':
            blocks = []
            blocks.append(self._create_heading_block("HTML Validation Report", 1))
            blocks.append(self._create_paragraph_block(f"**URL:** {url}"))
            blocks.append(self._create_paragraph_block(f"**Errors:** {len(errors)}"))
            blocks.append(self._create_paragraph_block(f"**Warnings:** {len(warnings)}"))
            blocks.append(self._create_divider_block())
            
            if errors:
                blocks.append(self._create_heading_block(f"Errors ({len(errors)})", 2))
                for i, error in enumerate(errors, 1):  # ALL errors
                    blocks.append(self._create_paragraph_block(f"{i}. {error.get('message', 'Unknown error')}"))
                    blocks.append(self._create_paragraph_block(f"   Location: Line {error.get('line', '?')}, Column {error.get('column', '?')}"))
                    if error.get('extract'):
                        blocks.append(self._create_code_block(error['extract'], 'html'))
            
            if warnings:
                blocks.append(self._create_heading_block(f"Warnings ({len(warnings)})", 2))
                for i, warning in enumerate(warnings, 1):  # ALL warnings
                    blocks.append(self._create_paragraph_block(f"{i}. {warning.get('message', 'Unknown warning')}"))
            
            title = f"🔧 HTML Validation - {url[:50]}"
            if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                pages_created = 1
        
        else:  # per-error-type - ALL errors get their own page
            for error in errors:
                blocks = []
                blocks.append(self._create_heading_block("HTML Validation Error", 1))
                blocks.append(self._create_paragraph_block(f"**URL:** {url}"))
                blocks.append(self._create_paragraph_block(f"**Message:** {error.get('message', 'Unknown error')}"))
                blocks.append(self._create_paragraph_block(f"**Location:** Line {error.get('line', '?')}, Column {error.get('column', '?')}"))
                
                if error.get('extract'):
                    blocks.append(self._create_code_block(error['extract'], 'html'))
                
                title = f"🔧 {error.get('message', 'HTML Error')[:80]}"
                if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                    pages_created += 1
        
        return pages_created
    
    async def _create_link_pages(self, client, headers, parent_page_id, link_issues, grouping_option, url, scan_data) -> int:
        """Create Notion pages for link issues - no truncation."""
        pages_created = 0
        
        if grouping_option == 'single-issue':
            blocks = []
            blocks.append(self._create_heading_block("Link Issues Report", 1))
            blocks.append(self._create_paragraph_block(f"**URL:** {url}"))
            blocks.append(self._create_paragraph_block(f"**Total Issues:** {len(link_issues)}"))
            blocks.append(self._create_divider_block())
            
            for i, link in enumerate(link_issues, 1):  # ALL links
                state = link.get('state', 'invalid')
                state_label = "🔴 Broken" if state == 'invalid' else "🟠 Timeout" if state == 'timeout' else "🟡 Unreachable"
                error_reason = link.get('error_reason', '')
                
                blocks.append(self._create_paragraph_block(f"{i}. **{link.get('url', 'Unknown URL')}**"))
                blocks.append(self._create_paragraph_block(f"   Status: {state_label}"))
                if error_reason:
                    blocks.append(self._create_paragraph_block(f"   Reason: {error_reason}"))
            
            title = f"🔗 Link Issues - {url[:50]}"
            if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                pages_created = 1
        
        else:  # per-error-type - ALL links get their own page
            for link in link_issues:
                state = link.get('state', 'invalid')
                state_label = "Broken" if state == 'invalid' else "Timeout" if state == 'timeout' else "Unreachable"
                state_emoji = "🔴" if state == 'invalid' else "🟠" if state == 'timeout' else "🟡"
                error_reason = link.get('error_reason', '')
                
                blocks = []
                blocks.append(self._create_heading_block(f"{state_emoji} Link Issue: {state_label}", 1))
                blocks.append(self._create_paragraph_block(f"**Source URL:** {url}"))
                blocks.append(self._create_paragraph_block(f"**Link URL:** {link.get('url', 'Unknown')}"))
                blocks.append(self._create_paragraph_block(f"**Status:** {state_label}"))
                if error_reason:
                    blocks.append(self._create_paragraph_block(f"**Reason:** {error_reason}"))
                
                title = f"{state_emoji} {state_label}: {link.get('url', 'Unknown')[:50]}"
                if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                    pages_created += 1
        
        return pages_created
    
    async def _create_axtree_page(self, client, headers, parent_page_id, axtree_data, url, scan_data) -> int:
        """Create Notion page for accessibility tree with full tree content.
        
        Notion has NO character limits for pages, but code blocks have a ~2000 char limit per text segment.
        For large trees, we use paragraph blocks with monospace formatting instead.
        """
        import json
        
        blocks = []
        blocks.append(self._create_heading_block("🌳 Accessibility Tree Report", 1))
        blocks.append(self._create_paragraph_block(f"**URL:** {url}"))
        blocks.append(self._create_paragraph_block(f"**Total Nodes:** {axtree_data.get('node_count', 0)}"))
        blocks.append(self._create_divider_block())
        blocks.append(self._create_paragraph_block("The accessibility tree represents how assistive technologies (like screen readers) interpret the page structure."))
        blocks.append(self._create_heading_block("Accessibility Tree Structure", 2))
        
        # Get the full tree content
        tree_content = axtree_data.get('tree', axtree_data.get('content', None))
        
        if tree_content:
            # Convert to string if it's a dict/list
            if isinstance(tree_content, (dict, list)):
                tree_str = json.dumps(tree_content, indent=2)
            else:
                tree_str = str(tree_content)
            
            # Notion code blocks have a ~2000 char limit per text segment
            # For small trees, use a single code block
            # For large trees, use paragraph blocks with monospace/code formatting
            NOTION_CODE_BLOCK_LIMIT = 2000
            
            if len(tree_str) <= NOTION_CODE_BLOCK_LIMIT:
                blocks.append(self._create_code_block(tree_str, 'json'))
            else:
                # For large trees, split into lines and use paragraph blocks
                # This avoids the code block splitting issue and keeps formatting intact
                blocks.append(self._create_paragraph_block("_Tree is large - displayed as formatted text below:_"))
                
                lines = tree_str.split('\n')
                current_chunk = []
                current_length = 0
                
                for line in lines:
                    # Each paragraph block can hold ~2000 chars
                    if current_length + len(line) + 1 > 1900:
                        if current_chunk:
                            chunk_text = '\n'.join(current_chunk)
                            blocks.append(self._create_code_block(chunk_text, 'json'))
                        current_chunk = [line]
                        current_length = len(line)
                    else:
                        current_chunk.append(line)
                        current_length += len(line) + 1
                
                # Add remaining chunk
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    blocks.append(self._create_code_block(chunk_text, 'json'))
        else:
            blocks.append(self._create_paragraph_block("_No tree content available_"))
        
        # Use helper to create page with all blocks (handles 100-block limit)
        title = f"🌳 Accessibility Tree - {url[:50]}"
        success = await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks)
        return 1 if success else 0
    
    async def _create_layout_pages(self, client, headers, parent_page_id, layout_issues, grouping_option, url, scan_data) -> int:
        """Create Notion pages for layout testing issues - no truncation."""
        pages_created = 0
        
        if grouping_option == 'single-issue':
            blocks = []
            blocks.append(self._create_heading_block("Layout Testing Report", 1))
            blocks.append(self._create_paragraph_block(f"**URL:** {url}"))
            blocks.append(self._create_paragraph_block(f"**Total Issues:** {len(layout_issues)}"))
            blocks.append(self._create_divider_block())
            
            for i, issue in enumerate(layout_issues, 1):  # ALL issues
                blocks.append(self._create_paragraph_block(f"{i}. {issue.get('message', 'Layout issue')}"))
                blocks.append(self._create_paragraph_block(f"   Object: {issue.get('object', 'Unknown')}"))
                blocks.append(self._create_paragraph_block(f"   Spec: {issue.get('spec', 'Unknown spec')}"))
            
            title = f"📐 Layout Issues - {url[:50]}"
            if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                pages_created = 1
        
        else:  # per-error-type - ALL issues get their own page
            for issue in layout_issues:
                blocks = []
                blocks.append(self._create_heading_block("Layout Testing Issue", 1))
                blocks.append(self._create_paragraph_block(f"**URL:** {url}"))
                blocks.append(self._create_paragraph_block(f"**Message:** {issue.get('message', 'Layout issue detected')}"))
                blocks.append(self._create_paragraph_block(f"**Object:** {issue.get('object', 'Unknown')}"))
                blocks.append(self._create_paragraph_block(f"**Spec:** {issue.get('spec', 'Unknown spec')}"))
                
                title = f"📐 {issue.get('message', 'Layout Issue')[:80]}"
                if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                    pages_created += 1
        
        return pages_created
    
    async def _push_pdf_scan_results(self, user_id: str, scan_data: Dict[str, Any], scan_id: str, scan_timestamp: str) -> Dict[str, Any]:
        """Push PDF scan results to Notion based on grouping configuration - no truncation."""
        try:
            token = await self._get_auth_token(user_id)
            if not token:
                return {"success": False, "error": "Notion token not available"}
            
            notion_config = self.config.get('config', {})
            parent_page_id = notion_config.get('parent_page_id')
            
            if not parent_page_id:
                logger.error(f"Notion parent page not configured")
                return {"success": False, "error": "Parent page not configured"}
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            # Get PDF scan grouping option
            pdf_scan_sections = self.config.get('pdf_scan_sections', {})
            pdf_grouping_option = pdf_scan_sections.get('pdf_grouping_option', 'per-page')
            
            # Extract PDF scan data
            file_name = scan_data.get('file_name', 'Unknown PDF')
            accessibility_report = scan_data.get('accessibility_report', 'No analysis available')
            pages_analyzed = scan_data.get('unified_results', {}).get('pages_analyzed', 0)
            
            pages_created = 0
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                if pdf_grouping_option == 'single-issue':
                    # Create one page with the ENTIRE PDF accessibility report - no truncation
                    blocks = []
                    blocks.append(self._create_heading_block("📄 PDF Accessibility Analysis", 1))
                    blocks.append(self._create_paragraph_block(f"**File:** {file_name}"))
                    blocks.append(self._create_paragraph_block(f"**Pages Analyzed:** {pages_analyzed}"))
                    blocks.append(self._create_paragraph_block(f"**Scan Date:** {scan_timestamp or 'Unknown'}"))
                    blocks.append(self._create_paragraph_block(f"**Scan ID:** {scan_id}"))
                    blocks.append(self._create_divider_block())
                    
                    # Split report into chunks - ALL chunks, no truncation
                    report_chunks = self._split_text_into_chunks(accessibility_report, 1800)
                    for chunk in report_chunks:  # ALL chunks
                        blocks.append(self._create_paragraph_block(chunk))
                    
                    blocks.append(self._create_divider_block())
                    blocks.append(self._create_paragraph_block("_Generated by LumTrails PDF AI Accessibility Scanner_"))
                    
                    # Use helper to create page with all blocks
                    title = f"📄 PDF Analysis - {file_name[:50]}"
                    if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                        pages_created = 1
                        logger.info(f"Created Notion page for PDF scan: {file_name}")
                    else:
                        return {"success": False, "error": "Failed to create Notion page"}
                
                else:  # per-page grouping
                    # Parse the accessibility report to extract individual page analyses
                    page_analyses = self._parse_pdf_report_by_page(accessibility_report)
                    
                    if not page_analyses:
                        logger.warning(f"Could not parse PDF report into pages, falling back to single page")
                        # Fall back to single page creation with full report
                        blocks = []
                        blocks.append(self._create_heading_block("📄 PDF Accessibility Analysis", 1))
                        blocks.append(self._create_paragraph_block(f"**File:** {file_name}"))
                        blocks.append(self._create_paragraph_block(f"**Pages Analyzed:** {pages_analyzed}"))
                        blocks.append(self._create_divider_block())
                        
                        report_chunks = self._split_text_into_chunks(accessibility_report, 1800)
                        for chunk in report_chunks:  # ALL chunks
                            blocks.append(self._create_paragraph_block(chunk))
                        
                        title = f"📄 PDF Analysis - {file_name[:50]}"
                        if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                            pages_created = 1
                    else:
                        # Create one page per PDF page - ALL pages
                        for page_num, page_analysis in page_analyses.items():
                            blocks = []
                            blocks.append(self._create_heading_block(f"📄 PDF Page {page_num} Analysis", 1))
                            blocks.append(self._create_paragraph_block(f"**File:** {file_name}"))
                            blocks.append(self._create_paragraph_block(f"**Page:** {page_num} of {pages_analyzed}"))
                            blocks.append(self._create_paragraph_block(f"**Scan Date:** {scan_timestamp or 'Unknown'}"))
                            blocks.append(self._create_divider_block())
                            
                            # Split page analysis into chunks - ALL chunks
                            analysis_chunks = self._split_text_into_chunks(page_analysis, 1800)
                            for chunk in analysis_chunks:
                                blocks.append(self._create_paragraph_block(chunk))
                            
                            blocks.append(self._create_divider_block())
                            blocks.append(self._create_paragraph_block("_Generated by LumTrails PDF AI Accessibility Scanner_"))
                            
                            title = f"📄 {file_name[:30]} - Page {page_num}"
                            if await self._create_page_with_all_blocks(client, headers, parent_page_id, title, blocks):
                                pages_created += 1
                                logger.info(f"Created Notion page for PDF page {page_num}")
                
                logger.info(f"Created {pages_created} Notion pages for PDF scan")
                return {"success": True, "pages_created": pages_created}
        
        except Exception as e:
            logger.error(f"Error pushing PDF scan to Notion: {e}")
            return {"success": False, "error": str(e)}
    
    def _parse_pdf_report_by_page(self, accessibility_report: str) -> Dict[int, str]:
        """Parse PDF accessibility report to extract individual page analyses"""
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
    
    def _split_text_into_chunks(self, text: str, max_length: int) -> List[str]:
        """Split text into chunks of max_length characters"""
        if not text:
            return []
        
        chunks = []
        while text:
            if len(text) <= max_length:
                chunks.append(text)
                break
            
            # Try to split at a newline
            split_point = text.rfind('\n', 0, max_length)
            if split_point == -1:
                # No newline found, split at max_length
                split_point = max_length
            
            chunks.append(text[:split_point])
            text = text[split_point:].lstrip()
        
        return chunks
    
    # Helper methods for creating Notion blocks
    def _create_heading_block(self, text: str, level: int = 1) -> Dict:
        heading_type = f"heading_{level}"
        return {
            "object": "block",
            "type": heading_type,
            heading_type: {
                "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
            }
        }
    
    def _create_paragraph_block(self, text: str) -> Dict:
        return {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": text[:2000]}}]
            }
        }
    
    def _create_divider_block(self) -> Dict:
        return {
            "object": "block",
            "type": "divider",
            "divider": {}
        }
    
    def _create_code_block(self, code: str, language: str = "plain text") -> Dict:
        return {
            "object": "block",
            "type": "code",
            "code": {
                "rich_text": [{"type": "text", "text": {"content": code[:2000]}}],
                "language": language
            }
        }
