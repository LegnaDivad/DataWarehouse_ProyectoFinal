#!/usr/bin/env python3
"""eda.py

Realiza un Análisis Exploratorio de Datos (EDA) para los CSV en la carpeta data/.
Genera un informe markdown en reports/EDA_REPORT.md, resúmenes CSV y figuras en reports/figs/.

Notas:
- Para archivos grandes (ej. pool_swaps.csv) hace lectura por chunks y muestreo por reservoir.
"""
import os
import math
import csv
from collections import defaultdict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

BASE = os.path.join(os.path.dirname(__file__))
DATA_DIR = BASE
REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
FIG_DIR = os.path.join(REPORT_DIR, "figs")
os.makedirs(REPORT_DIR, exist_ok=True)
os.makedirs(FIG_DIR, exist_ok=True)

FILES = [
    os.path.join(DATA_DIR, 'Bank_Price_Data_China new.csv'),
    os.path.join(DATA_DIR, 'final_dataset_tata_motors.csv'),
    os.path.join(DATA_DIR, 'pool_swaps.csv'),
]


def summarize_df(df: pd.DataFrame, name: str):
    summary = {}
    summary['rows'] = int(df.shape[0])
    summary['cols'] = int(df.shape[1])
    summary['dtypes'] = df.dtypes.astype(str).to_dict()
    summary['null_counts'] = df.isna().sum().to_dict()
    # descriptive stats for numeric
    num = df.select_dtypes(include=[np.number])
    if not num.empty:
        desc = num.describe().T
        summary['numeric_describe'] = desc.to_dict(orient='index')
    else:
        summary['numeric_describe'] = {}
    # save summary CSV
    out_csv = os.path.join(REPORT_DIR, f'summary_{name}.csv')
    pd.DataFrame({k: [v] for k, v in {'rows': summary['rows'], 'cols': summary['cols']}.items()}).to_csv(out_csv, index=False)
    return summary


def detect_outliers_series(s: pd.Series):
    # uses IQR and z-score
    s_clean = s.dropna()
    if s_clean.empty:
        return {}
    q1 = s_clean.quantile(0.25)
    q3 = s_clean.quantile(0.75)
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    mean = s_clean.mean()
    std = s_clean.std()
    iqr_mask = (s < low) | (s > high)
    z_mask = std > 0
    if z_mask:
        z_mask = ((s - mean).abs() > 3 * std)
    else:
        z_mask = pd.Series(False, index=s.index)
    out = {
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'low': low,
        'high': high,
        'mean': mean,
        'std': std,
        'n_outliers_iqr': int(iqr_mask.sum()),
        'n_outliers_z': int(z_mask.sum()),
    }
    return out


def eda_full():
    report_lines = []
    report_lines.append('# Informe EDA')
    report_lines.append('Este informe fue generado automáticamente por `data/eda.py`. Contiene: estructura, calidad, resumen estadístico y detección de anomalías para cada archivo en `data/`.')

    for path in FILES:
        name = os.path.basename(path)
        report_lines.append(f'\n## Archivo: {name}\n')
        report_lines.append(f'- Ruta: `{path}`')
        if 'pool_swaps.csv' in name:
            # procesar por chunks con muestreo
            report_lines.append('- Estrategia: lectura por chunks (muestrado + Welford para medias/var) debido al tamaño potencial).')
            chunk_size = 200000
            # reservoir sample of rows (keep up to sample_size rows)
            sample_size = 50000
            reservoir = []
            rng = np.random.RandomState(42)
            total = 0
            # aggregators
            nulls = defaultdict(int)
            numeric_welford = {}
            col_names = None
            for chunk in pd.read_csv(path, chunksize=chunk_size):
                if col_names is None:
                    col_names = list(chunk.columns)
                total += len(chunk)
                for c in chunk.columns:
                    nulls[c] += int(chunk[c].isna().sum())
                # numeric columns
                for c in chunk.select_dtypes(include=[np.number]).columns:
                    arr = chunk[c].dropna().values
                    if c not in numeric_welford:
                        numeric_welford[c] = {'n': 0, 'mean': 0.0, 'M2': 0.0, 'min': None, 'max': None}
                    w = numeric_welford[c]
                    for v in arr:
                        w['n'] += 1
                        delta = v - w['mean']
                        w['mean'] += delta / w['n']
                        delta2 = v - w['mean']
                        w['M2'] += delta * delta2
                        if w['min'] is None or v < w['min']:
                            w['min'] = v
                        if w['max'] is None or v > w['max']:
                            w['max'] = v
                # reservoir sampling rows
                for idx, row in chunk.iterrows():
                    if len(reservoir) < sample_size:
                        reservoir.append(row)
                    else:
                        j = rng.randint(0, total)
                        if j < sample_size:
                            reservoir[j] = row
            report_lines.append(f'- Filas procesadas (aprox): {total}')
            # make dataframe from reservoir
            if reservoir:
                samp_df = pd.DataFrame(reservoir)
            else:
                samp_df = pd.DataFrame(columns=col_names)
            # compile numeric summary from welford
            numeric_summary = {}
            for c, w in numeric_welford.items():
                n = w['n']
                mean = w['mean'] if n>0 else np.nan
                var = (w['M2']/ (n-1)) if n>1 else np.nan
                std = math.sqrt(var) if (var==var) else np.nan
                numeric_summary[c] = {'count': n, 'mean': mean, 'std': std, 'min': w['min'], 'max': w['max']}
            # nulls
            report_lines.append('\n### Calidad / Nulos')
            report_lines.append('\n- Conteo nulos por columna (muestra):')
            for c, cnt in nulls.items():
                report_lines.append(f'  - {c}: {cnt}')
            # outlier detection on sample numeric columns
            report_lines.append('\n### Detección de anomalías (muestra)')
            for c in samp_df.select_dtypes(include=[np.number]).columns:
                out = detect_outliers_series(samp_df[c])
                report_lines.append(f' - Columna `{c}`: IQR outliers (muestra) = {out.get("n_outliers_iqr",0)}, z-outliers (muestra) = {out.get("n_outliers_z",0)}; q1={out.get("q1"):}, q3={out.get("q3"):}')
                # save histogram
                try:
                    plt.figure(figsize=(6,3))
                    sns.histplot(samp_df[c].dropna(), bins=50, kde=False)
                    plt.title(f'{name} - {c}')
                    plt.tight_layout()
                    figpath = os.path.join(FIG_DIR, f'{name}_{c}.png')
                    plt.savefig(figpath)
                    plt.close()
                except Exception:
                    pass
            # write sample to CSV for inspection
            samp_df.head(200).to_csv(os.path.join(REPORT_DIR, f'sample_{name}.csv'), index=False)
            # write numeric summary
            pd.DataFrame.from_dict(numeric_summary, orient='index').to_csv(os.path.join(REPORT_DIR, f'numeric_summary_{name}.csv'))

        else:
            # cargar completamente
            df = pd.read_csv(path)
            s = summarize_df(df, name)
            report_lines.append(f'- Filas: {s["rows"]}, Columnas: {s["cols"]}')
            report_lines.append('- Tipos detectados (muestra):')
            for k, v in list(s['dtypes'].items())[:20]:
                report_lines.append(f'  - {k}: {v}')
            report_lines.append('\n- Nulos (primeras 20 columnas):')
            for k, v in list(s['null_counts'].items())[:20]:
                report_lines.append(f'  - {k}: {v}')
            # numeric describe
            num = df.select_dtypes(include=[np.number])
            if not num.empty:
                desc = num.describe().T
                # save describe
                desc.to_csv(os.path.join(REPORT_DIR, f'describe_{name}.csv'))
                # outlier detection
                report_lines.append('\n### Detección de anomalías')
                for c in num.columns:
                    out = detect_outliers_series(df[c])
                    report_lines.append(f' - Columna `{c}`: IQR outliers = {out.get("n_outliers_iqr",0)}, z-outliers = {out.get("n_outliers_z",0)}')
                    # plot
                    try:
                        plt.figure(figsize=(6,3))
                        sns.histplot(df[c].dropna(), bins=50)
                        plt.title(f'{name} - {c}')
                        plt.tight_layout()
                        figpath = os.path.join(FIG_DIR, f'{name}_{c}.png')
                        plt.savefig(figpath)
                        plt.close()
                    except Exception:
                        pass

    # write report
    report_path = os.path.join(REPORT_DIR, 'EDA_REPORT.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    print('EDA completado. Informe:', report_path)


if __name__ == '__main__':
    eda_full()
