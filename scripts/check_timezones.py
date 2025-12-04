import argparse
from zoneinfo import ZoneInfo
import pandas as pd
import sys


def find_time_column(df: pd.DataFrame):
    candidates = ['timestamp', 'time', 'date', 'datetime', 'dt']
    for c in candidates:
        if c in df.columns:
            return c
    # try to detect datetime-like columns
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            return c
    return None


def load_parquet(timeframe: str):
    fname = f"data/{timeframe}_all_pairs.parquet"
    print(f"Lade {fname}")
    try:
        df = pd.read_parquet(fname)
        return df
    except Exception as e:
        print(f"Fehler beim Laden der Parquet-Datei: {e}")
        print("Versuche Fallback: lade Raw-CSV für das einzelne Pair (falls vorhanden).")
        raise


def show_timestamp_examples(df: pd.DataFrame, timecol: str, pair: str, date_str: str):
    # filter pair
    pair_df = df[df['pair'] == pair].copy()
    if pair_df.empty:
        print(f"Kein Eintrag für Pair {pair} in den Daten gefunden.")
        return

    # ensure datetime
    if not pd.api.types.is_datetime64_any_dtype(pair_df[timecol]):
        pair_df[timecol] = pd.to_datetime(pair_df[timecol], utc=True, errors='coerce')

    pair_df = pair_df.sort_values(timecol).reset_index(drop=True)

    # show head / tail
    print('\nErste 3 Zeitstempel:')
    print(pair_df[[timecol, 'open', 'high', 'low', 'close']].head(3))
    print('\nLetzte 3 Zeitstempel:')
    print(pair_df[[timecol, 'open', 'high', 'low', 'close']].tail(3))

    # locate requested date
    target = pd.to_datetime(date_str)
    # find nearest index by date only (ignore time)
    pair_df['date_only'] = pair_df[timecol].dt.tz_convert('UTC').dt.date
    matches = pair_df[pair_df['date_only'] == target.date()]
    if matches.empty:
        # try find nearest
        nearest_idx = (pair_df[timecol].dt.tz_convert('UTC') - pd.Timestamp(target, tz='UTC')).abs().idxmin()
        row = pair_df.loc[nearest_idx]
        print(f"\nKein direkter Treffer für {date_str}. Nächste Zeile (UTC):\n{row[[timecol, 'open', 'high', 'low', 'close']].to_dict()}")
    else:
        print(f"\nGefundene Zeilen für {date_str} (UTC):")
        print(matches[[timecol, 'open', 'high', 'low', 'close']])

    # show conversions
    sample = pair_df.iloc[max(0, len(pair_df)//2) : max(3, len(pair_df)//2 + 3)]
    print('\nSample conversions (UTC vs Europe/Berlin):')
    for _, r in sample.iterrows():
        ts = r[timecol]
        if ts.tzinfo is None:
            # assume UTC
            ts = ts.tz_localize('UTC')
        berlin = ts.astimezone(ZoneInfo('Europe/Berlin'))
        print(f"UTC: {ts}  | Berlin: {berlin}  | open={r['open']} close={r['close']}")


def main():
    parser = argparse.ArgumentParser(description='Check timezone and timestamp alignment in parquet data')
    parser.add_argument('--timeframe', '-t', default='D', help='Timeframe filename prefix (e.g. D, H1, H4, W, M, 3D)')
    parser.add_argument('--pair', '-p', default='AUDUSD', help='Currency pair (e.g. AUDUSD)')
    parser.add_argument('--date', '-d', default=None, help='Date to inspect (YYYY-MM-DD)')
    args = parser.parse_args()

    try:
        df = load_parquet(args.timeframe)
    except Exception as e:
        print(f"Fehler beim Laden der Datei: {e}")
        # Fallback: versuche Raw CSV für das Pair im entsprechenden Raw-Ordner
        tf_map = {
            'D': 'D_raw', 'H1': 'H1_raw', 'H4': 'H4_raw', 'W': 'W_raw', 'M': 'M_raw', '3D': 'D_raw'
        }
        raw_folder = tf_map.get(args.timeframe, args.timeframe + '_raw')
        csv_path = f"data/{raw_folder}/{args.pair}.csv"
        try:
            print(f"Versuche CSV-Fallback: {csv_path}")
            df = pd.read_csv(csv_path)
            # ensure we have a 'pair' column for consistency
            if 'pair' not in df.columns:
                df['pair'] = args.pair
        except Exception as e2:
            print(f"Fehler beim Laden der CSV-Fallback-Datei: {e2}")
            sys.exit(1)

    timecol = find_time_column(df)
    if timecol is None:
        print("Keine Zeitspalte gefunden. Erwartete Spalten: timestamp/time/date/datetime oder Datetime-Typen.")
        print(f"Vorhandene Spalten: {df.columns.tolist()}")
        sys.exit(1)

    print(f"Verwendete Zeitspalte: {timecol}")
    if args.date:
        show_timestamp_examples(df, timecol, args.pair, args.date)
    else:
        print('Kein Datum angegeben; zeige nur Kopf-/Ende-Beispiele.')
        pair_df = df[df['pair'] == args.pair].copy()
        if pair_df.empty:
            print(f"Kein Eintrag für Pair {args.pair} gefunden.")
            sys.exit(0)
        if not pd.api.types.is_datetime64_any_dtype(pair_df[timecol]):
            pair_df[timecol] = pd.to_datetime(pair_df[timecol], utc=True, errors='coerce')
        print(pair_df[[timecol, 'open', 'high', 'low', 'close']].head())


if __name__ == '__main__':
    main()
