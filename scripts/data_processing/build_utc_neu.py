"""
Build UTC_NEU folder:
1. Copy H1, H4, 3D, W, M from raw → UTC_NEU (rename files)
2. Process D with +1 day shift → UTC_NEU/D
3. Export combined parquet files (one per timeframe with all pairs)
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent.parent.parent))
from config import *  # noqa: F401,F403


def shift_daily_index(df: pd.DataFrame) -> pd.DataFrame:
    """Shift Daily timestamps by +1 day (OANDA close -> TradingView open)."""
    df_copy = df.copy()
    df_copy.index = df_copy.index + timedelta(days=1)
    return df_copy


def main() -> None:
    print("=" * 70)
    print("BUILD UTC_NEU FOLDER")
    print("=" * 70)

    # Create UTC_NEU directory structure
    utc_neu_root = DATA_PATH / "UTC_NEU"
    utc_neu_root.mkdir(parents=True, exist_ok=True)

    timeframes = ["H1", "H4", "3D", "W", "M"]
    pairs = [
        "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
        "CADCHF", "CADJPY", "CHFJPY",
        "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
        "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
        "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
        "USDCAD", "USDCHF", "USDJPY"
    ]

    # Process H1, H4, 3D, W, M (direct copy with rename)
    print("\nProcessing H1, H4, 3D, W, M (direct copy):")
    print("-" * 70)
    for tf in timeframes:
        raw_folder = DATA_PATH / f"{tf}_raw"
        output_folder = utc_neu_root / tf
        output_folder.mkdir(parents=True, exist_ok=True)

        if not raw_folder.exists():
            print(f"  WARN: {tf}_raw not found")
            continue

        count = 0
        for pair in pairs:
            raw_file = raw_folder / f"{pair}.csv"
            if raw_file.exists():
                try:
                    df = pd.read_csv(raw_file, index_col=0, parse_dates=True)
                    output_file = output_folder / f"{pair}_{tf}_UTC.csv"
                    df.to_csv(output_file)
                    count += 1
                except Exception as exc:  # noqa: BLE001
                    print(f"  ERROR {pair} {tf}: {exc}")
        print(f"  {tf}: {count}/{len(pairs)} pairs copied")

    # Process Daily with +1 day shift
    print("\nProcessing D (with +1 day shift):")
    print("-" * 70)
    d_raw_folder = DATA_PATH / "D_raw"
    d_output_folder = utc_neu_root / "D"
    d_output_folder.mkdir(parents=True, exist_ok=True)

    if not d_raw_folder.exists():
        print("  WARN: D_raw not found")
    else:
        count = 0
        for pair in pairs:
            d_file = d_raw_folder / f"{pair}.csv"
            if d_file.exists():
                try:
                    df = pd.read_csv(d_file, index_col=0, parse_dates=True)
                    df = shift_daily_index(df)
                    output_file = d_output_folder / f"{pair}_D_UTC.csv"
                    df.to_csv(output_file)
                    count += 1
                except Exception as exc:  # noqa: BLE001
                    print(f"  ERROR {pair} D: {exc}")
        print(f"  D: {count}/{len(pairs)} pairs shifted")

    # Export combined parquet files (one per timeframe with all pairs)
    print("\nExporting combined parquet files:")
    print("-" * 70)
    all_timeframes = ["H1", "H4", "3D", "D", "W", "M"]
    parquet_folder = utc_neu_root / "Parquet"
    parquet_folder.mkdir(parents=True, exist_ok=True)

    for tf in all_timeframes:
        tf_folder = utc_neu_root / tf

        if not tf_folder.exists():
            print(f"  WARN: {tf} folder not found")
            continue

        dfs = []
        for pair in pairs:
            csv_file = tf_folder / f"{pair}_{tf}_UTC.csv"
            if csv_file.exists():
                try:
                    df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
                    df["pair"] = pair
                    dfs.append(df)
                except Exception as exc:  # noqa: BLE001
                    print(f"  ERROR {pair} {tf}: {exc}")

        if dfs:
            combined_df = pd.concat(dfs, ignore_index=False)
            parquet_file = parquet_folder / f"All_Pairs_{tf}_UTC.parquet"
            combined_df.to_parquet(parquet_file)
            print(f"  {tf}: combined {len(dfs)} pairs → {parquet_file.name}")
        else:
            print(f"  {tf}: no data found")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)
    print(f"\nOutput folders:")
    print(f"  CSV:     {utc_neu_root}")
    print(f"  Parquet: {parquet_folder}")


if __name__ == "__main__":
    main()
