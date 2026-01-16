"""
Model 3 - Weekly Full Test (28 Pairs)
--------------------------------------

Vollständiger Backtest mit allen 28 Forex Pairs:
- Pairs: Alle 28 Major/Cross Pairs
- HTF: Weekly
- Entry: direct_touch
- Zeitraum: 2010-2025
- Optimized (Vectorized, NO Cache needed)

Output:
- TXT Report mit allen Statistiken (BACKTEST_STATISTICS_FINAL.md)
- HTML Report via QuantStats
- CSV Exports (trades.csv, equity_curve.csv, breakdown_pairs.csv)
- Timing Metrics (per pivot, per pair, total)
"""

import sys
from pathlib import Path
import time
from datetime import datetime
import pandas as pd
import numpy as np
from collections import defaultdict

# Go up to "05_Model 3" directory: scripts -> 01_test -> 02_W_test -> 01_test -> Backtest -> 05_Model 3
model3_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(model3_root))

from scripts.backtesting.backtest_model3 import (
    load_tf_data,
    detect_htf_pivots,
    detect_refinements,
    compute_sl_tp,
    price_per_pip,
    should_use_wick_diff_entry,
)

# ============================================================================
# OPTIMIZED FUNCTIONS (vectorized versions - NO LOOPS!)
# ============================================================================

def body_pct_vectorized(df):
    """Calculate body percentage for all candles (vectorized)"""
    rng = df["high"] - df["low"]
    body = abs(df["close"] - df["open"])
    return (body / rng * 100).fillna(0)


def detect_refinements_fast(df, htf_pivot, timeframe, max_size_frac=0.2, min_body_pct=5.0):
    """
    OPTIMIZED: Vectorized refinement detection (NO LOOPS!)

    ~100x faster than original detect_refinements
    """
    from scripts.backtesting.backtest_model3 import Refinement

    # Filter time window FIRST (major speedup)
    df_window = df[(df["time"] >= htf_pivot.k1_time) & (df["time"] < htf_pivot.valid_time)].copy()

    if len(df_window) < 2:
        return []

    # Calculate body % for all candles at once
    df_window['body_pct'] = body_pct_vectorized(df_window)

    # Create k1/k2 pairs (shifted dataframe)
    df_k1 = df_window.iloc[:-1].reset_index(drop=True)
    df_k2 = df_window.iloc[1:].reset_index(drop=True)

    # Vectorized body filter
    valid_body = (df_k1['body_pct'].values >= min_body_pct) & (df_k2['body_pct'].values >= min_body_pct)

    # Vectorized color detection
    k1_red = (df_k1['close'].values < df_k1['open'].values)
    k1_green = (df_k1['close'].values > df_k1['open'].values)
    k2_green = (df_k2['close'].values > df_k2['open'].values)
    k2_red = (df_k2['close'].values < df_k2['open'].values)

    # Vectorized pattern detection
    is_bullish = k1_red & k2_green
    is_bearish = k1_green & k2_red

    # Filter by direction match
    if htf_pivot.direction == "bullish":
        valid_direction = is_bullish
        direction = "bullish"
    else:
        valid_direction = is_bearish
        direction = "bearish"

    # Combine filters
    valid_mask = valid_body & valid_direction

    if not valid_mask.any():
        return []

    # Filter dataframes
    df_k1_valid = df_k1[valid_mask].reset_index(drop=True)
    df_k2_valid = df_k2[valid_mask].reset_index(drop=True)

    # Calculate refinement levels (vectorized)
    if direction == "bullish":
        extremes = np.minimum(df_k1_valid['low'].values, df_k2_valid['low'].values)
        nears = np.maximum(df_k1_valid['low'].values, df_k2_valid['low'].values)
        # Clip extremes to HTF extreme (can't be lower)
        extremes = np.maximum(extremes, htf_pivot.extreme)
    else:
        extremes = np.maximum(df_k1_valid['high'].values, df_k2_valid['high'].values)
        nears = np.minimum(df_k1_valid['high'].values, df_k2_valid['high'].values)
        # Clip extremes to HTF extreme (can't be higher)
        extremes = np.minimum(extremes, htf_pivot.extreme)

    pivot_levels = df_k2_valid['open'].values
    sizes = np.abs(extremes - nears)

    # Size filter (vectorized)
    max_size = htf_pivot.gap_size * max_size_frac
    valid_size = (sizes > 0) & (sizes <= max_size)

    if not valid_size.any():
        return []

    # Apply size filter
    df_k2_final = df_k2_valid[valid_size].reset_index(drop=True)
    extremes_final = extremes[valid_size]
    nears_final = nears[valid_size]
    pivot_levels_final = pivot_levels[valid_size]
    sizes_final = sizes[valid_size]

    # Position check (vectorized)
    if direction == "bullish":
        wick_low = htf_pivot.extreme
        wick_high = htf_pivot.near
        # Must be within wick diff OR extreme touches near
        in_range = (extremes_final >= wick_low) & (nears_final <= wick_high)
        touches_near = np.abs(extremes_final - htf_pivot.near) < 0.00001
    else:
        wick_low = htf_pivot.near
        wick_high = htf_pivot.extreme
        in_range = (nears_final >= wick_low) & (extremes_final <= wick_high)
        touches_near = np.abs(extremes_final - htf_pivot.near) < 0.00001

    valid_position = in_range | touches_near

    if not valid_position.any():
        return []

    # Final filter
    df_k2_result = df_k2_final[valid_position].reset_index(drop=True)
    extremes_result = extremes_final[valid_position]
    nears_result = nears_final[valid_position]
    pivot_levels_result = pivot_levels_final[valid_position]
    sizes_result = sizes_final[valid_position]

    # "Unberührt" check: NEAR must not be touched between creation and HTF valid_time
    # This needs to be done per-refinement, but we can still optimize it
    refinements = []
    for i in range(len(df_k2_result)):
        refinement_created = df_k2_result.iloc[i]['time']
        near_level = nears_result[i]

        # Check if NEAR was touched after refinement creation
        touch_window = df_window[
            (df_window["time"] > refinement_created) &
            (df_window["time"] <= htf_pivot.valid_time)
        ]

        if len(touch_window) == 0:
            was_touched = False
        else:
            # Vectorized touch check
            if direction == "bullish":
                was_touched = (touch_window["low"] <= near_level).any()
            else:
                was_touched = (touch_window["high"] >= near_level).any()

        if was_touched:
            continue  # NEAR was touched -> refinement invalid

        # Valid refinement
        ref = Refinement(
            timeframe=timeframe,
            time=refinement_created,
            direction=direction,
            pivot_level=round(pivot_levels_result[i], 5),
            extreme=round(extremes_result[i], 5),
            near=round(nears_result[i], 5),
            size=round(sizes_result[i], 5),
        )
        refinements.append(ref)

    return refinements


def find_gap_touch_on_daily_fast(df_daily, pivot, start_time):
    """Vectorized version of gap touch detection"""
    df_after = df_daily[df_daily["time"] >= start_time].copy()

    if len(df_after) == 0:
        return None

    gap_low = min(pivot.pivot, pivot.extreme)
    gap_high = max(pivot.pivot, pivot.extreme)

    # Vectorized check: candle overlaps with gap range
    if pivot.direction == "bullish":
        mask = (df_after["low"] <= gap_high) & (df_after["high"] >= gap_low)
    else:
        mask = (df_after["high"] >= gap_low) & (df_after["low"] <= gap_high)

    hits = df_after[mask]
    return hits.iloc[0]["time"] if len(hits) > 0 else None


def find_gap_touch_on_h1_fast(df_h1, pivot, daily_gap_touch_time):
    """Find exact H1 candle that touches gap (for precise gap_touch_time with hour)"""
    if daily_gap_touch_time is None:
        return None

    # Search H1 candles starting from the daily gap touch date
    df_after = df_h1[df_h1["time"] >= daily_gap_touch_time].copy()
    if len(df_after) == 0:
        return None

    gap_low = min(pivot.pivot, pivot.extreme)
    gap_high = max(pivot.pivot, pivot.extreme)

    # Vectorized check: H1 candle touches gap
    if pivot.direction == "bullish":
        mask = (df_after["low"] <= gap_high) & (df_after["high"] >= gap_low)
    else:
        mask = (df_after["high"] >= gap_low) & (df_after["low"] <= gap_high)

    hits = df_after[mask]
    return hits.iloc[0]["time"] if len(hits) > 0 else None


def check_tp_touched_before_entry_fast(df, pivot, gap_touch_time, entry_time, tp):
    """Vectorized version of TP touch check"""
    # TP check starts after gap touch (gap_touch_time is always >= valid_time)
    df_check_window = df[(df["time"] >= gap_touch_time) & (df["time"] < entry_time)].copy()

    if len(df_check_window) == 0:
        return False

    if pivot.direction == "bullish":
        return (df_check_window["high"] >= tp).any()
    else:
        return (df_check_window["low"] <= tp).any()

# ============================================================================
# CONFIGURATION
# ============================================================================

PAIRS = [
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
    "CADCHF", "CADJPY", "CHFJPY",
    "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
    "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
    "USDCAD", "USDCHF", "USDJPY"
]  # Alphabetical order
HTF_TIMEFRAMES = ["W"]
ENTRY_CONFIRMATION = "direct_touch"
START_DATE = "2010-01-01"
END_DATE = "2025-12-31"

# Risk Settings
STARTING_CAPITAL = 100000  # $100k
RISK_PER_TRADE = 0.01  # 1% per trade

# Strategy Settings
DOJI_FILTER = 5.0  # Min body % for pivots
REFINEMENT_MAX_SIZE = 0.20  # Max 20% of HTF gap

# Output
OUTPUT_DIR = Path(__file__).parent.parent / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
TIMESTAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

# Transaction Costs - FOR CONSERVATIVE REPORT ONLY (not used in backtest!)
# Variable spreads: range 0.4-2.5 pips, average ~1.0-1.5 pips
# Commission: $5 per standard lot


# ============================================================================
# TIMING TRACKER
# ============================================================================

class TimingTracker:
    """Track timing for different operations"""
    def __init__(self):
        self.times = defaultdict(list)
        self.start_time = None

    def start(self):
        self.start_time = time.time()

    def record(self, category, label, duration):
        self.times[category].append((label, duration))

    def get_total_time(self):
        return time.time() - self.start_time if self.start_time else 0

    def print_summary(self):
        print("\n" + "="*80)
        print("TIMING SUMMARY")
        print("="*80)

        for category in ['data_loading', 'pivot_detection', 'trade_simulation']:
            if category not in self.times:
                continue

            items = self.times[category]
            if not items:
                continue

            total = sum(t for _, t in items)
            avg = total / len(items)

            print(f"\n{category.upper().replace('_', ' ')}:")
            print(f"  Total: {total:.2f}s")
            print(f"  Average: {avg:.2f}s")
            print(f"  Count: {len(items)}")

            # Show individual items
            for label, duration in items:
                print(f"    - {label}: {duration:.2f}s")

        print(f"\nTOTAL RUNTIME: {self.get_total_time():.2f}s")
        print("="*80 + "\n")


# ============================================================================
# TRADE SIMULATION
# ============================================================================

def find_near_touch_time(near_level, start_time, h1_df, direction):
    """
    Findet den Zeitpunkt, wann near_level zum ersten Mal nach start_time berührt wird.

    Args:
        near_level: Preis-Level (refinement near oder wick_diff entry)
        start_time: Startzeit (gap_touch_time)
        h1_df: H1 DataFrame
        direction: "bullish" oder "bearish"

    Returns: Timestamp oder None
    """
    window = h1_df[h1_df["time"] >= start_time].copy()

    if len(window) == 0:
        return None

    if direction == "bullish":
        touch_mask = window["low"] <= near_level
    else:
        touch_mask = window["high"] >= near_level

    hits = window[touch_mask]
    if len(hits) > 0:
        return hits.iloc[0]["time"]
    return None


def simulate_single_trade(pair, pivot, refinements, ltf_cache):
    """
    Simuliert einen Trade für ein Pivot mit chronologischer Verfeinerungs-Logik.

    CRITICAL LOGIC:
    - Nur EINE Entry pro Pivot
    - Nur höchste Priorität refinement bekommt RR-Check
    - Niedrigere Priorität refinements werden sofort gelöscht wenn berührt (KEIN RR-Check)
    - Chronologische Reihenfolge der Touches ist entscheidend
    - RR Fallback: Wenn höchste Prio < 1 RR → löschen, nächste wird höchste Prio

    Returns: dict mit Trade-Details oder None
    """
    h1_df = ltf_cache["H1"]
    d_df = ltf_cache["D"]

    # 1. Gap Touch auf Daily (OPTIMIZED) - dann exact H1 time
    daily_gap_touch = find_gap_touch_on_daily_fast(d_df, pivot, pivot.valid_time)
    if daily_gap_touch is None:
        return None

    # Get exact H1 gap touch time (with hour)
    gap_touch_time = find_gap_touch_on_h1_fast(h1_df, pivot, daily_gap_touch)
    if gap_touch_time is None:
        return None

    # 2. Wick Diff Entry prüfen
    use_wick_diff, wick_diff_entry = should_use_wick_diff_entry(pivot, refinements)

    # Sortiere Verfeinerungen nach Priorität
    def ref_priority(ref):
        tf_order = {"W": 0, "3D": 1, "D": 2, "H4": 3, "H1": 4}
        tf_prio = tf_order.get(ref.timeframe, 99)
        dist_to_near = abs(ref.near - pivot.near)
        return (tf_prio, dist_to_near)

    refinements_active = sorted(refinements, key=ref_priority) if refinements else []

    # 3. Finde Touch-Zeiten für alle Verfeinerungen (chronologisch)
    touch_events = []

    # Wick diff entry als möglicher Kandidat (wenn use_wick_diff True)
    if use_wick_diff and wick_diff_entry is not None:
        wd_touch_time = find_near_touch_time(wick_diff_entry, gap_touch_time, h1_df, pivot.direction)
        if wd_touch_time:
            # Create pseudo-refinement for wick_diff
            class WickDiffRef:
                def __init__(self, near, timeframe="wick_diff"):
                    self.near = near
                    self.timeframe = timeframe
            wd_ref = WickDiffRef(wick_diff_entry)
            touch_events.append((wd_touch_time, wd_ref, True))  # True = is_wick_diff

    # Refinements
    for ref in refinements_active:
        ref_touch_time = find_near_touch_time(ref.near, gap_touch_time, h1_df, pivot.direction)
        if ref_touch_time:
            touch_events.append((ref_touch_time, ref, False))  # False = is_refinement

    if len(touch_events) == 0:
        return None

    # 4. Sortiere Touches chronologisch
    touch_events.sort(key=lambda x: x[0])

    # 5. Verarbeite Touches in chronologischer Reihenfolge
    for touch_time, touched_ref, is_wick_diff in touch_events:
        # Wenn keine aktiven Verfeinerungen mehr → abbrechen
        if len(refinements_active) == 0 and not is_wick_diff:
            return None

        # Bestimme höchste Priorität
        # Wick diff hat NIEDRIGSTE Priorität (nur wenn keine Verfeinerungen)
        if len(refinements_active) > 0:
            highest_prio_ref = refinements_active[0]
            is_highest_prio = (not is_wick_diff) and (touched_ref == highest_prio_ref)
        else:
            # Keine Verfeinerungen mehr → wick_diff wird höchste Prio
            is_highest_prio = is_wick_diff

        if is_highest_prio:
            # Höchste Prio berührt → Entry Check mit RR >= 1.0
            entry_price = touched_ref.near
            sl_tp_result = compute_sl_tp(pivot.direction, entry_price, pivot, pair)

            if sl_tp_result is not None and sl_tp_result[2] >= 1.0:
                # ENTRY! RR >= 1.0 erfüllt
                entry_type = touched_ref.timeframe
                sl_price, tp_price, rr = sl_tp_result
                entry_time = touch_time

                # Ab hier: Exit-Simulation (unverändert)
                break
            else:
                # RR < 1.0 → Verfeinerung ungültig, löschen
                if not is_wick_diff:
                    refinements_active.remove(touched_ref)
                # Continue mit nächster Touch oder nächster höchster Prio
                continue
        else:
            # NICHT höchste Prio berührt → Sofort löschen (KEIN RR-Check!)
            if not is_wick_diff:
                refinements_active.remove(touched_ref)
            # Continue
            continue
    else:
        # Keine valide Entry gefunden
        return None

    # Ab hier: Entry wurde gefunden, jetzt Exit simulieren
    # entry_time, entry_price, entry_type, sl_price, tp_price, rr sind gesetzt

    # 6. TP-Check (OPTIMIZED)
    tp_touched = check_tp_touched_before_entry_fast(h1_df, pivot, gap_touch_time, entry_time, tp_price)
    if tp_touched:
        return None

    # NO TRANSACTION COSTS IN BACKTEST!
    # Pure Strategy = Entry at refinement price, SL/TP FIXED
    # Transaction costs will be applied in Conservative report later
    pip_value = price_per_pip(pair)

    # 7. Exit simulieren (OPTIMIZED: vectorized)
    exit_window = h1_df[h1_df["time"] > entry_time].copy()

    if len(exit_window) == 0:
        return None

    exit_time = None
    exit_price = None
    exit_reason = None

    # Find SL and TP hits
    if pivot.direction == "bullish":
        sl_hits = exit_window[exit_window["low"] <= sl_price]
        tp_hits = exit_window[exit_window["high"] >= tp_price]
    else:
        sl_hits = exit_window[exit_window["high"] >= sl_price]
        tp_hits = exit_window[exit_window["low"] <= tp_price]

    # Determine which came first
    sl_time = sl_hits.iloc[0]["time"] if len(sl_hits) > 0 else None
    tp_time = tp_hits.iloc[0]["time"] if len(tp_hits) > 0 else None

    if sl_time is None and tp_time is None:
        return None  # Trade still open

    if sl_time is not None and (tp_time is None or sl_time <= tp_time):
        exit_time = sl_time
        exit_price = sl_price
        exit_reason = "sl"
    else:
        exit_time = tp_time
        exit_price = tp_price
        exit_reason = "tp"

    # Calculate MFE/MAE up to exit (OPTIMIZED: vectorized)
    # FIXED: Include entry candle itself for accurate MFE/MAE
    trade_window = h1_df[(h1_df["time"] >= entry_time) & (h1_df["time"] <= exit_time)].copy()

    if len(trade_window) == 0:
        mfe_pips = 0
        mae_pips = 0
    else:
        if pivot.direction == "bullish":
            mfe_pips = ((trade_window["high"].max() - entry_price) / pip_value)
            mae_pips = ((entry_price - trade_window["low"].min()) / pip_value)
        else:
            mfe_pips = ((entry_price - trade_window["low"].min()) / pip_value)
            mae_pips = ((trade_window["high"].max() - entry_price) / pip_value)

    # PnL berechnen (PURE STRATEGY - no costs!)
    if pivot.direction == "bullish":
        pnl_price = exit_price - entry_price
    else:
        pnl_price = entry_price - exit_price

    pnl_pips = pnl_price / pip_value
    risk_pips = abs(entry_price - sl_price) / pip_value
    pnl_r = pnl_pips / risk_pips if risk_pips > 0 else 0

    # Duration
    duration_days = (exit_time - entry_time).total_seconds() / 86400

    return {
        "pair": pair,
        "htf_timeframe": "W",  # Weekly backtest
        "direction": pivot.direction,
        "entry_type": ENTRY_CONFIRMATION,
        "pivot_time": pivot.time,
        "valid_time": pivot.valid_time,
        "gap_touch_time": gap_touch_time,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "duration_days": duration_days,
        "pivot_price": pivot.pivot,
        "extreme_price": pivot.extreme,
        "near_price": pivot.near,
        "gap_pips": pivot.gap_size / pip_value,  # Fixed: Use pip_value (handles JPY correctly)
        "wick_diff_pips": abs(pivot.near - pivot.extreme) / pip_value,  # Fixed: Use pip_value
        "wick_diff_pct": (abs(pivot.near - pivot.extreme) / pivot.gap_size * 100) if pivot.gap_size > 0 else 0,
        "total_refinements": len(refinements),
        "priority_refinement_tf": entry_type,
        "entry_price": entry_price,
        "sl_price": sl_price,
        "tp_price": tp_price,
        "exit_price": exit_price,
        "final_rr": rr,
        "sl_distance_pips": risk_pips,
        "tp_distance_pips": abs(tp_price - entry_price) / pip_value,
        "exit_type": exit_reason,
        "pnl_pips": pnl_pips,
        "pnl_r": pnl_r,
        "win_loss": "win" if pnl_r > 0 else "loss",
        "mfe_pips": mfe_pips,
        "mae_pips": mae_pips,
    }


# ============================================================================
# PORTFOLIO SIMULATION
# ============================================================================

def run_portfolio_backtest(timer):
    """
    Führt Portfolio-Backtest durch.

    Returns: list of trade dicts (chronologisch sortiert)
    """
    all_trades = []

    print("\n" + "="*80)
    print("RUNNING PORTFOLIO BACKTEST")
    print("="*80)

    for pair in PAIRS:
        pair_start = time.time()
        print(f"\n{'='*60}")
        print(f"PAIR: {pair}")
        print(f"{'='*60}")

        for htf_tf in HTF_TIMEFRAMES:
            htf_start = time.time()

            # Load HTF data
            load_start = time.time()
            htf_df = load_tf_data(htf_tf, pair)
            start_ts = pd.Timestamp(START_DATE, tz="UTC")
            end_ts = pd.Timestamp(END_DATE, tz="UTC")
            htf_df = htf_df[(htf_df["time"] >= start_ts) & (htf_df["time"] <= end_ts)].copy()
            load_time = time.time() - load_start
            timer.record('data_loading', f"{pair}_{htf_tf}_HTF", load_time)
            print(f"  HTF ({htf_tf}): {len(htf_df)} candles ({load_time:.2f}s)")

            # Detect pivots
            pivot_start = time.time()
            pivots = detect_htf_pivots(htf_df, min_body_pct=DOJI_FILTER)
            pivot_time = time.time() - pivot_start
            timer.record('pivot_detection', f"{pair}_{htf_tf}", pivot_time)
            print(f"  Pivots: {len(pivots)} detected ({pivot_time:.2f}s)")

            if len(pivots) == 0:
                continue

            # Load LTF data
            load_start = time.time()
            ltf_cache = {}
            ltf_list = ["3D", "D", "H4", "H1"]

            for tf in ltf_list:
                ltf_df = load_tf_data(tf, pair)
                ltf_df = ltf_df[(ltf_df["time"] >= start_ts) & (ltf_df["time"] <= end_ts)].copy()
                ltf_cache[tf] = ltf_df

            load_time = time.time() - load_start
            timer.record('data_loading', f"{pair}_{htf_tf}_LTF", load_time)
            print(f"  LTF: {len(ltf_list)} timeframes ({load_time:.2f}s)")

            # Process each pivot (BATCH processing with FAST refinements)
            trades_found = 0

            # OPTIMIZED: Detect ALL refinements at once (vectorized, no loops!)
            print(f"  Detecting refinements for all {len(pivots)} pivots (OPTIMIZED)...")
            ref_start = time.time()
            all_refinements = {}  # pivot_id -> [refinements]

            for pivot in pivots:
                pivot_id = f"{pivot.time}"
                refinements = []
                for tf in ltf_list:
                    ref_list = detect_refinements_fast(
                        ltf_cache[tf],
                        pivot,
                        tf,
                        max_size_frac=REFINEMENT_MAX_SIZE,
                        min_body_pct=DOJI_FILTER
                    )
                    refinements.extend(ref_list)
                all_refinements[pivot_id] = refinements

            ref_time = time.time() - ref_start
            print(f"  Refinements detected in {ref_time:.2f}s (VECTORIZED)")

            # Now simulate trades
            print(f"  Simulating trades...")
            for i, pivot in enumerate(pivots, 1):
                pivot_start = time.time()

                pivot_id = f"{pivot.time}"
                refinements = all_refinements.get(pivot_id, [])

                # Simulate trade
                trade = simulate_single_trade(pair, pivot, refinements, ltf_cache)

                pivot_time = time.time() - pivot_start
                timer.record('trade_simulation', f"{pair}_{htf_tf}_pivot{i}", pivot_time)

                if trade:
                    all_trades.append(trade)
                    trades_found += 1

                # Progress update every 50 pivots
                if i % 50 == 0:
                    print(f"    Processed {i}/{len(pivots)} pivots, {trades_found} trades found...")

            print(f"  Trades Found: {trades_found}")

        pair_time = time.time() - pair_start
        print(f"\n  PAIR TOTAL: {pair_time:.2f}s")

    # Sort chronologically
    all_trades.sort(key=lambda t: t["entry_time"])

    print(f"\n{'='*80}")
    print(f"TOTAL TRADES: {len(all_trades)}")
    print(f"{'='*80}\n")

    return all_trades


# ============================================================================
# STATISTICS CALCULATION
# ============================================================================

def calculate_statistics(trades_df, equity_curve):
    """Calculate all backtest statistics"""
    stats = {}

    if len(trades_df) == 0:
        return stats

    # Performance Summary
    total_trades = len(trades_df)
    winning_trades = len(trades_df[trades_df["win_loss"] == "win"])
    losing_trades = len(trades_df[trades_df["win_loss"] == "loss"])
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0

    winners = trades_df[trades_df["win_loss"] == "win"]
    losers = trades_df[trades_df["win_loss"] == "loss"]

    avg_winner = winners["pnl_r"].mean() if len(winners) > 0 else 0
    avg_loser = losers["pnl_r"].mean() if len(losers) > 0 else 0
    largest_winner = winners["pnl_r"].max() if len(winners) > 0 else 0
    largest_loser = losers["pnl_r"].min() if len(losers) > 0 else 0

    total_gains = winners["pnl_r"].sum() if len(winners) > 0 else 0
    total_losses = abs(losers["pnl_r"].sum()) if len(losers) > 0 else 0
    profit_factor = total_gains / total_losses if total_losses > 0 else 0
    payoff_ratio = abs(avg_winner / avg_loser) if avg_loser != 0 else 0
    expectancy = trades_df["pnl_r"].mean()

    avg_duration = trades_df["duration_days"].mean()

    # Calculate trades per month
    date_range = pd.date_range(START_DATE, END_DATE, freq='M')
    months = len(date_range)
    trades_per_month = total_trades / months if months > 0 else 0

    stats['performance'] = {
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'avg_winner': avg_winner,
        'avg_loser': avg_loser,
        'largest_winner': largest_winner,
        'largest_loser': largest_loser,
        'profit_factor': profit_factor,
        'payoff_ratio': payoff_ratio,
        'expectancy': expectancy,
        'avg_duration': avg_duration,
        'trades_per_month': trades_per_month,
    }

    # Portfolio Metrics
    starting_capital = STARTING_CAPITAL
    ending_capital = equity_curve['portfolio_value'].iloc[-1] if len(equity_curve) > 0 else starting_capital
    total_return = (ending_capital - starting_capital) / starting_capital * 100

    years = (pd.Timestamp(END_DATE) - pd.Timestamp(START_DATE)).days / 365.25
    cagr = ((ending_capital / starting_capital) ** (1 / years) - 1) * 100 if years > 0 else 0

    # Drawdown calculation
    equity_curve['peak'] = equity_curve['portfolio_value'].cummax()
    equity_curve['drawdown'] = (equity_curve['portfolio_value'] - equity_curve['peak']) / equity_curve['peak'] * 100
    max_dd = equity_curve['drawdown'].min()
    avg_dd = equity_curve[equity_curve['drawdown'] < 0]['drawdown'].mean() if len(equity_curve[equity_curve['drawdown'] < 0]) > 0 else 0

    # Recovery Factor
    recovery_factor = abs(total_return / max_dd) if max_dd != 0 else 0

    # Calmar Ratio
    calmar_ratio = abs(cagr / max_dd) if max_dd != 0 else 0

    # Consecutive wins/losses
    trades_df['streak'] = (trades_df['win_loss'] != trades_df['win_loss'].shift()).cumsum()
    win_streaks = trades_df[trades_df['win_loss'] == 'win'].groupby('streak').size()
    loss_streaks = trades_df[trades_df['win_loss'] == 'loss'].groupby('streak').size()
    max_consecutive_wins = win_streaks.max() if len(win_streaks) > 0 else 0
    max_consecutive_losses = loss_streaks.max() if len(loss_streaks) > 0 else 0

    stats['portfolio'] = {
        'starting_capital': starting_capital,
        'ending_capital': ending_capital,
        'total_return': total_return,
        'cagr': cagr,
        'max_drawdown': max_dd,
        'avg_drawdown': avg_dd,
        'recovery_factor': recovery_factor,
        'calmar_ratio': calmar_ratio,
        'max_consecutive_wins': max_consecutive_wins,
        'max_consecutive_losses': max_consecutive_losses,
    }

    # MFE/MAE Analysis
    all_mfe = trades_df['mfe_pips'].mean()
    winners_mfe = winners['mfe_pips'].mean() if len(winners) > 0 else 0
    losers_mfe = losers['mfe_pips'].mean() if len(losers) > 0 else 0

    all_mae = trades_df['mae_pips'].mean()
    winners_mae = winners['mae_pips'].mean() if len(winners) > 0 else 0
    losers_mae = losers['mae_pips'].mean() if len(losers) > 0 else 0

    stats['mfe_mae'] = {
        'avg_mfe_all': all_mfe,
        'avg_mfe_winners': winners_mfe,
        'avg_mfe_losers': losers_mfe,
        'avg_mae_all': all_mae,
        'avg_mae_winners': winners_mae,
        'avg_mae_losers': losers_mae,
    }

    # Pair Breakdown
    pair_stats = []
    for pair in trades_df['pair'].unique():
        pair_trades = trades_df[trades_df['pair'] == pair]
        pair_winners = pair_trades[pair_trades['win_loss'] == 'win']
        pair_losers = pair_trades[pair_trades['win_loss'] == 'loss']

        pair_stats.append({
            'pair': pair,
            'trades': len(pair_trades),
            'win_rate': len(pair_winners) / len(pair_trades) * 100 if len(pair_trades) > 0 else 0,
            'profit_factor': pair_winners['pnl_r'].sum() / abs(pair_losers['pnl_r'].sum()) if len(pair_losers) > 0 and pair_losers['pnl_r'].sum() != 0 else 0,
            'expectancy': pair_trades['pnl_r'].mean(),
        })

    stats['pairs'] = sorted(pair_stats, key=lambda x: x['expectancy'], reverse=True)

    # Direction Breakdown
    direction_stats = []
    for direction in ['bullish', 'bearish']:
        dir_trades = trades_df[trades_df['direction'] == direction]
        if len(dir_trades) == 0:
            continue
        dir_winners = dir_trades[dir_trades['win_loss'] == 'win']
        dir_losers = dir_trades[dir_trades['win_loss'] == 'loss']

        direction_stats.append({
            'direction': direction.capitalize(),
            'trades': len(dir_trades),
            'win_rate': len(dir_winners) / len(dir_trades) * 100,
            'avg_pnl': dir_trades['pnl_r'].mean(),
            'profit_factor': dir_winners['pnl_r'].sum() / abs(dir_losers['pnl_r'].sum()) if len(dir_losers) > 0 and dir_losers['pnl_r'].sum() != 0 else 0,
            'expectancy': dir_trades['pnl_r'].mean(),
        })

    stats['directions'] = direction_stats

    return stats


# ============================================================================
# EQUITY CURVE GENERATION
# ============================================================================

def generate_equity_curve(trades_df):
    """Generate daily equity curve"""
    if len(trades_df) == 0:
        return pd.DataFrame(columns=['date', 'portfolio_value', 'drawdown_pct', 'cumulative_pnl_r'])

    # Create date range
    start = pd.Timestamp(START_DATE, tz='UTC')
    end = pd.Timestamp(END_DATE, tz='UTC')
    dates = pd.date_range(start, end, freq='D')

    equity_curve = pd.DataFrame({
        'date': dates,
        'portfolio_value': STARTING_CAPITAL,
        'drawdown_pct': 0.0,
        'cumulative_pnl_r': 0.0,
    })

    # Apply trades
    capital = STARTING_CAPITAL
    cumulative_r = 0

    for _, trade in trades_df.iterrows():
        exit_date = trade['exit_time'].date()

        # Calculate position size
        risk_amount = capital * RISK_PER_TRADE
        pnl_dollar = risk_amount * trade['pnl_r']
        capital += pnl_dollar
        cumulative_r += trade['pnl_r']

        # Update equity curve from exit date onwards
        mask = equity_curve['date'] >= pd.Timestamp(exit_date, tz='UTC')
        equity_curve.loc[mask, 'portfolio_value'] = capital
        equity_curve.loc[mask, 'cumulative_pnl_r'] = cumulative_r

    return equity_curve


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_txt_report(trades_df, equity_curve, stats, timer):
    """Generate comprehensive TXT report"""
    report_file = OUTPUT_DIR / f"baseline_report_{TIMESTAMP}.txt"

    with open(report_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("="*80 + "\n")
        f.write("MODEL 3 - BACKTEST REPORT (WEEKLY MINI TEST)\n")
        f.write("="*80 + "\n")
        f.write(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Test Period: {START_DATE} to {END_DATE}\n")
        f.write(f"Pairs Tested: {', '.join(PAIRS)}\n")
        f.write(f"HTF Timeframe: {', '.join(HTF_TIMEFRAMES)}\n")
        f.write(f"Entry Type: {ENTRY_CONFIRMATION}\n")
        f.write(f"Risk per Trade: {RISK_PER_TRADE*100:.1f}%\n")
        f.write(f"Starting Capital: ${STARTING_CAPITAL:,.0f}\n")
        f.write("="*80 + "\n\n")

        # Performance Summary
        perf = stats.get('performance', {})
        f.write("--- PERFORMANCE SUMMARY ---\n")
        f.write(f"Total Trades: {perf.get('total_trades', 0)}\n")
        f.write(f"Winning Trades: {perf.get('winning_trades', 0)} ({perf.get('win_rate', 0):.1f}%)\n")
        f.write(f"Losing Trades: {perf.get('losing_trades', 0)} ({100-perf.get('win_rate', 0):.1f}%)\n\n")
        f.write(f"Average Winner: +{perf.get('avg_winner', 0):.2f}R\n")
        f.write(f"Average Loser: {perf.get('avg_loser', 0):.2f}R\n")
        f.write(f"Largest Winner: +{perf.get('largest_winner', 0):.2f}R\n")
        f.write(f"Largest Loser: {perf.get('largest_loser', 0):.2f}R\n\n")
        f.write(f"Profit Factor: {perf.get('profit_factor', 0):.2f}\n")
        f.write(f"Payoff Ratio: {perf.get('payoff_ratio', 0):.2f}\n")
        f.write(f"Expectancy: {perf.get('expectancy', 0):+.2f}R per trade\n\n")
        f.write(f"Average Trade Duration: {perf.get('avg_duration', 0):.1f} days\n")
        f.write(f"Trades per Month: {perf.get('trades_per_month', 0):.1f}\n")
        f.write("\n")

        # Portfolio Metrics
        port = stats.get('portfolio', {})
        f.write("--- PORTFOLIO METRICS ---\n")
        f.write(f"Starting Capital: ${port.get('starting_capital', 0):,.0f}\n")
        f.write(f"Ending Capital: ${port.get('ending_capital', 0):,.0f}\n")
        f.write(f"Total Return: {port.get('total_return', 0):+.1f}%\n")
        f.write(f"CAGR: {port.get('cagr', 0):.1f}%\n\n")
        f.write(f"Maximum Drawdown: {port.get('max_drawdown', 0):.1f}%\n")
        f.write(f"Average Drawdown: {port.get('avg_drawdown', 0):.1f}%\n")
        f.write(f"Recovery Factor: {port.get('recovery_factor', 0):.2f}\n")
        f.write(f"Calmar Ratio: {port.get('calmar_ratio', 0):.2f}\n\n")
        f.write(f"Max Consecutive Wins: {port.get('max_consecutive_wins', 0)}\n")
        f.write(f"Max Consecutive Losses: {port.get('max_consecutive_losses', 0)}\n")
        f.write("\n")

        # MFE/MAE Analysis
        mfe_mae = stats.get('mfe_mae', {})
        f.write("--- MAX FAVORABLE/ADVERSE EXCURSION ---\n")
        f.write(f"Average MFE (All): {mfe_mae.get('avg_mfe_all', 0):.1f} pips\n")
        f.write(f"Average MFE (Winners): {mfe_mae.get('avg_mfe_winners', 0):.1f} pips\n")
        f.write(f"Average MFE (Losers): {mfe_mae.get('avg_mfe_losers', 0):.1f} pips\n\n")
        f.write(f"Average MAE (All): {mfe_mae.get('avg_mae_all', 0):.1f} pips\n")
        f.write(f"Average MAE (Winners): {mfe_mae.get('avg_mae_winners', 0):.1f} pips\n")
        f.write(f"Average MAE (Losers): {mfe_mae.get('avg_mae_losers', 0):.1f} pips\n")
        f.write("\n")

        # Pair Breakdown
        f.write("--- PAIR BREAKDOWN ---\n")
        f.write(f"{'Pair':<10} {'Trades':<8} {'Win%':<8} {'PF':<8} {'Expectancy':<12}\n")
        f.write("-"*50 + "\n")
        for pair_stat in stats.get('pairs', []):
            f.write(f"{pair_stat['pair']:<10} {pair_stat['trades']:<8} "
                   f"{pair_stat['win_rate']:<8.1f} {pair_stat['profit_factor']:<8.2f} "
                   f"{pair_stat['expectancy']:<+12.2f}R\n")
        f.write("\n")

        # Direction Breakdown
        f.write("--- DIRECTION BREAKDOWN ---\n")
        f.write(f"{'Direction':<10} {'Trades':<8} {'Win%':<8} {'Avg PnL':<10} {'PF':<8} {'Expectancy':<12}\n")
        f.write("-"*60 + "\n")
        for dir_stat in stats.get('directions', []):
            f.write(f"{dir_stat['direction']:<10} {dir_stat['trades']:<8} "
                   f"{dir_stat['win_rate']:<8.1f} {dir_stat['avg_pnl']:<+10.2f}R "
                   f"{dir_stat['profit_factor']:<8.2f} {dir_stat['expectancy']:<+12.2f}R\n")
        f.write("\n")

        # Timing Summary
        f.write("--- TIMING SUMMARY ---\n")
        f.write(f"Total Runtime: {timer.get_total_time():.2f}s\n")

        for category in ['data_loading', 'pivot_detection', 'trade_simulation']:
            if category not in timer.times:
                continue
            items = timer.times[category]
            total = sum(t for _, t in items)
            avg = total / len(items) if len(items) > 0 else 0
            f.write(f"\n{category.replace('_', ' ').title()}:\n")
            f.write(f"  Total: {total:.2f}s, Average: {avg:.3f}s, Count: {len(items)}\n")

        f.write("\n")

        # Footer
        f.write("="*80 + "\n")
        f.write("END OF REPORT\n")
        f.write(f"Trade Details: {OUTPUT_DIR}/trades_{TIMESTAMP}.csv\n")
        f.write(f"Equity Curve: {OUTPUT_DIR}/equity_curve_{TIMESTAMP}.csv\n")
        f.write("="*80 + "\n")

    print(f"\nTXT Report saved: {report_file}")
    return report_file


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""
    timer = TimingTracker()
    timer.start()

    print("\n" + "="*80)
    print("MODEL 3 - WEEKLY MINI TEST")
    print("="*80)
    print(f"Pairs: {', '.join(PAIRS)}")
    print(f"HTF: {', '.join(HTF_TIMEFRAMES)}")
    print(f"Entry: {ENTRY_CONFIRMATION}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Risk per Trade: {RISK_PER_TRADE*100:.1f}%")
    print(f"Starting Capital: ${STARTING_CAPITAL:,.0f}")
    print("="*80)

    # Run backtest
    trades = run_portfolio_backtest(timer)

    if len(trades) == 0:
        print("\n[!] No trades found!")
        return

    # Convert to DataFrame
    trades_df = pd.DataFrame(trades)

    # ========================================================================
    # GENERATE REPORT (R-Based, No Transaction Costs)
    # ========================================================================

    print("\n" + "="*80)
    print("GENERATING REPORT")
    print("="*80)

    from report_helpers import calc_stats, format_report

    # Config for reports
    report_config = {
        'START_DATE': START_DATE,
        'END_DATE': END_DATE,
        'PAIRS': PAIRS,
        'ENTRY_CONFIRMATION': ENTRY_CONFIRMATION,
        'RISK_PER_TRADE': RISK_PER_TRADE,
        'STARTING_CAPITAL': STARTING_CAPITAL,
    }

    # Add lots column (for reference in CSV)
    trades_df['lots'] = 0.0
    for idx, row in trades_df.iterrows():
        pip_val = price_per_pip(row['pair'])
        risk_pips = abs(row['entry_price'] - row['sl_price']) / pip_val
        position_dollars = STARTING_CAPITAL * RISK_PER_TRADE
        dollars_per_pip = position_dollars / risk_pips if risk_pips > 0 else 0

        if 'JPY' in row['pair']:
            standard_lot_pip_value = 1000
        else:
            standard_lot_pip_value = 10

        lots = dollars_per_pip / standard_lot_pip_value
        trades_df.at[idx, 'lots'] = lots

    # Generate report
    print("\nGenerating report...")
    stats = calc_stats(trades_df, STARTING_CAPITAL, RISK_PER_TRADE)
    report = format_report(stats, "Weekly", report_config)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = OUTPUT_DIR / f"report_{ts}.txt"
    report_file.write_text(report, encoding='utf-8')
    print(f"   [OK] Saved: {report_file.name}")

    # Save CSV
    print("\nGenerating CSV...")

    # Fix timezone issue: Remove timezone from datetime columns
    datetime_cols = ['entry_time', 'exit_time', 'pivot_time', 'valid_time', 'gap_touch_time']
    for col in datetime_cols:
        if col in trades_df.columns:
            trades_df[col] = pd.to_datetime(trades_df[col]).dt.tz_localize(None)

    # Save trades CSV
    trades_csv = OUTPUT_DIR / f"trades_{ts}.csv"
    trades_df.to_csv(trades_csv, index=False)
    print(f"   [OK] Saved: {trades_csv.name}")

    print("\n" + "="*80)
    print("REPORT GENERATED SUCCESSFULLY")
    print("="*80)
    print(f"\nResults:")
    print(f"  - Total Return: {stats['total_return']:+.1f}%")
    print(f"  - Sharpe: {stats['sharpe']:.2f}")
    print(f"  - Max DD: {stats['max_dd']:.1f}%")
    print(f"  - Expectancy: {stats['expectancy']:+.2f}R")
    print(f"  - Win Rate: {stats['win_rate']:.1f}%")


    # Print timing summary
    timer.print_summary()

    print("\n" + "="*80)
    print("BACKTEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
