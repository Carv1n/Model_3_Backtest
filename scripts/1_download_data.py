import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config import *
from oandapyV20 import API
import oandapyV20.endpoints.instruments as instruments
import pandas as pd
from datetime import datetime, timedelta
import time
import json

# Oanda API Client
client = API(access_token=OANDA_API_KEY, environment=OANDA_ACCOUNT_TYPE)

# Checkpoint file to track progress
CHECKPOINT_FILE = DATA_PATH / ".download_checkpoint.json"

def load_checkpoint():
    """Load progress checkpoint"""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return {"completed_timeframes": [], "completed_pairs": {}}

def save_checkpoint(checkpoint):
    """Save progress checkpoint"""
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)

def download_pair_data(pair, granularity):
    """Download ALL available historical data for one pair and timeframe"""
    
    print(f"Downloading {pair} - {granularity}...")
    
    params = {
        "granularity": granularity,
        "count": 5000  # Max per request
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
            
            # Update from_time for next batch (go backwards)
            oldest_time = candles[0]['time']
            params['to'] = oldest_time
            
            print(f"  Batch {batch_count}: {len(candles)} candles, total: {len(all_candles)}, oldest: {oldest_time}")
            
            # Rate limiting
            time.sleep(0.5)
            
            # Stop if we got less than 5000 (reached end of data)
            if len(candles) < 5000:
                break
                
        except Exception as e:
            print(f"  ⚠ Error in batch {batch_count}: {e}")
            print(f"  Continuing with {len(all_candles)} candles already fetched...")
            break
    
    # Convert to DataFrame
    if not all_candles:
        print(f"  ✗ No data for {pair}")
        return None
    
    data = []
    for candle in all_candles:
        if candle['complete']:  # Only complete candles
            data.append({
                'time': pd.to_datetime(candle['time']),
                'open': float(candle['mid']['o']),
                'high': float(candle['mid']['h']),
                'low': float(candle['mid']['l']),
                'close': float(candle['mid']['c']),
                'volume': int(candle['volume'])
            })
    
    if not data:
        print(f"  ✗ No complete candles for {pair}")
        return None
    
    df = pd.DataFrame(data)
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    
    print(f"  ✓ Downloaded {len(df)} complete candles from {df.index[0]} to {df.index[-1]}")
    
    return df

def save_pair_data_csv(pair_name, df, timeframe):
    """Save individual pair data as CSV (checkpoint)"""
    csv_file = DATA_PATH / f"{timeframe}_raw" / f"{pair_name}.csv"
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(csv_file)
    print(f"    → Saved CSV: {csv_file.name}")
    return csv_file

def download_all_data():
    """Download all pairs and timeframes with checkpointing"""
    
    # Oanda granularity mapping
    granularity_map = {
        "H1": "H1",
        "H4": "H4",
        "D": "D",
        "W": "W",
        "M": "M"
    }
    
    checkpoint = load_checkpoint()
    
    for tf in TIMEFRAMES:
        print(f"\n{'='*60}")
        print(f"TIMEFRAME: {tf}")
        print(f"{'='*60}\n")
        
        if tf in checkpoint["completed_timeframes"]:
            print(f"⊘ {tf} already downloaded. Skipping...")
            continue
        
        if tf not in checkpoint["completed_pairs"]:
            checkpoint["completed_pairs"][tf] = []
        
        csv_count = 0
        
        for pair in PAIRS:
            if pair in checkpoint["completed_pairs"][tf]:
                print(f"⊘ {pair} already downloaded. Skipping...")
                continue
            
            df = download_pair_data(pair, granularity_map[tf])
            
            if df is not None:
                # Save individual CSV file immediately (safe checkpoint)
                pair_clean = pair.replace("_", "")
                save_pair_data_csv(pair_clean, df, tf)
                csv_count += 1
                
                # Update checkpoint
                checkpoint["completed_pairs"][tf].append(pair)
                save_checkpoint(checkpoint)
            
            # Small delay between pairs
            time.sleep(0.2)
        
        if csv_count > 0:
            print(f"\n✓ Downloaded {csv_count} pairs for {tf} as CSV files")
            # Mark timeframe as complete
            checkpoint["completed_timeframes"].append(tf)
            save_checkpoint(checkpoint)
        else:
            print(f"\n✗ No new data downloaded for {tf}")
    
    print("\n" + "="*60)
    print("✓ DOWNLOAD COMPLETE - All data saved as CSV!")
    print("="*60)
    print(f"Next step: Run '2_convert_csv_to_parquet.py' to convert to Parquet")
    print("="*60)


if __name__ == "__main__":
    print("MODEL X - DATA DOWNLOAD (ALL AVAILABLE DATA → CSV)")
    print("="*60)
    
    # Create data folder if not exists
    DATA_PATH.mkdir(exist_ok=True)
    
    # Download all data as CSV
    download_all_data()