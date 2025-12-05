"""
Rebuild Weekly and Monthly data from Daily data for BOTH UTC and UTC+1.

This ensures proper aggregation matching TradingView's logic:
- Weekly: Aggregates Monday-Friday, timestamp = Friday 22:00 UTC (or 23:00 UTC+1)
- Monthly: Aggregates full month, timestamp = last trading day 22:00/23:00

The key insight: Oanda's pre-aggregated W/M data doesn't match TradingView.
We must aggregate from Daily ourselves.
"""

import pandas as pd
from pathlib import Path
import sys

def aggregate_to_weekly(daily_df, timezone_suffix):
    """
    Aggregate daily data to weekly bars.
    
    Weekly bar = Monday 00:00 to Friday close
    Timestamp = Friday at 22:00 (UTC) or 23:00 (UTC+1)
    """
    # Determine close hour based on timezone
    close_hour = 22 if timezone_suffix == 'UTC' else 23
    
    # Resample to weekly, anchoring on Friday
    weekly = daily_df.resample('W-FRI').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    # Remove incomplete weeks (NaN values)
    weekly = weekly.dropna()
    
    # Ensure timestamps are at correct hour (22:00 for UTC, 23:00 for UTC+1)
    weekly.index = weekly.index.map(lambda x: x.replace(hour=close_hour, minute=0, second=0))
    
    return weekly

def aggregate_to_monthly(daily_df, timezone_suffix):
    """
    Aggregate daily data to monthly bars.
    
    Monthly bar = Full calendar month
    Timestamp = Last trading day at 22:00 (UTC) or 23:00 (UTC+1)
    """
    # Determine close hour based on timezone
    close_hour = 22 if timezone_suffix == 'UTC' else 23
    
    # Resample to monthly (end of month)
    monthly = daily_df.resample('M').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    # Remove incomplete months
    monthly = monthly.dropna()
    
    # Ensure timestamps are at correct hour
    monthly.index = monthly.index.map(lambda x: x.replace(hour=close_hour, minute=0, second=0))
    
    return monthly

def process_pair_for_timezone(pair_name, timezone_path, timezone_suffix):
    """Process one pair for one timezone: rebuild W and M from D."""
    
    print(f"\n  {pair_name} ({timezone_suffix})")
    
    # Paths
    daily_path = timezone_path / "D" / f"{pair_name}_D_{timezone_suffix}.csv"
    weekly_path = timezone_path / "W" / f"{pair_name}_W_{timezone_suffix}.csv"
    monthly_path = timezone_path / "M" / f"{pair_name}_M_{timezone_suffix}.csv"
    
    # Load daily data
    daily_df = pd.read_csv(daily_path, parse_dates=[0], index_col=0)
    
    # Aggregate weekly
    weekly_df = aggregate_to_weekly(daily_df, timezone_suffix)
    weekly_df.to_csv(weekly_path)
    print(f"    Weekly: {len(weekly_df)} bars ({weekly_df.index[0]} to {weekly_df.index[-1]})")
    
    # Aggregate monthly
    monthly_df = aggregate_to_monthly(daily_df, timezone_suffix)
    monthly_df.to_csv(monthly_path)
    print(f"    Monthly: {len(monthly_df)} bars ({monthly_df.index[0]} to {monthly_df.index[-1]})")

def rebuild_parquet_files(timezone_path, timeframe, timezone_suffix):
    """Rebuild combined parquet file from individual CSVs."""
    
    print(f"\n  Building {timeframe} Parquet for {timezone_suffix}...")
    
    csv_dir = timezone_path / timeframe
    all_data = []
    
    for csv_file in sorted(csv_dir.glob(f"*_{timeframe}_{timezone_suffix}.csv")):
        pair = csv_file.stem.replace(f'_{timeframe}_{timezone_suffix}', '')
        
        df = pd.read_csv(csv_file, parse_dates=[0], index_col=0)
        df['pair'] = pair
        all_data.append(df)
    
    if not all_data:
        print(f"    WARNING: No CSV files found!")
        return
    
    # Combine all pairs
    combined = pd.concat(all_data)
    combined = combined.reset_index()
    combined = combined.set_index(['pair', 'time'])
    combined = combined.sort_index()
    
    # Save parquet
    parquet_path = timezone_path / f"All_Pairs_{timeframe}_{timezone_suffix}.parquet"
    combined.to_parquet(parquet_path)
    
    print(f"    ✓ {parquet_path.name}: {len(combined)} total bars, {combined.index.get_level_values('pair').nunique()} pairs")

def main():
    base_path = Path(__file__).parent.parent / "data"
    
    print("=" * 70)
    print("REBUILDING WEEKLY AND MONTHLY FROM DAILY DATA")
    print("=" * 70)
    print("\nProcessing both UTC and UTC+1 timezones")
    print("This ensures W/M data matches TradingView aggregation logic")
    print("\nStrategy:")
    print("  1. Load Daily data (already correct)")
    print("  2. Aggregate to Weekly (Monday-Friday, timestamp=Friday close)")
    print("  3. Aggregate to Monthly (full month, timestamp=month end)")
    print("  4. Rebuild Parquet files")
    print("=" * 70)
    
    # Get list of all pairs from UTC Daily folder
    utc_daily_dir = base_path / "UTC" / "D"
    pairs = []
    
    for daily_file in sorted(utc_daily_dir.glob("*_D_UTC.csv")):
        pair_name = daily_file.stem.replace('_D_UTC', '')
        pairs.append(pair_name)
    
    print(f"\nFound {len(pairs)} currency pairs\n")
    
    # Process UTC timezone
    print("=" * 70)
    print("PROCESSING UTC TIMEZONE")
    print("=" * 70)
    
    utc_path = base_path / "UTC"
    for pair in pairs:
        process_pair_for_timezone(pair, utc_path, "UTC")
    
    print("\n  Rebuilding Parquet files...")
    rebuild_parquet_files(utc_path, "W", "UTC")
    rebuild_parquet_files(utc_path, "M", "UTC")
    
    # Process UTC+1 timezone
    print("\n" + "=" * 70)
    print("PROCESSING UTC+1 TIMEZONE")
    print("=" * 70)
    
    utc1_path = base_path / "UTC+1"
    for pair in pairs:
        process_pair_for_timezone(pair, utc1_path, "UTC+1")
    
    print("\n  Rebuilding Parquet files...")
    rebuild_parquet_files(utc1_path, "W", "UTC+1")
    rebuild_parquet_files(utc1_path, "M", "UTC+1")
    
    print("\n" + "=" * 70)
    print("✓ REBUILD COMPLETE")
    print("=" * 70)
    print("\nAll Weekly and Monthly data has been rebuilt from Daily data")
    print("Both UTC and UTC+1 timezones processed")
    print("Data now matches TradingView aggregation logic")

if __name__ == "__main__":
    main()
