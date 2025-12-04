"""
Resample daily raw data to 3D raw CSVs and rebuild 3D_all_pairs.parquet.
- Input: data/D_raw/*.csv (per pair, UTC timestamps)
- Output: data/3D_raw/*.csv + data/3D_all_pairs.parquet (MultiIndex pair,time)
"""

import sys
from pathlib import Path
import pandas as pd

# Ensure we can import config
sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_PATH


def resample_pair_to_3d(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    if df.empty:
        raise ValueError("empty dataset")
    # Sort to guarantee chronological order
    df = df.sort_index()
    # Resample to 3D
    df_3d = df.resample('3D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    })
    # Drop periods with no data (open can be NaN)
    df_3d = df_3d.dropna(subset=['open', 'high', 'low', 'close'])
    return df_3d


def build_3d_raw_from_daily():
    d_folder = DATA_PATH / "D_raw"
    out_folder = DATA_PATH / "3D_raw"
    out_folder.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(d_folder.glob("*.csv"))
    if not csv_files:
        print("✗ No daily raw CSVs found in data/D_raw. Download daily data first.")
        return

    all_pairs = {}
    for csv_file in csv_files:
        pair = csv_file.stem
        try:
            df_3d = resample_pair_to_3d(csv_file)
            # Save per pair CSV
            out_path = out_folder / f"{pair}.csv"
            df_3d.to_csv(out_path)
            all_pairs[pair] = df_3d
            print(f"  ✓ {pair}: {len(df_3d)} candles -> {out_path.name}")
        except Exception as e:
            print(f"  ⚠ {pair}: skipped ({e})")

    if not all_pairs:
        print("✗ No pairs converted; 3D outputs not created.")
        return

    # Combine to MultiIndex DataFrame
    combined = pd.concat(all_pairs, names=['pair', 'time'])
    parquet_path = DATA_PATH / "3D_all_pairs.parquet"
    combined.to_parquet(parquet_path)
    print(f"\n✓ Saved 3D_all_pairs.parquet with {len(combined)} candles across {len(all_pairs)} pairs")
    print(f"  Date range: {combined.index.get_level_values('time').min()} to {combined.index.get_level_values('time').max()}")


if __name__ == "__main__":
    print("MODEL X - BUILD 3D RAW FROM DAILY")
    print("=" * 60)
    build_3d_raw_from_daily()
