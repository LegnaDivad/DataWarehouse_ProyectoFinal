import os
import json
import threading
import traceback
from datetime import datetime
from typing import Callable, Dict, Any, List
import uuid

from etl import run_etl

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE, 'data')
REPORTS_DIR = os.path.join(BASE, 'reports')
ETL_RUNS_DIR = os.path.join(REPORTS_DIR, 'etl_runs')
os.makedirs(ETL_RUNS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# In-memory store of runs (mirrors disk JSON). Structure:
# runs[run_id] = {status, created_at, started_at, finished_at, files, stages, errors, stats}
runs: Dict[str, Dict[str, Any]] = {}


def _persist_run(run_id: str):
    path = os.path.join(ETL_RUNS_DIR, f"{run_id}.json")
    with open(path, 'w', encoding='utf8') as f:
        json.dump(runs[run_id], f, default=str, ensure_ascii=False, indent=2)


def create_run(files: List[str]) -> str:
    run_id = uuid.uuid4().hex
    now = datetime.utcnow().isoformat() + 'Z'
    runs[run_id] = {
        'run_id': run_id,
        'status': 'queued',
        'created_at': now,
        'started_at': None,
        'finished_at': None,
        'files': files,
        'stages': {},
        'errors': [],
        'stats': {},
    }
    _persist_run(run_id)
    return run_id


def _progress_callback(run_id: str, stage: str, info: Dict[str, Any]):
    # append stage info
    entry = {'ts': datetime.utcnow().isoformat() + 'Z', **info}
    stages = runs[run_id].setdefault('stages', {})
    stages.setdefault(stage, []).append(entry)
    # update high-level status
    status = 'running'
    if info.get('status') == 'finished':
        # If all stages finished, we'll mark finished at end
        pass
    runs[run_id]['status'] = status
    _persist_run(run_id)


def _mark_started(run_id: str):
    runs[run_id]['started_at'] = datetime.utcnow().isoformat() + 'Z'
    runs[run_id]['status'] = 'running'
    _persist_run(run_id)


def _mark_finished(run_id: str, success: bool = True):
    runs[run_id]['finished_at'] = datetime.utcnow().isoformat() + 'Z'
    runs[run_id]['status'] = 'finished' if success else 'failed'
    _persist_run(run_id)


def _mark_error(run_id: str, exc: Exception):
    tb = traceback.format_exc()
    runs[run_id]['errors'].append(tb)
    runs[run_id]['status'] = 'failed'
    runs[run_id]['finished_at'] = datetime.utcnow().isoformat() + 'Z'
    _persist_run(run_id)


def start_run(run_id: str, pool_chunksize: int = 200000):
    """Start ETL in a background thread. Assumes uploaded files are already placed in data/ with their names."""

    def target():
        try:
            _mark_started(run_id)

            def cb(rid, stage, info):
                # wrap to ensure run_id is present
                _progress_callback(rid, stage, info)

            # call the ETL runner with our callback
            run_etl.run_all(progress_callback=cb, run_id=run_id, pool_chunksize=pool_chunksize)
            _mark_finished(run_id, success=True)
        except Exception as e:
            _mark_error(run_id, e)

    t = threading.Thread(target=target, daemon=True)
    t.start()
    return True


def get_run(run_id: str) -> Dict[str, Any]:
    if run_id in runs:
        return runs[run_id]
    # try load from disk
    path = os.path.join(ETL_RUNS_DIR, f"{run_id}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf8') as f:
            data = json.load(f)
        runs[run_id] = data
        return data
    raise KeyError(run_id)


def list_runs() -> List[str]:
    return list(runs.keys())
