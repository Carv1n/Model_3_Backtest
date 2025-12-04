import pandas as pd
from pathlib import Path

# Load 3D data
data_dir = Path(__file__).parent.parent / 'data'
df = pd.read_parquet(data_dir / '3D_all_pairs.parquet')

# Filter for GBPUSD
df = df.reset_index()
df = df[df['pair'] == 'GBPUSD'].copy()
df['time'] = pd.to_datetime(df['time'])
df = df.reset_index(drop=True)

# Find the specific pivot: generated 2005-09-26, valid should be 2005-10-02
# The pivot should be at index where K2 is 2005-09-29

# Find 2005-09-29 (K2)
k2_idx = df[df['time'] == '2005-09-29'].index[0]
print(f"K2 (2005-09-29) is at index: {k2_idx}")
print(f"K1 (prev) at {k2_idx-1}: {df.iloc[k2_idx-1]['time']}")
print(f"K2 (curr) at {k2_idx}: {df.iloc[k2_idx]['time']}")
print(f"K3 (next) at {k2_idx+1}: {df.iloc[k2_idx+1]['time']}")

# Now check detect_pivots logic
# The loop in detect_pivots goes: for i in range(1, len(df))
# which means at i=k2_idx, prev=K1, curr=K2
# So pivot['index'] = k2_idx = K2 index

print(f"\nSo when detect_pivots finds pivot at i={k2_idx}:")
print(f"  pivot['index'] = {k2_idx} (K2 timestamp: {df.iloc[k2_idx]['time']})")
print(f"  In export: pivot_complete_idx = {k2_idx} (should be K2)")
print(f"  In export: valid_idx = pivot_complete_idx + 1 = {k2_idx + 1}")
print(f"  valid_idx timestamp = {df.iloc[k2_idx + 1]['time']} (should be K3)")
