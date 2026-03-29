from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class IntegrationConfig(BaseModel):
    config: Dict[str, Any]

class GitHubConfig(BaseModel):
    repository: Optional[str] = None
    label: str = "accessibility"
    wcag_severity_filter: List[str] = ["High", "Medium", "Low"]
    wcag_grouping_option: str = "per-error-type"
    wcag_regroup_violations: bool = True

class WebScanSections(BaseModel):
    wcag_enabled: bool = True
    html_enabled: bool = True
    links_enabled: bool = True
    axtree_enabled: bool = False
    layout_enabled: bool = True

class GitHubConfigUpdate(BaseModel):
    repository: Optional[str] = None
    # WCAG specific fields (new naming convention)
    wcag_severity_filter: Optional[List[str]] = None
    wcag_grouping_option: Optional[str] = None
    wcag_regroup_violations: Optional[bool] = None
    # Module grouping options
    pdf_grouping_option: Optional[str] = None
    web_scan_sections: Optional[WebScanSections] = None
    html_grouping_option: Optional[str] = None
    links_grouping_option: Optional[str] = None
    layout_grouping_option: Optional[str] = None

class SlackConfig(BaseModel):
    channel: Optional[str] = None
    wcag_severity_filter: List[str] = ["High", "Medium", "Low"]
    wcag_grouping_option: str = "per-error-type"
    wcag_regroup_violations: bool = False  # Default False for Slack

class SlackConfigUpdate(BaseModel):
    channel: Optional[str] = None
    webhook_url: Optional[str] = None
    # WCAG specific fields (new naming convention)
    wcag_severity_filter: Optional[List[str]] = None
    wcag_grouping_option: Optional[str] = None
    wcag_regroup_violations: Optional[bool] = None
    # Module grouping options
    pdf_grouping_option: Optional[str] = None
    web_scan_sections: Optional[WebScanSections] = None
    html_grouping_option: Optional[str] = None
    links_grouping_option: Optional[str] = None
    layout_grouping_option: Optional[str] = None

class NotionConfig(BaseModel):
    page_url: Optional[str] = None
    parent_page_id: Optional[str] = None
    wcag_severity_filter: List[str] = ["High", "Medium", "Low"]
    wcag_grouping_option: str = "per-error-type"
    wcag_regroup_violations: bool = True  # Default True for Notion

class NotionConfigUpdate(BaseModel):
    page_url: Optional[str] = None
    parent_page_id: Optional[str] = None
    # WCAG specific fields (new naming convention)
    wcag_severity_filter: Optional[List[str]] = None
    wcag_grouping_option: Optional[str] = None
    wcag_regroup_violations: Optional[bool] = None
    # Module grouping options
    pdf_grouping_option: Optional[str] = None
    web_scan_sections: Optional[WebScanSections] = None
    html_grouping_option: Optional[str] = None
    links_grouping_option: Optional[str] = None
    layout_grouping_option: Optional[str] = None

class SlackWebhookConfig(BaseModel):
    webhook_url: str
    channel: Optional[str] = None

class OAuthCallback(BaseModel):
    code: str
    state: str
