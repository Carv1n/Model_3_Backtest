"""
Export simplified pivot gap data for TradingView validation.
Focuses on 3D, W, M timeframes for Model X.

Output columns:
- pair: currency pair
- timeframe: 3D, W, or M
- direction: bullish or bearish
- pivot_generated_date_utc: date when pivot is complete (after K2 closes) UTC
- pivot_generated_date_berlin: date when pivot is complete in Europe/Berlin timezone
- gap_high: upper boundary of pivot gap
- gap_low: lower boundary of pivot gap
- tp_level: take profit level (Fib -3 from pivot)
- sl_level: stop loss level (Fib 1.5 from pivot)
- trigger_date_utc: date when gap is touched/triggered (UTC, or empty if not triggered)
- trigger_date_berlin: date when gap is touched/triggered (Berlin, or empty if not triggered)
- candle_after_pivot_open, high, low, close: OHLC of first candle after pivot (UTC)
"""

import pandas as pd
import sys
import os
from pathlib import Path
from datetime import datetime
import pytz

BERLIN = pytz.timezone('Europe/Berlin')

# We keep modelx_pivot imports out to avoid conflicting logic; implement TV-style detection locally


def find_time_column(df):
    """Find the timestamp column in the DataFrame."""
    time_cols = [c for c in df.columns if c.lower() in ['time', 'timestamp', 'date', 'datetime']]
    if time_cols:
        return time_cols[0]
    return None


def detect_pivots_tv_style(df: pd.DataFrame, min_body_pct: float = 10.0, min_box_pips: float = 10.0, pair: str | None = None):
    """Detect pivots using the same rules as the provided PineScript (2-candle pattern).

    Rules:
    - prev red + curr green => bullish pivot
    - prev green + curr red => bearish pivot
    - both candles must have body/range * 100 >= min_body_pct
    - pivot is generated after current candle closes (index i)
    - bullish: pivot_level = max(prevClose, currOpen); gap_low = min(prevLow, currLow); gap_high = pivot_level
    - bearish: pivot_level = min(prevClose, currOpen); gap_high = max(prevHigh, currHigh); gap_low = pivot_level
    """
    pivots = []
    # Ensure sorted by time
    df = df.sort_values('time').reset_index(drop=True)

    def box_size_pips(top, bottom):
        size = abs(top - bottom)
        if pair and 'JPY' in pair:
            return size * 100
        return size * 10000

    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]

        # Body percentage
        def body_pct(row):
            rng = row['high'] - row['low']
            if rng == 0:
                return 0.0
            body = abs(row['close'] - row['open'])
            return (body / rng) * 100.0

        prev_body = body_pct(prev)
        curr_body = body_pct(curr)
        if prev_body < min_body_pct or curr_body < min_body_pct:
            continue

        prev_red = prev['close'] < prev['open']
        curr_green = curr['close'] > curr['open']
        prev_green = prev['close'] > prev['open']
        curr_red = curr['close'] < curr['open']

        if prev_red and curr_green:
            # Bullish pivot: K1 red, K2 green
            # Pivot Extreme = tiefster Low (längere untere Wick)
            pivot_extreme = min(prev['low'], curr['low'])
            
            # Berechne beide Varianten für Pivot Level
            variant_close_k1 = prev['close']
            variant_open_k2 = curr['open']
            
            # Größen beider Boxen
            size_close = variant_close_k1 - pivot_extreme
            size_open = variant_open_k2 - pivot_extreme
            
            # Nimm größere Variante als Pivot
            if size_close > size_open:
                pivot_level = variant_close_k1
            else:
                pivot_level = variant_open_k2
            
            # Gap box: vom Pivot bis Pivot Extreme
            gap_high = pivot_level
            gap_low = pivot_extreme
            gap_size = gap_high - gap_low
            
            if box_size_pips(gap_high, gap_low) < min_box_pips:
                continue
            
            # Bullish: TP von Oberkante (gap_high), SL von Unterkante (gap_low)
            tp_level = gap_high + 3.0 * gap_size
            sl_level = gap_low - 0.5 * gap_size
            
            pivots.append({
                'index': i,
                'is_bullish': True,
                'gap_high': gap_high,
                'gap_low': gap_low,
                'tp_level': tp_level,
                'sl_level': sl_level,
                'extreme': pivot_extreme,
            })
            
        elif prev_green and curr_red:
            # Bearish pivot: K1 green, K2 red
            # Pivot Extreme = höchster High (längere obere Wick)
            pivot_extreme = max(prev['high'], curr['high'])
            
            # Berechne beide Varianten für Pivot Level
            variant_close_k1 = prev['close']
            variant_open_k2 = curr['open']
            
            # Größen beider Boxen
            size_close = pivot_extreme - variant_close_k1
            size_open = pivot_extreme - variant_open_k2
            
            # Nimm größere Variante als Pivot
            if size_close > size_open:
                pivot_level = variant_close_k1
            else:
                pivot_level = variant_open_k2
            
            # Gap box: vom Pivot bis Pivot Extreme
            gap_low = pivot_level
            gap_high = pivot_extreme
            gap_size = gap_high - gap_low
            
            if box_size_pips(gap_high, gap_low) < min_box_pips:
                continue
            
            # Bearish: TP von Unterkante (gap_low), SL von Oberkante (gap_high)
            tp_level = gap_low - 3.0 * gap_size
            sl_level = gap_high + 0.5 * gap_size
            
            pivots.append({
                'index': i,
                'is_bullish': False,
                'gap_high': gap_high,
                'gap_low': gap_low,
                'tp_level': tp_level,
                'sl_level': sl_level,
                'extreme': pivot_extreme,
            })

    return pivots


def load_data_with_fallback(timeframe, pair):
    """Load data from Parquet or CSV with proper header handling."""
    data_dir = Path(__file__).parent.parent / "data"
    
    # Try Parquet first (for 3D which has no raw folder)
    parquet_path = data_dir / f"{timeframe}_all_pairs.parquet"
    if parquet_path.exists():
        try:
            df = pd.read_parquet(parquet_path)
            # Check if MultiIndex (pair, time)
            if isinstance(df.index, pd.MultiIndex):
                # Reset index to get pair and time as columns
                df = df.reset_index()
                # Filter for the specific pair
                df = df[df['pair'] == pair].copy()
            else:
                # Filter for the specific pair if 'pair' is a column
                if 'pair' in df.columns:
                    df = df[df['pair'] == pair].copy()
                else:
                    raise KeyError("No 'pair' column or index found")
            
            # Ensure time column is parsed correctly
            time_col = find_time_column(df)
            if time_col:
                if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
                    df[time_col] = pd.to_datetime(df[time_col], utc=True)
                elif df[time_col].dt.tz is None:
                    df[time_col] = df[time_col].dt.tz_localize('UTC')
            
            return df.reset_index(drop=True)
        except Exception as e:
            print(f"Warning: Could not read Parquet file: {e}")
    
    # Fall back to CSV
    csv_path = data_dir / f"{timeframe}_raw/{pair}.csv"
    
    if not csv_path.exists():
        raise FileNotFoundError(f"Neither Parquet nor CSV file found for {timeframe} {pair}")
    
    # Read CSV with explicit header handling
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Rename columns to expected names
    rename_map = {}
    for col in df.columns:
        if 'time' in col or 'date' in col:
            rename_map[col] = 'time'
        elif col == 'open':
            rename_map[col] = 'open'
        elif col == 'high':
            rename_map[col] = 'high'
        elif col == 'low':
            rename_map[col] = 'low'
        elif col == 'close':
            rename_map[col] = 'close'
    
    if rename_map:
        df = df.rename(columns=rename_map)
    
    # Parse time column
    time_col = find_time_column(df)
    if time_col:
        df[time_col] = pd.to_datetime(df[time_col], utc=True)
    
    # Add pair column
    df['pair'] = pair
    
    return df


def to_berlin_time(utc_time):
    """Convert UTC datetime to Europe/Berlin timezone."""
    if pd.isna(utc_time):
        return None
    berlin = pytz.timezone('Europe/Berlin')
    if utc_time.tzinfo is None:
        utc_time = pytz.utc.localize(utc_time)
    return utc_time.astimezone(berlin)


def export_gap_validation(timeframe, pair, output_file):
    """
    Export pivot gap data for validation.
    
    Key logic:
    - Pivot is "generated" after K2 closes (index i in detect_pivots)
    - pivot_generated_date: When K2 closes (when we KNOW there's a pivot)
    - valid_date: First candle AFTER pivot (index i+1) - when we can START trading it
    - trigger_date: First candle that ACTUALLY touches the gap (can be empty)
    - All dates are AFTER valid_date (never before or during)
    """
    print(f"Loading {timeframe} data for {pair}...")
    df = load_data_with_fallback(timeframe, pair)
    
    print(f"Detecting pivots for {pair} on {timeframe} (TV-style)...")
    pivots = detect_pivots_tv_style(df, pair=pair)
    
    print(f"Found {len(pivots)} pivots. Processing...")
    
    results = []
    
    for pivot in pivots:
        # Pivot is complete at index i (after K2 closes)
        pivot_complete_idx = pivot['index']
        
        # K2 close time (UTC)
        pivot_complete_time_utc = df.iloc[pivot_complete_idx]['time']
        pivot_complete_time_berlin = to_berlin_time(pivot_complete_time_utc)
        
        # Gap boundaries and levels
        gap_high = pivot['gap_high']
        gap_low = pivot['gap_low']
        tp_level = pivot['tp_level']
        sl_level = pivot['sl_level']
        
        # Calculate RR (Risk/Reward ratio) = TP distance / SL distance
        if pivot['is_bullish']:
            # Entry at gap_high
            entry = gap_high
            tp_distance = tp_level - entry  # TP is above entry
            sl_distance = entry - sl_level  # SL is below entry
        else:
            # Entry at gap_low
            entry = gap_low
            tp_distance = entry - tp_level  # TP is below entry
            sl_distance = sl_level - entry  # SL is above entry
        
        rr = tp_distance / sl_distance if sl_distance != 0 else 0
        
        # The pivot becomes VALID starting from the next candle (pivot_complete_idx + 1)
        valid_idx = pivot_complete_idx + 1
        
        if valid_idx >= len(df):
            continue  # Skip if there's no candle after pivot
        
        valid_time_utc = df.iloc[valid_idx]['time']
        valid_time_berlin = to_berlin_time(valid_time_utc)
        
        # Search for trigger starting from valid_idx
        trigger_date_utc = None
        trigger_date_berlin = None
        
        for j in range(valid_idx, len(df)):
            candle = df.iloc[j]
            # Check if candle touches the gap box
            if candle['low'] <= gap_high and candle['high'] >= gap_low:
                trigger_date_utc = candle['time']
                trigger_date_berlin = to_berlin_time(candle['time'])
                break
        
        # Format dates
        pivot_gen_utc_str = pd.Timestamp(pivot_complete_time_utc).strftime('%Y-%m-%d %H:%M:%S') if pivot_complete_time_utc is not None else ''
        pivot_gen_berlin_str = pivot_complete_time_berlin.strftime('%Y-%m-%d %H:%M:%S') if pivot_complete_time_berlin else ''
        
        valid_utc_str = pd.Timestamp(valid_time_utc).strftime('%Y-%m-%d %H:%M:%S') if valid_time_utc is not None else ''
        valid_berlin_str = valid_time_berlin.strftime('%Y-%m-%d %H:%M:%S') if valid_time_berlin else ''
        
        trigger_utc_str = pd.Timestamp(trigger_date_utc).strftime('%Y-%m-%d %H:%M:%S') if trigger_date_utc is not None else ''
        trigger_berlin_str = trigger_date_berlin.strftime('%Y-%m-%d %H:%M:%S') if trigger_date_berlin else ''
        
        # Get OHLC of first candle after pivot (the valid candle)
        valid_candle = df.iloc[valid_idx]
        
        results.append({
            'pair': pair,
            'timeframe': timeframe,
            'direction': 'bullish' if pivot['is_bullish'] else 'bearish',
            'pivot_generated_date_utc': pivot_gen_utc_str,
            'pivot_generated_date_berlin': pivot_gen_berlin_str,
            'valid_date_utc': valid_utc_str,
            'valid_date_berlin': valid_berlin_str,
            'gap_high': f"{gap_high:.5f}",
            'gap_low': f"{gap_low:.5f}",
            'tp_level': f"{tp_level:.5f}",
            'sl_level': f"{sl_level:.5f}",
            'rr': f"{rr:.2f}",
            'trigger_date_utc': trigger_utc_str,
            'trigger_date_berlin': trigger_berlin_str,
            'valid_candle_open': f"{valid_candle['open']:.5f}",
            'valid_candle_high': f"{valid_candle['high']:.5f}",
            'valid_candle_low': f"{valid_candle['low']:.5f}",
            'valid_candle_close': f"{valid_candle['close']:.5f}"
        })
    
    # Create DataFrame and export
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_file, index=False)
    print(f"Exported {len(results)} pivot gaps to {output_file}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Export pivot gaps for TradingView validation')
    parser.add_argument('-t', '--timeframe', required=True, choices=['3D', 'W', 'M'], 
                        help='Timeframe (3D, W, or M)')
    parser.add_argument('-p', '--pair', required=True, 
                        help='Currency pair (e.g., EURUSD)')
    parser.add_argument('-o', '--output', default=None,
                        help='Output CSV file (default: gaps_{pair}_{timeframe}.csv)')
    
    args = parser.parse_args()
    
    output_file = args.output
    if output_file is None:
        script_dir = Path(__file__).parent
        output_file = script_dir / f"gaps_{args.pair}_{args.timeframe}.csv"
    
    export_gap_validation(args.timeframe, args.pair, output_file)
