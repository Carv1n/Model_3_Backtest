"""
Step 1: Organize raw data into UTC folder with proper naming
Converts: H1_raw/AUDCAD.csv → UTC/H1/AUDCAD_H1_UTC.csv
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import DATA_PATH
import shutil

def organize_raw_to_utc():
    """Copy and rename raw data files to UTC folder structure"""
    
    print("="*60)
    print("STEP 1: ORGANIZE RAW DATA → UTC FOLDER")
    print("="*60 + "\n")
    
    # Timeframes to process
    timeframes = ['H1', 'H4', 'D', '3D', 'W', 'M']
    
    total_copied = 0
    
    for tf in timeframes:
        raw_folder = DATA_PATH / f"{tf}_raw"
        utc_folder = DATA_PATH / "UTC" / tf
        
        if not raw_folder.exists():
            print(f"⊘ {tf}_raw folder not found, skipping...")
            continue
        
        # Create UTC subfolder
        utc_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing {tf}...")
        
        # Find all CSV files
        csv_files = sorted(raw_folder.glob("*.csv"))
        
        if not csv_files:
            print(f"  No CSV files found in {tf}_raw")
            continue
        
        for csv_file in csv_files:
            pair_name = csv_file.stem  # e.g., AUDCAD
            
            # New filename: AUDCAD_H1_UTC.csv
            new_name = f"{pair_name}_{tf}_UTC.csv"
            new_path = utc_folder / new_name
            
            # Copy file
            shutil.copy2(csv_file, new_path)
            
            print(f"  ✓ {csv_file.name} → {new_name}")
            total_copied += 1
    
    print("\n" + "="*60)
    print(f"✓ STEP 1 COMPLETE: {total_copied} files organized into UTC/")
    print("="*60)


if __name__ == "__main__":
    organize_raw_to_utc()
