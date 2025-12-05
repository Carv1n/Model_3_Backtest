import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from export_pivot_gaps import load_data_with_fallback, detect_pivots_tv_style

# Load data
df = load_data_with_fallback('3D', 'GBPUSD')
print(f"Loaded DF shape: {df.shape}")

# Detect pivots
pivots = detect_pivots_tv_style(df, pair='GBPUSD')

# Find the pivot at generated_date 2005-09-26
target_date = pd.Timestamp('2005-09-26', tz='UTC')
df['time'] = pd.to_datetime(df['time'])

matching_pivots = []
for p in pivots:
    idx = p['index']
    if idx < len(df):
        k2_time = df.iloc[idx]['time']
        if k2_time.date() == target_date.date():
            matching_pivots.append((idx, p))

print(f"\nFound {len(matching_pivots)} pivots with K2 on 2005-09-26")

for idx, p in matching_pivots:
    direction = 'bullish' if p['is_bullish'] else 'bearish'
    print(f"\nPivot {direction} at index {idx}:")
    print(f"  K2 (pivot_complete_idx = {idx}): {df.iloc[idx]['time']}")
    
    valid_idx = idx + 1
    if valid_idx < len(df):
        print(f"  K3 (valid_idx = {valid_idx}): {df.iloc[valid_idx]['time']}")
    else:
        print(f"  K3 (valid_idx = {valid_idx}): OUT OF BOUNDS")
    
    if idx > 0:
        print(f"  K1 (prev at {idx-1}): {df.iloc[idx-1]['time']}")
