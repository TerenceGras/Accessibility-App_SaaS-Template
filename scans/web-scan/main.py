"""
LumTrails Web Accessibility Scanner
====================================
Zero-overlap multi-module accessibility scanner implementing:
- axe-core (Element-level WCAG violations)
- Nu Html Checker (Markup validation)
- Playwright AX Tree (Accessibility tree snapshot)
- Galen (Layout testing)
- Linkinator (Link health check)

All modules run in parallel for maximum performance.
Results stored permanently in Firebase Storage.
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, HttpUrl, Field
from playwright.async_api import async_playwright, Browser, Page
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from enum import Enum
import asyncio
import logging
import os
import json
import httpx
import subprocess
import tempfile
import re

# Google Auth for service-to-service authentication
import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import id_token as google_id_token
import google.auth.transport.requests

# Import web scan storage manager
try:
    from web_storage import web_storage_manager
    STORAGE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Web scan storage not available: {e}")
    STORAGE_AVAILABLE = False
    web_storage_manager = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LumTrails Web Accessibility Scanner",
    description="Multi-module zero-overlap accessibility scanner",
    version="3.0.0"
)

# Configuration
PORT = int(os.getenv("PORT", 8080))
API_URL = os.getenv("API_URL", "")
NU_CHECKER_URL = os.getenv("NU_CHECKER_URL", "https://validator.nu")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# CORS middleware - Restrict to internal services in production
if ENVIRONMENT == "production":
    cors_origins = [
        os.getenv("MAIN_API_URL", ""),
        os.getenv("EXTERNAL_API_URL", ""),
    ]
else:
    cors_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Security headers middleware
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)


# =============================================================================
# OIDC Token for Service-to-Service Authentication
# =============================================================================

def get_oidc_token(audience: str) -> str:
    """
    Get an OIDC identity token for authenticating to another Cloud Run service.
    Uses the default service account's identity.
    """
    try:
        # Get credentials from the default service account
        credentials, project = google.auth.default()
        
        # Create a new request for fetching the token
        auth_req = google.auth.transport.requests.Request()
        
        # Fetch an ID token for the target audience (the API URL)
        token = google_id_token.fetch_id_token(auth_req, audience)
        
        logger.info(f"Successfully fetched OIDC token for audience: {audience}")
        return token
    except Exception as e:
        logger.error(f"Failed to fetch OIDC token: {e}")
        raise


# SSRF Protection - Block internal/private URLs
import ipaddress
from urllib.parse import urlparse

BLOCKED_HOSTS = {
    'localhost', '127.0.0.1', '0.0.0.0',
    '169.254.169.254',  # GCP/AWS metadata server
    'metadata.google.internal',
}

BLOCKED_PREFIXES = [
    '10.', '172.16.', '172.17.', '172.18.', '172.19.',
    '172.20.', '172.21.', '172.22.', '172.23.', '172.24.',
    '172.25.', '172.26.', '172.27.', '172.28.', '172.29.',
    '172.30.', '172.31.', '192.168.',
]

def validate_scan_url(url: str) -> tuple[bool, str]:
    """
    Validate URL is safe to scan (not internal/private).
    Returns (is_valid, error_message)
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname.lower() if parsed.hostname else ''
        
        # Block internal/private hosts
        if host in BLOCKED_HOSTS:
            return False, f"Blocked host: {host}"
        
        for prefix in BLOCKED_PREFIXES:
            if host.startswith(prefix):
                return False, f"Blocked private IP range: {host}"
        
        # Block private IP ranges
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local:
                return False, f"Private/loopback IP not allowed: {host}"
        except ValueError:
            pass  # Not an IP, continue validation
        
        # Only allow http/https
        if parsed.scheme not in ('http', 'https'):
            return False, f"Only http/https schemes allowed, got: {parsed.scheme}"
        
        return True, ""
    except Exception as e:
        return False, f"URL validation error: {str(e)}"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ScanModule(str, Enum):
    """Available scan modules"""
    AXE = "axe"
    NU = "nu"
    AX_TREE = "axTree"
    GALEN = "galen"
    LINKS = "links"


class ScanRequest(BaseModel):
    """Request model for web scan"""
    url: HttpUrl
    modules: Optional[List[str]] = Field(
        default=[m.value for m in ScanModule],
        description="List of modules to run. If empty, runs all modules."
    )
    viewport_width: Optional[int] = Field(default=1920, description="Browser viewport width")
    viewport_height: Optional[int] = Field(default=1080, description="Browser viewport height")
    galen_breakpoints: Optional[List[Dict[str, int]]] = Field(
        default=[
            {"width": 320, "height": 568},   # Mobile
            {"width": 768, "height": 1024},  # Tablet
            {"width": 1920, "height": 1080}  # Desktop
        ],
        description="Viewport sizes for Galen layout testing"
    )
    link_depth: Optional[int] = Field(default=1, description="Link crawl depth (0=current page only)")
    timeout: Optional[int] = Field(default=120000, description="Page load timeout in ms")


class CloudTaskPayload(BaseModel):
    """Cloud Task payload model"""
    task_id: str
    url: str
    user_id: str
    user_email: str
    created_at: str
    modules: Optional[List[str]] = None
    callback_url: Optional[str] = None
    is_external_api: Optional[bool] = False
    credits_reserved: Optional[bool] = False
    credits_required: Optional[int] = None


class ScanResponse(BaseModel):
    """Complete scan response"""
    url: str
    timestamp: str
    modules_executed: List[str]
    scan_duration_ms: int
    axe: Optional[Dict[str, Any]] = None
    nu: Optional[Dict[str, Any]] = None
    axTree: Optional[Dict[str, Any]] = None
    galen: Optional[Dict[str, Any]] = None
    links: Optional[Dict[str, Any]] = None
    meta: Dict[str, Any]


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: str
    version: str


# ============================================================================
# SCANNER MODULES
# ============================================================================

class AxeScanner:
    """axe-core element-level WCAG violation detection"""
    
    @staticmethod
    async def scan(page: Page) -> Dict[str, Any]:
        """Run axe-core scan on the page"""
        try:
            # Inject axe-core
            with open('/app/axe.min.js', 'r') as f:
                axe_source = f.read()
            
            await page.evaluate(axe_source)
            
            # Run axe scan
            results = await page.evaluate("""
                async () => {
                    const results = await axe.run();
                    return {
                        violations: results.violations.map(v => ({
                            id: v.id,
                            impact: v.impact,
                            tags: v.tags,
                            description: v.description,
                            help: v.help,
                            helpUrl: v.helpUrl,
                            nodes: v.nodes.map(n => ({
                                target: n.target,
                                html: n.html,
                                impact: n.impact,
                                failureSummary: n.failureSummary
                            }))
                        })),
                        passes: results.passes.map(p => ({
                            id: p.id,
                            tags: p.tags,
                            description: p.description,
                            help: p.help,
                            nodes: p.nodes.map(n => ({
                                target: n.target,
                                html: n.html
                            }))
                        })),
                        incomplete: results.incomplete.map(i => ({
                            id: i.id,
                            impact: i.impact,
                            tags: i.tags,
                            description: i.description,
                            help: i.help,
                            nodes: i.nodes.map(n => ({
                                target: n.target,
                                html: n.html
                            }))
                        })),
                        inapplicable: results.inapplicable.map(i => ({
                            id: i.id,
                            tags: i.tags,
                            description: i.description
                        }))
                    };
                }
            """)
            
            return results
            
        except Exception as e:
            logger.error(f"Axe scan failed: {str(e)}")
            return {"error": str(e), "violations": [], "passes": [], "incomplete": [], "inapplicable": []}


class NuValidator:
    """Nu HTML Checker - Markup conformance validation"""
    
    @staticmethod
    async def scan(page: Page) -> Dict[str, Any]:
        """Validate HTML markup using Nu validator"""
        try:
            # Get page HTML
            html_content = await page.content()
            
            # Call Nu validator API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{NU_CHECKER_URL}/?out=json",
                    headers={"Content-Type": "text/html; charset=utf-8"},
                    content=html_content.encode('utf-8')
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Format messages with enhanced context
                    messages = []
                    for msg in result.get('messages', []):
                        enhanced_msg = {
                            "type": msg.get('type'),
                            "message": msg.get('message'),
                            "extract": msg.get('extract'),
                            "line": msg.get('lastLine'),
                            "column": msg.get('lastColumn'),
                            "hilite_start": msg.get('hiliteStart'),
                            "hilite_length": msg.get('hiliteLength')
                        }
                        
                        # Add subType if available (warning, fatal, etc.)
                        if msg.get('subType'):
                            enhanced_msg['subType'] = msg.get('subType')
                        
                        # Add detailed location range if available
                        if msg.get('firstLine'):
                            enhanced_msg['first_line'] = msg.get('firstLine')
                        if msg.get('firstColumn'):
                            enhanced_msg['first_column'] = msg.get('firstColumn')
                        if msg.get('lastLine'):
                            enhanced_msg['last_line'] = msg.get('lastLine')
                        if msg.get('lastColumn'):
                            enhanced_msg['last_column'] = msg.get('lastColumn')
                        
                        # Add offset if available (helps locate exact character in extract)
                        if msg.get('offset') is not None:
                            enhanced_msg['offset'] = msg.get('offset')
                        
                        messages.append(enhanced_msg)
                    
                    return {
                        "messages": messages,
                        "errors": [m for m in messages if m['type'] == 'error'],
                        "warnings": [m for m in messages if m['type'] in ['warning', 'info']]
                    }
                else:
                    logger.error(f"Nu validator returned status {response.status_code}")
                    return {"error": f"Validator error: {response.status_code}", "messages": []}
                    
        except Exception as e:
            logger.error(f"Nu validation failed: {str(e)}")
            return {"error": str(e), "messages": []}


class AxTreeExtractor:
    """Playwright Accessibility Tree extraction"""
    
    @staticmethod
    async def scan(page: Page) -> Dict[str, Any]:
        """Extract accessibility tree snapshot"""
        try:
            # Get accessibility snapshot
            snapshot = await page.accessibility.snapshot()
            
            if snapshot is None:
                return {"tree": None, "note": "No accessibility tree available"}
            
            return {
                "tree": snapshot,
                "role": snapshot.get('role'),
                "name": snapshot.get('name'),
                "children_count": len(snapshot.get('children', []))
            }
            
        except Exception as e:
            logger.error(f"AX Tree extraction failed: {str(e)}")
            return {"error": str(e), "tree": None}


class GalenTester:
    """Galen Framework - Layout and visual testing"""
    
    @staticmethod
    async def scan(page: Page, breakpoints: List[Dict[str, int]]) -> Dict[str, Any]:
        """Test layout across multiple viewports"""
        try:
            viewport_results = []
            
            for bp in breakpoints:
                width = bp.get('width', 1920)
                height = bp.get('height', 1080)
                
                # Set viewport
                await page.set_viewport_size({"width": width, "height": height})
                await asyncio.sleep(0.5)  # Allow reflow
                
                # Capture layout metrics
                metrics = await page.evaluate("""
                    () => {
                        const body = document.body;
                        const html = document.documentElement;
                        
                        return {
                            viewport: {
                                width: window.innerWidth,
                                height: window.innerHeight
                            },
                            scroll: {
                                width: Math.max(body.scrollWidth, html.scrollWidth),
                                height: Math.max(body.scrollHeight, html.scrollHeight)
                            },
                            hasHorizontalScroll: body.scrollWidth > window.innerWidth,
                            hasVerticalScroll: body.scrollHeight > window.innerHeight,
                            elements: {
                                overlapping: document.querySelectorAll('[style*="z-index"]').length,
                                hidden: document.querySelectorAll('[hidden], [aria-hidden="true"]').length,
                                visible: document.querySelectorAll('*:not([hidden]):not([aria-hidden="true"])').length
                            }
                        };
                    }
                """)
                
                # Take screenshot for reference
                screenshot = await page.screenshot(full_page=False)
                
                viewport_results.append({
                    "viewport": {"width": width, "height": height},
                    "metrics": metrics,
                    "has_overflow": metrics.get('hasHorizontalScroll', False),
                    "screenshot_size": len(screenshot)
                })
            
            return {
                "viewport_results": viewport_results,
                "breakpoints_tested": len(breakpoints),
                "layout_issues": []  # Placeholder for more sophisticated layout checking
            }
            
        except Exception as e:
            logger.error(f"Galen testing failed: {str(e)}")
            return {"error": str(e), "viewport_results": []}


class LinkChecker:
    """Linkinator - Link health validation with robust parallel checking
    
    States:
    - valid: Link responded with a success status (2xx, 3xx) or is behind bot protection (403/429)
    - invalid: Link responded with an error status (4xx, 5xx excluding 403/429) - the link is broken
    - timeout: Link did not respond within the timeout period - server unreachable or slow
    - unreachable: Connection failed (DNS error, refused, etc.) - cannot determine if link is valid
    """
    
    MAX_CONCURRENT_CHECKS = 50  # Limit concurrent requests to avoid overwhelming servers
    REQUEST_TIMEOUT = 20.0  # Timeout per request in seconds (increased for slow servers)
    MAX_RETRIES = 3  # Number of retries for failed requests (increased for reliability)
    
    # Comprehensive browser-like headers to maximize success rate
    BROWSER_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9,fr;q=0.8,de;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
    }
    
    @staticmethod
    def _is_valid_url(url: str) -> tuple[bool, str]:
        """Validate URL format before making request.
        Returns (is_valid, error_message)
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Must have scheme and netloc
            if not parsed.scheme:
                return False, "Missing URL scheme (http/https)"
            if not parsed.netloc:
                return False, "Missing domain"
            if parsed.scheme not in ('http', 'https'):
                return False, f"Unsupported scheme: {parsed.scheme}"
            
            # Check for malformed URLs
            if ' ' in url and '%20' not in url:
                return False, "URL contains unencoded spaces"
            
            return True, ""
        except Exception as e:
            return False, f"Invalid URL format: {str(e)[:50]}"
    
    @staticmethod
    async def scan(page: Page, depth: int = 1) -> Dict[str, Any]:
        """Check link health on the page with robust parallel requests
        
        Uses Playwright/page only to extract links (not to check them).
        All link validation is done using httpx with browser-like headers.
        
        Returns links categorized as:
        - valid_links: Successfully reachable links (2xx/3xx or 403/429 bot protection)
        - invalid_links: Links that returned error responses (4xx/5xx excluding 403/429)
        - timeout_links: Links that did not respond in time
        - unreachable_links: Links where connection failed (DNS error, refused, etc.)
        """
        try:
            # Extract all links from the page using Playwright
            links = await page.evaluate("""
                () => {
                    const anchors = Array.from(document.querySelectorAll('a[href]'));
                    return anchors.map(a => ({
                        href: a.href,
                        text: a.textContent.trim(),
                        rel: a.rel,
                        target: a.target
                    }));
                }
            """)
            
            # Filter and deduplicate links
            checked_urls: Set[str] = set()
            links_to_check = []
            skipped_links = []
            
            for link in links[:100]:  # Limit to first 100 links
                url = link['href']
                if url in checked_urls:
                    continue
                if url.startswith(('mailto:', 'tel:', 'javascript:', 'data:', '#')):
                    continue
                
                # Validate URL format before adding to check list
                is_valid, error_msg = LinkChecker._is_valid_url(url)
                if not is_valid:
                    skipped_links.append({
                        "url": url,
                        "status": 0,
                        "state": "invalid",
                        "text": link['text'][:100] if link['text'] else "",
                        "error_reason": error_msg
                    })
                    checked_urls.add(url)
                    continue
                
                checked_urls.add(url)
                links_to_check.append(link)
            
            # Semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(LinkChecker.MAX_CONCURRENT_CHECKS)
            
            async def check_single_link(link: Dict, client: httpx.AsyncClient) -> Dict:
                """Check a single link with robust retry logic and multiple strategies
                
                Returns:
                - state: 'valid' | 'invalid' | 'timeout' | 'unreachable'
                - status: HTTP status code (0 if no response)
                """
                async with semaphore:
                    url = link['href']
                    last_error = None
                    last_status = 0
                    
                    for attempt in range(LinkChecker.MAX_RETRIES + 1):
                        try:
                            # Strategy 1: Try HEAD first (faster, less bandwidth)
                            try:
                                response = await client.head(
                                    url, 
                                    timeout=LinkChecker.REQUEST_TIMEOUT,
                                    follow_redirects=True
                                )
                                status = response.status_code
                                last_status = status
                                
                                # If HEAD returns 405, 403, or 503, try GET
                                if status in (405, 403, 503, 500):
                                    response = await client.get(
                                        url, 
                                        timeout=LinkChecker.REQUEST_TIMEOUT,
                                        follow_redirects=True
                                    )
                                    status = response.status_code
                                    last_status = status
                            except httpx.HTTPStatusError as e:
                                status = e.response.status_code
                                last_status = status
                            
                            # Categorize status codes
                            # Valid: 2xx and 3xx responses
                            if status < 400:
                                return {
                                    "url": url,
                                    "status": status,
                                    "state": "valid",
                                    "text": link['text'][:100] if link['text'] else ""
                                }
                            
                            # Rate limited (429) or Forbidden (403) - treat as valid (bot detection)
                            # Many sites block automated requests but the link is actually valid
                            elif status in (403, 429):
                                return {
                                    "url": url,
                                    "status": status,
                                    "state": "valid",
                                    "text": link['text'][:100] if link['text'] else "",
                                    "note": "Bot protection detected - link likely valid"
                                }
                            
                            # 503 Service Unavailable - temporary issue, treat as unreachable
                            elif status == 503:
                                return {
                                    "url": url,
                                    "status": status,
                                    "state": "unreachable",
                                    "text": link['text'][:100] if link['text'] else "",
                                    "error_reason": "Service temporarily unavailable (503)"
                                }
                            
                            # Invalid: 4xx and 5xx responses (excluding 403/429/503)
                            else:
                                return {
                                    "url": url,
                                    "status": status,
                                    "state": "invalid",
                                    "text": link['text'][:100] if link['text'] else "",
                                    "error_reason": f"HTTP {status}"
                                }
                                
                        except httpx.TimeoutException:
                            last_error = "timeout"
                            if attempt < LinkChecker.MAX_RETRIES:
                                await asyncio.sleep(1.0 * (attempt + 1))
                                continue
                        except httpx.ConnectError as e:
                            error_str = str(e)
                            # Check for specific connection errors
                            if "getaddrinfo failed" in error_str or "Name or service not known" in error_str:
                                last_error = "DNS resolution failed"
                            elif "Connection refused" in error_str:
                                last_error = "Connection refused"
                            elif "SSL" in error_str or "certificate" in error_str.lower():
                                last_error = "SSL/TLS error"
                            else:
                                last_error = "Connection failed"
                            if attempt < LinkChecker.MAX_RETRIES:
                                await asyncio.sleep(1.0 * (attempt + 1))
                                continue
                        except httpx.TooManyRedirects:
                            return {
                                "url": url,
                                "status": 0,
                                "state": "invalid",
                                "text": link['text'][:100] if link['text'] else "",
                                "error_reason": "Too many redirects (redirect loop)"
                            }
                        except httpx.HTTPStatusError as e:
                            last_status = e.response.status_code
                            if last_status in (403, 429):
                                return {
                                    "url": url,
                                    "status": last_status,
                                    "state": "valid",
                                    "text": link['text'][:100] if link['text'] else "",
                                    "note": "Bot protection detected"
                                }
                            last_error = f"HTTP {last_status}"
                            if attempt < LinkChecker.MAX_RETRIES:
                                await asyncio.sleep(1.0 * (attempt + 1))
                                continue
                        except Exception as e:
                            error_str = str(e)
                            # Handle URL validation errors from httpx
                            if "URL" in error_str or "path" in error_str.lower():
                                return {
                                    "url": url,
                                    "status": 0,
                                    "state": "invalid",
                                    "text": link['text'][:100] if link['text'] else "",
                                    "error_reason": "Malformed URL"
                                }
                            last_error = error_str[:100] if len(error_str) > 100 else error_str
                            if attempt < LinkChecker.MAX_RETRIES:
                                await asyncio.sleep(1.0 * (attempt + 1))
                                continue
                    
                    # All retries exhausted - categorize by error type
                    if last_error == "timeout":
                        return {
                            "url": url,
                            "status": 0,
                            "state": "timeout",
                            "text": link['text'][:100] if link['text'] else "",
                            "error_reason": "Request timed out after multiple attempts"
                        }
                    elif last_error in ("DNS resolution failed", "Connection refused", "Connection failed", "SSL/TLS error"):
                        # Connection-level failures - can't determine if link is valid
                        return {
                            "url": url,
                            "status": 0,
                            "state": "unreachable",
                            "text": link['text'][:100] if link['text'] else "",
                            "error_reason": last_error
                        }
                    else:
                        return {
                            "url": url,
                            "status": last_status,
                            "state": "invalid",
                            "text": link['text'][:100] if link['text'] else "",
                            "error_reason": last_error or "Unknown error"
                        }
            
            # Execute all checks in parallel
            # Try with HTTP/2 first, fall back to HTTP/1.1 if needed
            try:
                async with httpx.AsyncClient(
                    timeout=LinkChecker.REQUEST_TIMEOUT,
                    follow_redirects=True,
                    headers=LinkChecker.BROWSER_HEADERS,
                    http2=True  # Enable HTTP/2 for better compatibility
                ) as client:
                    tasks = [check_single_link(link, client) for link in links_to_check]
                    link_results_raw = await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as http2_error:
                logger.warning(f"HTTP/2 client failed, falling back to HTTP/1.1: {http2_error}")
                async with httpx.AsyncClient(
                    timeout=LinkChecker.REQUEST_TIMEOUT,
                    follow_redirects=True,
                    headers=LinkChecker.BROWSER_HEADERS,
                    http2=False  # Fallback to HTTP/1.1
                ) as client:
                    tasks = [check_single_link(link, client) for link in links_to_check]
                    link_results_raw = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and keep only valid results
            link_results = [r for r in link_results_raw if isinstance(r, dict)]
            
            # Add any skipped links (URL validation failures)
            link_results.extend(skipped_links)
            
            # Categorize results by state
            valid_links = [l for l in link_results if l['state'] == 'valid']
            invalid_links = [l for l in link_results if l['state'] == 'invalid']
            timeout_links = [l for l in link_results if l['state'] == 'timeout']
            unreachable_links = [l for l in link_results if l['state'] == 'unreachable']
            
            return {
                "links": link_results,
                "total_links": len(links),
                "checked_links": len(link_results),
                "valid_links": valid_links,
                "invalid_links": invalid_links,
                "timeout_links": timeout_links,
                "unreachable_links": unreachable_links,
                # Keep backward compatibility
                "broken_links": invalid_links,
                "error_links": timeout_links + unreachable_links,  # Include unreachable in errors
                "warning_links": []  # No longer used, kept for compatibility
            }
            
        except Exception as e:
            logger.error(f"Link checking failed: {str(e)}")
            return {"error": str(e), "links": []}


# ============================================================================
# MAIN SCANNER ORCHESTRATOR
# ============================================================================

class WebScanner:
    """Main orchestrator for parallel module execution"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
    
    async def initialize_browser(self):
        """Initialize Playwright browser"""
        if not self.browser:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
    
    async def close_browser(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
            self.browser = None
    
    async def scan(self, request: ScanRequest) -> ScanResponse:
        """Execute scan with selected modules in parallel"""
        start_time = datetime.now()
        url = str(request.url)
        
        # SSRF Protection: Validate URL before scanning
        is_valid, error_msg = validate_scan_url(url)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid or blocked URL: {error_msg}")
        
        logger.info(f"Starting scan for URL: {url}")
        
        # Initialize browser
        await self.initialize_browser()
        
        # Create page
        context = await self.browser.new_context(
            viewport={"width": request.viewport_width, "height": request.viewport_height}
        )
        page = await context.new_page()
        
        try:
            # Navigate to URL with more lenient wait strategy
            # Use 'domcontentloaded' instead of 'networkidle' for faster loading
            # networkidle can timeout on sites with continuous network activity
            logger.info(f"Navigating to {url} with {request.timeout}ms timeout...")
            try:
                await page.goto(url, timeout=request.timeout, wait_until="domcontentloaded")
                logger.info(f"Successfully loaded {url} (DOM ready)")
                # Give it a moment for dynamic content to load
                await asyncio.sleep(2)
            except Exception as nav_error:
                logger.error(f"Navigation failed for {url}: {str(nav_error)}")
                # Try one more time with an even more lenient strategy
                logger.info(f"Retrying navigation with 'load' wait strategy...")
                await page.goto(url, timeout=request.timeout, wait_until="load")
                logger.info(f"Successfully loaded {url} (basic load)")
                await asyncio.sleep(1)
            
            # Prepare module tasks
            tasks = {}
            modules_to_run = request.modules or [m.value for m in ScanModule]
            
            if ScanModule.AXE.value in modules_to_run:
                tasks['axe'] = AxeScanner.scan(page)
            
            if ScanModule.NU.value in modules_to_run:
                tasks['nu'] = NuValidator.scan(page)
            
            if ScanModule.AX_TREE.value in modules_to_run:
                tasks['axTree'] = AxTreeExtractor.scan(page)
            
            if ScanModule.GALEN.value in modules_to_run:
                tasks['galen'] = GalenTester.scan(page, request.galen_breakpoints)
            
            if ScanModule.LINKS.value in modules_to_run:
                tasks['links'] = LinkChecker.scan(page, request.link_depth)
            
            # Execute all tasks in parallel
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            logger.info(f"Scan completed for {url}")
            
            # Map results to module names
            scan_results = {}
            for i, module_name in enumerate(tasks.keys()):
                result = results[i]
                if isinstance(result, Exception):
                    logger.error(f"Module {module_name} failed: {str(result)}")
                    scan_results[module_name] = {"error": str(result)}
                else:
                    scan_results[module_name] = result
            
            # Calculate duration
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Build response
            response = ScanResponse(
                url=url,
                timestamp=start_time.isoformat(),
                modules_executed=list(tasks.keys()),
                scan_duration_ms=duration_ms,
                axe=scan_results.get('axe'),
                nu=scan_results.get('nu'),
                axTree=scan_results.get('axTree'),
                galen=scan_results.get('galen'),
                links=scan_results.get('links'),
                meta={
                    "viewport": {"width": request.viewport_width, "height": request.viewport_height},
                    "user_agent": await page.evaluate("navigator.userAgent"),
                    "page_title": await page.title(),
                    "final_url": page.url
                }
            )
            
            return response
            
        finally:
            await page.close()
            await context.close()


# ============================================================================
# FASTAPI ENDPOINTS
# ============================================================================

# Global scanner instance
scanner = WebScanner()


@app.on_event("startup")
async def startup_event():
    """Initialize browser on startup"""
    logger.info("Initializing web scanner...")
    await scanner.initialize_browser()
    logger.info("Web scanner ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down web scanner...")
    await scanner.close_browser()
    logger.info("Web scanner stopped")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="web-scanner",
        version="3.0.0"
    )


@app.post("/scan")
async def scan_endpoint(payload: CloudTaskPayload):
    """
    Process scan from Cloud Task and store result in API
    This endpoint is called by Cloud Tasks
    """
    try:
        logger.info(f"Processing Cloud Task scan for {payload.url}")
        logger.info(f"Task ID: {payload.task_id}, Modules: {payload.modules}")
        
        # Build scan request (run ALL modules by default)
        try:
            request = ScanRequest(
                url=payload.url,
                modules=payload.modules or [m.value for m in ScanModule]
            )
            logger.info(f"ScanRequest created successfully with modules: {request.modules}")
        except Exception as req_error:
            logger.error(f"Failed to create ScanRequest: {str(req_error)}")
            logger.error(f"Payload data: url={payload.url}, modules={payload.modules}")
            raise
        
        # Execute scan
        logger.info(f"Starting scan execution for {payload.url}")
        scan_result = await scanner.scan(request)
        logger.info(f"Scan completed successfully. Modules executed: {scan_result.modules_executed}")
        
        # Transform to complete result format - all scan data in unified_results
        full_result = {
            "id": payload.task_id,
            "url": str(scan_result.url),
            "timestamp": scan_result.timestamp,
            "testEngine": {
                "name": "LumTrails Multi-Module Scanner",
                "version": "3.0.0",
                "modules": scan_result.modules_executed
            },
            "unified_results": {
                "scan_format_version": "3.0.0",
                "modules_executed": scan_result.modules_executed,
                "scan_duration_ms": scan_result.scan_duration_ms,
                "axe": scan_result.axe,
                "nu": scan_result.nu,
                "axTree": scan_result.axTree,
                "galen": scan_result.galen,
                "links": scan_result.links,
                "meta": scan_result.meta
            },
            "scanDuration": scan_result.scan_duration_ms,
            "status": "completed",
            "user_id": payload.user_id,
            "user_email": payload.user_email
        }
        
        result_size = len(json.dumps(full_result))
        logger.info(f"Full scan result size: ~{result_size} bytes")
        
        # Upload full result to Firebase Storage
        if not STORAGE_AVAILABLE or not web_storage_manager:
            logger.error("Storage manager not available")
            raise HTTPException(status_code=500, detail="Storage service unavailable")
        
        storage_url = await web_storage_manager.store_scan_result(
            scan_data=full_result,
            user_id=payload.user_id,
            scan_id=payload.task_id
        )
        
        if not storage_url:
            logger.error("Failed to upload scan result to Firebase Storage")
            raise HTTPException(status_code=500, detail="Failed to store scan result in storage")
        
        logger.info(f"Scan result uploaded to Firebase Storage: {storage_url}")
        
        # Create minimal metadata for Firestore
        metadata = {
            "id": payload.task_id,
            "url": str(scan_result.url),
            "timestamp": scan_result.timestamp,
            "status": "completed",
            "user_id": payload.user_id,
            "user_email": payload.user_email,
            "storage_url": storage_url,
            "storage_path": f"web-scan-results/{payload.user_id}/{payload.task_id}.json",
            "scan_format_version": "3.0.0",
            "modules_executed": scan_result.modules_executed,
            "scan_duration_ms": scan_result.scan_duration_ms,
            "created_at": datetime.utcnow().isoformat(),
            "credits_reserved": payload.credits_reserved,
            "credits_required": payload.credits_required,
            # Summary counts for quick overview
            "summary": {
                # Count actual violation nodes, not categories
                "total_violations": sum(len(v.get("nodes", [])) for v in scan_result.axe.get("violations", [])) if scan_result.axe else 0,
                "total_passes": sum(len(p.get("nodes", [])) for p in scan_result.axe.get("passes", [])) if scan_result.axe else 0,
                "total_html_errors": len([m for m in scan_result.nu.get("messages", []) if m.get("type") == "error"]) if scan_result.nu else 0,
                "total_broken_links": len([l for l in scan_result.links.get("links", []) if l.get("state") == "broken"]) if scan_result.links else 0
            }
        }
        
        # Send metadata to API for Firestore storage
        # Get OIDC token for service-to-service authentication
        try:
            oidc_token = get_oidc_token(API_URL)
            auth_headers = {"Authorization": f"Bearer {oidc_token}"}
        except Exception as token_error:
            logger.error(f"Failed to get OIDC token: {token_error}")
            auth_headers = {}
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            store_response = await client.post(
                f"{API_URL}/web-scan/store-result",
                json=metadata,
                headers=auth_headers
            )
            
            if store_response.status_code != 200:
                logger.error(f"Failed to store metadata in API: {store_response.status_code}")
                raise HTTPException(status_code=500, detail="Failed to store scan metadata")
        
        logger.info(f"Successfully completed and stored scan {payload.task_id}")
        return {"status": "success", "task_id": payload.task_id}
        
    except Exception as e:
        logger.error(f"Cloud Task scan failed for task {payload.task_id}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Error details:", exc_info=True)  # This logs the full stack trace
        
        # Notify API of failure
        try:
            # Get OIDC token for failure notification
            try:
                oidc_token = get_oidc_token(API_URL)
                auth_headers = {"Authorization": f"Bearer {oidc_token}"}
            except Exception:
                auth_headers = {}
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"{API_URL}/web-scan/store-result",
                    json={
                        "id": payload.task_id,
                        "url": payload.url,
                        "timestamp": datetime.now().isoformat(),
                        "testEngine": {"name": "LumTrails Multi-Module Scanner", "version": "3.0.0"},
                        "violations": [],
                        "passes": [],
                        "incomplete": [],
                        "inapplicable": [],
                        "unified_results": {"error": str(e)},
                        "scanDuration": 0,
                        "status": "failed",
                        "user_id": payload.user_id,
                        "user_email": payload.user_email,
                        "error_message": str(e),
                        "credits_reserved": payload.credits_reserved,
                        "credits_required": payload.credits_required
                    },
                    headers=auth_headers
                )
        except Exception as callback_error:
            logger.error(f"Failed to notify API of scan failure: {str(callback_error)}")
        
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/direct-scan", response_model=ScanResponse)
async def direct_scan_endpoint(request: ScanRequest):
    """
    Direct scan endpoint for testing or synchronous scans
    Returns results immediately without storing in API
    """
    try:
        result = await scanner.scan(request)
        return result
    except Exception as e:
        logger.error(f"Direct scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync-scan")
async def sync_scan_endpoint(payload: CloudTaskPayload):
    """
    Synchronous scan endpoint for External API
    Returns full scan results immediately in v3.0.0 unified_results format
    Does NOT store to Firebase Storage or Firestore (caller handles storage)
    """
    try:
        logger.info(f"Processing SYNCHRONOUS scan for {payload.url}")
        logger.info(f"Task ID: {payload.task_id}, Modules: {payload.modules}")
        
        # Build scan request
        request = ScanRequest(
            url=payload.url,
            modules=payload.modules or [m.value for m in ScanModule]
        )
        logger.info(f"ScanRequest created with modules: {request.modules}")
        
        # Execute scan
        logger.info(f"Starting scan execution for {payload.url}")
        scan_result = await scanner.scan(request)
        logger.info(f"Scan completed. Modules executed: {scan_result.modules_executed}")
        
        # Transform to complete result format - all scan data in unified_results
        full_result = {
            "id": payload.task_id,
            "url": str(scan_result.url),
            "timestamp": scan_result.timestamp,
            "testEngine": {
                "name": "LumTrails Multi-Module Scanner",
                "version": "3.0.0",
                "modules": scan_result.modules_executed
            },
            "unified_results": {
                "scan_format_version": "3.0.0",
                "modules_executed": scan_result.modules_executed,
                "scan_duration_ms": scan_result.scan_duration_ms,
                "axe": scan_result.axe,
                "nu": scan_result.nu,
                "axTree": scan_result.axTree,
                "galen": scan_result.galen,
                "links": scan_result.links,
                "meta": scan_result.meta
            },
            "scanDuration": scan_result.scan_duration_ms,
            "status": "completed",
            "user_id": payload.user_id,
            "user_email": payload.user_email
        }
        
        result_size = len(json.dumps(full_result))
        logger.info(f"Sync scan complete. Result size: ~{result_size} bytes")
        
        return full_result
        
    except Exception as e:
        logger.error(f"Sync scan failed for task {payload.task_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
