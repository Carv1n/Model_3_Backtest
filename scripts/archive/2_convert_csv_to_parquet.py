import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import *
import pandas as pd
from collections import defaultdict

def convert_csv_to_parquet():
    """Convert all CSV files to single Parquet files per timeframe"""
    
    print("MODEL X - CONVERT CSV TO PARQUET")
    print("="*60 + "\n")
    
    for tf in TIMEFRAMES:
        csv_folder = DATA_PATH / f"{tf}_raw"
        
        if not csv_folder.exists():
            print(f"⚠ No CSV data for {tf} found. Skipping...")
            continue
        
        print(f"Converting {tf}...")
        
        # Collect all CSV files for this timeframe
        csv_files = sorted(csv_folder.glob("*.csv"))
        
        if not csv_files:
            print(f"  ✗ No CSV files found in {csv_folder}")
            continue
        
        all_pairs_data = {}
        error_pairs = []
        
        for csv_file in csv_files:
            pair_name = csv_file.stem  # Filename without .csv
            
            try:
                df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                
                # Validate data
                if len(df) == 0:
                    print(f"  ⚠ {pair_name}: Empty dataset, skipping")
                    error_pairs.append(pair_name)
                    continue
                
                all_pairs_data[pair_name] = df
                print(f"  ✓ Loaded {pair_name}: {len(df)} candles")
                
            except Exception as e:
                print(f"  ✗ Error loading {pair_name}: {e}")
                error_pairs.append(pair_name)
        
        if not all_pairs_data:
            print(f"  ✗ No valid data for {tf}")
            continue
        
        # Combine all pairs into MultiIndex DataFrame
        try:
            combined = pd.concat(all_pairs_data, names=['pair', 'time'])
            
            # Save as Parquet
            output_file = DATA_PATH / f"{tf}_all_pairs.parquet"
            combined.to_parquet(output_file)
            
            print(f"\n  ✓ Saved {tf}: {output_file}")
            print(f"    - Total pairs: {len(all_pairs_data)}")
            print(f"    - Total candles: {len(combined)}")
            print(f"    - Date range: {combined.index.get_level_values('time').min()} to {combined.index.get_level_values('time').max()}")
            
            if error_pairs:
                print(f"    - Skipped pairs: {', '.join(error_pairs)}")
            
            print()
            
        except Exception as e:
            print(f"  ✗ Error combining {tf} data: {e}")

def create_3d_from_daily():
    """3D data is manually added from TradingView exports"""
    
    print("="*60)
    print("3D DATA - MANUAL IMPORT FROM TRADINGVIEW")
    print("="*60 + "\n")
    
    csv_folder = DATA_PATH / "3D_raw"
    
    if not csv_folder.exists():
        print("⚠ WARNING: 3D_raw folder not found!")
        print("  Please add your TradingView 3D exports to data/3D_raw/")
        print("  Example: data/3D_raw/EURUSD.csv, data/3D_raw/GBPUSD.csv, etc.")
        return
    
    csv_files = list(csv_folder.glob("*.csv"))
    
    if not csv_files:
        print("⚠ WARNING: No 3D CSV files found in data/3D_raw/")
        print("  Please export 3D data from TradingView and place in data/3D_raw/")
        return
    
    print(f"✓ Found {len(csv_files)} 3D CSV files in 3D_raw folder")
    print("  3D data will be processed with other timeframes")
    return

def verify_data():
    """Show sample data for verification"""
    
    print("\n" + "="*60)
    print("DATA VERIFICATION")
    print("="*60 + "\n")
    
    # Check EURUSD H1
    h1_file = DATA_PATH / "H1_all_pairs.parquet"
    
    if not h1_file.exists():
        print("⚠ H1 data not found")
        return
    
    try:
        df = pd.read_parquet(h1_file)
        
        if 'EURUSD' in df.index.get_level_values('pair'):
            eurusd = df.loc['EURUSD']
            
            print("EURUSD H1 - Last 10 candles:\n")
            print(eurusd.tail(10))
            
            print("\n" + "="*60)
            print("✓ Verify these values with TradingView!")
            print("="*60)
        else:
            print("⚠ EURUSD not found in H1 data")
            
    except Exception as e:
        print(f"✗ Error verifying data: {e}")

if __name__ == "__main__":
    convert_csv_to_parquet()
    create_3d_from_daily()
    verify_data()
    
    print("\n" + "="*60)
    print("✓ CONVERSION COMPLETE!")
    print("="*60)
