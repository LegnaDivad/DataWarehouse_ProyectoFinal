from typing import Dict, Any, List, Optional, Tuple
import uuid

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn import metrics

from app.services import etl as etl_service
from app.services import plots as plots_service


class TrainingError(Exception):
    pass


def _select_algorithms(names: Optional[List[str]] = None):
    registry = {
        "linear": LinearRegression,
        "rf": RandomForestRegressor,
        "gbr": GradientBoostingRegressor,
    }

    if not names:
        names = list(registry.keys())

    models = {}
    for n in names:
        if n not in registry:
            raise TrainingError(f"Unknown algorithm '{n}'")
        # simple, fast defaults; can be tuned later
        if n == "rf":
            models[n] = registry[n](n_estimators=120, random_state=42, n_jobs=-1)
        elif n == "gbr":
            models[n] = registry[n](random_state=42)
        else:
            models[n] = registry[n]()
    return models


def _ensure_numeric_features(df: pd.DataFrame, feature_cols: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    X = df[feature_cols].copy()

    # Forzar a numérico cualquier columna object
    for col in X.columns:
        if X[col].dtype == object:
            X[col] = pd.to_numeric(X[col], errors="coerce")

    numeric_cols = X.select_dtypes(include=["number", "float", "int"]).columns.tolist()
    if not numeric_cols:
        raise TrainingError("No numeric feature columns available for modeling")

    X = X[numeric_cols].fillna(0)
    return X, numeric_cols


def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae = metrics.mean_absolute_error(y_true, y_pred)
    mse = metrics.mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = metrics.r2_score(y_true, y_pred)
    return {"mae": mae, "mse": mse, "rmse": rmse, "r2": r2}


def _prepare_target(df: pd.DataFrame, target_col: str) -> Tuple[pd.Series, pd.Series]:
    """
    Devuelve (y, mask) donde y es el target numérico y mask indica
    qué filas del DF original son válidas.
    - Si el target ya es numérico, solo hace to_numeric + filtra NaN.
    - Si es categórico yes/no, lo mapea a 1/0.
    """
    s = df[target_col]
    from pandas.api.types import is_numeric_dtype, is_object_dtype

    # Caso 1: ya es numérico
    if is_numeric_dtype(s):
        y = pd.to_numeric(s, errors="coerce")
        mask = y.notna()
        return y.loc[mask], mask

    # Caso 2: categórico tipo yes/no
    if is_object_dtype(s) or s.dtype == "category":
        s_str = s.astype(str).str.strip().str.lower()
        uniques = set(s_str.dropna().unique())

        # Soportar explícitamente yes/no
        if uniques.issubset({"yes", "no"}):
            mapping = {"no": 0, "yes": 1}
            y = s_str.map(mapping)
            mask = y.notna()
            return y.loc[mask], mask

        # Si queremos, aquí podríamos añadir más mappings (true/false, etc.)

        raise TrainingError(
            f"Target column '{target_col}' no es numérica ni binaria yes/no. "
            f"Valores únicos detectados (ejemplo): {list(uniques)[:10]}"
        )

    # Otros tipos raros
    raise TrainingError(
        f"Tipo de datos no soportado para la columna objetivo '{target_col}' "
        f"(dtype={s.dtype}). Debe ser numérica o binaria yes/no."
    )


def train_and_evaluate_models(
    etl_config_id: str,
    algorithms: Optional[List[str]] = None,
    test_size: float = 0.2,
    random_state: int = 42,
    metric_primary: str = "rmse",
) -> Dict[str, Any]:
    training_run_id = uuid.uuid4().hex

    # 1) Ejecutar ETL y cargar dataset procesado
    meta = etl_service.run_etl_and_store(etl_config_id)
    df = pd.read_csv(meta["processed_path"])
    target_col = meta["target_col"]
    feature_cols = meta["feature_cols"]

    if df.empty:
        raise TrainingError(
            f"El dataset procesado en '{meta['processed_path']}' no tiene filas. "
            "Revisa la configuración del ETL, filtros o el archivo de origen."
        )

    if target_col not in df.columns:
        raise TrainingError(f"Target column '{target_col}' missing in processed dataset")
    if not feature_cols:
        raise TrainingError("No feature columns specified")

    # 2) Asegurar features numéricos
    X, numeric_cols = _ensure_numeric_features(df, feature_cols)

    # 3) Preparar target numérico (maneja yes/no -> 1/0)
    y, mask = _prepare_target(df, target_col)
    X = X.loc[mask]

    if len(X) == 0:
        raise TrainingError(
            f"No quedan filas válidas después de preparar el target '{target_col}'. "
            "Verifica que esa columna tenga valores adecuados y que el ETL no esté eliminando todo."
        )

    if len(X) < 2:
        raise TrainingError(
            f"Solo hay {len(X)} muestra(s) válida(s) después del filtrado; "
            "se necesitan al menos 2 para hacer train/test split."
        )

    # 4) Split de entrenamiento/prueba
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    # 5) Seleccionar y entrenar modelos
    models = _select_algorithms(algorithms)
    results: Dict[str, Dict[str, Any]] = {}
    predictions: Dict[str, Dict[str, np.ndarray]] = {}

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        metrics_dict = _compute_metrics(y_test, y_pred)
        results[name] = {
            "metrics": metrics_dict,
            "feature_cols": numeric_cols,
        }
        predictions[name] = {"y_true": y_test.to_numpy(), "y_pred": np.array(y_pred)}

    if metric_primary not in ["rmse", "mae", "mse", "r2"]:
        raise TrainingError("Unsupported primary metric")

    def metric_key(item):
        m = item[1]["metrics"][metric_primary]
        return m if metric_primary != "r2" else -m

    best_name, _ = min(results.items(), key=metric_key)
    best_preds = predictions.get(best_name, {})

    plots = plots_service.generate_regression_plots(
        training_run_id=training_run_id,
        metric_primary=metric_primary,
        results=results,
        best_model_name=best_name,
        y_true_best=best_preds.get("y_true"),
        y_pred_best=best_preds.get("y_pred"),
    )

    return {
        "training_run_id": training_run_id,
        "etl_run_id": meta["etl_run_id"],
        "etl_config_id": etl_config_id,
        "dataset_id": meta["dataset_id"],
        "metric_primary": metric_primary,
        "models": results,
        "best_model": {
            "name": best_name,
            "metrics": results[best_name]["metrics"],
        },
        "plots": plots,
        "explanation": f"Seleccionado {best_name} por menor {metric_primary.upper()} entre los modelos evaluados.",
    }
