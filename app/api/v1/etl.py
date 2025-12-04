from fastapi import APIRouter, HTTPException

from app.schemas.training import ETLConfigRequest, ETLConfigResponse, ETLRunRequest, ETLRunResult
from app.services import etl as etl_service
from app.services import datasets as datasets_service

router = APIRouter()


@router.post("/configure", response_model=ETLConfigResponse)
def configure_etl(payload: ETLConfigRequest):
    try:
        datasets_service.get_dataset_entry(payload.dataset_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")

    df = datasets_service.load_dataset(payload.dataset_id)
    if payload.target_col not in df.columns:
        raise HTTPException(status_code=400, detail="Target column not found in dataset")
    feature_cols = payload.feature_cols or [c for c in df.columns if c != payload.target_col]
    feature_cols = [c for c in feature_cols if c in df.columns and c != payload.target_col]
    drop_cols = payload.drop_cols or []
    config = {
        "dataset_id": payload.dataset_id,
        "target_col": payload.target_col,
        "feature_cols": feature_cols,
        "drop_cols": drop_cols,
        "missing_strategy": payload.missing_strategy,
        "normalize_numeric": payload.normalize_numeric,
        "date_cols": payload.date_cols or [],
    }
    config_id = etl_service.save_config(config)
    return ETLConfigResponse(
        etl_config_id=config_id,
        dataset_id=payload.dataset_id,
        target_col=payload.target_col,
        feature_cols=feature_cols,
        drop_cols=drop_cols,
        missing_strategy=payload.missing_strategy,
        normalize_numeric=payload.normalize_numeric,
        date_cols=payload.date_cols or [],
    )


@router.post("/run", response_model=ETLRunResult)
def run_etl(payload: ETLRunRequest):
    try:
        meta = etl_service.run_etl_and_store(payload.etl_config_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="ETL config not found")
    except etl_service.ETLError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ETLRunResult(**meta)
