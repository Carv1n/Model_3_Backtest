"""
Convert UTC raw CSVs to Europe/Berlin-local timestamps for visual checks (TradingView alignment).
- Input: data/{TF}_raw/*.csv (UTC timestamps)
- Output: data/{TF}_berlin/*.csv (timestamps localized to Europe/Berlin), plus optional parquet join per TF
- Target TFs: D, W, M, 3D (3D already resampled from D)
"""

import sys
from pathlib import Path
import pandas as pd
import pytz

# import config for DATA_PATH
sys.path.append(str(Path(__file__).parent.parent))
from config import DATA_PATH

BERLIN = pytz.timezone('Europe/Berlin')


def convert_folder(tf: str):
    src = DATA_PATH / f"{tf}_raw"
    dst = DATA_PATH / f"{tf}_berlin"
    dst.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(src.glob("*.csv"))
    if not csv_files:
        print(f"⚠ No CSV files in {src}")
        return

    all_pairs = {}
    for csv_file in csv_files:
        pair = csv_file.stem
        try:
            df = pd.read_csv(csv_file, parse_dates=True, index_col=0)
            if df.empty:
                print(f"  ⚠ {pair}: empty, skip")
                continue
            # ensure tz-aware UTC then convert to Berlin
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC')
            df.index = df.index.tz_convert(BERLIN)
            out = dst / csv_file.name
            df.to_csv(out)
            all_pairs[pair] = df
            print(f"  ✓ {pair}: {len(df)} rows -> {out.relative_to(DATA_PATH)}")
        except Exception as e:
            print(f"  ✗ {pair}: {e}")

    if not all_pairs:
        print(f"✗ No converted data for {tf}")
        return

    combined = pd.concat(all_pairs, names=['pair', 'time'])
    parquet_path = DATA_PATH / f"{tf}_berlin.parquet"
    combined.to_parquet(parquet_path)
    print(f"  → parquet: {parquet_path.name} ({len(combined)} rows)")


def main():
    tfs = ["D", "W", "M", "3D"]
    print("CONVERT UTC -> Europe/Berlin for", tfs)
    for tf in tfs:
        print(f"\n=== {tf} ===")
        convert_folder(tf)


if __name__ == "__main__":
    main()
