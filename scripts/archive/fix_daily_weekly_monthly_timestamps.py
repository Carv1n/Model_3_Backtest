"""
Fix timestamp alignment for Daily, Weekly, Monthly data
Oanda gives us candle OPEN time, TradingView shows candle CLOSE time
We need to shift timestamps FORWARD to match TradingView
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import DATA_PATH
import pandas as pd

def fix_timestamps():
    """Fix timestamps for D, W, M timeframes to match TradingView"""
    
    print("="*60)
    print("FIXING DAILY, WEEKLY, MONTHLY TIMESTAMPS")
    print("="*60 + "\n")
    
    # Timeframes that need fixing and their shift amounts
    timeframe_shifts = {
        'D': pd.Timedelta(days=1),      # Shift forward 1 day
        'W': pd.Timedelta(days=7),      # Shift forward 1 week
        'M': pd.DateOffset(months=1)    # Shift forward 1 month
    }
    
    # Process both UTC and UTC+1
    for timezone in ['UTC', 'UTC+1']:
        print(f"\n{'='*60}")
        print(f"Processing {timezone} timezone...")
        print(f"{'='*60}\n")
        
        for tf, shift in timeframe_shifts.items():
            print(f"Fixing {tf}...")
            
            # Fix CSV files
            csv_folder = DATA_PATH / timezone / tf
            
            if not csv_folder.exists():
                print(f"  ⊘ {timezone}/{tf} folder not found, skipping...")
                continue
            
            csv_files = sorted(csv_folder.glob(f"*_{tf}_{timezone}.csv"))
            
            if not csv_files:
                print(f"  No CSV files found")
                continue
            
            for csv_file in csv_files:
                try:
                    # Read CSV
                    df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                    
                    # Shift timestamps FORWARD (to show candle close to match TradingView)
                    df.index = df.index + shift
                    
                    # Save
                    df.to_csv(csv_file)
                    
                    pair_name = csv_file.stem.split('_')[0]
                    print(f"  ✓ {pair_name}: {len(df)} candles, shifted by {shift}")
                    
                except Exception as e:
                    print(f"  ✗ {csv_file.name}: Error - {e}")
            
            # Fix Parquet file
            parquet_file = DATA_PATH / timezone / f"All_Pairs_{tf}_{timezone}.parquet"
            
            if parquet_file.exists():
                try:
                    print(f"\n  Fixing Parquet: {parquet_file.name}...")
                    
                    # Read Parquet
                    df = pd.read_parquet(parquet_file)
                    
                    # Get time index (MultiIndex with pair, time)
                    if isinstance(df.index, pd.MultiIndex):
                        time_idx = df.index.get_level_values('time')
                        # Shift timestamps FORWARD
                        time_idx = time_idx + shift
                        # Update index
                        df.index = df.index.set_levels(time_idx, level='time')
                    else:
                        df.index = df.index + shift
                    
                    # Save
                    df.to_parquet(parquet_file)
                    
                    print(f"  ✓ Parquet updated, shifted by {shift}\n")
                    
                except Exception as e:
                    print(f"  ✗ Parquet error: {e}\n")
    
    print("\n" + "="*60)
    print("✓ TIMESTAMP FIXES COMPLETE")
    print("="*60)
    print("\nD, W, M timestamps now show candle CLOSE time (matches TradingView)")


if __name__ == "__main__":
    fix_timestamps()
