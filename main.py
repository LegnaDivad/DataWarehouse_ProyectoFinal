from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1 import datasets as datasets_router
from app.api.v1 import etl as etl_router
from app.api.v1 import training as training_router


app = FastAPI(title="Data Mining API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets_router.router, prefix="/api/v1/datasets", tags=["datasets"])
app.include_router(etl_router.router, prefix="/api/v1/etl", tags=["etl"])
app.include_router(training_router.router, prefix="/api/v1/training", tags=["training"])

static_dir = Path(__file__).resolve().parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates_dir = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@app.get("/", include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
