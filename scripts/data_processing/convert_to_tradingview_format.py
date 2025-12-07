"""
Convert OANDA Weekly/Monthly raw data to TradingView date convention.

Scope:
- Only fix Weekly (W) and Monthly (M) dates, keeping OANDA prices/volume.
- Do NOT export H1, H4, Daily, or 3D here.

Logic:
- Build a corrected Daily calendar from D_raw by shifting the index +1 day
  (OANDA close timestamp -> TradingView open timestamp).
- Derive Weekly labels from corrected Daily: resample to weeks anchored on Monday.
- Derive Monthly labels from corrected Daily: resample to month-start; first
  label per month is the first available trading day in that month.
- Replace only the index of W_raw/M_raw with these labels, after length check.

Output: data/UTC_TradingView/W/, data/UTC_TradingView/M/
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


def build_weekly_calendar_from_daily(daily_df: pd.DataFrame) -> pd.DatetimeIndex:
    """Return weekly labels (Mondays) derived from corrected Daily."""
    weekly = daily_df.resample("W-MON", label="left", closed="left").size()
    return weekly.index


def build_monthly_calendar_from_daily(daily_df: pd.DataFrame) -> pd.DatetimeIndex:
    """Return monthly labels (month start) derived from corrected Daily."""
    monthly = daily_df.resample("MS", label="left", closed="left").size()
    return monthly.index


def main() -> None:
    print("=" * 70)
    print("CONVERT OANDA W/M DATES TO TRADINGVIEW FORMAT")
    print("=" * 70)
    print("\nProcessing:")
    print("  Weekly: shift timestamps +1 day (close -> open)")
    print("  Monthly: shift timestamps +1 day (close -> open)")
    print("  NOTE: H1/H4/D/3D are NOT exported here")
    print("\nOutput: data/UTC_TradingView/W and /M")
    print("=" * 70)

    weekly_raw_folder = DATA_PATH / "W_raw"
    monthly_raw_folder = DATA_PATH / "M_raw"
    output_w_folder = DATA_PATH / "UTC_TradingView" / "W"
    output_m_folder = DATA_PATH / "UTC_TradingView" / "M"
    output_w_folder.mkdir(parents=True, exist_ok=True)
    output_m_folder.mkdir(parents=True, exist_ok=True)

    if not weekly_raw_folder.exists():
        print("  WARN: W_raw not found")
        return

    weekly_files = list(weekly_raw_folder.glob("*.csv"))
    monthly_files = list(monthly_raw_folder.glob("*.csv"))

    for w_file in weekly_files:
        pair = w_file.stem
        try:
            df_w = pd.read_csv(w_file, index_col=0, parse_dates=True)
            df_w = shift_daily_index(df_w)  # +1 day shift
            df_w.to_csv(output_w_folder / f"{pair}_W_UTC.csv")
            print(f"  OK {pair}: W shifted ({len(df_w)} candles)")
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {pair}: {exc}")

    for m_file in monthly_files:
        pair = m_file.stem
        try:
            df_m = pd.read_csv(m_file, index_col=0, parse_dates=True)
            df_m = shift_daily_index(df_m)  # +1 day shift
            df_m.to_csv(output_m_folder / f"{pair}_M_UTC.csv")
            print(f"  OK {pair}: M shifted ({len(df_m)} candles)")
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR {pair}: {exc}")

    print("\n" + "=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()
