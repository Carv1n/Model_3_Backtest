"""
Model 3 Backtest (Standard-Variante)
------------------------------------

- Pivot-TF: W (Weekly) nur
- Verfeinerungen: 1H, 4H, D, 3D, W (höchste gültige wird genutzt)
- Entry: Sofort bei Berührung der höchsten validen Verfeinerung (kein Close-Warten),
        nachdem die HTF-Pivot-Gap zuerst getriggert wurde
- Doji-Filter: 2 %
- Versatz: keiner
- Verfeinerungsgröße: max 20 % der HTF-Pivot-Gap
- SL: >= 60 Pips und jenseits Fib 1.1 (aus HTF-Pivot), RR 1–1.5, TP = Fib -1
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
# Utilities
# --------------------------------------------------------------------------- #


def pips(price_diff: float, pair: str) -> float:
    return abs(price_diff) * (100 if "JPY" in pair else 10000)


def price_per_pip(pair: str) -> float:
    return 0.01 if "JPY" in pair else 0.0001


def body_pct(row: pd.Series) -> float:
    rng = row["high"] - row["low"]
    if rng == 0:
        return 0.0
    body = abs(row["close"] - row["open"])
    return (body / rng) * 100.0


def load_tf_data(timeframe: str, pair: str) -> pd.DataFrame:
    """Lädt Parquet-Daten für ein Pair/TF (UTC Parquet)."""
    base = Path(__file__).parent.parent.parent.parent / "Data" / "Chartdata" / "Forex" / "Parquet"
    path = base / f"All_Pairs_{timeframe}_UTC.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Fehlende Daten: {path}")
    df = pd.read_parquet(path)

    # MultiIndex (pair, time) → in Spalten umwandeln
    if isinstance(df.index, pd.MultiIndex) and set(df.index.names) >= {"pair", "time"}:
        df = df.reset_index()

    # Falls Zeit als Index ohne Spaltennamen vorliegt
    if "pair" not in df.columns and df.index.name == "pair":
        df = df.reset_index()
    if "time" not in df.columns and df.index.name == "time":
        df = df.reset_index()

    if "pair" not in df.columns:
        raise KeyError(f"'pair' Spalte fehlt in {path}")
    df = df[df["pair"] == pair].copy()

    # Zeitspalte finden
    time_col = None
    for col in df.columns:
        if col.lower() in {"time", "timestamp", "date", "datetime"}:
            time_col = col
            break
    if time_col is None:
        raise KeyError(f"Keine Zeitspalte in {path}")

    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df[time_col] = pd.to_datetime(df[time_col], utc=True)
    elif df[time_col].dt.tz is None:
        df[time_col] = df[time_col].dt.tz_localize("UTC")
    df = df.rename(columns={time_col: "time"})
    return df.sort_values("time").reset_index(drop=True)


# --------------------------------------------------------------------------- #
# Datenklassen
# --------------------------------------------------------------------------- #


@dataclass
class Pivot:
    index: int
    time: pd.Timestamp
    direction: str  # 'bullish' | 'bearish'
    pivot: float
    extreme: float
    near: float
    gap_size: float

    @property
    def gap_low(self) -> float:
        return min(self.pivot, self.extreme)

    @property
    def gap_high(self) -> float:
        return max(self.pivot, self.extreme)


@dataclass
class Refinement:
    timeframe: str
    time: pd.Timestamp
    pivot_level: float
    extreme: float
    size: float
    direction: str  # 'bullish' | 'bearish'

    @property
    def entry_level(self) -> float:
        # Entry am Pivot-Level der Verfeinerung
        return self.pivot_level


@dataclass
class Trade:
    pair: str
    direction: str
    pivot_time: pd.Timestamp
    entry_time: pd.Timestamp
    entry_price: float
    tp_price: float
    sl_price: float
    exit_time: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    pnl_pips: Optional[float] = None
    pnl_r: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "pair": self.pair,
            "direction": self.direction,
            "pivot_time": self.pivot_time,
            "entry_time": self.entry_time,
            "entry_price": self.entry_price,
            "tp_price": self.tp_price,
            "sl_price": self.sl_price,
            "exit_time": self.exit_time,
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
            "pnl_pips": self.pnl_pips,
            "pnl_r": self.pnl_r,
        }


# --------------------------------------------------------------------------- #
# Pivot- und Verfeinerungslogik
# --------------------------------------------------------------------------- #


def detect_htf_pivots(df: pd.DataFrame, min_body_pct: float = 2.0) -> List[Pivot]:
    pivots: List[Pivot] = []
    for i in range(1, len(df)):
        k1 = df.iloc[i - 1]
        k2 = df.iloc[i]
        if body_pct(k1) < min_body_pct or body_pct(k2) < min_body_pct:
            continue

        prev_red = k1["close"] < k1["open"]
        prev_green = k1["close"] > k1["open"]
        curr_green = k2["close"] > k2["open"]
        curr_red = k2["close"] < k2["open"]

        if prev_red and curr_green:
            direction = "bullish"
        elif prev_green and curr_red:
            direction = "bearish"
        else:
            continue

        if direction == "bullish":
            extreme = min(k1["low"], k2["low"])
            near = max(k1["low"], k2["low"])
        else:
            extreme = max(k1["high"], k2["high"])
            near = min(k1["high"], k2["high"])

        pivot_level = k2["open"]  # kein Versatz, reines Open K2
        gap_size = abs(pivot_level - extreme)

        pivots.append(
            Pivot(
                index=i,
                time=k2["time"],
                direction=direction,
                pivot=pivot_level,
                extreme=extreme,
                near=near,
                gap_size=gap_size,
            )
        )
    return pivots


def detect_refinements(
    df: pd.DataFrame,
    htf_pivot: Pivot,
    timeframe: str,
    max_size_frac: float = 0.2,
    min_body_pct: float = 2.0,
) -> List[Refinement]:
    refinements: List[Refinement] = []
    # wick diff boundaries
    wick_low = min(htf_pivot.extreme, htf_pivot.near)
    wick_high = max(htf_pivot.extreme, htf_pivot.near)
    max_size = htf_pivot.gap_size * max_size_frac

    for i in range(1, len(df)):
        k1 = df.iloc[i - 1]
        k2 = df.iloc[i]
        if k2["time"] <= htf_pivot.time:
            continue  # erst nach HTF-Pivot

        if body_pct(k1) < min_body_pct or body_pct(k2) < min_body_pct:
            continue

        prev_red = k1["close"] < k1["open"]
        prev_green = k1["close"] > k1["open"]
        curr_green = k2["close"] > k2["open"]
        curr_red = k2["close"] < k2["open"]

        if prev_red and curr_green:
            direction = "bullish"
        elif prev_green and curr_red:
            direction = "bearish"
        else:
            continue

        if direction == "bullish":
            extreme = min(k1["low"], k2["low"])
            near = max(k1["low"], k2["low"])
        else:
            extreme = max(k1["high"], k2["high"])
            near = min(k1["high"], k2["high"])

        pivot_level = k2["open"]
        size = abs(pivot_level - extreme)
        if size > max_size or size == 0:
            continue

        # Position: innerhalb Wick-Diff, Ausnahme: exakt auf Pivot Near erlaubt
        low = min(pivot_level, extreme)
        high = max(pivot_level, extreme)
        inside = (low >= wick_low and high <= wick_high) or np.isclose(high, htf_pivot.near)
        if not inside:
            continue

        refinements.append(
            Refinement(
                timeframe=timeframe,
                time=k2["time"],
                pivot_level=pivot_level,
                extreme=extreme,
                size=size,
                direction=direction,
            )
        )

    return refinements


# --------------------------------------------------------------------------- #
# SL/TP Berechnung
# --------------------------------------------------------------------------- #


def compute_sl_tp(
    direction: str, entry: float, pivot: Pivot, pair: str
) -> Optional[Tuple[float, float, float]]:
    gap = pivot.gap_size
    fib0 = pivot.pivot
    fib1 = pivot.extreme

    if direction == "bullish":
        tp = fib0 + gap  # Fib -1 über Pivot
        fib11 = fib1 - 0.1 * gap
        base_sl = fib11
        min_sl = entry - 60 * price_per_pip(pair)
        sl = min(base_sl, min_sl)
        if sl >= entry:
            sl = entry - 60 * price_per_pip(pair)
    else:
        tp = fib0 - gap  # Fib -1 unter Pivot
        fib11 = fib1 + 0.1 * gap
        base_sl = fib11
        min_sl = entry + 60 * price_per_pip(pair)
        sl = max(base_sl, min_sl)
        if sl <= entry:
            sl = entry + 60 * price_per_pip(pair)

    # RR prüfen
    if direction == "bullish":
        risk = entry - sl
        reward = tp - entry
    else:
        risk = sl - entry
        reward = entry - tp

    if risk <= 0 or reward <= 0:
        return None

    rr = reward / risk
    if rr < 1.0:
        return None
    if rr > 1.5:
        # SL nach außen verschieben, so dass RR = 1.5
        if direction == "bullish":
            sl = entry - reward / 1.5
        else:
            sl = entry + reward / 1.5
    return sl, tp, rr


# --------------------------------------------------------------------------- #
# Backtest-Engine
# --------------------------------------------------------------------------- #


class Model3Backtester:
    def __init__(self, pairs: List[str]):
        self.pairs = pairs
        self.trades: List[Trade] = []

    def run(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        for pair in self.pairs:
            print(f"\n=== {pair} (W) ===")
            w_df = load_tf_data("W", pair)
            if start_date:
                w_df = w_df[w_df["time"] >= pd.Timestamp(start_date, tz="UTC")]
            if end_date:
                w_df = w_df[w_df["time"] <= pd.Timestamp(end_date, tz="UTC")]

            htf_pivots = detect_htf_pivots(w_df, min_body_pct=2.0)
            print(f"Pivots gefunden: {len(htf_pivots)}")

            # Cache untere TFs
            cache = {
                "H1": load_tf_data("H1", pair),
                "H4": load_tf_data("H4", pair),
                "D": load_tf_data("D", pair),
                "3D": load_tf_data("3D", pair),
            }

            # Entry-Simulation auf H1
            h1_df = cache["H1"]

            for pivot in htf_pivots:
                self._process_pivot(pair, pivot, cache, h1_df)

        return pd.DataFrame([t.to_dict() for t in self.trades])

    def _process_pivot(self, pair: str, pivot: Pivot, cache: Dict[str, pd.DataFrame], h1_df: pd.DataFrame):
        # Refinements sammeln
        refinements: List[Refinement] = []
        tf_order = ["W", "3D", "D", "H4", "H1"]  # Priorität absteigend
        for tf in tf_order:
            if tf == "W":
                # W-Refinement = HTF selbst nicht nötig
                continue
            ref_list = detect_refinements(cache[tf], pivot, tf, max_size_frac=0.2, min_body_pct=2.0)
            refinements.extend(ref_list)

        if not refinements:
            return

        # höchste TF zuerst
        def tf_priority(tf: str) -> int:
            order = {"W": 0, "3D": 1, "D": 2, "H4": 3, "H1": 4}
            return order.get(tf, 99)

        refinements.sort(key=lambda r: tf_priority(r.timeframe))
        current_ref_idx = 0

        # erstes Gap-Trigger auf H1 suchen
        gap_low, gap_high = pivot.gap_low, pivot.gap_high
        start_mask = h1_df["time"] > pivot.time
        h1_after = h1_df[start_mask].reset_index(drop=True)
        if h1_after.empty:
            return

        gap_touch_idx = None
        for idx, row in h1_after.iterrows():
            if row["low"] <= gap_high and row["high"] >= gap_low:
                gap_touch_idx = idx
                break
        if gap_touch_idx is None:
            return

        # ab Gap-Trigger nach Verfeinerung suchen
        for idx in range(gap_touch_idx, len(h1_after)):
            row = h1_after.iloc[idx]
            # aktuelle Verfeinerung
            if current_ref_idx >= len(refinements):
                break
            ref = refinements[current_ref_idx]

            # Verfeinerung invalidieren, wenn Preis sie schon durchschlägt? -> hier: wenn komplett überschritten
            ref_low = min(ref.pivot_level, ref.extreme)
            ref_high = max(ref.pivot_level, ref.extreme)
            # Entry-Touch
            if row["low"] <= ref.entry_level <= row["high"]:
                # Entry auslösen
                entry_price = ref.entry_level
                direction = pivot.direction
                sl_tp = compute_sl_tp(direction, entry_price, pivot, pair)
                if sl_tp is None:
                    current_ref_idx += 1
                    continue
                sl, tp, rr = sl_tp
                entry_time = row["time"]

                trade = Trade(
                    pair=pair,
                    direction=direction,
                    pivot_time=pivot.time,
                    entry_time=entry_time,
                    entry_price=entry_price,
                    tp_price=tp,
                    sl_price=sl,
                )

                exit_info = self._simulate_trade(h1_after, idx + 1, trade)
                if exit_info:
                    self.trades.append(exit_info)
                break
            else:
                # wenn Kerze die Verfeinerung durchbricht, nächstes Refinement
                if row["high"] > ref_high and row["low"] < ref_low:
                    current_ref_idx += 1
                    continue

    def _simulate_trade(self, h1_after: pd.DataFrame, start_idx: int, trade: Trade) -> Optional[Trade]:
        for i in range(start_idx, len(h1_after)):
            candle = h1_after.iloc[i]
            if trade.direction == "bullish":
                if candle["low"] <= trade.sl_price:
                    trade.exit_price = trade.sl_price
                    trade.exit_time = candle["time"]
                    trade.exit_reason = "sl"
                    trade.pnl_pips = -pips(trade.entry_price - trade.sl_price, trade.pair)
                    trade.pnl_r = trade.pnl_pips / pips(trade.entry_price - trade.sl_price, trade.pair)
                    return trade
                if candle["high"] >= trade.tp_price:
                    trade.exit_price = trade.tp_price
                    trade.exit_time = candle["time"]
                    trade.exit_reason = "tp"
                    trade.pnl_pips = pips(trade.tp_price - trade.entry_price, trade.pair)
                    trade.pnl_r = trade.pnl_pips / pips(trade.entry_price - trade.sl_price, trade.pair)
                    return trade
            else:
                if candle["high"] >= trade.sl_price:
                    trade.exit_price = trade.sl_price
                    trade.exit_time = candle["time"]
                    trade.exit_reason = "sl"
                    trade.pnl_pips = -pips(trade.sl_price - trade.entry_price, trade.pair)
                    trade.pnl_r = trade.pnl_pips / pips(trade.sl_price - trade.entry_price, trade.pair)
                    return trade
                if candle["low"] <= trade.tp_price:
                    trade.exit_price = trade.tp_price
                    trade.exit_time = candle["time"]
                    trade.exit_reason = "tp"
                    trade.pnl_pips = pips(trade.entry_price - trade.tp_price, trade.pair)
                    trade.pnl_r = trade.pnl_pips / pips(trade.sl_price - trade.entry_price, trade.pair)
                    return trade

        # kein Exit -> schließen am letzten Kurs
        last = h1_after.iloc[-1]
        trade.exit_price = last["close"]
        trade.exit_time = last["time"]
        trade.exit_reason = "manual"
        if trade.direction == "bullish":
            trade.pnl_pips = pips(trade.exit_price - trade.entry_price, trade.pair)
            trade.pnl_r = trade.pnl_pips / pips(trade.entry_price - trade.sl_price, trade.pair)
        else:
            trade.pnl_pips = pips(trade.entry_price - trade.exit_price, trade.pair)
            trade.pnl_r = trade.pnl_pips / pips(trade.sl_price - trade.entry_price, trade.pair)
        return trade


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main():
    parser = argparse.ArgumentParser(description="Model 3 Backtest (Standard, Pivot W)")
    parser.add_argument(
        "--pairs",
        nargs="+",
        default=[
            "AUDCAD",
            "AUDCHF",
            "AUDJPY",
            "AUDNZD",
            "AUDUSD",
            "CADCHF",
            "CADJPY",
            "CHFJPY",
            "EURAUD",
            "EURCAD",
            "EURCHF",
            "EURGBP",
            "EURJPY",
            "EURNZD",
            "EURUSD",
            "GBPAUD",
            "GBPCAD",
            "GBPCHF",
            "GBPJPY",
            "GBPNZD",
            "GBPUSD",
            "NZDCAD",
            "NZDCHF",
            "NZDJPY",
            "NZDUSD",
            "USDCAD",
            "USDCHF",
            "USDJPY",
        ],
        help="Pairs (default: alle 28 Forex-Paare)",
    )
    parser.add_argument("--start-date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--output", type=str, default=None, help="Pfad für CSV-Export")
    args = parser.parse_args()

    bt = Model3Backtester(pairs=args.pairs)
    results = bt.run(start_date=args.start_date, end_date=args.end_date)

    print(f"\nTrades: {len(results)}")
    if len(results) > 0:
        print(results[["pair", "direction", "entry_time", "exit_reason", "pnl_pips"]].head())

    if args.output:
        out = Path(args.output)
        results.to_csv(out, index=False)
        print(f"Gespeichert: {out}")


if __name__ == "__main__":
    main()

