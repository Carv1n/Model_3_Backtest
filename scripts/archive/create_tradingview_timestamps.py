"""
Create TradingView-compatible timestamps from Oanda UTC data.

This script adjusts Oanda's timestamps to match TradingView's labeling:
- Daily: 21:00 UTC → 00:00 UTC next day (+3 hours)
- Weekly: Friday 21:00 → Monday 00:00 (+3 days + 3 hours)
- Monthly: Month-end 21:00 → Next month 00:00 (+1 day + 3 hours)
- H1/H4/3D: Keep as-is (already aligned)

Original Oanda data remains in UTC/ folder.
Adjusted data goes to UTC_TradingView/ folder.
"""

import pandas as pd
from pathlib import Path
import shutil

def adjust_timestamp_for_tradingview(df, timeframe):
    """
    Adjust Oanda timestamps to match TradingView conventions.
    
    Oanda:
    - Daily closes at 21:00 UTC (17:00 EST)
    - Weekly closes at 21:00 UTC on Friday
    - Monthly closes at 21:00 UTC on last day
    
    TradingView:
    - Daily closes at 00:00 UTC (midnight)
    - Weekly closes at 00:00 UTC on Monday
    - Monthly closes at 00:00 UTC on 1st of month
    """
    
    if timeframe in ['H1', 'H4', '3D']:
        # These are already aligned
        return df
    
    elif timeframe == 'D':
        # Shift from 21:00 to 00:00 next day (+3 hours)
        df.index = df.index + pd.Timedelta(hours=3)
        return df
    
    elif timeframe == 'W':
        # Shift from Friday 21:00 to Monday 00:00 (+3 days + 3 hours)
        df.index = df.index + pd.Timedelta(days=3, hours=3)
        return df
    
    elif timeframe == 'M':
        # Shift from month-end 21:00 to next month 1st 00:00 (+3 hours, then next day)
        # This is complex because month lengths vary
        new_index = []
        for timestamp in df.index:
            # Add 3 hours to get to midnight
            new_ts = timestamp + pd.Timedelta(hours=3)
            new_index.append(new_ts)
        df.index = pd.DatetimeIndex(new_index)
        return df
    
    return df

def process_timezone_folder(source_path, dest_path):
    """Process all timeframes from source to destination with adjusted timestamps."""
    
    print(f"\nProcessing: {source_path.name} → {dest_path.name}")
    print("=" * 70)
    
    # Create destination folders
    dest_path.mkdir(parents=True, exist_ok=True)
    
    for timeframe in ['H1', 'H4', 'D', '3D', 'W', 'M']:
        print(f"\n{timeframe}:")
        
        source_tf_folder = source_path / timeframe
        dest_tf_folder = dest_path / timeframe
        dest_tf_folder.mkdir(exist_ok=True)
        
        if not source_tf_folder.exists():
            print(f"  ⚠ Source folder not found, skipping")
            continue
        
        # Process each CSV
        for csv_file in sorted(source_tf_folder.glob("*.csv")):
            df = pd.read_csv(csv_file, parse_dates=[0], index_col=0)
            
            # Adjust timestamps
            df_adjusted = adjust_timestamp_for_tradingview(df, timeframe)
            
            # Save to destination
            dest_file = dest_tf_folder / csv_file.name.replace("_UTC.", "_UTC_TradingView.")
            df_adjusted.to_csv(dest_file)
            
            if timeframe in ['D', 'W', 'M']:
                print(f"  ✓ {csv_file.stem}: {df.index[0]} → {df_adjusted.index[0]}")
            else:
                print(f"  ✓ {csv_file.stem}: No change (aligned)")
        
        # Create Parquet file
        print(f"  Creating Parquet...")
        all_pairs = []
        
        for csv_file in sorted(dest_tf_folder.glob("*.csv")):
            pair = csv_file.stem.replace(f"_{timeframe}_UTC_TradingView", "")
            df = pd.read_csv(csv_file, parse_dates=[0], index_col=0)
            df['pair'] = pair
            all_pairs.append(df)
        
        if all_pairs:
            combined = pd.concat(all_pairs)
            combined = combined.reset_index()
            combined.columns = ['time', 'open', 'high', 'low', 'close', 'volume', 'pair']
            combined = combined.set_index(['pair', 'time'])
            combined = combined.sort_index()
            
            parquet_file = dest_path / f"All_Pairs_{timeframe}_UTC_TradingView.parquet"
            combined.to_parquet(parquet_file)
            print(f"  ✓ Parquet: {len(combined)} bars, {combined.index.get_level_values('pair').nunique()} pairs")

def main():
    base_path = Path(__file__).parent.parent / "data"
    
    print("=" * 70)
    print("CREATING TRADINGVIEW-COMPATIBLE TIMESTAMPS")
    print("=" * 70)
    print("\nThis will:")
    print("1. Keep original Oanda data in UTC/ folder")
    print("2. Create adjusted data in UTC_TradingView/ folder")
    print("\nTimestamp adjustments:")
    print("  - Daily: 21:00 UTC → 00:00 UTC next day (+3h)")
    print("  - Weekly: Friday 21:00 → Monday 00:00 (+3d +3h)")
    print("  - Monthly: Month-end 21:00 → 1st 00:00 (+3h)")
    print("  - H1/H4/3D: No change (already aligned)")
    print("=" * 70)
    
    # Process UTC → UTC_TradingView
    source_utc = base_path / "UTC"
    dest_tv = base_path / "UTC_TradingView"
    
    if not source_utc.exists():
        print("\n✗ ERROR: UTC folder not found!")
        print("  Run 0_complete_fresh_download.py first")
        return
    
    process_timezone_folder(source_utc, dest_tv)
    
    print("\n" + "=" * 70)
    print("✓ COMPLETE! TRADINGVIEW-COMPATIBLE DATA CREATED")
    print("=" * 70)
    print("\nFolder structure:")
    print("  - UTC/: Original Oanda timestamps (21:00 close)")
    print("  - UTC_TradingView/: TradingView timestamps (00:00 close)")
    print("\nBoth are valid for backtesting!")
    print("Use UTC_TradingView/ for COT/Seasonality alignment.")

if __name__ == "__main__":
    main()
