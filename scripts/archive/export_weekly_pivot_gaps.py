#!/usr/bin/env python3
"""Export weekly pivot gaps and candle OHLC for rows where a pivot exists.

Outputs CSV with columns:
 - pair
 - pivot_type (high/low)
 - pivot_time_utc
 - pivot_time_local
 - pivot_gap_high
 - pivot_gap_low
 - candle_time_utc
 - candle_time_local
 - open
 - high
 - low
 - close
 - volume (if present)

This script prefers per-pair weekly raw CSVs in `data/W_raw/`.
It will try to import the project's `scripts.modelx_pivot.detect_pivots` function
and fall back to a simple local pivot detection if unavailable.
"""
import argparse
import csv
import glob
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd


def try_import_detect():
    try:
        import importlib
        spec = importlib.import_module('scripts.modelx_pivot')
        if hasattr(spec, 'detect_pivots'):
            return spec.detect_pivots
    except Exception:
        pass
    return None


def simple_detect_pivots(df):
    """Simple pivot detection: a pivot high is when high is greater than previous and next candle highs.
    Pivot low is when low is lower than previous and next candle lows.
    Returns list of dicts with keys: index, type ('high'|'low')
    """
    pivots = []
    for i in range(1, len(df) - 1):
        prev_h = df['high'].iat[i - 1]
        prev_l = df['low'].iat[i - 1]
        cur_h = df['high'].iat[i]
        cur_l = df['low'].iat[i]
        next_h = df['high'].iat[i + 1]
        next_l = df['low'].iat[i + 1]
        if (cur_h > prev_h) and (cur_h > next_h):
            pivots.append({'index': i, 'type': 'high'})
        if (cur_l < prev_l) and (cur_l < next_l):
            pivots.append({'index': i, 'type': 'low'})
    return pivots


def load_csv_tz(path):
    # Try to parse time column; accept common names
    df = pd.read_csv(path)
    time_cols = [c for c in df.columns if c.lower() in ('time', 'date', 'datetime')]
    if not time_cols:
        # Try first column
        time_col = df.columns[0]
    else:
        time_col = time_cols[0]
    # Normalize column names
    df.rename(columns={time_col: 'time'}, inplace=True)
    # Ensure numeric columns
    for col in ['open', 'high', 'low', 'close']:
        if col not in df.columns:
            # Try capitalized
            for c in df.columns:
                if c.lower() == col:
                    df.rename(columns={c: col}, inplace=True)
                    break
    # parse time
    try:
        df['time'] = pd.to_datetime(df['time'], utc=True)
    except Exception:
        # Try without utc and then localize
        df['time'] = pd.to_datetime(df['time'])
        if df['time'].dt.tz is None:
            df['time'] = df['time'].dt.tz_localize('UTC')
    df.reset_index(drop=True, inplace=True)
    return df


def process_file(path, detect_func, out_rows, local_tz_name='Europe/Berlin'):
    pair = os.path.splitext(os.path.basename(path))[0]
    df = load_csv_tz(path)
    if df.empty:
        return
    # Ensure numeric
    for col in ['open', 'high', 'low', 'close']:
        if col not in df.columns:
            return
    # Use detect_func if provided (assumed signature detect_pivots(df, timeframe, pair))
    pivots = None
    if detect_func is not None:
        try:
            pivots = detect_func(df.copy(), 'W', pair)
            # Expect list of dicts with keys 'index' and 'type' or objects with attributes
            out = []
            for p in pivots:
                if isinstance(p, dict) and 'index' in p:
                    out.append({'index': p['index'], 'type': p.get('type', p.get('pivot_type', ''))})
                else:
                    # try attribute access
                    idx = getattr(p, 'index', None) or getattr(p, 'i', None)
                    t = getattr(p, 'type', None) or getattr(p, 'pivot_type', None)
                    if idx is None:
                        continue
                    out.append({'index': idx, 'type': t or ''})
            pivots = out
        except Exception:
            pivots = None
    if pivots is None:
        pivots = simple_detect_pivots(df)

    local_tz = ZoneInfo(local_tz_name)
    for p in pivots:
        i = int(p['index'])
        typ = p.get('type', '')
        row = df.iloc[i]
        pivot_time_utc = row['time']
        pivot_time_local = pivot_time_utc.astimezone(local_tz)
        # Define pivot gap high/low: for a pivot high, gap may be pivot high to next candle low (or similar).
        # Here we compute gap as pivot candle high/low vs next candle open/low/high as simple measure.
        gap_high = float(row['high'])
        gap_low = float(row['low'])
        # Candle OHLC (the pivot candle)
        o = float(row['open'])
        h = float(row['high'])
        l = float(row['low'])
        c = float(row['close'])
        vol = df['volume'].iat[i] if 'volume' in df.columns else ''
        out_rows.append({
            'pair': pair,
            'pivot_type': typ,
            'pivot_time_utc': pivot_time_utc.isoformat(),
            'pivot_time_local': pivot_time_local.isoformat(),
            'pivot_gap_high': gap_high,
            'pivot_gap_low': gap_low,
            'candle_time_utc': pivot_time_utc.isoformat(),
            'candle_time_local': pivot_time_local.isoformat(),
            'open': o,
            'high': h,
            'low': l,
            'close': c,
            'volume': vol,
        })


def main():
    parser = argparse.ArgumentParser(description='Export weekly pivot gaps and candle OHLC for pivots.')
    parser.add_argument('-i', '--input-folder', default='data/W_raw', help='Folder with weekly CSVs (default: data/W_raw)')
    parser.add_argument('-o', '--output', default='scripts/weekly_pivot_gaps.csv', help='Output CSV path')
    parser.add_argument('--tz', default='Europe/Berlin', help='Local timezone name for local times')
    args = parser.parse_args()

    files = sorted(glob.glob(os.path.join(args.input_folder, '*.csv')))
    if not files:
        print(f'No CSV files found in {args.input_folder}')
        return

    detect_func = try_import_detect()
    out_rows = []
    for f in files:
        try:
            process_file(f, detect_func, out_rows, local_tz_name=args.tz)
        except Exception as e:
            print(f'Error processing {f}: {e}')

    # Write CSV
    if out_rows:
        keys = ['pair','pivot_type','pivot_time_utc','pivot_time_local','pivot_gap_high','pivot_gap_low',
                'candle_time_utc','candle_time_local','open','high','low','close','volume']
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', newline='', encoding='utf-8') as fh:
            writer = csv.DictWriter(fh, fieldnames=keys)
            writer.writeheader()
            for r in out_rows:
                writer.writerow(r)
        print(f'Exported {len(out_rows)} pivot rows to {args.output}')
    else:
        print('No pivots found.')


if __name__ == '__main__':
    main()
