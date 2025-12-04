import pandas as pd
from pathlib import Path

# Load 3D data
data_dir = Path(__file__).parent.parent / 'data'
df = pd.read_parquet(data_dir / '3D_all_pairs.parquet')

# Filter for GBPUSD and around 2005-09-26 to 2005-10-02
df = df.reset_index()
df = df[df['pair'] == 'GBPUSD'].copy()
df['time'] = pd.to_datetime(df['time'])

# Find rows around 2005-09-26
result = df[(df['time'] >= '2005-09-24') & (df['time'] <= '2005-10-03')][['time', 'open', 'high', 'low', 'close']]
print("3D GBPUSD data around 2005-09-26:")
print(result.to_string())

# Find the pivot rows (indices)
all_rows = df[(df['time'] >= '2005-09-24') & (df['time'] <= '2005-10-03')].copy()
all_rows['index'] = range(len(all_rows))
print("\nWith indices:")
print(all_rows[['index', 'time', 'open', 'high', 'low', 'close']].to_string())
