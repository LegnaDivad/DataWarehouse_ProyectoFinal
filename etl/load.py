import os
import pandas as pd

PROCESSED_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
os.makedirs(PROCESSED_DIR, exist_ok=True)


def write_processed_df(df: pd.DataFrame, filename: str, mode: str = 'w'):
    """Write processed DataFrame to disk.

    Parameters
    - df: DataFrame to write
    - filename: output filename (used as-is under data/processed)
    - mode: 'w' (write) or 'a' (append). Append is supported only for CSV without compression.

    By default writes CSV encoded as UTF-8. If filename ends with '.parquet' and pyarrow
    is available, will write parquet instead.
    Returns the absolute path written.
    """
    path = os.path.join(PROCESSED_DIR, filename)
    _, ext = os.path.splitext(filename.lower())

    # atomic write helper: write to temp then replace
    def _atomic_replace(tmp_path, final_path):
        os.replace(tmp_path, final_path)

    # Parquet path
    if ext == '.parquet':
        try:
            # prefer pyarrow if installed
            import pyarrow  # noqa: F401
            engine = 'pyarrow'
        except Exception:
            engine = None
        if mode == 'a':
            # append to parquet is non-trivial; raise for now
            raise ValueError('Append mode not supported for parquet outputs')
        tmp = path + '.tmp'
        if engine:
            df.to_parquet(tmp, engine=engine, index=False)
        else:
            # fallback: use pandas default (may error if no engine)
            df.to_parquet(tmp, index=False)
        _atomic_replace(tmp, path)
        return path

    # default: CSV
    # only allow append for plain CSV (no compression)
    if mode == 'a':
        # if file doesn't exist, behave like write
        if not os.path.exists(path):
            mode = 'w'

    if mode == 'w':
        tmp = path + '.tmp'
        # ensure utf-8 encoding explicitly
        df.to_csv(tmp, index=False, encoding='utf-8')
        _atomic_replace(tmp, path)
    else:
        # append mode
        # write to a temporary file then append to final to avoid partial header issues
        tmp = path + '.tmp'
        df.to_csv(tmp, index=False, encoding='utf-8', header=False)
        # open the tmp and append its bytes to the target file
        with open(path, 'ab') as f_out, open(tmp, 'rb') as f_in:
            f_out.write(f_in.read())
        os.remove(tmp)

    return path
