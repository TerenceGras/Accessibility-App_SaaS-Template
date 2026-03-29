from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class IntegrationTask(BaseModel):
    user_id: str
    scan_id: str
    platform: str
    scan_data: Dict[str, Any]
    timestamp: str

class ScanResult(BaseModel):
    id: str
    url: str
    violations: List[Dict[str, Any]]
    passes: List[Dict[str, Any]]
    incomplete: List[Dict[str, Any]]
    timestamp: str
    scan_duration: Optional[int] = None
