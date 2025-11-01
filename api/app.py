import os
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime

from . import runner

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE, 'data')
UPLOADS_DIR = os.path.join(DATA_DIR, 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

app = FastAPI(title='ETL Runner API', version='0.1')


@app.post('/upload')
async def upload_and_start(files: List[UploadFile] = File(...)):
    """Upload one or more files and start an ETL run. Returns run_id."""
    if not files:
        raise HTTPException(status_code=400, detail='No files uploaded')

    # Create run and folders
    file_names = [f.filename for f in files]
    run_id = runner.create_run(file_names)
    run_upload_dir = os.path.join(UPLOADS_DIR, run_id)
    os.makedirs(run_upload_dir, exist_ok=True)

    # Save files to uploads dir and also to data root (so ETL can find them)
    for upload in files:
        target_upload_path = os.path.join(run_upload_dir, upload.filename)
        target_data_path = os.path.join(DATA_DIR, upload.filename)
        contents = await upload.read()
        with open(target_upload_path, 'wb') as f:
            f.write(contents)
        # also write to data/ so ETL sees file by name
        with open(target_data_path, 'wb') as f:
            f.write(contents)

    # start the ETL in background
    runner.start_run(run_id)

    return JSONResponse({'run_id': run_id}, status_code=202)


@app.get('/status/{run_id}')
def get_status(run_id: str):
    try:
        data = runner.get_run(run_id)
        return JSONResponse(data)
    except KeyError:
        raise HTTPException(status_code=404, detail='Run not found')


@app.get('/runs')
def list_all_runs():
    return {'runs': runner.list_runs()}
