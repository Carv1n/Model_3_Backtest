import pandas as pd
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from export_pivot_gaps import load_data_with_fallback, detect_pivots_tv_style

# Load just GBPUSD
df = load_data_with_fallback('3D', 'GBPUSD')
print(f"Loaded DF shape: {df.shape}")
print(f"DF Index range: 0 to {len(df)-1}")
print(f"First row time: {df.iloc[0]['time']}")
print(f"Last row time: {df.iloc[-1]['time']}")

# Detect pivots
pivots = detect_pivots_tv_style(df, pair='GBPUSD')
print(f"\nFound {len(pivots)} pivots")

# Find pivots for 2005-09-29
df['time'] = pd.to_datetime(df['time'])
target_date = pd.Timestamp('2005-09-29', tz='UTC')

matching_pivots = [p for p in pivots if p['index'] < len(df) and df.iloc[p['index']]['time'].date() == target_date.date()]
print(f"\nPivots with K2 on 2005-09-29: {len(matching_pivots)}")

for p in matching_pivots[:2]:
    idx = p['index']
    if idx < len(df):
        k2_time = df.iloc[idx]['time']
        print(f"  Pivot at index {idx} (K2 time: {k2_time}, direction: {'bullish' if p['is_bullish'] else 'bearish'})")
        if idx + 1 < len(df):
            k3_time = df.iloc[idx + 1]['time']
            print(f"    Next candle (valid_idx={idx+1}): {k3_time}")
