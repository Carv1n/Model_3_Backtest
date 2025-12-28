"""
Parquet Generator - Forex Data
-------------------------------

Konvertiert CSV-Files zu Parquet-Format:
- Input: Data/Chartdata/Forex/{TF}/{PAIR}_{TF}_UTC.csv
- Output: Data/Chartdata/Forex/Parquet/All_Pairs_{TF}_UTC.parquet

Ein Parquet-File pro Timeframe mit allen 28 Pairs.
MultiIndex: (pair, time)
"""

import pandas as pd
from pathlib import Path
from typing import List

# Forex Pairs
PAIRS = [
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
    "CADCHF", "CADJPY", "CHFJPY",
    "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
    "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
    "USDCAD", "USDCHF", "USDJPY"
]

# Timeframes
TIMEFRAMES = ["H1", "H4", "D", "3D", "W", "M"]

def load_csv(csv_path: Path) -> pd.DataFrame:
    """Lädt eine CSV und standardisiert die Spalten."""
    df = pd.read_csv(csv_path)

    # Finde Zeit-Spalte
    time_col = None
    for col in df.columns:
        if col.lower() in {"time", "timestamp", "date", "datetime"}:
            time_col = col
            break

    if time_col is None:
        raise ValueError(f"Keine Zeit-Spalte in {csv_path}")

    # Rename zu 'time'
    if time_col != "time":
        df.rename(columns={time_col: "time"}, inplace=True)

    # Zu Datetime mit UTC
    df["time"] = pd.to_datetime(df["time"], utc=True)

    # Standardisiere Spaltennamen (lowercase)
    df.columns = [col.lower() for col in df.columns]

    # Stelle sicher: time, open, high, low, close
    required = ["time", "open", "high", "low", "close"]
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Fehlende Spalte '{col}' in {csv_path}")

    # Nur relevante Spalten
    df = df[required].copy()

    # Sortiere nach Zeit
    df.sort_values("time", inplace=True)

    return df


def generate_parquet_for_timeframe(tf: str, data_root: Path, output_root: Path):
    """Generiert ein Parquet-File für einen Timeframe mit allen Pairs."""
    print(f"\n{'='*60}")
    print(f"Timeframe: {tf}")
    print(f"{'='*60}")

    all_dfs = []

    for pair in PAIRS:
        csv_path = data_root / tf / f"{pair}_{tf}_UTC.csv"

        if not csv_path.exists():
            print(f"  [SKIP] {pair}: {csv_path} nicht gefunden")
            continue

        try:
            df = load_csv(csv_path)
            df["pair"] = pair
            all_dfs.append(df)
            print(f"  [OK] {pair}: {len(df)} Kerzen geladen")
        except Exception as e:
            print(f"  [ERROR] {pair}: {e}")
            continue

    if not all_dfs:
        print(f"  [WARN] Keine Daten fuer {tf} gefunden!")
        return

    # Kombiniere alle Pairs
    combined = pd.concat(all_dfs, ignore_index=True)

    # Setze MultiIndex (pair, time)
    combined.set_index(["pair", "time"], inplace=True)
    combined.sort_index(inplace=True)

    # Speichere als Parquet
    output_path = output_root / f"All_Pairs_{tf}_UTC.parquet"
    output_root.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(output_path, engine="pyarrow", compression="snappy")

    print(f"\n  [SAVED] {output_path}")
    print(f"    Total: {len(combined)} Zeilen, {len(PAIRS)} Pairs")
    print(f"    Groesse: {output_path.stat().st_size / 1024 / 1024:.2f} MB")


def main():
    # Pfade
    project_root = Path(__file__).parent.parent.parent.parent
    data_root = project_root / "Data" / "Chartdata" / "Forex"
    output_root = data_root / "Parquet"

    print("="*60)
    print("PARQUET GENERATOR - FOREX DATA")
    print("="*60)
    print(f"Input:  {data_root}")
    print(f"Output: {output_root}")

    # Generiere für jeden Timeframe
    for tf in TIMEFRAMES:
        generate_parquet_for_timeframe(tf, data_root, output_root)

    print("\n" + "="*60)
    print("FERTIG!")
    print("="*60)
    print(f"\nParquet-Files: {output_root}")
    print("\nGenerierte Files:")
    for tf in TIMEFRAMES:
        p = output_root / f"All_Pairs_{tf}_UTC.parquet"
        if p.exists():
            print(f"  [OK] {p.name} ({p.stat().st_size / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
