import pandas as pd
from pathlib import Path
import pytz

def load_data_with_fallback(timeframe, pair):
    """Load data from Parquet or CSV with proper header handling."""
    data_dir = Path(__file__).parent.parent / "data"
    
    # Try Parquet first (for 3D which has no raw folder)
    parquet_path = data_dir / f"{timeframe}_all_pairs.parquet"
    print(f"Loading from {parquet_path}")
    df = pd.read_parquet(parquet_path)
    # Check if MultiIndex (pair, time)
    if isinstance(df.index, pd.MultiIndex):
        # Reset index to get pair and time as columns
        df = df.reset_index()
        # Filter for the specific pair
        df = df[df['pair'] == pair].copy()
    return df

# Load data
df = load_data_with_fallback('3D', 'GBPUSD')

# Find 2005-09-29
df['time'] = pd.to_datetime(df['time'])
print(f"DataFrame shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")

k2_row = df[df['time'].dt.strftime('%Y-%m-%d') == '2005-09-29'].iloc[0]
k2_idx = df[df['time'].dt.strftime('%Y-%m-%d') == '2005-09-29'].index[0]
print(f"\nK2 (2005-09-29):")
print(f"  Index in full DF: {k2_idx}")
print(f"  Time: {k2_row['time']}")

# Now simulate what export does
pivot_complete_idx = k2_idx
valid_idx = pivot_complete_idx + 1

print(f"\nExport calculation:")
print(f"  pivot_complete_idx = {pivot_complete_idx}")
print(f"  valid_idx = {valid_idx}")
print(f"  df.iloc[valid_idx]['time'] = {df.iloc[valid_idx]['time']}")
