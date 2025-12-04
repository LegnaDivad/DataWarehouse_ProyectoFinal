from typing import Any, Dict, List, Optional
from pydantic import BaseModel, HttpUrl


class UploadURLRequest(BaseModel):
    url: HttpUrl
    filename: Optional[str] = None


class DatasetInfo(BaseModel):
    dataset_id: str
    filename: str
    path: str
    rows: Optional[int] = None
    cols: Optional[int] = None
    created_at: str
    source: str


class DatasetPreview(BaseModel):
    dataset_id: str
    columns: List[str]
    rows: int
    sample: List[Dict[str, Any]]
