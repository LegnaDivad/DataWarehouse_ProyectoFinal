"""Orquestador ETL: permite ejecutar extract/transform/load por dataset y completo.

Uso:
  python -m etl.run_etl  # ejecuta todo
  from etl.run_etl import run_all
"""
import os
from etl import extract, transform, load
import pandas as pd
import logging

BASE = os.path.join(os.path.dirname(__file__), '..')
REPORTS = os.path.join(BASE, 'reports')
os.makedirs(REPORTS, exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger('etl')


def etl_bank_prices(progress_callback=None, run_id=None):
    """Run ETL for bank prices. Optionally call progress_callback(run_id, stage, info)."""
    stage = 'bank_prices'
    logger.info('ETL -> Bank_Price_Data_China new.csv')
    if progress_callback:
        progress_callback(run_id, stage, {'status': 'started'})
    df = extract.read_csv_full('Bank_Price_Data_China new.csv')
    df_t = transform.transform_bank_prices(df)
    out = load.write_processed_df(df_t, 'Bank_Price_Data_China_new.processed.csv')
    logger.info('Wrote %s', out)
    if progress_callback:
        progress_callback(run_id, stage, {'status': 'finished', 'output': out, 'rows': len(df_t)})


def etl_tata(progress_callback=None, run_id=None):
    stage = 'tata_motors'
    logger.info('ETL -> final_dataset_tata_motors.csv')
    if progress_callback:
        progress_callback(run_id, stage, {'status': 'started'})
    df = extract.read_csv_full('final_dataset_tata_motors.csv')
    df_t = transform.transform_tata(df)
    out = load.write_processed_df(df_t, 'final_dataset_tata_motors.processed.csv')
    logger.info('Wrote %s', out)
    if progress_callback:
        progress_callback(run_id, stage, {'status': 'finished', 'output': out, 'rows': len(df_t)})


def etl_pool_swaps(chunksize: int = 200000, progress_callback=None, run_id=None):
    stage = 'pool_swaps'
    logger.info('ETL -> pool_swaps.csv (streaming)')
    if progress_callback:
        progress_callback(run_id, stage, {'status': 'started'})
    reader = extract.read_csv_chunks('pool_swaps.csv', chunksize=chunksize)
    first = True
    total_rows = 0
    chunk_idx = 0
    for chunk in reader:
        chunk_idx += 1
        total_rows += len(chunk)
        # transform chunk
        chunk_t = transform.transform_pool_swaps_chunk(chunk)
        # write out
        mode = 'w' if first else 'a'
        load.write_processed_df(chunk_t, 'pool_swaps.processed.csv', mode=mode)
        first = False
        logger.info('Processed chunk rows=%d', len(chunk))
        if progress_callback:
            progress_callback(run_id, stage, {'status': 'chunk_processed', 'chunk_index': chunk_idx, 'chunk_rows': len(chunk), 'total_rows': total_rows})
    logger.info('Completed pool_swaps. total_rows=%d', total_rows)
    if progress_callback:
        progress_callback(run_id, stage, {'status': 'finished', 'total_rows': total_rows})


def run_all(progress_callback=None, run_id=None, pool_chunksize: int = 200000):
    """Run the full ETL pipeline.

    progress_callback(run_id, stage, info) will be called if provided.
    """
    etl_bank_prices(progress_callback=progress_callback, run_id=run_id)
    etl_tata(progress_callback=progress_callback, run_id=run_id)
    etl_pool_swaps(chunksize=pool_chunksize, progress_callback=progress_callback, run_id=run_id)


if __name__ == '__main__':
    run_all()
