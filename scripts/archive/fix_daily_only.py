"""
Fix Daily timestamps only - shift back 1 day
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import DATA_PATH
import pandas as pd

def fix_daily_timestamps():
    """Fix Daily timestamps only - shift FORWARD 1 day"""
    
    print("="*60)
    print("FIXING DAILY TIMESTAMPS ONLY")
    print("="*60 + "\n")
    
    shift = pd.Timedelta(days=1)
    
    # Process both UTC and UTC+1
    for timezone in ['UTC', 'UTC+1']:
        print(f"\n{'='*60}")
        print(f"Processing {timezone} timezone...")
        print(f"{'='*60}\n")
        
        # Fix CSV files
        csv_folder = DATA_PATH / timezone / 'D'
        
        if not csv_folder.exists():
            print(f"  ⊘ {timezone}/D folder not found, skipping...")
            continue
        
        csv_files = sorted(csv_folder.glob(f"*_D_{timezone}.csv"))
        
        if not csv_files:
            print(f"  No CSV files found")
            continue
        
        for csv_file in csv_files:
            try:
                # Read CSV
                df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                
                # Shift timestamps FORWARD 1 day
                df.index = df.index + shift
                
                # Save
                df.to_csv(csv_file)
                
                pair_name = csv_file.stem.split('_')[0]
                print(f"  ✓ {pair_name}: {len(df)} candles, shifted forward +1 day")
                
            except Exception as e:
                print(f"  ✗ {csv_file.name}: Error - {e}")
        
        # Fix Parquet file
        parquet_file = DATA_PATH / timezone / f"All_Pairs_D_{timezone}.parquet"
        
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
                
                print(f"  ✓ Parquet updated, shifted forward +1 day\n")
                
            except Exception as e:
                print(f"  ✗ Parquet error: {e}\n")
    
    print("\n" + "="*60)
    print("✓ DAILY TIMESTAMP FIX COMPLETE")
    print("="*60)
    print("\nDaily timestamps shifted forward +1 day")


if __name__ == "__main__":
    fix_daily_timestamps()
