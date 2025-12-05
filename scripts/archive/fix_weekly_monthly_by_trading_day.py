"""
Fix Weekly and Monthly timestamps by shifting forward by ONE TRADING DAY.

Weekly: Friday -> Monday (+3 days)
Monthly: Last trading day of month -> First trading day of next month
"""

import pandas as pd
from pathlib import Path
import sys

def shift_to_next_trading_day(timestamp, timeframe):
    """
    Shift timestamp to next trading day.
    
    Weekly: Friday 23:00 -> Monday 23:00 (+3 days)
    Monthly: More complex - need to skip weekends
    """
    if timeframe == 'W':
        # Weekly bars close on Friday, shift to Monday (+3 days)
        return timestamp + pd.Timedelta(days=3)
    elif timeframe == 'M':
        # Monthly: shift forward until we hit a weekday
        new_timestamp = timestamp + pd.Timedelta(days=1)
        while new_timestamp.weekday() >= 5:  # 5=Saturday, 6=Sunday
            new_timestamp += pd.Timedelta(days=1)
        return new_timestamp
    return timestamp

def fix_csv_timestamps(csv_path, timeframe):
    """Fix timestamps in CSV file."""
    print(f"\nProcessing: {csv_path.name}")
    
    df = pd.read_csv(csv_path, parse_dates=[0], index_col=0)
    print(f"  Original first timestamp: {df.index[0]}")
    print(f"  Original last timestamp: {df.index[-1]}")
    
    # Shift all timestamps
    df.index = df.index.map(lambda x: shift_to_next_trading_day(x, timeframe))
    
    print(f"  New first timestamp: {df.index[0]}")
    print(f"  New last timestamp: {df.index[-1]}")
    
    # Save back
    df.to_csv(csv_path)
    print(f"  ✓ {csv_path.name} shifted forward by 1 trading day")

def fix_parquet_timestamps(parquet_path, timeframe):
    """Fix timestamps in Parquet file."""
    print(f"\nProcessing Parquet: {parquet_path.name}")
    
    df = pd.read_parquet(parquet_path)
    
    # Get original time index
    time_idx = df.index.get_level_values('time')
    print(f"  Original first timestamp: {time_idx[0]}")
    print(f"  Original last timestamp: {time_idx[-1]}")
    
    # Shift all timestamps
    new_time_idx = time_idx.map(lambda x: shift_to_next_trading_day(x, timeframe))
    
    # Rebuild MultiIndex
    new_index = pd.MultiIndex.from_arrays(
        [df.index.get_level_values('pair'), new_time_idx],
        names=['pair', 'time']
    )
    df.index = new_index
    
    print(f"  New first timestamp: {df.index.get_level_values('time')[0]}")
    print(f"  New last timestamp: {df.index.get_level_values('time')[-1]}")
    
    # Save back
    df.to_parquet(parquet_path)
    print(f"  ✓ {parquet_path.name} shifted forward by 1 trading day")

def main():
    base_path = Path(__file__).parent.parent / "data" / "UTC+1"
    
    print("=" * 60)
    print("FIXING WEEKLY AND MONTHLY TIMESTAMPS")
    print("Shift: +1 TRADING DAY (not +1 bar)")
    print("Weekly: Friday -> Monday (+3 days)")
    print("Monthly: Last trading day -> First trading day of next month")
    print("=" * 60)
    
    # Fix Weekly CSVs
    print("\n--- Processing Weekly CSVs ---")
    weekly_csv_dir = base_path / "W"
    for csv_file in sorted(weekly_csv_dir.glob("*.csv")):
        fix_csv_timestamps(csv_file, 'W')
    
    # Fix Monthly CSVs
    print("\n--- Processing Monthly CSVs ---")
    monthly_csv_dir = base_path / "M"
    for csv_file in sorted(monthly_csv_dir.glob("*.csv")):
        fix_csv_timestamps(csv_file, 'M')
    
    # Fix Weekly Parquet
    print("\n--- Processing Weekly Parquet ---")
    weekly_parquet = base_path / "All_Pairs_W_UTC+1.parquet"
    if weekly_parquet.exists():
        fix_parquet_timestamps(weekly_parquet, 'W')
    
    # Fix Monthly Parquet
    print("\n--- Processing Monthly Parquet ---")
    monthly_parquet = base_path / "All_Pairs_M_UTC+1.parquet"
    if monthly_parquet.exists():
        fix_parquet_timestamps(monthly_parquet, 'M')
    
    print("\n" + "=" * 60)
    print("✓ WEEKLY AND MONTHLY TIMESTAMP FIX COMPLETE")
    print("=" * 60)
    print("\nWeekly timestamps shifted forward +3 days (Friday -> Monday)")
    print("Monthly timestamps shifted forward to next trading day")

if __name__ == "__main__":
    main()
