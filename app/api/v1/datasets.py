from fastapi import APIRouter, UploadFile, File, HTTPException

from app.schemas.datasets import DatasetInfo, UploadURLRequest, DatasetPreview
from app.services import datasets as datasets_service

router = APIRouter()


@router.post("/upload-file", response_model=DatasetInfo)
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    content = await file.read()
    entry = datasets_service.register_dataset_from_bytes(file.filename, content, source="upload")
    return DatasetInfo(**entry)


@router.post("/upload-url", response_model=DatasetInfo)
async def upload_url(payload: UploadURLRequest):
    try:
        entry = datasets_service.download_from_url(str(payload.url), filename=payload.filename)
    except datasets_service.DatasetError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return DatasetInfo(**entry)


@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
async def preview_dataset(dataset_id: str, rows: int = 5):
    try:
        data = datasets_service.preview_dataset(dataset_id, n_rows=rows)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return DatasetPreview(**data)
