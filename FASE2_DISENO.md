# FASE 2 – Diseno FastAPI y flujo end-to-end

- Objetivo: Regresion de precios de cierre (`close`) para acciones (banca China, Tata Motors), soportando carga de CSV, ETL configurable, entrenamiento de 3 modelos y visualizacion de metricas/plots.
- Base de datos de referencia: `data/Bank_Price_Data_China new.csv` y `data/final_dataset_tata_motors.csv` (regresion por defecto).

## Arbol de directorios propuesto
```
main.py                      # monta FastAPI, incluye routers v1, sirve templates/static
app/
  api/v1/
    datasets.py              # upload archivo/URL, preview
    etl.py                   # configurar/ejecutar ETL
    training.py              # entrenar/evaluar 3 modelos, devolver metricas/plots
  services/
    datasets.py              # guardar/leer CSV locales/URL, info basica
    etl.py                   # pipeline pandas configurable
    models.py                # split, entrenamiento de modelos, metricas, seleccion
    plots.py                 # graficas y guardado en static/plots/
  schemas/
    datasets.py              # Pydantic para upload/preview
    training.py              # Pydantic para config ETL + entrenamiento
templates/
  index.html                 # forms de carga/configuracion
  results.html               # metricas y graficas
static/plots/                # PNG/SVG generados
data/, data/processed/       # reutilizar existentes para insumos y salidas
```

## Endpoints (diseno)
- `POST /api/v1/datasets/upload-file`
  - Recibe: `multipart/form-data` con `file` CSV.
  - Devuelve: `{dataset_id, filename, rows, cols, sample_head}`.
- `POST /api/v1/datasets/upload-url`
  - Recibe: JSON `{url, filename?}`.
  - Devuelve: `{dataset_id, filename, downloaded: true, rows, cols, sample_head}`.
- `POST /api/v1/etl/configure`
  - Recibe: `{dataset_id, target_col, feature_cols?, drop_cols?, date_col?, fillna?, scalers?}`.
  - Devuelve: `{etl_config_id, summary}`.
- `POST /api/v1/etl/run`
  - Recibe: `{etl_config_id}` (o config inline).
  - Devuelve: `{etl_run_id, status, processed_path, rows, cols, schema}`.
- `POST /api/v1/training/run`
  - Recibe: `{etl_run_id, target_col, feature_cols?, split:{type:'temporal'|'random', test_size}, algorithms?:['linear','rf','gbr','xgb'], metric_primary:'rmse'}`.
  - Devuelve: `{training_run_id, metrics:{alg:{rmse,mae,r2}}, best_model:{name,rmse}, plots:{pred_vs_real, residuals, importances}}`.
- `GET /` -> render `index.html`.
- `GET /results` -> render `results.html` (consume datos de metricas/plots).

## Servicios clave
- `datasets`: valida extension, guarda en `data/uploads/` y copia a `data/`, preview con `head()`.
- `etl`: limpieza de tipos/fechas, seleccion de columnas, imputacion simple, salida en `data/processed/{dataset_id}.processed.csv`.
- `models`: split train/test (temporal o aleatorio), entrena `LinearRegression`, `RandomForestRegressor`, `GradientBoostingRegressor` (usa `XGBRegressor` si esta disponible), calcula MAE/MSE/RMSE/R2, elige ganador por RMSE.
- `plots`: genera pred vs real, residuales, importancias; guarda en `static/plots/{training_run_id}_*.png`.

## Frontend -> API
- `index.html`: formularios para `upload-file` (multipart) y `upload-url` (fetch JSON); seccion para configurar target/features y lanzar `etl/run`; boton para `training/run`.
- `results.html`: al cargar, consulta un listado de runs (p.ej. `GET /api/v1/training/runs` si se agrega) y muestra metricas + `<img src="/static/plots/{...}.png">`.

## Metricas y criterio
- Metricas: MAE, MSE, RMSE, R2.
- Criterio de seleccion: menor RMSE es el ganador; MAE y R2 como apoyo; revisar importancias para interpretabilidad.
