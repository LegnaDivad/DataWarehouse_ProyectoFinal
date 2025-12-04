import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

import matplotlib

matplotlib.use("Agg")  # headless backend
import matplotlib.pyplot as plt  # noqa: E402
import seaborn as sns  # noqa: E402
import numpy as np  # noqa: E402

BASE_DIR = Path(__file__).resolve().parents[2]
PLOTS_DIR = BASE_DIR / "static" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)


def _unique_filename(prefix: str) -> Path:
    return PLOTS_DIR / f"{prefix}_{uuid.uuid4().hex}.png"


def plot_metric_bar(results: Dict[str, Dict[str, Any]], metric: str, training_run_id: str) -> str:
    names = list(results.keys())
    values = [results[n]["metrics"][metric] for n in names]
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x=names, y=values, ax=ax)
    ax.set_title(f"{metric.upper()} comparison")
    ax.set_ylabel(metric.upper())
    for i, v in enumerate(values):
        ax.text(i, v, f"{v:.3f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    path = _unique_filename(f"{training_run_id}_{metric}_comparison")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return f"/static/plots/{path.name}"


def plot_actual_vs_pred(y_true: np.ndarray, y_pred: np.ndarray, training_run_id: str, model_name: str) -> str:
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.scatter(y_true, y_pred, alpha=0.5, s=12, label="Predicciones")
    lims = [
        np.min([ax.get_xlim(), ax.get_ylim()]),
        np.max([ax.get_xlim(), ax.get_ylim()]),
    ]
    ax.plot(lims, lims, "k--", alpha=0.6, label="y = x")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Real")
    ax.set_ylabel("Predicho")
    ax.set_title(f"Real vs Predicho ({model_name})")
    ax.legend()
    fig.tight_layout()
    path = _unique_filename(f"{training_run_id}_real_vs_pred")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return f"/static/plots/{path.name}"


def plot_residuals(y_true: np.ndarray, y_pred: np.ndarray, training_run_id: str, model_name: str) -> str:
    residuals = y_true - y_pred
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(residuals, kde=True, ax=ax, bins=30, color="steelblue")
    ax.set_title(f"Distribución de residuales ({model_name})")
    ax.set_xlabel("Residual (Real - Predicho)")
    fig.tight_layout()
    path = _unique_filename(f"{training_run_id}_residuals")
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return f"/static/plots/{path.name}"


def generate_regression_plots(
    training_run_id: str,
    metric_primary: str,
    results: Dict[str, Dict[str, Any]],
    best_model_name: str,
    y_true_best: Optional[np.ndarray] = None,
    y_pred_best: Optional[np.ndarray] = None,
) -> List[Dict[str, str]]:
    plots: List[Dict[str, str]] = []
    metric_path = plot_metric_bar(results, metric_primary, training_run_id)
    plots.append(
        {
            "path": metric_path,
            "title": f"Comparación {metric_primary.upper()}",
            "description": f"Barra comparativa de {metric_primary.upper()} (menor es mejor) entre modelos.",
        }
    )

    if y_true_best is not None and y_pred_best is not None:
        scatter_path = plot_actual_vs_pred(y_true_best, y_pred_best, training_run_id, best_model_name)
        plots.append(
            {
                "path": scatter_path,
                "title": f"Real vs predicho ({best_model_name})",
                "description": "Dispersión de valores reales vs predichos para el modelo ganador; cercanía a la diagonal indica buen ajuste.",
            }
        )
        resid_path = plot_residuals(y_true_best, y_pred_best, training_run_id, best_model_name)
        plots.append(
            {
                "path": resid_path,
                "title": f"Residuales ({best_model_name})",
                "description": "Distribución de residuales del modelo ganador; centrado en 0 indica menor sesgo.",
            }
        )
    return plots
