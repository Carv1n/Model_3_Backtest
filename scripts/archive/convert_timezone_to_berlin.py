"""
Convert all downloaded data from UTC to Europe/Berlin timezone
This ensures data matches TradingView which uses Berlin timezone
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import DATA_PATH
import pandas as pd

def convert_csv_files():
    """Convert all CSV files from UTC to Berlin timezone"""
    
    print("="*60)
    print("CONVERTING CSV FILES FROM UTC TO EUROPE/BERLIN")
    print("="*60 + "\n")
    
    # Find all CSV files in raw folders
    raw_folders = [f for f in DATA_PATH.iterdir() if f.is_dir() and f.name.endswith('_raw')]
    
    total_converted = 0
    
    for folder in sorted(raw_folders):
        print(f"\nConverting {folder.name}...")
        
        csv_files = sorted(folder.glob("*.csv"))
        
        if not csv_files:
            print(f"  No CSV files found")
            continue
        
        for csv_file in csv_files:
            try:
                # Read CSV with time as index
                df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                
                # Check if already timezone-aware
                if df.index.tz is None:
                    # Assume UTC and localize
                    df.index = df.index.tz_localize('UTC')
                elif df.index.tz.zone != 'UTC':
                    print(f"  ⚠️  {csv_file.name}: Already in {df.index.tz.zone}, skipping")
                    continue
                
                # Convert to Berlin timezone
                df.index = df.index.tz_convert('Europe/Berlin')
                
                # Remove timezone info (make naive) but keep Berlin time
                df.index = df.index.tz_localize(None)
                
                # Save back to CSV
                df.to_csv(csv_file)
                
                print(f"  ✓ {csv_file.name}: {len(df)} candles converted")
                total_converted += 1
                
            except Exception as e:
                print(f"  ✗ {csv_file.name}: Error - {e}")
    
    print("\n" + "="*60)
    print(f"✓ CONVERSION COMPLETE: {total_converted} files converted")
    print("="*60)


def convert_parquet_files():
    """Convert all Parquet files from UTC to Berlin timezone"""
    
    print("\n" + "="*60)
    print("CONVERTING PARQUET FILES FROM UTC TO EUROPE/BERLIN")
    print("="*60 + "\n")
    
    # Find all Parquet files
    parquet_files = sorted(DATA_PATH.glob("*_all_pairs.parquet"))
    
    if not parquet_files:
        print("No Parquet files found. Run convert_csv_to_parquet.py first.")
        return
    
    for parquet_file in parquet_files:
        try:
            print(f"Converting {parquet_file.name}...")
            
            # Read Parquet
            df = pd.read_parquet(parquet_file)
            
            # Get time index (might be MultiIndex with pair, time)
            if isinstance(df.index, pd.MultiIndex):
                time_idx = df.index.get_level_values('time')
            else:
                time_idx = df.index
            
            # Check timezone
            if time_idx.tz is None:
                # Assume UTC and localize
                time_idx = time_idx.tz_localize('UTC')
            elif time_idx.tz.zone != 'UTC':
                print(f"  ⚠️  Already in {time_idx.tz.zone}, skipping")
                continue
            
            # Convert to Berlin
            time_idx = time_idx.tz_convert('Europe/Berlin')
            
            # Remove timezone info (make naive) but keep Berlin time
            time_idx = time_idx.tz_localize(None)
            
            # Update index
            if isinstance(df.index, pd.MultiIndex):
                df.index = df.index.set_levels(time_idx, level='time')
            else:
                df.index = time_idx
            
            # Save back
            df.to_parquet(parquet_file)
            
            print(f"  ✓ Converted to Berlin timezone")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "="*60)
    print("✓ PARQUET CONVERSION COMPLETE")
    print("="*60)


def verify_conversion():
    """Verify one file to show the conversion worked"""
    
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60 + "\n")
    
    # Try to find EURUSD H1
    h1_file = DATA_PATH / "H1_all_pairs.parquet"
    
    if h1_file.exists():
        df = pd.read_parquet(h1_file)
        
        if 'EURUSD' in df.index.get_level_values('pair'):
            eurusd = df.loc['EURUSD']
            
            print("EURUSD H1 - Last 5 candles:\n")
            print(eurusd.tail(5))
            
            print("\n✓ Verify these timestamps match TradingView (Europe/Berlin)")
        else:
            print("EURUSD not found in data")
    else:
        print("H1 Parquet file not found yet")


if __name__ == "__main__":
    print("\nMODEL X - TIMEZONE CONVERSION: UTC → EUROPE/BERLIN")
    print("This makes data match TradingView timestamps\n")
    
    # Convert CSV files first
    convert_csv_files()
    
    # Then convert Parquet files
    convert_parquet_files()
    
    # Verify
    verify_conversion()
    
    print("\n" + "="*60)
    print("✓ ALL CONVERSIONS COMPLETE!")
    print("="*60)
    print("\nYour data now uses Europe/Berlin timezone (same as TradingView)")
