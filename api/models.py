from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RunStageUpdate(BaseModel):
    status: str
    info: Optional[Dict[str, Any]] = None


class RunStatus(BaseModel):
    run_id: str
    status: str
    created_at: Optional[str]
    started_at: Optional[str]
    finished_at: Optional[str]
    files: List[str]
    stages: Dict[str, List[Dict[str, Any]]]
    errors: List[str]
    stats: Dict[str, Any]
