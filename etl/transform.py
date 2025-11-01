import pandas as pd
import numpy as np
import math
from typing import Iterable


def clean_numeric_column(series: pd.Series) -> pd.Series:
    """Asegura que una serie sea numérica: quita espacios, comas, convierte a float; coerce errors."""
    if series.dtype == object:
        s = series.str.strip().str.replace(',', '').str.replace('\u00A0', '')
        # Replace leading zeros that look like '04.06' -> keep as '4.06' only if leading zero before dot
        s = s.str.replace(r'^0+(?=\.)', '', regex=True)
        return pd.to_numeric(s, errors='coerce')
    else:
        return pd.to_numeric(series, errors='coerce')


def transform_bank_prices(df: pd.DataFrame) -> pd.DataFrame:
    # Parse Date DD/MM/YYYY
    df = df.copy()
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
    # Convert all other columns to numeric
    for c in df.columns:
        if c != 'Date':
            df[c] = clean_numeric_column(df[c])
    return df


def transform_tata(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # timestamp -> datetime aware
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    # date -> date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    # Clean numeric columns
    for c in df.columns:
        if c not in ['timestamp', 'date']:
            df[c] = clean_numeric_column(df[c])
    return df


def transform_pool_swaps_chunk(df: pd.DataFrame) -> pd.DataFrame:
    """Transformaciones por chunk para pool_swaps:
    - convertir cantidades a numéricas
    - calcular token_amount_*_ui si no existe, usando decimals
    - parsear fecha
    """
    df = df.copy()
    # parse date/block_time
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    elif 'block_time' in df.columns:
        df['date'] = pd.to_datetime(df['block_time'], unit='s', errors='coerce')

    # numeric coercion
    for c in df.columns:
        if c.startswith('token_amount') or c.endswith('_usd') or c in ['slot', 'num_swaps', 'decimals_a', 'decimals_b']:
            df[c] = clean_numeric_column(df[c])

    # compute UI columns if available
    if 'token_amount_a' in df.columns and 'decimals_a' in df.columns:
        df['token_amount_a_ui_calc'] = df.apply(lambda r: (r['token_amount_a'] / (10 ** int(r['decimals_a']))) if (pd.notna(r['token_amount_a']) and pd.notna(r['decimals_a'])) else np.nan, axis=1)
    if 'token_amount_b' in df.columns and 'decimals_b' in df.columns:
        df['token_amount_b_ui_calc'] = df.apply(lambda r: (r['token_amount_b'] / (10 ** int(r['decimals_b']))) if (pd.notna(r['token_amount_b']) and pd.notna(r['decimals_b'])) else np.nan, axis=1)

    return df


def detect_anomalies_numeric(series: pd.Series):
    s = series.dropna()
    if s.empty:
        return {}
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    mask = (series < low) | (series > high)
    return {
        'q1': q1,
        'q3': q3,
        'iqr': iqr,
        'low': low,
        'high': high,
        'n_outliers': int(mask.sum()),
    }
