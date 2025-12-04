import json
import uuid
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
import requests

BASE_DIR = Path(__file__).resolve().parents[2]
DATASETS_DIR = BASE_DIR / "data" / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)
INDEX_PATH = DATASETS_DIR / "index.json"


class DatasetError(Exception):
    pass


def _load_index() -> Dict[str, Dict[str, Any]]:
    if INDEX_PATH.exists():
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_index(index: Dict[str, Dict[str, Any]]) -> None:
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _shape_from_csv(path: Path) -> Dict[str, int]:
    df = pd.read_csv(path)
    return {"rows": len(df), "cols": len(df.columns)}


def register_dataset_from_bytes(filename: str, content: bytes, source: str) -> Dict[str, Any]:
    index = _load_index()
    dataset_id = uuid.uuid4().hex
    safe_name = Path(filename).name or "dataset.csv"
    stored_path = DATASETS_DIR / f"{dataset_id}_{safe_name}"
    stored_path.write_bytes(content)
    shape = _shape_from_csv(stored_path)
    entry = {
        "dataset_id": dataset_id,
        "filename": safe_name,
        "path": str(stored_path),
        "rows": shape["rows"],
        "cols": shape["cols"],
        "created_at": pd.Timestamp.utcnow().isoformat(),
        "source": source,
    }
    index[dataset_id] = entry
    _save_index(index)
    return entry


def download_from_url(url: str, filename: Optional[str] = None) -> Dict[str, Any]:
    resp = requests.get(url, timeout=30)
    if not resp.ok:
        raise DatasetError(f"Failed to download dataset. Status {resp.status_code}")
    inferred_name = filename or Path(url).name or "dataset.csv"
    return register_dataset_from_bytes(inferred_name, resp.content, source="url")


def get_dataset_entry(dataset_id: str) -> Dict[str, Any]:
    index = _load_index()
    if dataset_id not in index:
        raise FileNotFoundError(f"Dataset {dataset_id} not found")
    return index[dataset_id]


def get_dataset_path(dataset_id: str) -> Path:
    entry = get_dataset_entry(dataset_id)
    return Path(entry["path"])


def preview_dataset(dataset_id: str, n_rows: int = 5) -> Dict[str, Any]:
    path = get_dataset_path(dataset_id)
    df = pd.read_csv(path, nrows=n_rows)
    return {
        "dataset_id": dataset_id,
        "columns": df.columns.tolist(),
        "rows": len(df),
        "sample": df.to_dict(orient="records"),
    }


def load_dataset(dataset_id: str) -> pd.DataFrame:
    path = get_dataset_path(dataset_id)
    return pd.read_csv(path)
