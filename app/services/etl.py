import json
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

from app.services import datasets

BASE_DIR = Path(__file__).resolve().parents[2]
ETL_CONFIGS_DIR = BASE_DIR / "data" / "etl_configs"
ETL_CONFIGS_DIR.mkdir(parents=True, exist_ok=True)
ETL_OUTPUTS_DIR = BASE_DIR / "data" / "processed"
ETL_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
ETL_RUNS_DIR = BASE_DIR / "reports" / "etl_runs"
ETL_RUNS_DIR.mkdir(parents=True, exist_ok=True)


class ETLError(Exception):
    pass


def save_config(config: Dict[str, Any]) -> str:
    config_id = uuid.uuid4().hex
    path = ETL_CONFIGS_DIR / f"{config_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    return config_id


def load_config(config_id: str) -> Dict[str, Any]:
    path = ETL_CONFIGS_DIR / f"{config_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"ETL config {config_id} not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def handle_missing(df: pd.DataFrame, strategy: str, target_col: str) -> pd.DataFrame:
    if strategy == "drop":
        return df.dropna(subset=[target_col])
    df_out = df.copy()
    numeric_cols = df_out.select_dtypes(include=["number"]).columns
    non_numeric = [c for c in df_out.columns if c not in numeric_cols]
    if strategy == "mean":
        df_out[numeric_cols] = df_out[numeric_cols].fillna(df_out[numeric_cols].mean())
    elif strategy == "median":
        df_out[numeric_cols] = df_out[numeric_cols].fillna(df_out[numeric_cols].median())
    elif strategy == "zero":
        df_out[numeric_cols] = df_out[numeric_cols].fillna(0)
    df_out = df_out.dropna(subset=[target_col])
    for c in non_numeric:
        df_out[c] = df_out[c].fillna("")
    return df_out


def _normalize_numeric(df: pd.DataFrame, feature_cols: List[str]) -> Dict[str, Dict[str, float]]:
    numeric_cols = df[feature_cols].select_dtypes(include=["number"]).columns
    stats: Dict[str, Dict[str, float]] = {}
    for col in numeric_cols:
        mean = float(df[col].mean())
        std = float(df[col].std()) if float(df[col].std()) != 0 else 0.0
        stats[col] = {"mean": mean, "std": std}
        if std != 0:
            df[col] = (df[col] - mean) / std
    return stats


def run_etl(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    df_out = df.copy()
    date_cols = config.get("date_cols") or []
    for col in date_cols:
        if col in df_out.columns:
            df_out[col] = pd.to_datetime(df_out[col], errors="coerce")

    drop_cols = config.get("drop_cols") or []
    to_drop = [c for c in drop_cols if c in df_out.columns]
    if to_drop:
        df_out = df_out.drop(columns=to_drop)

    target_col = config["target_col"]
    if target_col not in df_out.columns:
        raise ETLError(f"Target column '{target_col}' not found in dataset")

    feature_cols = config.get("feature_cols")
    if not feature_cols:
        feature_cols = [c for c in df_out.columns if c != target_col]
    else:
        feature_cols = [c for c in feature_cols if c in df_out.columns and c != target_col]

    if not feature_cols:
        raise ETLError("No feature columns available after selection")

    selected_cols = feature_cols + [target_col]
    df_out = df_out[selected_cols]

    for col in selected_cols:
        if df_out[col].dtype == object:
            df_out[col] = pd.to_numeric(df_out[col], errors="ignore")

    strategy = config.get("missing_strategy", "drop")
    df_out = handle_missing(df_out, strategy=strategy, target_col=target_col)

    normalization_info: Optional[Dict[str, Dict[str, float]]] = None
    if config.get("normalize_numeric"):
        normalization_info = _normalize_numeric(df_out, feature_cols)

    return {
        "df": df_out,
        "feature_cols": feature_cols,
        "target_col": target_col,
        "normalization": normalization_info,
    }


def run_etl_and_store(config_id: str) -> Dict[str, Any]:
    config = load_config(config_id)
    dataset_id = config["dataset_id"]
    df = datasets.load_dataset(dataset_id)
    result = run_etl(df, config)
    etl_run_id = uuid.uuid4().hex
    processed_path = ETL_OUTPUTS_DIR / f"{etl_run_id}.processed.csv"
    result["df"].to_csv(processed_path, index=False, encoding="utf-8")
    meta = {
        "etl_run_id": etl_run_id,
        "etl_config_id": config_id,
        "dataset_id": dataset_id,
        "processed_path": str(processed_path),
        "rows": len(result["df"]),
        "cols": len(result["df"].columns),
        "feature_cols": result["feature_cols"],
        "target_col": result["target_col"],
        "normalization": result["normalization"],
        "created_at": pd.Timestamp.utcnow().isoformat(),
    }
    run_meta_path = ETL_RUNS_DIR / f"{etl_run_id}.json"
    with open(run_meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    return meta
