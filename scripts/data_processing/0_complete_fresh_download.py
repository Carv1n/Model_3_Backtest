"""
MASTER SCRIPT: Complete data download and organization from scratch.

This script will:
1. Download ALL data fresh from Oanda (H1, H4, D, W, M)
2. Create 3D data from Daily data (aggregate every 3 days)
3. Organize everything into UTC folder with consistent timestamps
4. Create Parquet files

Everything will be synchronized and consistent - ALL IN UTC!
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import *
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
import pandas as pd
import time
import shutil

# Oanda API Client
client = API(access_token=OANDA_API_KEY, environment=OANDA_ACCOUNT_TYPE)

def download_pair_data(pair, granularity):
    """Download ALL available historical data for one pair and timeframe"""
    
    print(f"  Downloading {pair} - {granularity}...")
    
    params = {
        "granularity": granularity,
        "count": 5000
    }
    
    all_candles = []
    batch_count = 0
    
    while True:
        try:
            r = instruments.InstrumentsCandles(instrument=pair, params=params)
            response = client.request(r)
            
            candles = response.get('candles', [])
            if not candles:
                break
                
            all_candles.extend(candles)
            batch_count += 1
            
            oldest_time = candles[0]['time']
            params['to'] = oldest_time
            
            if batch_count % 10 == 0:
                print(f"    Batch {batch_count}: {len(all_candles)} total candles")
            
            time.sleep(0.5)
            
            if len(candles) < 5000:
                break
                
        except Exception as e:
            print(f"    ⚠ Error: {e}")
            break
    
    if not all_candles:
        return None
    
    data = []
    for candle in all_candles:
        if candle['complete']:
            data.append({
                'time': pd.to_datetime(candle['time'], utc=True),
                'open': float(candle['mid']['o']),
                'high': float(candle['mid']['h']),
                'low': float(candle['mid']['l']),
                'close': float(candle['mid']['c']),
                'volume': int(candle['volume'])
            })
    
    if not data:
        return None
    
    df = pd.DataFrame(data)
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    
    # Make timezone-naive but keep UTC values (for consistency)
    if df.index.tz is not None:
        df.index = df.index.tz_localize(None)
    
    print(f"    ✓ {len(df)} candles: {df.index[0]} to {df.index[-1]}")
    
    return df

def create_3d_from_daily(daily_df):
    """Create 3D (3-day) data from daily data"""
    print(f"    Creating 3D from Daily...")
    
    # Resample to 3-day periods
    df_3d = daily_df.resample('3D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    
    # Remove incomplete periods
    df_3d = df_3d.dropna()
    
    print(f"    ✓ {len(df_3d)} 3D candles created")
    return df_3d

def main():
    print("=" * 70)
    print("COMPLETE DATA DOWNLOAD AND ORGANIZATION - FRESH START")
    print("=" * 70)
    print("\nThis will:")
    print("1. Download H1, H4, D, W, M from Oanda (overwrites raw folders)")
    print("2. Create 3D from Daily data")
    print("3. Organize into UTC folder")
    print("4. Create Parquet files (UTC only)")
    print("\nAll data will be synchronized and consistent - ALL IN UTC!")
    print("=" * 70)
    
    input("\nPress ENTER to start clean download (or Ctrl+C to cancel)...")
    
    # Granularity mapping
    timeframes_oanda = {
        "H1": "H1",
        "H4": "H4",
        "D": "D",
        "W": "W",
        "M": "M"
    }
    
    # Step 1: Download all timeframes from Oanda
    print("\n" + "=" * 70)
    print("STEP 1: DOWNLOADING FROM OANDA")
    print("=" * 70)
    
    all_data = {}  # Store all downloaded data
    
    for tf, gran in timeframes_oanda.items():
        print(f"\n{tf} Timeframe:")
        print("-" * 50)
        
        # Create raw folder
        raw_folder = DATA_PATH / f"{tf}_raw"
        if raw_folder.exists():
            print(f"  Cleaning old {tf}_raw folder...")
            shutil.rmtree(raw_folder)
        raw_folder.mkdir(parents=True, exist_ok=True)
        
        all_data[tf] = {}
        
        for pair in PAIRS:
            df = download_pair_data(pair, gran)
            
            if df is not None:
                pair_clean = pair.replace("_", "")
                
                # Save to raw
                csv_file = raw_folder / f"{pair_clean}.csv"
                df.to_csv(csv_file)
                
                all_data[tf][pair_clean] = df
            
            time.sleep(0.2)
    
    # Step 2: Create 3D from Daily
    print("\n" + "=" * 70)
    print("STEP 2: CREATING 3D FROM DAILY DATA")
    print("=" * 70)
    
    raw_3d_folder = DATA_PATH / "3D_raw"
    if raw_3d_folder.exists():
        shutil.rmtree(raw_3d_folder)
    raw_3d_folder.mkdir(parents=True, exist_ok=True)
    
    all_data["3D"] = {}
    
    for pair_clean, daily_df in all_data["D"].items():
        print(f"\n  {pair_clean}")
        df_3d = create_3d_from_daily(daily_df)
        
        csv_file = raw_3d_folder / f"{pair_clean}.csv"
        df_3d.to_csv(csv_file)
        
        all_data["3D"][pair_clean] = df_3d
    
    # Step 3: Organize into UTC folder
    print("\n" + "=" * 70)
    print("STEP 3: ORGANIZING INTO UTC FOLDER")
    print("=" * 70)
    
    utc_path = DATA_PATH / "UTC"
    if utc_path.exists():
        print("  Cleaning old UTC folder...")
        shutil.rmtree(utc_path)
    utc_path.mkdir(parents=True, exist_ok=True)
    
    for tf in ["H1", "H4", "D", "3D", "W", "M"]:
        tf_folder = utc_path / tf
        tf_folder.mkdir(exist_ok=True)
        
        print(f"\n  {tf}:")
        for pair_clean, df in all_data[tf].items():
            output_file = tf_folder / f"{pair_clean}_{tf}_UTC.csv"
            df.to_csv(output_file)
            print(f"    ✓ {output_file.name}")
    
    # Step 4: Create Parquet files
    print("\n" + "=" * 70)
    print("STEP 4: CREATING PARQUET FILES (UTC)")
    print("=" * 70)
    
    for tf in ["H1", "H4", "D", "3D", "W", "M"]:
        tf_folder = utc_path / tf
        all_pairs = []
        
        print(f"\n  {tf}:")
        for csv_file in sorted(tf_folder.glob(f"*_{tf}_UTC.csv")):
            pair = csv_file.stem.replace(f"_{tf}_UTC", "")
            df = pd.read_csv(csv_file, parse_dates=[0], index_col=0)
            df['pair'] = pair
            all_pairs.append(df)
        
        if all_pairs:
            combined = pd.concat(all_pairs)
            combined = combined.reset_index()
            combined = combined.set_index(['pair', 'time'])
            combined = combined.sort_index()
            
            parquet_file = utc_path / f"All_Pairs_{tf}_UTC.parquet"
            combined.to_parquet(parquet_file)
            print(f"    ✓ {parquet_file.name}: {len(combined)} bars, {combined.index.get_level_values('pair').nunique()} pairs")
    
    print("\n" + "=" * 70)
    print("✓ COMPLETE! ALL DATA DOWNLOADED AND ORGANIZED")
    print("=" * 70)
    print("\nData structure:")
    print("  - UTC folder: All timeframes (H1, H4, D, 3D, W, M)")
    print("  - Parquet files: Combined data for fast loading")
    print("  - 3D data: Created from Daily aggregation")
    print("\nEverything is synchronized and consistent - ALL IN UTC!")
    print("Ready for backtesting!")

if __name__ == "__main__":
    main()
