# Pipeline ETL (Extracción, Transformación y Carga)

Arquitectura modular: `etl/extract.py`, `etl/transform.py`, `etl/load.py`, `etl/run_etl.py`.

Cómo usar

1. Activar el entorno configurado (VS Code ya configuró `.venv`).
2. Instalar dependencias: `pip install -r requirements.txt` (ya se instaló en este entorno durante la sesión).
3. Ejecutar pipeline completo (procesado streaming para `pool_swaps.csv`):

```powershell
C:/Users/adpj8/OneDrive/Escritorio/DataWarehouse_PF/.venv/Scripts/python.exe -m etl.run_etl
```

Salidas

- `data/processed/Bank_Price_Data_China_new.processed.csv`
- `data/processed/final_dataset_tata_motors.processed.csv`
- `data/processed/pool_swaps.processed.csv` (escrito en streaming por chunks)
- Logs e informes parciales en `reports/`.

Diseño y contratos

- extract.read_csv_full(filename) -> pd.DataFrame
- extract.read_csv_chunks(filename, chunksize) -> iterable de DataFrame chunks
- transform.\* funciones: reciben DataFrame(s) y devuelven DataFrame limpio/transformado
- load.write_processed_df(df, filename, mode) -> escribe o concatena en `data/processed`

Consideraciones

- `pool_swaps.csv` se procesa por chunks para evitar cargar todo en memoria.
- Las transformaciones aplicadas incluyen parseo de fechas, coerción numérica y cálculo de cantidades UI a partir de `decimals`.
- El pipeline está modular: puedes llamar a `etl.etl_bank_prices()` o `etl.etl_tata()` de forma independiente.
