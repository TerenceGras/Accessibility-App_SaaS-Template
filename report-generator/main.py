from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from weasyprint import HTML
from jinja2 import Template
from datetime import datetime
import logging
import traceback
import os

from translations import get_translations, get_analysis_type_display

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="LumTrails Report Generator")

# -------------------------------------------------------------------
# Security Configuration
# -------------------------------------------------------------------
import os
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# CORS - Restrict to internal services in production
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
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
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

# -------------------------------------------------------------------
# Pydantic Models
# -------------------------------------------------------------------

class ViolationNode(BaseModel):
    target: Optional[Any] = None
    html: Optional[str] = None


class WCAGViolation(BaseModel):
    help: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    impact: Optional[str] = "moderate"
    helpUrl: Optional[str] = None
    help_url: Optional[str] = None
    nodes: Optional[List[ViolationNode]] = None


class HTMLError(BaseModel):
    message: str
    extract: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None


class BrokenLink(BaseModel):
    url: str
    text: Optional[str] = None
    status: int
    error_reason: Optional[str] = None
    state: Optional[str] = None  # valid, invalid, timeout, unreachable


class ViewportMetrics(BaseModel):
    width: int
    height: int


class ElementMetrics(BaseModel):
    visible: int
    hidden: int


class LayoutMetrics(BaseModel):
    hasHorizontalScroll: bool
    elements: ElementMetrics


class ViewportResult(BaseModel):
    viewport: ViewportMetrics
    metrics: LayoutMetrics


class AxeData(BaseModel):
    violations: Optional[List[WCAGViolation]] = []
    passes: Optional[List[Dict[str, Any]]] = []
    incomplete: Optional[List[Dict[str, Any]]] = []


class NuData(BaseModel):
    errors: Optional[List[HTMLError]] = []
    warnings: Optional[List[Dict[str, Any]]] = []


class AxTreeData(BaseModel):
    tree: Optional[Any] = None


class GalenData(BaseModel):
    viewport_results: Optional[List[ViewportResult]] = []


class LinksData(BaseModel):
    links: Optional[List[Dict[str, Any]]] = []
    broken_links: Optional[List[BrokenLink]] = []
    error_links: Optional[List[BrokenLink]] = []
    # New fields for updated link states
    valid_links: Optional[List[Dict[str, Any]]] = []
    invalid_links: Optional[List[Dict[str, Any]]] = []
    timeout_links: Optional[List[Dict[str, Any]]] = []
    checked_links: Optional[int] = 0
    total_links: Optional[int] = 0


class CompanyInfo(BaseModel):
    company_name: Optional[str] = None
    vat_number: Optional[str] = None
    address: Optional[Dict[str, str]] = None


class UnifiedResults(BaseModel):
    axe: Optional[AxeData] = None
    nu: Optional[NuData] = None
    axTree: Optional[AxTreeData] = None
    galen: Optional[GalenData] = None
    links: Optional[LinksData] = None
    accessibility_report: Optional[str] = None


class WebScanReportRequest(BaseModel):
    url: str
    unified_results: Optional[UnifiedResults] = None
    timestamp: Optional[str] = None
    taskId: Optional[str] = None
    language: Optional[str] = "en"
    company_info: Optional[CompanyInfo] = None


class PDFScanReportRequest(BaseModel):
    file_name: str
    accessibility_report: Optional[str] = None
    unified_results: Optional[UnifiedResults] = None
    timestamp: Optional[str] = None
    analysis_type: Optional[str] = None
    language: Optional[str] = "en"
    company_info: Optional[CompanyInfo] = None

# -------------------------------------------------------------------
# Helper: Accessibility Tree Formatting
# -------------------------------------------------------------------

def format_tree_node(node, level=0, max_depth=5):
    """Recursively format accessibility tree node for clean display."""
    if level > max_depth:
        return "    " * level + "...(tree continues)\n"

    indent = "  " * level
    role = node.get("role", "unknown")
    name = node.get("name", "")
    line = f"{indent}[{role}] {name}\n" if name else f"{indent}[{role}]\n"

    result = line
    for child in node.get("children", []):
        result += format_tree_node(child, level + 1, max_depth)

    return result

# -------------------------------------------------------------------
# Logo Loader
# -------------------------------------------------------------------

def get_logo_base64():
    """Load and encode the LumTrails logo as base64."""
    import base64

    logo_path = os.path.join(os.path.dirname(__file__), "lumtrails_logo.png")

    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
                logger.info(f"Loaded logo: {logo_path}")
                return f"data:image/png;base64,{data}"
        except Exception as e:
            logger.warning(f"Failed to load PNG logo: {e}")

    # fallback SVG
    svg = """
    <svg width="80" height="80" viewBox="0 0 80 80">
      <circle cx="40" cy="40" r="35" fill="#3ac7f2" opacity="0.2"/>
      <circle cx="40" cy="40" r="25" fill="none" stroke="#3ac7f2" stroke-width="4"/>
      <path d="M 40 20 L 40 60 M 20 40 L 60 40" stroke="#3ac7f2" stroke-width="5" stroke-linecap="round"/>
    </svg>
    """
    encoded = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"

LUMTRAILS_LOGO_BASE64 = get_logo_base64()

# -------------------------------------------------------------------
# CSS Selector Syntax Highlighting
# -------------------------------------------------------------------

def highlight_css_selector(selector_text):
    """Apply syntax highlighting to CSS selectors."""
    import re

    if not selector_text or not isinstance(selector_text, str):
        return selector_text

    if isinstance(selector_text, (list, tuple)):
        selector_text = str(selector_text[0]) if selector_text else ""

    result = selector_text
    result = re.sub(r"#([\w-]+)", r'<span style="color:#D73A49;">#\1</span>', result)
    result = re.sub(r"\.([\w-]+)", r'<span style="color:#6F42C1;">.\1</span>', result)
    result = re.sub(r"\[([^\]]+)\]", r'<span style="color:#22863A;">[\1]</span>', result)
    result = re.sub(r"::?([\w-]+)", r'<span style="color:#005CC5;">:\1</span>', result)
    result = re.sub(
        r"(?:^|(?<=[>\s]))([a-z][\w-]*?)(?=[\s.#:\[>]|$)",
        r'<span style="color:#0066CC;">\1</span>',
        result,
    )
    result = re.sub(r"([>+~])", r'<span style="color:#6A737D;">\1</span>', result)

    return result

# -------------------------------------------------------------------
# Load Template
# -------------------------------------------------------------------

def load_template(filename: str) -> str:
    """Load HTML template from disk."""
    path = os.path.join(os.path.dirname(__file__), filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Template error: {e}")
        raise HTTPException(500, detail=f"Template loading failed: {e}")

# -------------------------------------------------------------------
# Health Check
# -------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "report-generator"}

# -------------------------------------------------------------------
# Generate Web Scan Report
# -------------------------------------------------------------------

@app.post("/generate/web-scan")
async def generate_web_scan_report(request: WebScanReportRequest):
    try:
        logger.info(f"Generating web scan report for: {request.url}")

        unified = request.unified_results or UnifiedResults()

        axe = unified.axe or AxeData()
        nu = unified.nu or NuData()
        ax_tree = unified.axTree or AxTreeData()
        galen = unified.galen or GalenData()
        links = unified.links or LinksData()

        violations = axe.violations or []
        passes = axe.passes or []

        total_violation_nodes = sum(len(v.nodes or []) for v in violations)
        total_pass_nodes = sum(len(p.get("nodes", [])) for p in passes)

        html_errors = nu.errors or []

        all_links = links.links or []
        
        # Support all link states: valid, invalid, timeout, unreachable
        # Old states: ok, broken, error, warning (backward compatible)
        invalid_links = [
            BrokenLink(
                url=l.get("url", ""), 
                text=l.get("text"), 
                status=l.get("status", 0),
                error_reason=l.get("error_reason"),
                state="invalid"
            )
            for l in all_links if l.get("state") in ("invalid", "broken")
        ]
        timeout_links = [
            BrokenLink(
                url=l.get("url", ""), 
                text=l.get("text"), 
                status=l.get("status", 0),
                error_reason=l.get("error_reason", "Request timed out"),
                state="timeout"
            )
            for l in all_links if l.get("state") == "timeout"
        ]
        unreachable_links = [
            BrokenLink(
                url=l.get("url", ""), 
                text=l.get("text"), 
                status=l.get("status", 0),
                error_reason=l.get("error_reason", "Connection failed"),
                state="unreachable"
            )
            for l in all_links if l.get("state") == "unreachable"
        ]
        # Backward compatibility: error links without specific state
        error_links_fallback = [
            BrokenLink(
                url=l.get("url", ""), 
                text=l.get("text"), 
                status=l.get("status", 0),
                error_reason=l.get("error_reason"),
                state="error"
            )
            for l in all_links if l.get("state") == "error"
        ]
        
        # For template: combine all issue links
        broken_links = invalid_links  # Only truly broken links (HTTP errors)
        connection_issue_links = timeout_links + unreachable_links + error_links_fallback

        viewport_results = galen.viewport_results or []

        tree_data = format_tree_node(ax_tree.tree) if ax_tree.tree else None

        # Get translations for the requested language
        lang = request.language or "en"
        t = get_translations(lang)

        modules_enabled = []
        if violations or passes:
            modules_enabled.append("WCAG Compliance Testing")
        if html_errors or nu.warnings:
            modules_enabled.append("HTML Markup Validation")
        if tree_data:
            modules_enabled.append("Accessibility Tree Analysis")
        if viewport_results:
            modules_enabled.append("Responsive Layout Testing")
        if all_links:
            modules_enabled.append("Link Health Check")

        formatted_timestamp = None
        if request.timestamp:
            try:
                dt = datetime.fromisoformat(request.timestamp.replace("Z", "+00:00"))
                formatted_timestamp = dt.strftime("%B %d, %Y at %H:%M UTC")
            except:
                formatted_timestamp = request.timestamp

        # Prepare company info for the template
        company_info = None
        if request.company_info:
            company_info = {
                "company_name": request.company_info.company_name,
                "vat_number": request.company_info.vat_number,
                "address": request.company_info.address,
            }

        template_data = {
            "logo": LUMTRAILS_LOGO_BASE64,
            "url": request.url,
            "timestamp": formatted_timestamp,
            "task_id": request.taskId,
            "modules_enabled": modules_enabled,
            "wcag_violations": total_violation_nodes,
            "html_errors": len(html_errors),
            "broken_links": len(invalid_links),  # Only count invalid links as broken
            "timeout_links_count": len(timeout_links),
            "unreachable_links_count": len(unreachable_links),
            "tests_passed": total_pass_nodes,
            "has_wcag": bool(violations or passes),
            "has_html": bool(html_errors or nu.warnings),
            "has_tree": tree_data is not None,
            "has_layout": bool(viewport_results),
            "has_links": bool(all_links),
            "violations": violations,
            "html_errors_list": html_errors,
            "tree_data": tree_data,
            "viewport_results": viewport_results,
            "broken_links_list": broken_links,  # Only invalid_links (HTTP errors)
            "connection_issue_links_list": connection_issue_links,  # Timeout + unreachable
            "timeout_links_list": timeout_links,
            "unreachable_links_list": unreachable_links,
            "invalid_links_list": invalid_links,
            "checked_links": links.checked_links or 0,
            "t": t,  # Translations
            "company_info": company_info,
        }

        template = Template(load_template("web_scan_template.html"))
        template.globals["highlight_css"] = highlight_css_selector
        html = template.render(**template_data)

        pdf_bytes = HTML(string=html).write_pdf()

        safe_name = request.url.replace("http://", "").replace("https://", "").replace("/", "-")[:50]

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=web-accessibility-report-{safe_name}.pdf"}
        )

    except Exception as e:
        logger.error(f"Web scan error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Failed to generate report: {e}")

# -------------------------------------------------------------------
# Generate PDF Scan Report
# -------------------------------------------------------------------

@app.post("/generate/pdf-scan")
async def generate_pdf_scan_report(request: PDFScanReportRequest):
    try:
        logger.info(f"Generating PDF scan report for: {request.file_name}")

        accessibility_report = (
            request.accessibility_report
            or (request.unified_results.accessibility_report if request.unified_results else None)
        )

        if not accessibility_report:
            raise HTTPException(400, "No accessibility report data found in request")

        # Get translations for the requested language
        lang = request.language or "en"
        t = get_translations(lang)

        formatted_timestamp = None
        if request.timestamp:
            try:
                dt = datetime.fromisoformat(request.timestamp.replace("Z", "+00:00"))
                formatted_timestamp = dt.strftime("%B %d, %Y at %H:%M UTC")
            except:
                formatted_timestamp = request.timestamp

        # Prepare company info for the template
        company_info = None
        if request.company_info:
            company_info = {
                "company_name": request.company_info.company_name,
                "vat_number": request.company_info.vat_number,
                "address": request.company_info.address,
            }

        # Get translated analysis type display
        raw_analysis_type = request.analysis_type or "ai_vision_free_text"
        translated_analysis_type = get_analysis_type_display(raw_analysis_type, lang)

        template_data = {
            "logo": LUMTRAILS_LOGO_BASE64,
            "file_name": request.file_name,
            "timestamp": formatted_timestamp,
            "analysis_type": translated_analysis_type,
            "accessibility_report": accessibility_report,
            "t": t,  # Translations
            "company_info": company_info,
        }

        html = Template(load_template("pdf_scan_template.html")).render(**template_data)
        pdf_bytes = HTML(string=html).write_pdf()

        safe_name = request.file_name.replace(".pdf", "").replace(" ", "-")[:50]

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=pdf-accessibility-report-{safe_name}.pdf"}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF scan error: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(500, f"Failed to generate report: {e}")

# -------------------------------------------------------------------
# Entry Point
# -------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
