"""
Entry Confirmation Optimization
--------------------------------

Tests 5 Entry Confirmation methods:
1. direct_touch (baseline - current default)
2. 1h_close_at_close (entry AT 1H close price when close is beyond entry)
3. 1h_close_at_near (entry when near touched AFTER good 1H close)
4. 4h_close_at_close (entry AT 4H close price when close is beyond entry)
5. 4h_close_at_near (entry when near touched AFTER good 4H close)

Key Logic Changes:
- direct_touch: Entry immediately when price touches entry level (current)
- 1h_close_at_close: Entry AT close price when 1H close is beyond entry
  - If 1H close moves back into gap → refinement gets deleted
  - Entry price = close price (not near!)
  - RR check at close price
- 1h_close_at_near: Entry when near touched AFTER 1H close confirms
  - If 1H close moves back into gap → refinement gets deleted
  - If 1H close is good → wait for near touch again
  - Entry price = near (original)
  - RR check at near price
- 4h_close_at_close: Entry AT close price when 4H close is beyond entry
- 4h_close_at_near: Entry when near touched AFTER 4H close confirms

Expected Results:
- direct_touch: Most trades, more fakeouts
- 1h_close_at_close: Fewer trades, worse RR (entry further from near)
- 1h_close_at_near: Fewer trades, best RR (entry at near after confirmation)
- 4h_close_at_close: Fewest trades, worst RR
- 4h_close_at_near: Fewest trades, best quality

Output:
- 5 reports per HTF timeframe (W, 3D, M)
- 15 CSV files total in results/Entry_Confirmation/Trades/
- Summary comparison report

Walk-Forward: YES (critical rule!)
"""

import sys
from pathlib import Path
import time
from datetime import datetime
import pandas as pd
import numpy as np
from collections import defaultdict
from multiprocessing import Pool, cpu_count

# Go up to "05_Model 3" directory
BASE_DIR = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(BASE_DIR))

from scripts.backtesting.backtest_model3 import (
    load_tf_data,
    detect_htf_pivots,
    compute_sl_tp,
    price_per_pip,
    should_use_wick_diff_entry,
)

# Import Phase 2 helpers for report generation
phase2_scripts = BASE_DIR / "Backtest" / "02_technical" / "01_Single_TF" / "scripts"
sys.path.insert(0, str(phase2_scripts))

from report_helpers import calc_stats

# ============================================================================
# CONFIGURATION
# ============================================================================

TIMEFRAMES = ["W", "3D", "M"]
ENTRY_TYPES = ["direct_touch", "1h_close_at_close", "1h_close_at_near", "4h_close_at_close", "4h_close_at_near"]

PAIRS = [
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
    "CADCHF", "CADJPY", "CHFJPY",
    "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
    "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
    "USDCAD", "USDCHF", "USDJPY"
]

START_DATE = "2005-01-01"
END_DATE = "2025-12-31"

# Risk Settings
STARTING_CAPITAL = 100000  # $100k
RISK_PER_TRADE = 0.01  # 1% per trade

# Strategy Settings (default from Phase 2)
DOJI_FILTER = 5.0  # Min body % for pivots
REFINEMENT_MAX_SIZE = 0.20  # Max 20% of HTF gap

# Output
OUTPUT_DIR = BASE_DIR / "Backtest" / "03_optimization" / "01_Single_TF" / "02_Entry_Confirmation"
TRADES_DIR = OUTPUT_DIR / "Trades"

# Create directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TRADES_DIR.mkdir(parents=True, exist_ok=True)

# Global cache
DATA_CACHE = {}

def init_worker(shared_cache):
    """Initialize worker process with shared cache"""
    global DATA_CACHE
    DATA_CACHE = shared_cache

# ============================================================================
# HELPER FUNCTIONS (copied from backtest_all.py with optimizations)
# ============================================================================

def body_pct_vectorized(df):
    """Calculate body percentage for all candles (vectorized)"""
    rng = df["high"] - df["low"]
    body = abs(df["close"] - df["open"])
    return (body / rng * 100).fillna(0)


def detect_refinements_fast(df, htf_pivot, timeframe, max_size_frac=0.2, min_body_pct=5.0):
    """OPTIMIZED: Vectorized refinement detection"""
    from scripts.backtesting.backtest_model3 import Refinement

    df_window = df[(df["time"] >= htf_pivot.k1_time) & (df["time"] < htf_pivot.valid_time)].copy()

    if len(df_window) < 2:
        return []

    df_window['body_pct'] = body_pct_vectorized(df_window)

    df_k1 = df_window.iloc[:-1].reset_index(drop=True)
    df_k2 = df_window.iloc[1:].reset_index(drop=True)

    valid_body = (df_k1['body_pct'].values >= min_body_pct) & (df_k2['body_pct'].values >= min_body_pct)

    k1_red = (df_k1['close'].values < df_k1['open'].values)
    k1_green = (df_k1['close'].values > df_k1['open'].values)
    k2_green = (df_k2['close'].values > df_k2['open'].values)
    k2_red = (df_k2['close'].values < df_k2['open'].values)

    is_bullish = k1_red & k2_green
    is_bearish = k1_green & k2_red

    if htf_pivot.direction == "bullish":
        valid_direction = is_bullish
        direction = "bullish"
    else:
        valid_direction = is_bearish
        direction = "bearish"

    valid_mask = valid_body & valid_direction

    if not valid_mask.any():
        return []

    df_k1_valid = df_k1[valid_mask].reset_index(drop=True)
    df_k2_valid = df_k2[valid_mask].reset_index(drop=True)

    if direction == "bullish":
        extremes = np.minimum(df_k1_valid['low'].values, df_k2_valid['low'].values)
        nears = np.maximum(df_k1_valid['low'].values, df_k2_valid['low'].values)
        extremes = np.maximum(extremes, htf_pivot.extreme)
    else:
        extremes = np.maximum(df_k1_valid['high'].values, df_k2_valid['high'].values)
        nears = np.minimum(df_k1_valid['high'].values, df_k2_valid['high'].values)
        extremes = np.minimum(extremes, htf_pivot.extreme)

    pivot_levels = df_k2_valid['open'].values
    sizes = np.abs(extremes - nears)

    max_size = htf_pivot.gap_size * max_size_frac
    valid_size = (sizes > 0) & (sizes <= max_size)

    if not valid_size.any():
        return []

    df_k2_final = df_k2_valid[valid_size].reset_index(drop=True)
    extremes_final = extremes[valid_size]
    nears_final = nears[valid_size]
    pivot_levels_final = pivot_levels[valid_size]
    sizes_final = sizes[valid_size]

    if direction == "bullish":
        wick_low = htf_pivot.extreme
        wick_high = htf_pivot.near
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

    df_k2_result = df_k2_final[valid_position].reset_index(drop=True)
    extremes_result = extremes_final[valid_position]
    nears_result = nears_final[valid_position]
    pivot_levels_result = pivot_levels_final[valid_position]
    sizes_result = sizes_final[valid_position]

    refinements = []
    for i in range(len(df_k2_result)):
        refinement_created = df_k2_result.iloc[i]['time']
        near_level = nears_result[i]

        touch_window = df_window[
            (df_window["time"] > refinement_created) &
            (df_window["time"] <= htf_pivot.valid_time)
        ]

        if len(touch_window) == 0:
            was_touched = False
        else:
            if direction == "bullish":
                was_touched = (touch_window["low"] <= near_level).any()
            else:
                was_touched = (touch_window["high"] >= near_level).any()

        if was_touched:
            continue

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
    """Vectorized version of gap touch detection on Daily"""
    df_after = df_daily[df_daily["time"] >= start_time].copy()

    if len(df_after) == 0:
        return None

    gap_low = min(pivot.pivot, pivot.extreme)
    gap_high = max(pivot.pivot, pivot.extreme)

    if pivot.direction == "bullish":
        mask = (df_after["low"] <= gap_high) & (df_after["high"] >= gap_low)
    else:
        mask = (df_after["high"] >= gap_low) & (df_after["low"] <= gap_high)

    hits = df_after[mask]
    return hits.iloc[0]["time"] if len(hits) > 0 else None


def find_gap_touch_on_h1_fast(df_h1, pivot, daily_gap_touch_time):
    """Find exact H1 candle that touches gap"""
    if daily_gap_touch_time is None:
        return None

    df_after = df_h1[df_h1["time"] >= daily_gap_touch_time].copy()
    if len(df_after) == 0:
        return None

    gap_low = min(pivot.pivot, pivot.extreme)
    gap_high = max(pivot.pivot, pivot.extreme)

    if pivot.direction == "bullish":
        mask = (df_after["low"] <= gap_high) & (df_after["high"] >= gap_low)
    else:
        mask = (df_after["high"] >= gap_low) & (df_after["low"] <= gap_high)

    hits = df_after[mask]
    return hits.iloc[0]["time"] if len(hits) > 0 else None


def check_tp_touched_before_entry_fast(df, pivot, gap_touch_time, entry_time, tp):
    """Vectorized version of TP touch check"""
    df_check_window = df[(df["time"] >= gap_touch_time) & (df["time"] < entry_time)].copy()

    if len(df_check_window) == 0:
        return False

    if pivot.direction == "bullish":
        return (df_check_window["high"] >= tp).any()
    else:
        return (df_check_window["low"] <= tp).any()


# ============================================================================
# MODIFIED ENTRY CONFIRMATION LOGIC
# ============================================================================

def find_entry_with_confirmation(near_level, start_time, df_h1, df_h4, direction, entry_type):
    """
    Find entry time and entry price based on confirmation type.

    Args:
        near_level: Original entry price level (refinement near or wick_diff)
        start_time: Gap touch time
        df_h1: H1 dataframe
        df_h4: H4 dataframe (can be None for HTF=3D)
        direction: "bullish" or "bearish"
        entry_type: "direct_touch", "1h_close_at_close", "1h_close_at_near",
                    "4h_close_at_close", "4h_close_at_near"

    Returns:
        (entry_time, entry_price, was_invalidated)
        - entry_time: Timestamp of entry or None
        - entry_price: Actual entry price (can differ from near_level!)
        - was_invalidated: True if refinement was invalidated (close back in gap)
    """

    if entry_type == "direct_touch":
        # Original logic: Entry at first touch of near_level
        window = df_h1[df_h1["time"] >= start_time].copy()

        if len(window) == 0:
            return None, None, False

        if direction == "bullish":
            touch_mask = window["low"] <= near_level
        else:
            touch_mask = window["high"] >= near_level

        hits = window[touch_mask]
        if len(hits) > 0:
            return hits.iloc[0]["time"], near_level, False
        return None, None, False

    elif entry_type == "1h_close_at_close":
        # Entry AT close price when 1H close is beyond entry level
        window = df_h1[df_h1["time"] >= start_time].copy()

        if len(window) == 0:
            return None, None, False

        for idx, candle in window.iterrows():
            if direction == "bullish":
                # Check if close is above near_level (beyond, out of gap)
                if candle["close"] > near_level:
                    # Valid entry AT CLOSE PRICE
                    return candle["time"], candle["close"], False
                # Check if touched but close back in gap
                elif candle["low"] <= near_level < candle["close"]:
                    # Touched but didn't close beyond → wait
                    continue
                elif candle["close"] <= near_level and candle["low"] <= near_level:
                    # Close moved back into gap → invalidated
                    return None, None, True
            else:
                # Bearish: close must be below near_level
                if candle["close"] < near_level:
                    return candle["time"], candle["close"], False
                elif candle["high"] >= near_level > candle["close"]:
                    continue
                elif candle["close"] >= near_level and candle["high"] >= near_level:
                    return None, None, True

        return None, None, False

    elif entry_type == "1h_close_at_near":
        # Entry when near touched AFTER 1H close confirms (2-phase)
        window = df_h1[df_h1["time"] >= start_time].copy()

        if len(window) == 0:
            return None, None, False

        # Phase 1: Find confirmation candle (close beyond near_level)
        confirmation_time = None
        for idx, candle in window.iterrows():
            if direction == "bullish":
                if candle["close"] > near_level:
                    # Confirmed! Now wait for near touch
                    confirmation_time = candle["time"]
                    break
                elif candle["close"] <= near_level and candle["low"] <= near_level:
                    # Invalidated
                    return None, None, True
            else:
                if candle["close"] < near_level:
                    confirmation_time = candle["time"]
                    break
                elif candle["close"] >= near_level and candle["high"] >= near_level:
                    return None, None, True

        if confirmation_time is None:
            # Never confirmed
            return None, None, False

        # Phase 2: Find near touch AFTER confirmation
        window_after = df_h1[df_h1["time"] > confirmation_time].copy()

        if len(window_after) == 0:
            return None, None, False

        if direction == "bullish":
            touch_mask = window_after["low"] <= near_level
        else:
            touch_mask = window_after["high"] >= near_level

        hits = window_after[touch_mask]
        if len(hits) > 0:
            # Entry at near_level (original)
            return hits.iloc[0]["time"], near_level, False
        return None, None, False

    elif entry_type == "4h_close_at_close":
        # Entry AT close price when 4H close is beyond entry level
        if df_h4 is None or len(df_h4) == 0:
            return None, None, False

        window = df_h4[df_h4["time"] >= start_time].copy()

        if len(window) == 0:
            return None, None, False

        for idx, candle in window.iterrows():
            if direction == "bullish":
                if candle["close"] > near_level:
                    return candle["time"], candle["close"], False
                elif candle["low"] <= near_level < candle["close"]:
                    continue
                elif candle["close"] <= near_level and candle["low"] <= near_level:
                    return None, None, True
            else:
                if candle["close"] < near_level:
                    return candle["time"], candle["close"], False
                elif candle["high"] >= near_level > candle["close"]:
                    continue
                elif candle["close"] >= near_level and candle["high"] >= near_level:
                    return None, None, True

        return None, None, False

    elif entry_type == "4h_close_at_near":
        # Entry when near touched AFTER 4H close confirms (2-phase)
        if df_h4 is None or len(df_h4) == 0:
            return None, None, False

        window = df_h4[df_h4["time"] >= start_time].copy()

        if len(window) == 0:
            return None, None, False

        # Phase 1: Find confirmation candle
        confirmation_time = None
        for idx, candle in window.iterrows():
            if direction == "bullish":
                if candle["close"] > near_level:
                    confirmation_time = candle["time"]
                    break
                elif candle["close"] <= near_level and candle["low"] <= near_level:
                    return None, None, True
            else:
                if candle["close"] < near_level:
                    confirmation_time = candle["time"]
                    break
                elif candle["close"] >= near_level and candle["high"] >= near_level:
                    return None, None, True

        if confirmation_time is None:
            return None, None, False

        # Phase 2: Find near touch AFTER confirmation (use H1 for precision)
        window_after = df_h1[df_h1["time"] > confirmation_time].copy()

        if len(window_after) == 0:
            return None, None, False

        if direction == "bullish":
            touch_mask = window_after["low"] <= near_level
        else:
            touch_mask = window_after["high"] >= near_level

        hits = window_after[touch_mask]
        if len(hits) > 0:
            return hits.iloc[0]["time"], near_level, False
        return None, None, False

    return None, None, False


def check_tp_touched_between_confirmation_and_entry(df_h1, df_h4, pivot, near_level, gap_touch_time, entry_time, entry_type, tp_price):
    """
    For "at_near" entry types: Check if TP was touched between confirmation close and actual entry.
    This invalidates the setup (similar to TP check between gap touch and entry).

    Args:
        df_h1: H1 dataframe
        df_h4: H4 dataframe (can be None)
        pivot: HTF pivot
        near_level: Near level
        gap_touch_time: Gap touch time
        entry_time: Actual entry time (when near was touched)
        entry_type: Entry confirmation type
        tp_price: TP price

    Returns:
        True if TP was touched (setup invalid), False otherwise
    """
    if "at_near" not in entry_type:
        # Only check for "at_near" variants
        return False

    # Find the confirmation close time
    # We need to re-run the confirmation logic to find when close happened
    if "1h" in entry_type:
        window = df_h1[df_h1["time"] >= gap_touch_time].copy()
        confirmation_time = None
        for idx, candle in window.iterrows():
            if pivot.direction == "bullish":
                if candle["close"] > near_level:
                    confirmation_time = candle["time"]
                    break
            else:
                if candle["close"] < near_level:
                    confirmation_time = candle["time"]
                    break
    elif "4h" in entry_type:
        if df_h4 is None or len(df_h4) == 0:
            return False
        window = df_h4[df_h4["time"] >= gap_touch_time].copy()
        confirmation_time = None
        for idx, candle in window.iterrows():
            if pivot.direction == "bullish":
                if candle["close"] > near_level:
                    confirmation_time = candle["time"]
                    break
            else:
                if candle["close"] < near_level:
                    confirmation_time = candle["time"]
                    break
    else:
        return False

    if confirmation_time is None:
        return False

    # Check if TP was touched between confirmation_time and entry_time
    check_window = df_h1[(df_h1["time"] > confirmation_time) & (df_h1["time"] < entry_time)].copy()

    if len(check_window) == 0:
        return False

    if pivot.direction == "bullish":
        return (check_window["high"] >= tp_price).any()
    else:
        return (check_window["low"] <= tp_price).any()


def simulate_single_trade(pair, pivot, refinements, ltf_cache, htf_timeframe, entry_type):
    """
    Modified simulate_single_trade with entry confirmation logic.

    Key changes:
    - Uses find_entry_with_confirmation() instead of find_near_touch_time()
    - Handles refinement invalidation (close back in gap)
    - Checks TP between confirmation and entry for "at_near" variants
    """
    h1_df = ltf_cache["H1"]
    h4_df = ltf_cache.get("H4")  # Might be None for HTF=3D
    d_df = ltf_cache["D"]

    # 1. Gap Touch
    daily_gap_touch = find_gap_touch_on_daily_fast(d_df, pivot, pivot.valid_time)
    if daily_gap_touch is None:
        return None

    gap_touch_time = find_gap_touch_on_h1_fast(h1_df, pivot, daily_gap_touch)
    if gap_touch_time is None:
        return None

    # 2. Wick Diff Entry
    use_wick_diff, wick_diff_entry = should_use_wick_diff_entry(pivot, refinements)

    # Priority sorting
    def ref_priority(ref):
        tf_order = {"W": 0, "3D": 1, "D": 2, "H4": 3, "H1": 4}
        tf_prio = tf_order.get(ref.timeframe, 99)
        dist_to_near = abs(ref.near - pivot.near)
        return (tf_prio, dist_to_near)

    refinements_active = sorted(refinements, key=ref_priority) if refinements else []

    # 3. Find entry events WITH CONFIRMATION
    touch_events = []

    if use_wick_diff and wick_diff_entry is not None:
        wd_entry_time, wd_entry_price, wd_invalidated = find_entry_with_confirmation(
            wick_diff_entry, gap_touch_time, h1_df, h4_df, pivot.direction, entry_type
        )
        if wd_entry_time:
            class WickDiffRef:
                def __init__(self, near, entry_price, timeframe="wick_diff"):
                    self.near = near
                    self.entry_price = entry_price
                    self.timeframe = timeframe
            wd_ref = WickDiffRef(wick_diff_entry, wd_entry_price)
            touch_events.append((wd_entry_time, wd_ref, True))  # True = is_wick_diff

    # Refinements
    for ref in refinements_active[:]:  # Copy list to allow removal
        ref_entry_time, ref_entry_price, ref_invalidated = find_entry_with_confirmation(
            ref.near, gap_touch_time, h1_df, h4_df, pivot.direction, entry_type
        )

        if ref_invalidated:
            # Refinement invalidated (close back in gap) → remove
            refinements_active.remove(ref)
            continue

        if ref_entry_time:
            # Store entry price in ref object
            ref.entry_price = ref_entry_price
            touch_events.append((ref_entry_time, ref, False))

    if len(touch_events) == 0:
        return None

    # 4. Sort chronologically
    touch_events.sort(key=lambda x: x[0])

    # 5. Process first valid entry (chronological order + priority)
    for touch_time, touched_ref, is_wick_diff in touch_events:
        if len(refinements_active) == 0 and not is_wick_diff:
            return None

        if len(refinements_active) > 0:
            highest_prio_ref = refinements_active[0]
            is_highest_prio = (not is_wick_diff) and (touched_ref == highest_prio_ref)
        else:
            is_highest_prio = is_wick_diff

        if is_highest_prio:
            # Use actual entry price (can differ from near for "at_close" types!)
            entry_price = touched_ref.entry_price
            sl_tp_result = compute_sl_tp(pivot.direction, entry_price, pivot, pair)

            if sl_tp_result is not None and sl_tp_result[2] >= 1.0:
                # ENTRY! (if RR >= 1.0)
                entry_type_label = touched_ref.timeframe
                sl_price, tp_price, rr = sl_tp_result
                entry_time = touch_time

                # CRITICAL: For "at_near" variants, check if TP was touched between confirmation and entry
                # (Similar to TP check between gap touch and entry)
                if check_tp_touched_between_confirmation_and_entry(
                    h1_df, h4_df, pivot, touched_ref.near, gap_touch_time, entry_time, entry_type, tp_price
                ):
                    # TP touched between confirmation and entry → Invalid setup
                    if not is_wick_diff:
                        refinements_active.remove(touched_ref)
                    continue  # Try next refinement

                # Valid entry!
                break
            else:
                if not is_wick_diff:
                    refinements_active.remove(touched_ref)
                continue
        else:
            if not is_wick_diff:
                refinements_active.remove(touched_ref)
            continue
    else:
        return None

    # 6. TP Check
    tp_touched = check_tp_touched_before_entry_fast(h1_df, pivot, gap_touch_time, entry_time, tp_price)
    if tp_touched:
        return None

    pip_value = price_per_pip(pair)

    # 7. Exit simulation
    exit_window = h1_df[h1_df["time"] > entry_time].copy()

    if len(exit_window) == 0:
        return None

    exit_time = None
    exit_price = None
    exit_reason = None

    if pivot.direction == "bullish":
        sl_hits = exit_window[exit_window["low"] <= sl_price]
        tp_hits = exit_window[exit_window["high"] >= tp_price]
    else:
        sl_hits = exit_window[exit_window["high"] >= sl_price]
        tp_hits = exit_window[exit_window["low"] <= tp_price]

    sl_time = sl_hits.iloc[0]["time"] if len(sl_hits) > 0 else None
    tp_time = tp_hits.iloc[0]["time"] if len(tp_hits) > 0 else None

    if sl_time is None and tp_time is None:
        return None

    if sl_time is not None and (tp_time is None or sl_time <= tp_time):
        exit_time = sl_time
        exit_price = sl_price
        exit_reason = "sl"
    else:
        exit_time = tp_time
        exit_price = tp_price
        exit_reason = "tp"

    # MFE/MAE
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

    # PnL
    if pivot.direction == "bullish":
        pnl_price = exit_price - entry_price
    else:
        pnl_price = entry_price - exit_price

    pnl_pips = pnl_price / pip_value
    risk_pips = abs(entry_price - sl_price) / pip_value
    pnl_r = pnl_pips / risk_pips if risk_pips > 0 else 0

    duration_days = (exit_time - entry_time).total_seconds() / 86400

    return {
        "pair": pair,
        "htf_timeframe": htf_timeframe,
        "direction": pivot.direction,
        "entry_type": entry_type,
        "pivot_time": pivot.time,
        "valid_time": pivot.valid_time,
        "gap_touch_time": gap_touch_time,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "duration_days": duration_days,
        "pivot_price": pivot.pivot,
        "extreme_price": pivot.extreme,
        "near_price": pivot.near,
        "gap_pips": pivot.gap_size / pip_value,
        "wick_diff_pips": abs(pivot.near - pivot.extreme) / pip_value,
        "wick_diff_pct": (abs(pivot.near - pivot.extreme) / pivot.gap_size * 100) if pivot.gap_size > 0 else 0,
        "total_refinements": len(refinements),
        "priority_refinement_tf": entry_type_label,
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
# DATA LOADING
# ============================================================================

def load_parquet_file(tf):
    """Load entire parquet file (all pairs) for a timeframe"""
    base = BASE_DIR.parent.parent / "Data" / "Chartdata" / "Forex" / "Parquet"
    path = base / f"All_Pairs_{tf}_UTC.parquet"

    if not path.exists():
        raise FileNotFoundError(f"Missing data: {path}")

    df = pd.read_parquet(path)

    if isinstance(df.index, pd.MultiIndex) and set(df.index.names) >= {"pair", "time"}:
        df = df.reset_index()

    if "pair" not in df.columns and df.index.name == "pair":
        df = df.reset_index()
    if "time" not in df.columns and df.index.name == "time":
        df = df.reset_index()

    time_col = None
    for col in df.columns:
        if col.lower() in {"time", "timestamp", "date", "datetime"}:
            time_col = col
            break

    if time_col is None:
        raise KeyError(f"No time column in {path}")

    if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
        df[time_col] = pd.to_datetime(df[time_col], utc=True)
    elif df[time_col].dt.tz is None:
        df[time_col] = df[time_col].dt.tz_localize("UTC")

    df = df.rename(columns={time_col: "time"})

    for col in ["open", "high", "low", "close"]:
        if col in df.columns:
            df[col] = df[col].round(5)

    return df.sort_values("time").reset_index(drop=True)


def load_all_data_for_timeframe(htf_timeframe, pairs, start_date, end_date):
    """Pre-loads ALL data for a timeframe into RAM cache"""
    print(f"\n[DATA LOADING] Pre-loading all data for {htf_timeframe}...")

    start_ts = pd.Timestamp(start_date, tz="UTC")
    end_ts = pd.Timestamp(end_date, tz="UTC")

    all_tfs = ["M", "W", "3D", "D", "H4", "H1"]
    htf_idx = all_tfs.index(htf_timeframe)
    needed_tfs = [htf_timeframe] + all_tfs[htf_idx + 1:]

    cache = {pair: {} for pair in pairs}

    for tf in needed_tfs:
        print(f"  Loading {tf} data... ", end='', flush=True)

        df_all = load_parquet_file(tf)
        df_all = df_all[(df_all["time"] >= start_ts) & (df_all["time"] <= end_ts)].copy()

        for pair in pairs:
            df_pair = df_all[df_all["pair"] == pair].copy()
            cache[pair][tf] = df_pair

        print(f"✓ ({len(df_all)} candles, split into {len(pairs)} pairs)")

    print(f"  ✓ All data loaded into RAM cache")
    return cache


# ============================================================================
# BACKTEST EXECUTION
# ============================================================================

def process_single_pair(args):
    """Worker function for multiprocessing"""
    pair, htf_timeframe, entry_type, start_date, end_date = args

    pair_data = DATA_CACHE.get(pair, {})
    htf_df = pair_data.get(htf_timeframe)

    if htf_df is None or len(htf_df) == 0:
        return (pair, [])

    pivots = detect_htf_pivots(htf_df, min_body_pct=DOJI_FILTER)

    if len(pivots) == 0:
        return (pair, [])

    all_tfs = ["M", "W", "3D", "D", "H4", "H1"]
    htf_idx = all_tfs.index(htf_timeframe)
    ltf_list = all_tfs[htf_idx + 1:]

    ltf_cache = {tf: pair_data.get(tf) for tf in ltf_list}

    all_refinements = {}
    for pivot in pivots:
        pivot_id = f"{pivot.time}"
        refinements = []
        for tf in ltf_list:
            if ltf_cache[tf] is not None:
                ref_list = detect_refinements_fast(
                    ltf_cache[tf],
                    pivot,
                    tf,
                    max_size_frac=REFINEMENT_MAX_SIZE,
                    min_body_pct=DOJI_FILTER
                )
                refinements.extend(ref_list)
        all_refinements[pivot_id] = refinements

    pair_trades = []
    for pivot in pivots:
        pivot_id = f"{pivot.time}"
        refinements = all_refinements.get(pivot_id, [])
        trade = simulate_single_trade(pair, pivot, refinements, ltf_cache, htf_timeframe, entry_type)
        if trade:
            pair_trades.append(trade)

    return (pair, pair_trades)


def run_backtest(htf_timeframe, entry_type):
    """Run backtest for one HTF timeframe + one entry type"""
    print(f"\n{'='*80}")
    print(f"BACKTEST: {htf_timeframe} | Entry: {entry_type}")
    print(f"{'='*80}")

    cache = load_all_data_for_timeframe(htf_timeframe, PAIRS, START_DATE, END_DATE)

    pair_args = [(pair, htf_timeframe, entry_type, START_DATE, END_DATE) for pair in PAIRS]

    num_processes = cpu_count()
    print(f"\n[PROCESSING] Running backtest with {num_processes} CPU cores...")
    print(f"{'='*80}")

    all_trades = []
    completed = 0

    with Pool(processes=num_processes, initializer=init_worker, initargs=(cache,)) as pool:
        for pair, pair_trades in pool.imap_unordered(process_single_pair, pair_args, chunksize=1):
            completed += 1
            if pair_trades:
                all_trades.extend(pair_trades)
                print(f"  [{completed:2d}/{len(PAIRS)}] {pair}: {len(pair_trades)} trades")
            else:
                print(f"  [{completed:2d}/{len(PAIRS)}] {pair}: 0 trades")

    all_trades.sort(key=lambda t: (t["entry_time"], t["pair"]))

    print(f"\n{'='*80}")
    print(f"TOTAL TRADES ({htf_timeframe} | {entry_type}): {len(all_trades)}")
    print(f"{'='*80}\n")

    return all_trades


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report(htf_timeframe, entry_type, trades_df):
    """Generate report and CSV for one configuration"""
    if len(trades_df) == 0:
        print(f"\n[!] No trades for {htf_timeframe} | {entry_type} - skipping report")
        return

    print(f"\n[REPORT] Generating report for {htf_timeframe} | {entry_type}")

    # Calculate stats
    stats = calc_stats(trades_df, STARTING_CAPITAL, RISK_PER_TRADE)

    if stats is None:
        print(f"  [!] Stats calculation failed")
        return

    # Generate report text
    lines = []
    lines.append("=" * 80)
    lines.append(f"ENTRY CONFIRMATION OPTIMIZATION")
    lines.append(f"HTF: {htf_timeframe} | Entry Type: {entry_type}")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Period: {START_DATE} to {END_DATE}")
    lines.append(f"Pairs: {len(PAIRS)} pairs")
    lines.append(f"Risk per Trade: {RISK_PER_TRADE*100:.1f}%")
    lines.append("")
    lines.append("=" * 80)
    lines.append("PERFORMANCE METRICS")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total Trades:       {stats['total_trades']}")
    lines.append(f"Win Rate:           {stats['win_rate']:.1f}%")
    lines.append(f"Expectancy:         {stats['expectancy']:+.3f}R")
    lines.append(f"SQN:                {stats['sqn']:.2f}")
    lines.append(f"Profit Factor:      {stats['profit_factor']:.2f}")
    lines.append(f"Max DD:             {stats['max_dd']:+.1f}R")
    lines.append(f"Cumulative R:       {stats['cumulative_r']:+.1f}R")
    lines.append(f"Avg Duration:       {stats['avg_duration_days']:.1f} days")
    lines.append(f"Avg Concurrent:     {stats['avg_concurrent']:.1f}")
    lines.append(f"Max Concurrent:     {stats['max_concurrent']}")
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    # Save report
    report_file = OUTPUT_DIR / f"{htf_timeframe}_{entry_type}_report.txt"
    report_file.write_text("\n".join(lines), encoding='utf-8')
    print(f"  ✓ Report: {report_file.name}")

    # Save CSV
    datetime_cols = ['entry_time', 'exit_time', 'pivot_time', 'valid_time', 'gap_touch_time']
    for col in datetime_cols:
        if col in trades_df.columns:
            trades_df[col] = pd.to_datetime(trades_df[col]).dt.tz_localize(None)

    trades_csv = TRADES_DIR / f"{htf_timeframe}_{entry_type}_trades.csv"
    trades_df.to_csv(trades_csv, index=False)
    print(f"  ✓ CSV: {trades_csv.name}")

    print(f"  → Trades: {stats['total_trades']} | Exp: {stats['expectancy']:+.3f}R | WR: {stats['win_rate']:.1f}% | SQN: {stats['sqn']:.2f}")


def generate_comparison_report(all_results):
    """Generate comparison report across all configurations"""
    lines = []
    lines.append("=" * 80)
    lines.append("ENTRY CONFIRMATION OPTIMIZATION - SUMMARY")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Configurations Tested: {len(all_results)}")
    lines.append(f"HTF Timeframes: {', '.join(TIMEFRAMES)}")
    lines.append(f"Entry Types: {', '.join(ENTRY_TYPES)}")
    lines.append("")
    lines.append("=" * 80)
    lines.append("COMPARISON TABLE")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'HTF':<5} {'Entry Type':<15} {'Trades':>7} {'Exp(R)':>8} {'WR(%)':>7} {'SQN':>7} {'PF':>7} {'MaxDD':>8} {'AvgDur':>8}")
    lines.append("-" * 80)

    for result in all_results:
        htf = result['htf']
        entry = result['entry_type']
        stats = result['stats']

        if stats is not None:
            lines.append(
                f"{htf:<5} {entry:<15} {stats['total_trades']:>7} "
                f"{stats['expectancy']:>+7.3f}R {stats['win_rate']:>6.1f}% "
                f"{stats['sqn']:>6.2f} {stats['profit_factor']:>6.2f} "
                f"{stats['max_dd']:>+7.1f}R {stats['avg_duration_days']:>7.1f}d"
            )
        else:
            lines.append(f"{htf:<5} {entry:<15} {'NO DATA':>7}")

    lines.append("")
    lines.append("=" * 80)
    lines.append("INSIGHTS")
    lines.append("=" * 80)
    lines.append("")

    # Group by HTF
    for htf in TIMEFRAMES:
        lines.append(f"{htf} Timeframe:")
        htf_results = [r for r in all_results if r['htf'] == htf and r['stats'] is not None]

        if len(htf_results) == 0:
            lines.append("  No data available")
            lines.append("")
            continue

        # Sort by expectancy
        htf_results.sort(key=lambda x: x['stats']['expectancy'], reverse=True)

        best = htf_results[0]
        lines.append(f"  Best: {best['entry_type']} → Exp: {best['stats']['expectancy']:+.3f}R | WR: {best['stats']['win_rate']:.1f}%")

        # Compare to direct_touch baseline
        baseline = next((r for r in htf_results if r['entry_type'] == 'direct_touch'), None)
        if baseline and best['entry_type'] != 'direct_touch':
            exp_diff = best['stats']['expectancy'] - baseline['stats']['expectancy']
            wr_diff = best['stats']['win_rate'] - baseline['stats']['win_rate']
            trade_diff = baseline['stats']['total_trades'] - best['stats']['total_trades']
            trade_pct = (trade_diff / baseline['stats']['total_trades'] * 100) if baseline['stats']['total_trades'] > 0 else 0

            lines.append(f"  vs Baseline (direct_touch):")
            lines.append(f"    Expectancy: {exp_diff:+.3f}R")
            lines.append(f"    Win Rate: {wr_diff:+.1f}%")
            lines.append(f"    Trades Lost: {trade_diff} ({trade_pct:.1f}%)")

        lines.append("")

    lines.append("=" * 80)
    lines.append("RECOMMENDATION")
    lines.append("=" * 80)
    lines.append("")

    # Find overall best
    valid_results = [r for r in all_results if r['stats'] is not None]
    if len(valid_results) > 0:
        best_overall = max(valid_results, key=lambda x: x['stats']['expectancy'])
        lines.append(f"Best Overall Configuration:")
        lines.append(f"  HTF: {best_overall['htf']}")
        lines.append(f"  Entry Type: {best_overall['entry_type']}")
        lines.append(f"  Expectancy: {best_overall['stats']['expectancy']:+.3f}R")
        lines.append(f"  Win Rate: {best_overall['stats']['win_rate']:.1f}%")
        lines.append(f"  Trades: {best_overall['stats']['total_trades']}")
        lines.append(f"  SQN: {best_overall['stats']['sqn']:.2f}")

    lines.append("")
    lines.append("=" * 80)
    lines.append("NEXT STEPS")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Walk-Forward Validation:")
    lines.append("  Test the top 3 configurations across multiple time windows")
    lines.append("  to verify robustness and avoid overfitting.")
    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF SUMMARY")
    lines.append("=" * 80)

    summary_file = OUTPUT_DIR / "summary_comparison.txt"
    summary_file.write_text("\n".join(lines), encoding='utf-8')
    print(f"\n✓ Summary report: {summary_file.name}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution"""
    start_time = time.time()

    print("\n" + "="*80)
    print("ENTRY CONFIRMATION OPTIMIZATION")
    print("="*80)
    print(f"HTF Timeframes: {', '.join(TIMEFRAMES)}")
    print(f"\nEntry Types:")
    print(f"  1. direct_touch (baseline)")
    print(f"  2. 1h_close_at_close (entry at 1H close price)")
    print(f"  3. 1h_close_at_near (entry at near after 1H confirmation)")
    print(f"  4. 4h_close_at_close (entry at 4H close price)")
    print(f"  5. 4h_close_at_near (entry at near after 4H confirmation)")
    print(f"\nPairs: {len(PAIRS)} pairs")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Risk per Trade: {RISK_PER_TRADE*100:.1f}%")
    print(f"\nTotal Configurations: {len(TIMEFRAMES) * len(ENTRY_TYPES)} = 15 backtests")
    print("="*80)

    all_results = []

    for htf_tf in TIMEFRAMES:
        for entry_type in ENTRY_TYPES:
            # Run backtest
            trades = run_backtest(htf_tf, entry_type)

            # Convert to DataFrame
            trades_df = pd.DataFrame(trades)

            # Calculate stats
            stats = calc_stats(trades_df, STARTING_CAPITAL, RISK_PER_TRADE) if len(trades_df) > 0 else None

            # Store result
            all_results.append({
                'htf': htf_tf,
                'entry_type': entry_type,
                'trades': trades,
                'stats': stats
            })

            # Generate individual report
            if len(trades_df) > 0:
                generate_report(htf_tf, entry_type, trades_df)

    # Generate comparison report
    generate_comparison_report(all_results)

    total_time = time.time() - start_time

    print("\n" + "="*80)
    print("OPTIMIZATION COMPLETE")
    print("="*80)
    print(f"\nTotal Runtime: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"\nOutput Directory: {OUTPUT_DIR}")
    print(f"  - {len(all_results)} individual reports")
    print(f"  - {len(all_results)} CSV files in Trades/")
    print(f"  - 1 summary comparison report")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
