import os
import pandas as pd

BASE = os.path.join(os.path.dirname(__file__), '..', 'data')


def path_for(filename: str) -> str:
    return os.path.join(BASE, filename)


def read_csv_full(filename: str, **kwargs) -> pd.DataFrame:
    """Leer CSV completo con pandas (para archivos pequeños/medianos)."""
    path = path_for(filename)
    return pd.read_csv(path, **kwargs)


def read_csv_chunks(filename: str, chunksize: int = 200000, **kwargs):
    """Generador de chunks para archivos grandes."""
    path = path_for(filename)
    return pd.read_csv(path, chunksize=chunksize, **kwargs)


def list_data_files():
    return [
        path_for('Bank_Price_Data_China new.csv'),
        path_for('final_dataset_tata_motors.csv'),
        path_for('pool_swaps.csv'),
    ]
