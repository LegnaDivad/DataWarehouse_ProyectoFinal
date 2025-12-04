from fastapi import APIRouter, HTTPException

from app.schemas.training import TrainingRequest, TrainingResult
from app.services import models as models_service

router = APIRouter()


@router.post("/run", response_model=TrainingResult)
def run_training(payload: TrainingRequest):
    try:
        result = models_service.train_and_evaluate_models(
            etl_config_id=payload.etl_config_id,
            algorithms=payload.algorithms,
            test_size=payload.test_size,
            random_state=payload.random_state,
            metric_primary=payload.metric_primary,
        )
    except models_service.TrainingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
