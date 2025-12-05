"""
Step 3: Convert CSV files to Parquet format for both UTC and UTC+1
Creates: All_Pairs_H1_UTC.parquet and All_Pairs_H1_UTC+1.parquet
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import DATA_PATH
import pandas as pd

def create_parquet_files():
    """Create Parquet files for all timeframes in both UTC and UTC+1"""
    
    print("="*60)
    print("STEP 3: CREATE PARQUET FILES")
    print("="*60 + "\n")
    
    # Timeframes to process
    timeframes = ['H1', 'H4', 'D', '3D', 'W', 'M']
    
    # Process both UTC and UTC+1
    for timezone in ['UTC', 'UTC+1']:
        print(f"\n{'='*60}")
        print(f"Processing {timezone} timezone...")
        print(f"{'='*60}\n")
        
        for tf in timeframes:
            tf_folder = DATA_PATH / timezone / tf
            
            if not tf_folder.exists():
                print(f"⊘ {timezone}/{tf} folder not found, skipping...")
                continue
            
            print(f"Converting {tf}...")
            
            # Find all CSV files for this timeframe
            csv_pattern = f"*_{tf}_{timezone}.csv"
            csv_files = sorted(tf_folder.glob(csv_pattern))
            
            if not csv_files:
                print(f"  No CSV files found")
                continue
            
            all_pairs_data = {}
            
            for csv_file in csv_files:
                try:
                    # Extract pair name (e.g., AUDCAD from AUDCAD_H1_UTC.csv)
                    pair_name = csv_file.stem.split('_')[0]
                    
                    # Read CSV
                    df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                    
                    if len(df) == 0:
                        print(f"  ⚠️  {pair_name}: Empty dataset, skipping")
                        continue
                    
                    all_pairs_data[pair_name] = df
                    print(f"  ✓ Loaded {pair_name}: {len(df)} candles")
                    
                except Exception as e:
                    print(f"  ✗ Error loading {csv_file.name}: {e}")
            
            if not all_pairs_data:
                print(f"  No valid data for {tf}")
                continue
            
            # Combine all pairs into MultiIndex DataFrame
            try:
                combined = pd.concat(all_pairs_data, names=['pair', 'time'])
                
                # Save as Parquet in the timezone folder root
                output_file = DATA_PATH / timezone / f"All_Pairs_{tf}_{timezone}.parquet"
                combined.to_parquet(output_file)
                
                print(f"\n  ✓ Saved: {output_file.name}")
                print(f"    - Total pairs: {len(all_pairs_data)}")
                print(f"    - Total candles: {len(combined)}")
                print(f"    - Date range: {combined.index.get_level_values('time').min()} to {combined.index.get_level_values('time').max()}")
                print()
                
            except Exception as e:
                print(f"  ✗ Error creating Parquet: {e}")
    
    print("\n" + "="*60)
    print("✓ STEP 3 COMPLETE: All Parquet files created")
    print("="*60)


if __name__ == "__main__":
    create_parquet_files()
