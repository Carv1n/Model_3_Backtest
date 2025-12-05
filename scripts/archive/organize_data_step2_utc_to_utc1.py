"""
Step 2: Convert UTC data to UTC+1 (Berlin timezone)
Converts: UTC/H1/AUDCAD_H1_UTC.csv → UTC+1/H1/AUDCAD_H1_UTC+1.csv
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import DATA_PATH
import pandas as pd

def convert_utc_to_utc1():
    """Convert UTC data to UTC+1 (Berlin) timezone"""
    
    print("="*60)
    print("STEP 2: CONVERT UTC → UTC+1 (BERLIN TIMEZONE)")
    print("="*60 + "\n")
    
    # Timeframes to process
    timeframes = ['H1', 'H4', 'D', '3D', 'W', 'M']
    
    total_converted = 0
    
    for tf in timeframes:
        utc_folder = DATA_PATH / "UTC" / tf
        utc1_folder = DATA_PATH / "UTC+1" / tf
        
        if not utc_folder.exists():
            print(f"⊘ UTC/{tf} folder not found, skipping...")
            continue
        
        # Create UTC+1 subfolder
        utc1_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing {tf}...")
        
        # Find all UTC CSV files
        csv_files = sorted(utc_folder.glob("*_UTC.csv"))
        
        if not csv_files:
            print(f"  No UTC CSV files found in {tf}")
            continue
        
        for csv_file in csv_files:
            try:
                # Read CSV
                df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                
                # Localize to UTC if not already timezone-aware
                if df.index.tz is None:
                    df.index = df.index.tz_localize('UTC')
                
                # Convert to Europe/Berlin (UTC+1 winter, UTC+2 summer with DST)
                df.index = df.index.tz_convert('Europe/Berlin')
                
                # Remove timezone info (make naive) but keep Berlin time
                df.index = df.index.tz_localize(None)
                
                # New filename: Replace _UTC with _UTC+1
                pair_tf = csv_file.stem.replace('_UTC', '')  # e.g., AUDCAD_H1
                new_name = f"{pair_tf}_UTC+1.csv"
                new_path = utc1_folder / new_name
                
                # Save
                df.to_csv(new_path)
                
                print(f"  ✓ {csv_file.name} → {new_name}")
                total_converted += 1
                
            except Exception as e:
                print(f"  ✗ {csv_file.name}: Error - {e}")
    
    print("\n" + "="*60)
    print(f"✓ STEP 2 COMPLETE: {total_converted} files converted to UTC+1/")
    print("="*60)


if __name__ == "__main__":
    convert_utc_to_utc1()
