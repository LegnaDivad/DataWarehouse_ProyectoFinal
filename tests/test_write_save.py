import os
import sys
import pathlib
import pandas as pd
# ensure project root is on sys.path when running this script directly
PROJECT_ROOT = str(pathlib.Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from etl import load

print('PROCESSED_DIR:', load.PROCESSED_DIR)

df = pd.DataFrame({'a': [1,2,3], 'b': ['x','y','z']})

# write CSV
csv_path = load.write_processed_df(df, 'test_output.csv', mode='w')
print('WROTE CSV:', csv_path, os.path.exists(csv_path))

# append CSV
df2 = pd.DataFrame({'a':[4], 'b':['w']})
csv_path2 = load.write_processed_df(df2, 'test_output.csv', mode='a')
print('APPENDED CSV:', csv_path2, open(csv_path2,'r',encoding='utf-8').read())

# try parquet
try:
    pq_path = load.write_processed_df(df, 'test_output.parquet', mode='w')
    print('WROTE PARQUET:', pq_path, os.path.exists(pq_path))
except Exception as e:
    print('PARQUET WRITE FAILED:', e)

print('DONE')
