"""
Adapter for transforming scan results from the new unified format to integration-ready data.
Handles extraction of data from the modular web scan structure (v3.0.0).
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Mapping from UI severity levels to axe-core impact values
SEVERITY_TO_IMPACT = {
    'critical': 'critical',
    'high': 'critical',  # High maps to critical in axe-core
    'serious': 'serious',
    'medium': 'serious',  # Medium maps to serious in axe-core
    'moderate': 'moderate',
    'low': 'moderate',    # Low maps to moderate in axe-core
    'minor': 'minor'
}


class WebScanResultsAdapter:
    """Adapter for transforming web scan results from unified format"""
    
    @staticmethod
    def _normalize_severity_filter(severity_filter: List[str]) -> set:
        """
        Normalize severity filter to axe-core impact values.
        Handles both UI values (High, Medium, Low) and axe-core values (critical, serious, moderate, minor).
        """
        normalized = set()
        for severity in severity_filter:
            severity_lower = severity.lower()
            # Map to axe-core impact value
            impact = SEVERITY_TO_IMPACT.get(severity_lower)
            if impact:
                normalized.add(impact)
            else:
                # If not in mapping, try to use as-is (already an axe-core value)
                normalized.add(severity_lower)
        
        logger.info(f"Normalized severity filter from {severity_filter} to {normalized}")
        return normalized
    
    @staticmethod
    def extract_wcag_violations(scan_data: Dict[str, Any], severity_filter: List[str]) -> List[Dict[str, Any]]:
        """
        Extract WCAG compliance violations from axe-core results
        
        Args:
            scan_data: Full scan data dictionary
            severity_filter: List of severity levels to include (e.g., ['High', 'Medium', 'Low'] or ['critical', 'serious', 'moderate', 'minor'])
        
        Returns:
            List of formatted violation dictionaries
        """
        violations = []
        unified_results = scan_data.get('unified_results', {})
        axe_results = unified_results.get('axe', {})
        
        if not axe_results:
            logger.warning("No axe-core results found in unified_results")
            return violations
        
        raw_violations = axe_results.get('violations', [])
        logger.info(f"Found {len(raw_violations)} axe-core violations")
        
        # Normalize severity filter to axe-core impact values
        allowed_impacts = WebScanResultsAdapter._normalize_severity_filter(severity_filter)
        
        for i, violation in enumerate(raw_violations):
            impact = violation.get('impact', 'moderate')
            
            # Check if this impact level passes the filter
            if impact not in allowed_impacts:
                logger.debug(f"Skipping violation with impact '{impact}' - not in allowed impacts {allowed_impacts}")
                continue
            
            nodes = violation.get('nodes', [])
            
            if nodes:
                # Create violation entry for each node
                for j, node in enumerate(nodes):
                    violations.append({
                        'tool': 'Axe-core',
                        'id': violation.get('id', ''),
                        'impact': impact,
                        'description': violation.get('description', ''),
                        'help': violation.get('help', ''),
                        'helpUrl': violation.get('helpUrl', ''),
                        'nodes': [node],
                        'unique_id': f"axe-{violation.get('id', 'unknown')}-{i}-{j}"
                    })
            else:
                # General violation without specific nodes
                violations.append({
                    'tool': 'Axe-core',
                    'id': violation.get('id', ''),
                    'impact': impact,
                    'description': violation.get('description', ''),
                    'help': violation.get('help', ''),
                    'helpUrl': violation.get('helpUrl', ''),
                    'nodes': [],
                    'unique_id': f"axe-{violation.get('id', 'unknown')}-{i}-general"
                })
        
        logger.info(f"Extracted {len(violations)} WCAG violations after filtering")
        return violations
    
    @staticmethod
    def extract_html_errors(scan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract HTML validation errors from Nu HTML Checker results
        
        Args:
            scan_data: Full scan data dictionary
        
        Returns:
            List of formatted HTML error dictionaries
        """
        html_errors = []
        unified_results = scan_data.get('unified_results', {})
        nu_results = unified_results.get('nu', {})
        
        if not nu_results:
            logger.warning("No Nu HTML Checker results found in unified_results")
            return html_errors
        
        # Nu HTML Checker returns all messages in a single 'messages' array
        all_messages = nu_results.get('messages', [])
        logger.info(f"Found {len(all_messages)} HTML validation messages")
        
        # Process all messages
        for i, msg in enumerate(all_messages):
            msg_type = msg.get('type', 'info')
            html_errors.append({
                'type': msg_type,
                'message': msg.get('message', ''),
                'extract': msg.get('extract', ''),
                'line': msg.get('line', 0),
                'column': msg.get('column', 0),
                'hilite_start': msg.get('hilite_start', 0),
                'hilite_length': msg.get('hilite_length', 0),
                'unique_id': f"html-{msg_type}-{i}"
            })
        
        logger.info(f"Extracted {len(html_errors)} total HTML validation issues")
        return html_errors
    
    @staticmethod
    def extract_link_issues(scan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract broken/problematic links from link checker results
        
        Args:
            scan_data: Full scan data dictionary
        
        Returns:
            List of formatted link issue dictionaries with state info
        """
        link_issues = []
        unified_results = scan_data.get('unified_results', {})
        links_results = unified_results.get('links', {})
        
        if not links_results:
            logger.warning("No Linkinator results found in unified_results")
            return link_issues
        
        # Support all link state formats
        # New format: invalid_links, timeout_links, unreachable_links
        # Old format: broken_links, error_links, warning_links
        
        invalid_links = links_results.get('invalid_links', [])
        timeout_links = links_results.get('timeout_links', [])
        unreachable_links = links_results.get('unreachable_links', [])
        
        # Fallback to old format if new format not available
        if not invalid_links:
            invalid_links = links_results.get('broken_links', [])
        if not timeout_links and not unreachable_links:
            # Old error_links may include both timeout and unreachable
            timeout_links = links_results.get('error_links', [])
        
        logger.info(f"Found {len(invalid_links)} invalid links, {len(timeout_links)} timeout links, {len(unreachable_links)} unreachable links")
        
        # Process invalid links (HTTP 4xx/5xx errors - truly broken)
        for i, link in enumerate(invalid_links):
            error_reason = link.get('error_reason', '')
            if not error_reason and link.get('status', 0) > 0:
                error_reason = f"HTTP {link.get('status')}"
            link_issues.append({
                'url': link.get('url', ''),
                'status': link.get('status', 0),
                'state': 'invalid',
                'text': link.get('text', ''),
                'error_reason': error_reason,
                'unique_id': f"link-invalid-{i}"
            })
        
        # Process timeout links (no response received)
        for i, link in enumerate(timeout_links):
            link_issues.append({
                'url': link.get('url', ''),
                'status': link.get('status', 0),
                'state': 'timeout',
                'text': link.get('text', ''),
                'error_reason': link.get('error_reason', 'Request timed out'),
                'unique_id': f"link-timeout-{i}"
            })
        
        # Process unreachable links (connection failed, DNS error, etc.)
        for i, link in enumerate(unreachable_links):
            link_issues.append({
                'url': link.get('url', ''),
                'status': link.get('status', 0),
                'state': 'unreachable',
                'text': link.get('text', ''),
                'error_reason': link.get('error_reason', 'Connection failed'),
                'unique_id': f"link-unreachable-{i}"
            })
        
        logger.info(f"Extracted {len(link_issues)} total link issues")
        return link_issues
    
    @staticmethod
    def extract_axtree_data(scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract accessibility tree data from axTree results
        
        Args:
            scan_data: Full scan data dictionary
        
        Returns:
            Dictionary containing accessibility tree data
        """
        unified_results = scan_data.get('unified_results', {})
        axtree_results = unified_results.get('axTree', {})
        
        if not axtree_results or axtree_results.get('tree') is None:
            logger.warning("No axTree results found in unified_results")
            return {'has_data': False, 'node_count': 0}
        
        tree = axtree_results.get('tree', {})
        
        # Count nodes recursively in the tree
        def count_nodes(node):
            if not node:
                return 0
            count = 1
            children = node.get('children', [])
            for child in children:
                count += count_nodes(child)
            return count
        
        node_count = count_nodes(tree)
        logger.info(f"Extracted axTree data with {node_count} nodes")
        
        return {
            'tree': tree,
            'role': axtree_results.get('role', tree.get('role') if tree else None),
            'name': axtree_results.get('name', tree.get('name') if tree else None),
            'node_count': node_count,
            'has_data': tree is not None
        }
    
    @staticmethod
    def extract_layout_issues(scan_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract layout testing issues from Galen results
        
        Args:
            scan_data: Full scan data dictionary
        
        Returns:
            List of formatted layout issue dictionaries
        """
        layout_issues = []
        unified_results = scan_data.get('unified_results', {})
        galen_results = unified_results.get('galen', {})
        
        if not galen_results:
            logger.warning("No Galen results found in unified_results")
            return layout_issues
        
        # Galen results contain viewport_results with layout issues
        raw_issues = galen_results.get('layout_issues', [])
        viewport_results = galen_results.get('viewport_results', [])
        
        logger.info(f"Found {len(raw_issues)} layout issues across {len(viewport_results)} viewports")
        
        for i, issue in enumerate(raw_issues):
            layout_issues.append({
                'object': issue.get('object', ''),
                'spec': issue.get('spec', ''),
                'message': issue.get('message', ''),
                'area': issue.get('area', {}),
                'viewport': issue.get('viewport', {}),
                'unique_id': f"layout-{i}"
            })
        
        # Also report viewport-level information (overflow, etc.)
        for i, vp_result in enumerate(viewport_results):
            if vp_result.get('has_overflow'):
                layout_issues.append({
                    'object': 'viewport',
                    'spec': 'overflow-check',
                    'message': f"Horizontal overflow detected at {vp_result['viewport']['width']}x{vp_result['viewport']['height']}",
                    'viewport': vp_result['viewport'],
                    'metrics': vp_result.get('metrics', {}),
                    'unique_id': f"layout-overflow-{i}"
                })
        
        logger.info(f"Extracted {len(layout_issues)} layout issues")
        return layout_issues
    

