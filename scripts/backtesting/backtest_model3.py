"""
Model 3 Backtest (Standard-Variante)
------------------------------------

- Pivot-TF: 3D, W, M (alle HTF-Pivots)
- Verfeinerungen: 1H, 4H, D, 3D, W (höchste gültige wird genutzt)
- Entry: 1H Close Bestätigung (default) | parametrisierbar: 1h_close, 4h_close, direct_touch
- Doji-Filter: 5%
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
    time: pd.Timestamp  # K2 OPEN Zeit
    k1_time: pd.Timestamp  # K1 OPEN Zeit
    direction: str  # 'bullish' | 'bearish'
    pivot: float
    extreme: float
    near: float
    gap_size: float
    valid_time: pd.Timestamp = None  # Pivot ist valide NACH Close K2 (= K3 OPEN)

    @property
    def gap_low(self) -> float:
        return min(self.pivot, self.extreme)

    @property
    def gap_high(self) -> float:
        return max(self.pivot, self.extreme)

    @property
    def wick_diff_low(self) -> float:
        return min(self.extreme, self.near)

    @property
    def wick_diff_high(self) -> float:
        return max(self.extreme, self.near)


@dataclass
class Refinement:
    timeframe: str
    time: pd.Timestamp
    pivot_level: float
    extreme: float
    near: float
    size: float
    direction: str  # 'bullish' | 'bearish'

    @property
    def entry_level(self) -> float:
        # Entry am NEAR der Verfeinerung (nicht extreme, da extreme näher am SL ist)
        return self.near


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
    # Validation-Felder
    htf_timeframe: Optional[str] = None
    pivot_valid_time: Optional[pd.Timestamp] = None
    pivot_level: Optional[float] = None
    pivot_extreme: Optional[float] = None
    pivot_near: Optional[float] = None
    pivot_gap_low: Optional[float] = None
    pivot_gap_high: Optional[float] = None
    pivot_wick_diff_low: Optional[float] = None
    pivot_wick_diff_high: Optional[float] = None
    gap_touch_time: Optional[pd.Timestamp] = None
    refinement_tf: Optional[str] = None
    refinement_pivot: Optional[float] = None
    refinement_extreme: Optional[float] = None
    refinement_entry: Optional[float] = None

    def to_dict(self) -> Dict:
        return {
            "pair": self.pair,
            "direction": self.direction,
            "htf_timeframe": self.htf_timeframe,
            # Pivot Info
            "pivot_time": self.pivot_time,
            "pivot_valid_time": self.pivot_valid_time,
            "pivot_level": self.pivot_level,
            "pivot_extreme": self.pivot_extreme,
            "pivot_near": self.pivot_near,
            "pivot_gap_low": self.pivot_gap_low,
            "pivot_gap_high": self.pivot_gap_high,
            "pivot_wick_diff_low": self.pivot_wick_diff_low,
            "pivot_wick_diff_high": self.pivot_wick_diff_high,
            # Gap Touch
            "gap_touch_time": self.gap_touch_time,
            # Refinement Info
            "refinement_tf": self.refinement_tf,
            "refinement_pivot": self.refinement_pivot,
            "refinement_extreme": self.refinement_extreme,
            "refinement_entry": self.refinement_entry,
            # Trade Info
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


def detect_htf_pivots(df: pd.DataFrame, min_body_pct: float = 5.0) -> List[Pivot]:
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

        # Pivot ist valide NACH Close von K2 (= Open der nächsten Kerze)
        if i + 1 < len(df):
            valid_time = df.iloc[i + 1]["time"]
        else:
            valid_time = k2["time"]  # Letzte Kerze: verwende K2-Zeit

        pivots.append(
            Pivot(
                index=i,
                time=k2["time"],
                k1_time=k1["time"],
                direction=direction,
                pivot=pivot_level,
                extreme=extreme,
                near=near,
                gap_size=gap_size,
                valid_time=valid_time,
            )
        )
    return pivots


def detect_refinements(
    df: pd.DataFrame,
    htf_pivot: Pivot,
    timeframe: str,
    max_size_frac: float = 0.2,
    min_body_pct: float = 5.0,
) -> List[Refinement]:
    """
    Sucht nach Verfeinerungen (kleinere Pivots) die:
    1. WÄHREND K1/K2 des HTF-Pivots entstanden sind (K2 zwischen htf_pivot.k1_time und htf_pivot.valid_time)
    2. Innerhalb der Wick Difference liegen (oder Extreme exakt auf HTF Near)
    3. Max 20% der HTF Pivot Gap groß sind
    4. NICHT berührt wurden bis HTF-Pivot valide wurde (K2 Close)
    5. Gleiche Richtung wie HTF-Pivot haben
    6. Doji-Filter: Body >= 5%

    WICHTIG: Alle Timestamps = OPEN-Zeit der Bars!
    """
    refinements: List[Refinement] = []

    # Wick Difference = Zone von NEAR bis EXTREME (zwischen den beiden Wicks!)
    # Bullish: NEAR (höherer Low) bis EXTREME (tiefster Low)
    # Bearish: EXTREME (höchster High) bis NEAR (tieferer High)
    if htf_pivot.direction == "bullish":
        wick_low = htf_pivot.extreme  # tiefster Punkt
        wick_high = htf_pivot.near    # höherer Low
    else:  # bearish
        wick_low = htf_pivot.near     # tieferer High
        wick_high = htf_pivot.extreme # höchster Punkt

    max_size = htf_pivot.gap_size * max_size_frac

    # Zeitfenster: Refinements müssen WÄHREND K1/K2 des HTF-Pivots entstanden sein
    # K2 der Verfeinerung muss >= htf_pivot.k1_time UND < htf_pivot.valid_time sein
    # (alle Timestamps sind OPEN-Zeit der Bars!)

    for i in range(1, len(df)):
        k1 = df.iloc[i - 1]
        k2 = df.iloc[i]

        # Zeitfenster-Check: K2 muss zwischen HTF K1 und HTF K3 (valid_time) liegen
        if k2["time"] < htf_pivot.k1_time or k2["time"] >= htf_pivot.valid_time:
            continue  # außerhalb des Zeitfensters

        # Doji-Filter: Body >= 5%
        if body_pct(k1) < min_body_pct or body_pct(k2) < min_body_pct:
            continue

        # Pivot-Pattern erkennen
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

        # Nur Refinements mit gleicher Richtung wie HTF-Pivot
        if direction != htf_pivot.direction:
            continue

        # Refinement-Struktur berechnen
        if direction == "bullish":
            extreme = min(k1["low"], k2["low"])
            near = max(k1["low"], k2["low"])
        else:
            extreme = max(k1["high"], k2["high"])
            near = min(k1["high"], k2["high"])

        pivot_level = k2["open"]

        # WICHTIG: Size der Verfeinerung = EXTREME bis NEAR (Wick Diff!)
        # NICHT Pivot bis Extreme!
        size = abs(extreme - near)

        # Größen-Check: max 20% der HTF Pivot Gap (IMMER, keine Ausnahme!)
        if size > max_size or size == 0:
            continue

        # Position-Check: Verfeinerung muss KOMPLETT in Wick Diff liegen
        # ODER: Extreme der Verfeinerung liegt EXAKT auf HTF Pivot Near
        # (= Verfeinerung außerhalb aber schneidet sich in einem Punkt)

        # Verfeinerung Wick Diff = von NEAR bis EXTREME der Verfeinerung
        if direction == "bullish":
            ref_wick_low = extreme  # tiefster Punkt der Verfeinerung
            ref_wick_high = near    # höherer Punkt
        else:  # bearish
            ref_wick_low = near     # tieferer Punkt
            ref_wick_high = extreme # höchster Punkt

        # Check 1: KOMPLETT innerhalb Wick Diff des HTF-Pivots?
        completely_inside = (ref_wick_low >= wick_low and ref_wick_high <= wick_high)

        # Check 2: Extreme der Verfeinerung EXAKT auf HTF Pivot Near?
        extreme_on_near = np.isclose(extreme, htf_pivot.near, atol=0.00001)

        if not (completely_inside or extreme_on_near):
            continue  # Weder komplett inside noch Extreme auf Near

        # "Unberührt"-Check: NEAR der Verfeinerung darf nicht berührt worden sein
        # zwischen ihrer Entstehung (k2["time"]) und HTF-Pivot valid_time
        refinement_created = k2["time"]

        # Hole nur Candles im relevanten Zeitfenster (Optimierung!)
        touch_window = df[
            (df["time"] > refinement_created) &
            (df["time"] <= htf_pivot.valid_time)
        ]

        # Check ob NEAR der Verfeinerung berührt wurde
        was_touched = False
        for _, candle in touch_window.iterrows():
            if direction == "bullish":
                # Bullish: NEAR berührt wenn candle low <= near
                if candle["low"] <= near:
                    was_touched = True
                    break
            else:  # bearish
                # Bearish: NEAR berührt wenn candle high >= near
                if candle["high"] >= near:
                    was_touched = True
                    break

        if was_touched:
            continue  # NEAR wurde berührt -> Verfeinerung ungültig

        # Alle Checks bestanden -> gültige Refinement
        refinements.append(
            Refinement(
                timeframe=timeframe,
                time=k2["time"],
                pivot_level=pivot_level,
                extreme=extreme,
                near=near,
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
        fib11 = fib1 - 0.1 * gap  # Fib 1.1 unter Extreme
        min_sl_from_entry = entry - 60 * price_per_pip(pair)
        # SL muss BEIDE Bedingungen erfüllen: >= 60 Pips von Entry UND unter Fib 1.1
        sl = min(fib11, min_sl_from_entry)
        # Falls SL zu nah am Entry (sollte nicht passieren), auf Min. 60 Pips setzen
        if sl >= entry:
            return None  # Setup ungültig, SL kann nicht gesetzt werden
    else:
        tp = fib0 - gap  # Fib -1 unter Pivot
        fib11 = fib1 + 0.1 * gap  # Fib 1.1 über Extreme
        min_sl_from_entry = entry + 60 * price_per_pip(pair)
        # SL muss BEIDE Bedingungen erfüllen: >= 60 Pips von Entry UND über Fib 1.1
        sl = max(fib11, min_sl_from_entry)
        # Falls SL zu nah am Entry (sollte nicht passieren), auf Min. 60 Pips setzen
        if sl <= entry:
            return None  # Setup ungültig, SL kann nicht gesetzt werden

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
    def __init__(self, pairs: List[str], htf_timeframes: List[str] = None, entry_confirmation: str = "direct_touch", max_pivots_per_pair: int = None):
        self.pairs = pairs
        self.htf_timeframes = htf_timeframes or ["3D", "W", "M"]
        self.entry_confirmation = entry_confirmation  # "direct_touch" (Standard), "1h_close", "4h_close"
        self.max_pivots_per_pair = max_pivots_per_pair  # Limitiere Pivots für schnellere Validation
        self.trades: List[Trade] = []

    def run(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> pd.DataFrame:
        for pair in self.pairs:
            print(f"\n=== {pair} ===")

            # Cache alle TFs (HTF + LTF)
            print("  Lade Daten...")
            cache = {
                "H1": load_tf_data("H1", pair),
                "H4": load_tf_data("H4", pair),
                "D": load_tf_data("D", pair),
                "3D": load_tf_data("3D", pair),
                "W": load_tf_data("W", pair),
                "M": load_tf_data("M", pair),
            }

            # Entry-Simulation auf H1
            h1_df = cache["H1"]

            # OPTIMIERUNG: Filtere H1-Daten sofort wenn start_date gesetzt
            if start_date:
                start_ts = pd.Timestamp(start_date, tz="UTC")
                h1_df = h1_df[h1_df["time"] >= start_ts].copy()
                print(f"  H1-Daten gefiltert: {len(h1_df)} Kerzen ab {start_date}")
            if end_date:
                end_ts = pd.Timestamp(end_date, tz="UTC")
                h1_df = h1_df[h1_df["time"] <= end_ts].copy()

            # Für jeden HTF-Timeframe Pivots finden
            for htf_tf in self.htf_timeframes:
                print(f"  {htf_tf} Pivots:")
                htf_df = cache[htf_tf].copy()

                if start_date:
                    htf_df = htf_df[htf_df["time"] >= pd.Timestamp(start_date, tz="UTC")]
                if end_date:
                    htf_df = htf_df[htf_df["time"] <= pd.Timestamp(end_date, tz="UTC")]

                htf_pivots = detect_htf_pivots(htf_df, min_body_pct=5.0)
                print(f"    {len(htf_pivots)} gefunden")

                # Limitiere Pivot-Anzahl für Validation (zufälliges Sampling)
                if self.max_pivots_per_pair and len(htf_pivots) > self.max_pivots_per_pair:
                    import random
                    htf_pivots = random.sample(htf_pivots, self.max_pivots_per_pair)
                    print(f"    -> {len(htf_pivots)} zufaellig ausgewaehlt (Validation-Modus)")

                for i, pivot in enumerate(htf_pivots, 1):
                    print(f"    Prozessiere Pivot {i}/{len(htf_pivots)}...", end="\r")
                    self._process_pivot(pair, htf_tf, pivot, cache, h1_df)
                print()  # Neue Zeile nach Progress

        return pd.DataFrame([t.to_dict() for t in self.trades])

    def _process_pivot(self, pair: str, htf_tf: str, pivot: Pivot, cache: Dict[str, pd.DataFrame], h1_df: pd.DataFrame):
        # Refinements sammeln - nur auf TFs unter dem HTF-Pivot
        refinements: List[Refinement] = []
        # TF-Hierarchie: M > W > 3D > D > H4 > H1
        all_tfs = ["M", "W", "3D", "D", "H4", "H1"]
        htf_idx = all_tfs.index(htf_tf)
        ltf_tfs = all_tfs[htf_idx + 1:]  # Nur niedrigere TFs

        # DEBUG
        debug = False  # Setze auf True für detailliertes Debugging
        if debug:
            print(f"\n  [DEBUG] Pivot @ {pivot.time}, Direction: {pivot.direction}")
            print(f"  [DEBUG] Gap: {pivot.gap_size:.5f}, Wick Diff: {abs(pivot.near - pivot.extreme):.5f}")
            print(f"  [DEBUG] Suche Verfeinerungen in TFs: {ltf_tfs}")

        for tf in ltf_tfs:
            if tf not in cache:
                continue
            ref_list = detect_refinements(cache[tf], pivot, tf, max_size_frac=0.2, min_body_pct=5.0)
            if debug and ref_list:
                print(f"  [DEBUG] {tf}: {len(ref_list)} Verfeinerung(en) gefunden")
            refinements.extend(ref_list)

        if not refinements:
            if debug:
                print(f"  [DEBUG] Keine Verfeinerungen gefunden -> Skip Pivot")
            return

        # höchste TF zuerst (M > W > 3D > D > H4 > H1)
        def tf_priority(tf: str) -> int:
            order = {"M": 0, "W": 1, "3D": 2, "D": 3, "H4": 4, "H1": 5}
            return order.get(tf, 99)

        refinements.sort(key=lambda r: tf_priority(r.timeframe))
        current_ref_idx = 0

        # Gap-Trigger & Entry-Suche NUR NACH pivot.valid_time (= nach Close K2)
        gap_low, gap_high = pivot.gap_low, pivot.gap_high
        start_mask = h1_df["time"] >= pivot.valid_time  # WICHTIG: >= valid_time, NICHT > pivot.time!
        h1_after = h1_df[start_mask].reset_index(drop=True)
        if h1_after.empty:
            return

        # OPTIMIERUNG: Vectorized Gap-Touch Detection
        gap_touched = (h1_after["low"] <= gap_high) & (h1_after["high"] >= gap_low)
        if not gap_touched.any():
            if debug:
                print(f"  [DEBUG] Pivot Gap wurde NIE berührt -> Skip")
            return
        gap_touch_idx = gap_touched.idxmax()  # Erste True-Position
        gap_touch_time = h1_after.iloc[gap_touch_idx]["time"]

        if debug:
            print(f"  [DEBUG] Gap Touch @ {gap_touch_time}")

        # WICHTIG: Gap Touch muss NACH valid_time sein!
        if gap_touch_time < pivot.valid_time:
            if debug:
                print(f"  [DEBUG] Gap Touch VOR valid_time -> Skip (sollte nicht passieren!)")
            return  # Sollte nicht passieren, aber Sicherheitscheck

        # ab Gap-Trigger nach Verfeinerung suchen
        if debug:
            print(f"  [DEBUG] Suche Entry ab Gap-Touch, {len(refinements)} Verfeinerung(en) verfuegbar")
            print(f"  [DEBUG] Erste Verfeinerung: TF={refinements[0].timeframe}, Entry-Level (NEAR)={refinements[0].entry_level:.5f}")

        for idx in range(gap_touch_idx, len(h1_after)):
            row = h1_after.iloc[idx]
            # aktuelle Verfeinerung
            if current_ref_idx >= len(refinements):
                if debug:
                    print(f"  [DEBUG] Alle Verfeinerungen aufgebraucht, kein Trade")
                break
            ref = refinements[current_ref_idx]

            # Verfeinerung invalidieren, wenn Preis sie schon durchschlägt
            ref_low = min(ref.pivot_level, ref.extreme, ref.near)
            ref_high = max(ref.pivot_level, ref.extreme, ref.near)

            # Entry-Touch prüfen (Entry = NEAR der Verfeinerung!)
            touched = row["low"] <= ref.entry_level <= row["high"]

            if touched:
                if debug:
                    print(f"  [DEBUG] Verfeinerung berührt @ {row['time']}, Entry-Level={ref.entry_level:.5f}")
                # Entry-Bestätigung abhängig von Modus
                if self.entry_confirmation == "direct_touch":
                    # Direkter Entry ohne Close-Bestätigung
                    entry_price = ref.entry_level
                    entry_time = row["time"]
                    entry_confirmed = True
                elif self.entry_confirmation == "1h_close":
                    # 1H Close Bestätigung
                    if pivot.direction == "bullish":
                        entry_confirmed = row["close"] > ref.entry_level
                    else:
                        entry_confirmed = row["close"] < ref.entry_level

                    if entry_confirmed:
                        # Entry bei Open der nächsten Candle
                        if idx + 1 >= len(h1_after):
                            current_ref_idx += 1
                            continue
                        next_candle = h1_after.iloc[idx + 1]
                        entry_price = next_candle["open"]
                        entry_time = next_candle["time"]
                    else:
                        # Close nicht bestätigt → Verfeinerung löschen
                        current_ref_idx += 1
                        continue
                elif self.entry_confirmation == "4h_close":
                    # 4H Close Bestätigung (vereinfacht: prüfe ob 1H close bestätigt, sonst skip)
                    # TODO: Für vollständige 4H-Implementierung müsste man 4H-Daten nutzen
                    if pivot.direction == "bullish":
                        entry_confirmed = row["close"] > ref.entry_level
                    else:
                        entry_confirmed = row["close"] < ref.entry_level

                    if entry_confirmed:
                        if idx + 1 >= len(h1_after):
                            current_ref_idx += 1
                            continue
                        next_candle = h1_after.iloc[idx + 1]
                        entry_price = next_candle["open"]
                        entry_time = next_candle["time"]
                    else:
                        current_ref_idx += 1
                        continue
                else:
                    # Default: direct touch
                    entry_price = ref.entry_level
                    entry_time = row["time"]
                    entry_confirmed = True

                if entry_confirmed:
                    direction = pivot.direction
                    sl_tp = compute_sl_tp(direction, entry_price, pivot, pair)
                    if sl_tp is None:
                        if debug:
                            print(f"  [DEBUG] SL/TP Setup ungültig (RR < 1.0 oder SL zu nah) -> nächste Verfeinerung")
                        current_ref_idx += 1
                        continue
                    sl, tp, rr = sl_tp
                    if debug:
                        print(f"  [DEBUG] Entry bestätigt! SL={sl:.5f}, TP={tp:.5f}, RR={rr:.2f}")

                    trade = Trade(
                        pair=pair,
                        direction=direction,
                        pivot_time=pivot.time,
                        entry_time=entry_time,
                        entry_price=entry_price,
                        tp_price=tp,
                        sl_price=sl,
                        # Validation-Felder - Pivot Info
                        htf_timeframe=htf_tf,
                        pivot_valid_time=pivot.valid_time,
                        pivot_level=pivot.pivot,
                        pivot_extreme=pivot.extreme,
                        pivot_near=pivot.near,
                        pivot_gap_low=pivot.gap_low,
                        pivot_gap_high=pivot.gap_high,
                        pivot_wick_diff_low=pivot.wick_diff_low,
                        pivot_wick_diff_high=pivot.wick_diff_high,
                        # Gap Touch
                        gap_touch_time=gap_touch_time,
                        # Refinement Info
                        refinement_tf=ref.timeframe,
                        refinement_pivot=ref.pivot_level,
                        refinement_extreme=ref.extreme,
                        refinement_entry=ref.entry_level,
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
    parser = argparse.ArgumentParser(description="Model 3 Backtest (Standard, Pivot 3D/W/M)")
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
    parser.add_argument(
        "--htf-timeframes",
        nargs="+",
        default=["3D", "W", "M"],
        help="HTF Pivot Timeframes (default: 3D W M)",
    )
    parser.add_argument(
        "--entry-confirmation",
        type=str,
        default="direct_touch",
        choices=["direct_touch", "1h_close", "4h_close"],
        help="Entry Bestätigung: direct_touch (default), 1h_close, 4h_close",
    )
    parser.add_argument("--start-date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, default=None, help="YYYY-MM-DD")
    parser.add_argument("--output", type=str, default=None, help="Pfad für CSV-Export")
    args = parser.parse_args()

    bt = Model3Backtester(pairs=args.pairs, htf_timeframes=args.htf_timeframes, entry_confirmation=args.entry_confirmation)
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

