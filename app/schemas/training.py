from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class ETLConfigRequest(BaseModel):
    dataset_id: str
    target_col: str
    feature_cols: Optional[List[str]] = None
    drop_cols: Optional[List[str]] = None

    # Solo permite estos valores y "drop" por defecto
    missing_strategy: Literal["drop", "mean", "median", "zero"] = "drop"

    normalize_numeric: bool = False
    date_cols: Optional[List[str]] = None


class ETLConfigResponse(BaseModel):
    etl_config_id: str
    dataset_id: str
    target_col: str
    feature_cols: List[str]
    drop_cols: List[str]
    missing_strategy: str
    normalize_numeric: bool
    date_cols: List[str]


class ETLRunRequest(BaseModel):
    etl_config_id: str


class ETLRunResult(BaseModel):
    etl_run_id: str
    etl_config_id: str
    dataset_id: str
    processed_path: str
    rows: int
    cols: int
    feature_cols: List[str]
    target_col: str
    normalization: Optional[Dict[str, Any]] = None


class TrainingRequest(BaseModel):
    etl_config_id: str
    algorithms: Optional[List[str]] = None  # ['linear','rf','gbr']
    test_size: float = Field(0.2, ge=0.05, le=0.5)
    random_state: int = 42

    # Igual, solo permite estas métricas
    metric_primary: Literal["rmse", "mae", "mse", "r2"] = "rmse"


class ModelMetrics(BaseModel):
    mae: float
    mse: float
    rmse: float
    r2: float


class ModelResult(BaseModel):
    metrics: ModelMetrics
    feature_cols: List[str]


class BestModel(BaseModel):
    name: str
    metrics: ModelMetrics


class PlotInfo(BaseModel):
    path: str
    title: str
    description: str


class TrainingResult(BaseModel):
    training_run_id: str
    etl_run_id: str
    etl_config_id: str
    dataset_id: str
    metric_primary: str
    models: Dict[str, ModelResult]
    best_model: BestModel
    plots: List[PlotInfo]
    explanation: str
