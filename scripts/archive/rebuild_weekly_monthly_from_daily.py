"""
Rebuild Weekly and Monthly data from Daily data with correct timestamps and values.

The issue: We can't just shift timestamps - we need to re-aggregate from Daily data
with the correct week/month boundaries that match TradingView.

TradingView convention:
- Weekly bar timestamp = Monday (last trading day of the week)
- Weekly bar shows Sunday close to Friday close data
- Monthly bar timestamp = First trading day of new month
- Monthly bar shows previous month's data
"""

import pandas as pd
from pathlib import Path
import numpy as np

def is_trading_day(date):
    """Check if date is a trading day (Monday-Friday)."""
    return date.weekday() < 5

def get_next_trading_day(date):
    """Get next trading day after given date."""
    next_day = date + pd.Timedelta(days=1)
    while not is_trading_day(next_day):
        next_day += pd.Timedelta(days=1)
    return next_day

def aggregate_to_weekly(daily_df):
    """
    Aggregate daily data to weekly with correct TradingView convention.
    
    Weekly bar closes on Friday 23:00, but timestamp shows Monday 23:00.
    So we group by week ending Friday, then shift timestamp to Monday.
    """
    print("\n  Aggregating to weekly...")
    
    # Resample to weekly, anchoring on Friday ('W-FRI')
    weekly = daily_df.resample('W-FRI').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    # Remove any rows with NaN (incomplete weeks)
    weekly = weekly.dropna()
    
    # Shift timestamps from Friday to Monday (+3 days)
    weekly.index = weekly.index + pd.Timedelta(days=3)
    
    print(f"    Created {len(weekly)} weekly bars")
    print(f"    First: {weekly.index[0]} - Last: {weekly.index[-1]}")
    
    return weekly

def aggregate_to_monthly(daily_df):
    """
    Aggregate daily data to monthly with correct TradingView convention.
    
    Monthly bar closes on last trading day of month, but timestamp shows 
    first trading day of next month.
    """
    print("\n  Aggregating to monthly...")
    
    # Resample to monthly (end of month)
    monthly = daily_df.resample('M').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    # Remove any rows with NaN
    monthly = monthly.dropna()
    
    # Shift timestamps to first trading day of next month
    new_index = []
    for timestamp in monthly.index:
        next_trading_day = get_next_trading_day(timestamp)
        new_index.append(next_trading_day)
    
    monthly.index = pd.DatetimeIndex(new_index)
    
    print(f"    Created {len(monthly)} monthly bars")
    print(f"    First: {monthly.index[0]} - Last: {monthly.index[-1]}")
    
    return monthly

def process_pair(pair_name, daily_path, weekly_path, monthly_path):
    """Process one currency pair: rebuild weekly and monthly from daily."""
    print(f"\n{'='*60}")
    print(f"Processing: {pair_name}")
    print('='*60)
    
    # Load daily data
    daily_df = pd.read_csv(daily_path, parse_dates=[0], index_col=0)
    print(f"  Daily data: {len(daily_df)} bars")
    print(f"    First: {daily_df.index[0]}")
    print(f"    Last: {daily_df.index[-1]}")
    
    # Rebuild weekly
    weekly_df = aggregate_to_weekly(daily_df)
    weekly_df.to_csv(weekly_path)
    print(f"  ✓ Saved: {weekly_path.name}")
    
    # Rebuild monthly
    monthly_df = aggregate_to_monthly(daily_df)
    monthly_df.to_csv(monthly_path)
    print(f"  ✓ Saved: {monthly_path.name}")

def rebuild_parquet_files(base_path, timeframe):
    """Rebuild combined parquet file from individual CSVs."""
    print(f"\n{'='*60}")
    print(f"Rebuilding {timeframe} Parquet file")
    print('='*60)
    
    csv_dir = base_path / timeframe
    all_data = []
    
    for csv_file in sorted(csv_dir.glob("*_UTC+1.csv")):
        pair = csv_file.stem.replace(f'_{timeframe}_UTC+1', '')
        print(f"  Loading {pair}...")
        
        df = pd.read_csv(csv_file, parse_dates=[0], index_col=0)
        df['pair'] = pair
        all_data.append(df)
    
    # Combine all pairs
    combined = pd.concat(all_data)
    combined = combined.reset_index()
    combined = combined.set_index(['pair', 'time'])
    combined = combined.sort_index()
    
    # Save parquet
    parquet_path = base_path / f"All_Pairs_{timeframe}_UTC+1.parquet"
    combined.to_parquet(parquet_path)
    
    print(f"  ✓ Saved: {parquet_path.name}")
    print(f"    Total bars: {len(combined)}")
    print(f"    Pairs: {combined.index.get_level_values('pair').nunique()}")

def main():
    base_path = Path(__file__).parent.parent / "data" / "UTC+1"
    
    print("=" * 60)
    print("REBUILDING WEEKLY AND MONTHLY FROM DAILY DATA")
    print("=" * 60)
    print("\nThis will:")
    print("1. Load Daily data (already corrected)")
    print("2. Re-aggregate to Weekly (week ends Friday, timestamp Monday)")
    print("3. Re-aggregate to Monthly (month end -> first trading day next month)")
    print("4. Rebuild Parquet files")
    print("\nThis ensures VALUES match the TIMESTAMPS!")
    print("=" * 60)
    
    # Get all pairs from daily folder
    daily_dir = base_path / "D"
    pairs = []
    
    for daily_file in sorted(daily_dir.glob("*_D_UTC+1.csv")):
        pair_name = daily_file.stem.replace('_D_UTC+1', '')
        pairs.append(pair_name)
    
    print(f"\nFound {len(pairs)} currency pairs")
    
    # Process each pair
    for pair in pairs:
        daily_path = base_path / "D" / f"{pair}_D_UTC+1.csv"
        weekly_path = base_path / "W" / f"{pair}_W_UTC+1.csv"
        monthly_path = base_path / "M" / f"{pair}_M_UTC+1.csv"
        
        process_pair(pair, daily_path, weekly_path, monthly_path)
    
    # Rebuild parquet files
    rebuild_parquet_files(base_path, 'W')
    rebuild_parquet_files(base_path, 'M')
    
    print("\n" + "=" * 60)
    print("✓ REBUILD COMPLETE")
    print("=" * 60)
    print("\nWeekly and Monthly data now have:")
    print("- Correct timestamps (Friday->Monday, Month end->Month start)")
    print("- Correct values (re-aggregated from Daily data)")
    print("- Full alignment with TradingView")

if __name__ == "__main__":
    main()
