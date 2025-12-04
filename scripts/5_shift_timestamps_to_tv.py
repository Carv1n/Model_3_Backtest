"""
Shift Berlin-localized timestamps to align with TradingView candle naming convention.
- Daily: shift to next day (name by close time, not open time)
- Weekly: shift to Monday 00:00 (TradingView weekly close = Sunday 23:00, but shown as Monday bar)
- Monthly: shift to next month (name by month end, shown as first bar of next month in TV)

This fixes the 1-day offset issue.
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_PATH


def shift_daily_to_tv_convention(df):
    """Shift by +1 day (simple time shift, timezone-agnostic)."""
    df.index = df.index + pd.Timedelta(days=1)
    return df


def shift_weekly_to_tv_convention(df):
    """Shift by +2 days and normalize to 00:00."""
    df.index = df.index + pd.Timedelta(days=2)
    df.index = df.index.floor('D')
    return df


def shift_monthly_to_tv_convention(df):
    """Shift by +1 day and normalize to 00:00."""
    df.index = df.index + pd.Timedelta(days=1)
    df.index = df.index.floor('D')
    return df


def shift_3d_to_tv_convention(df):
    """Shift by +1 day (simple time shift, timezone-agnostic)."""
    df.index = df.index + pd.Timedelta(days=1)
    return df


def process_folder(tf: str, shift_func):
    src = DATA_PATH / f"{tf}_berlin"
    dst = DATA_PATH / f"{tf}_berlin_tv"
    dst.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(src.glob("*.csv"))
    if not csv_files:
        print(f"  ⚠ No CSV files in {src}")
        return

    all_pairs = {}
    for csv_file in csv_files:
        pair = csv_file.stem
        try:
            # Read CSV without parsing dates (to avoid TZ confusion)
            df = pd.read_csv(csv_file)
            if df.empty:
                print(f"    [W] {pair}: empty")
                continue
            
            # Parse the 'time' column as datetime (naive initially)
            df['time'] = pd.to_datetime(df['time'])
            df = df.set_index('time')
            
            # Apply shift function  
            df = shift_func(df)
            
            out = dst / csv_file.name
            # Save directly (no tz issues this way)
            df.to_csv(out)
            all_pairs[pair] = df
            print(f"    [OK] {pair}: {len(df)} rows")
        except Exception as e:
            print(f"    [FAIL] {pair}: {str(e)[:50]}")

    if not all_pairs:
        print(f"  ✗ No shifted data for {tf}")
        return

    combined = pd.concat(all_pairs, names=['pair', 'time'])
    parquet_path = DATA_PATH / f"{tf}_berlin_tv.parquet"
    combined.to_parquet(parquet_path)
    print(f"    → parquet: {parquet_path.name} ({len(combined)} rows)")


def main():
    print("SHIFT Berlin timestamps to TradingView candle convention")
    print("=" * 60)
    
    print("\n=== D (Daily) ===")
    process_folder("D", shift_daily_to_tv_convention)
    
    print("\n=== W (Weekly) ===")
    process_folder("W", shift_weekly_to_tv_convention)
    
    print("\n=== M (Monthly) ===")
    process_folder("M", shift_monthly_to_tv_convention)
    
    print("\n=== 3D (3-Day) ===")
    process_folder("3D", shift_3d_to_tv_convention)
    
    print("\n" + "=" * 60)
    print("✓ Shifted data in *_berlin_tv folders")


if __name__ == "__main__":
    main()
