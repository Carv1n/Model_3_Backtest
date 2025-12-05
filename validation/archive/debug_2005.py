import pandas as pd
from pathlib import Path

# Load data
data_dir = Path(__file__).parent.parent / "data"
df = pd.read_parquet(data_dir / "3D_all_pairs.parquet")
df = df.reset_index()
df = df[df['pair'] == 'GBPUSD'].copy()
df = df.reset_index(drop=True)

df['time'] = pd.to_datetime(df['time'])

# Find 2005-09-29 in the data
target = df[df['time'].dt.strftime('%Y-%m-%d') == '2005-09-29']
print(f"Rows with 2005-09-29: {len(target)}")
if len(target) > 0:
    idx = target.index[0]
    print(f"Found at index {idx}")
    
    # Show context
    start = max(0, idx - 2)
    end = min(len(df), idx + 3)
    print(f"\nContext (indices {start}-{end}):")
    print(df.iloc[start:end][['time', 'open', 'high', 'low', 'close']].to_string())
    
    # Check body percentages for pivot detection
    if idx > 0:
        prev = df.iloc[idx - 1]
        curr = df.iloc[idx]
        
        def body_pct(row):
            rng = row['high'] - row['low']
            if rng == 0:
                return 0.0
            body = abs(row['close'] - row['open'])
            return (body / rng) * 100.0
        
        prev_body = body_pct(prev)
        curr_body = body_pct(curr)
        
        print(f"\nPivot detection check:")
        print(f"  K1 (prev) close < open: {prev['close'] < prev['open']} (body: {prev_body:.1f}%)")
        print(f"  K2 (curr) close > open: {curr['close'] > curr['open']} (body: {curr_body:.1f}%)")
        print(f"  Both body >= 10%: {prev_body >= 10 and curr_body >= 10}")
