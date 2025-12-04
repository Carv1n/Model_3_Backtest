import pandas as pd
from zoneinfo import ZoneInfo
import argparse
import sys
import os

import importlib.util
spec = importlib.util.spec_from_file_location("modelx_pivot", os.path.join(os.path.dirname(__file__), "modelx_pivot.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
detect_pivots = mod.detect_pivots


def find_time_column(df: pd.DataFrame):
    candidates = ['timestamp', 'time', 'date', 'datetime', 'dt']
    for c in candidates:
        if c in df.columns:
            return c
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            return c
    return None


def load_data_with_fallback(timeframe: str, pair: str) -> pd.DataFrame:
    # Prefer per-pair raw CSV for exact timestamp alignment with TradingView
    tf_map = {
        'D': 'D_raw', 'H1': 'H1_raw', 'H4': 'H4_raw', 'W': 'W_raw', 'M': 'M_raw', '3D': 'D_raw'
    }
    raw_folder = tf_map.get(timeframe, timeframe + '_raw')
    csv_path = f"data/{raw_folder}/{pair}.csv"
    if os.path.exists(csv_path):
        # read header raw to ensure correct column names (avoid engine quirks)
        with open(csv_path, 'r', encoding='utf-8') as fh:
            header_line = fh.readline().strip()
        header_cols = [c.strip() for c in header_line.split(',')]
        # remove BOM if present
        header_cols[0] = header_cols[0].lstrip('\ufeff')
        df = pd.read_csv(csv_path, header=0, names=header_cols)
        # handle cases where first column had no name and was shifted
        if 'pair' not in df.columns:
            df['pair'] = pair
        if 'time' not in df.columns:
            # if first column is time values, promote it
            first_col = df.columns[0]
            sample = str(df.iloc[0, 0])
            if any(x in sample for x in ['+', '-', ':', ' ']):
                df = df.rename(columns={first_col: 'time'})
        return df
    # parquet fallback if CSV missing
    parquet_path = f"data/{timeframe}_all_pairs.parquet"
    try:
        if os.path.exists(parquet_path):
            df = pd.read_parquet(parquet_path)
            return df
    except Exception:
        pass
    raise FileNotFoundError(f"Keine Daten für {pair} {timeframe} gefunden.")


def export_checks(timeframe: str, pair: str, date=None, out='pivot_checks.csv'):
    df = load_data_with_fallback(timeframe, pair)
    print(f"Geladene Spalten: {list(df.columns)}")
    timecol = find_time_column(df)
    if timecol is None:
        raise ValueError('Keine Zeitspalte in Daten gefunden')
    # ensure datetime tz-aware UTC
    if not pd.api.types.is_datetime64_any_dtype(df[timecol]):
        df[timecol] = pd.to_datetime(df[timecol], utc=True, errors='coerce')
    else:
        if df[timecol].dt.tz is None:
            df[timecol] = df[timecol].dt.tz_localize('UTC')
        else:
            df[timecol] = df[timecol].dt.tz_convert('UTC')

    # ensure ordering
    df = df.sort_values(timecol).reset_index(drop=True)

    pivots = detect_pivots(df, timeframe, pair)

    rows = []
    for pv in pivots:
        idx = pv.index
        # pivot time
        pivot_time_utc = df.loc[idx, timecol]
        pivot_time_local = pivot_time_utc.astimezone(ZoneInfo('Europe/Berlin'))
        # gather next 5 candles
        next_rows = []
        for k in range(1, 6):
            i = idx + k
            if i < len(df):
                r = df.loc[i]
                t_utc = r[timecol]
                t_local = t_utc.astimezone(ZoneInfo('Europe/Berlin'))
                next_rows.append({
                    't_utc': t_utc.isoformat(), 't_local': t_local.isoformat(),
                    'open': r.get('open'), 'high': r.get('high'), 'low': r.get('low'), 'close': r.get('close')
                })
            else:
                next_rows.append(None)

        rows.append({
            'pair': pair,
            'timeframe': timeframe,
            'pivot_idx': idx,
            'pivot_time_utc': pivot_time_utc.isoformat(),
            'pivot_time_local': pivot_time_local.isoformat(),
            'pivot_level': pv.pivot_level,
            'pivot_extreme': pv.pivot_extreme,
            'pivot_near': pv.pivot_near,
            'is_bullish': pv.is_bullish,
            'sl': pv.sl_level,
            'tp': pv.tp_level,
            'next_candles': next_rows
        })

    # write CSV with flattened next candles
    out_rows = []
    for r in rows:
        base = {k: r[k] for k in ['pair','timeframe','pivot_idx','pivot_time_utc','pivot_time_local','pivot_level','pivot_extreme','pivot_near','is_bullish','sl','tp']}
        for i, nr in enumerate(r['next_candles'], start=1):
            if nr is None:
                base.update({f'next{i}_t_utc':'', f'next{i}_t_local':'', f'next{i}_open':'', f'next{i}_high':'', f'next{i}_low':'', f'next{i}_close':''})
            else:
                base.update({f'next{i}_t_utc': nr['t_utc'], f'next{i}_t_local': nr['t_local'], f'next{i}_open': nr['open'], f'next{i}_high': nr['high'], f'next{i}_low': nr['low'], f'next{i}_close': nr['close']})
        out_rows.append(base)

    out_df = pd.DataFrame(out_rows)
    out_df.to_csv(out, index=False)
    print(f'Exportiert {len(out_rows)} Pivot-Prüfzeilen nach {out}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-t','--timeframe', default='D')
    parser.add_argument('-p','--pair', default='AUDUSD')
    parser.add_argument('-o','--out', default='pivot_checks.csv')
    args = parser.parse_args()
    export_checks(args.timeframe, args.pair, out=args.out)


if __name__ == '__main__':
    main()
