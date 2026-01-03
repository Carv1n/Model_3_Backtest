"""
Model 3 - Combined Backtest (W, 3D, M)
---------------------------------------

Runs backtests for all 3 HTF timeframes in one script:
- Weekly (W)
- 3-Day (3D)
- Monthly (M)

Generates separate reports and CSVs for each timeframe.

Output (per timeframe):
- TXT Report: results/{TF}_report.txt
- CSV Trades: results/Trades/{TF}_trades.csv

Settings:
- Entry: direct_touch
- Risk: 1% per trade
- Period: 2010-2024
- Pairs: All 28 Major/Cross Pairs
- NO Transaction Costs (R-based only)
"""

import sys
from pathlib import Path
import time
from datetime import datetime
import pandas as pd
import numpy as np
from collections import defaultdict

# Go up to "05_Model 3" directory
model3_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(model3_root))

from scripts.backtesting.backtest_model3 import (
    load_tf_data,
    detect_htf_pivots,
    compute_sl_tp,
    price_per_pip,
    should_use_wick_diff_entry,
)

# ============================================================================
# OPTIMIZED FUNCTIONS (vectorized versions)
# ============================================================================

def body_pct_vectorized(df):
    """Calculate body percentage for all candles (vectorized)"""
    rng = df["high"] - df["low"]
    body = abs(df["close"] - df["open"])
    return (body / rng * 100).fillna(0)


def detect_refinements_fast(df, htf_pivot, timeframe, max_size_frac=0.2, min_body_pct=5.0):
    """
    OPTIMIZED: Vectorized refinement detection (NO LOOPS!)
    """
    from scripts.backtesting.backtest_model3 import Refinement

    # Filter time window FIRST
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
        extremes = np.maximum(extremes, htf_pivot.extreme)
    else:
        extremes = np.maximum(df_k1_valid['high'].values, df_k2_valid['high'].values)
        nears = np.minimum(df_k1_valid['high'].values, df_k2_valid['high'].values)
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
    """Vectorized version of gap touch detection on Daily"""
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
ENTRY_CONFIRMATION = "direct_touch"
START_DATE = "2010-01-01"
END_DATE = "2024-12-31"

# Risk Settings
STARTING_CAPITAL = 100000  # $100k
RISK_PER_TRADE = 0.01  # 1% per trade

# Strategy Settings
DOJI_FILTER = 5.0  # Min body % for pivots
REFINEMENT_MAX_SIZE = 0.20  # Max 20% of HTF gap

# Output
RESULTS_DIR = Path(__file__).parent.parent / "results"
TRADES_DIR = RESULTS_DIR / "Trades"

# Create directories
TRADES_DIR.mkdir(parents=True, exist_ok=True)

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


def simulate_single_trade(pair, pivot, refinements, ltf_cache, htf_timeframe):
    """
    Simuliert einen Trade für ein Pivot mit chronologischer Verfeinerungs-Logik.

    CRITICAL LOGIC:
    - Nur EINE Entry pro Pivot
    - Nur höchste Priorität refinement bekommt RR-Check
    - Niedrigere Priorität refinements werden sofort gelöscht wenn berührt (KEIN RR-Check)
    - Chronologische Reihenfolge der Touches ist entscheidend
    - RR Fallback: Wenn höchste Prio < 1 RR → löschen, nächste wird höchste Prio

    Args:
        htf_timeframe: 'W', '3D', or 'M'

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
    # R-based only
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

    # PnL berechnen (R-based - no costs!)
    if pivot.direction == "bullish":
        pnl_price = exit_price - entry_price
    else:
        pnl_price = entry_price - exit_price

    pnl_pips = pnl_price / pip_value
    risk_pips = abs(entry_price - sl_price) / pip_value
    pnl_r = pnl_pips / risk_pips if risk_pips > 0 else 0

    # Duration
    duration_days = (exit_time - entry_time).total_seconds() / 86400

    # FIXED: Use correct pip_divisor for JPY pairs
    pip_divisor = 100 if 'JPY' in pair else 10000

    return {
        "pair": pair,
        "htf_timeframe": htf_timeframe,  # NOW DYNAMIC!
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
        "gap_pips": pivot.gap_size / pip_value,
        "wick_diff_pips": abs(pivot.near - pivot.extreme) / pip_value,
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
# PORTFOLIO SIMULATION (PER TIMEFRAME)
# ============================================================================

def run_backtest_for_timeframe(htf_timeframe):
    """
    Führt Backtest für einen HTF-Timeframe durch (W, 3D, oder M).

    Returns: list of trade dicts
    """
    all_trades = []

    print(f"\n{'='*80}")
    print(f"BACKTEST: {htf_timeframe}")
    print(f"{'='*80}")

    for pair in PAIRS:
        print(f"\n{pair}:")

        # Load HTF data
        htf_df = load_tf_data(htf_timeframe, pair)
        start_ts = pd.Timestamp(START_DATE, tz="UTC")
        end_ts = pd.Timestamp(END_DATE, tz="UTC")
        htf_df = htf_df[(htf_df["time"] >= start_ts) & (htf_df["time"] <= end_ts)].copy()
        print(f"  HTF ({htf_timeframe}): {len(htf_df)} candles")

        # Detect pivots
        pivots = detect_htf_pivots(htf_df, min_body_pct=DOJI_FILTER)
        print(f"  Pivots: {len(pivots)}")

        if len(pivots) == 0:
            continue

        # Load LTF data
        ltf_cache = {}

        # CRITICAL FIX: LTF list must EXCLUDE the HTF itself!
        # For 3D HTF, we can't search refinements on 3D data (timing conflict)
        # For M HTF, we need to include W refinements
        all_tfs = ["M", "W", "3D", "D", "H4", "H1"]
        htf_idx = all_tfs.index(htf_timeframe)
        ltf_list = all_tfs[htf_idx + 1:]  # All TFs below HTF

        for tf in ltf_list:
            ltf_df = load_tf_data(tf, pair)
            ltf_df = ltf_df[(ltf_df["time"] >= start_ts) & (ltf_df["time"] <= end_ts)].copy()
            ltf_cache[tf] = ltf_df

        # Detect ALL refinements at once (vectorized)
        all_refinements = {}
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

        # Simulate trades
        trades_found = 0
        for pivot in pivots:
            pivot_id = f"{pivot.time}"
            refinements = all_refinements.get(pivot_id, [])

            # Simulate trade
            trade = simulate_single_trade(pair, pivot, refinements, ltf_cache, htf_timeframe)

            if trade:
                all_trades.append(trade)
                trades_found += 1

        print(f"  Trades Found: {trades_found}")

    # Sort chronologically
    all_trades.sort(key=lambda t: t["entry_time"])

    print(f"\n{'='*80}")
    print(f"TOTAL TRADES ({htf_timeframe}): {len(all_trades)}")
    print(f"{'='*80}\n")

    return all_trades


# ============================================================================
# REPORT GENERATION
# ============================================================================

def generate_report_for_timeframe(htf_timeframe, trades_df):
    """
    Generiert Report und CSV für einen Timeframe.
    """
    if len(trades_df) == 0:
        print(f"\n[!] No trades for {htf_timeframe} - skipping report")
        return

    print(f"\n{'='*80}")
    print(f"GENERATING REPORT: {htf_timeframe}")
    print(f"{'='*80}")

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
    stats = calc_stats(trades_df, STARTING_CAPITAL, RISK_PER_TRADE)
    report = format_report(stats, htf_timeframe, report_config)

    # Save report
    report_file = RESULTS_DIR / f"{htf_timeframe}_report.txt"
    report_file.write_text(report, encoding='utf-8')
    print(f"  ✓ Report: {report_file.name}")

    # Save CSV
    # Fix timezone issue: Remove timezone from datetime columns
    datetime_cols = ['entry_time', 'exit_time', 'pivot_time', 'valid_time', 'gap_touch_time']
    for col in datetime_cols:
        if col in trades_df.columns:
            trades_df[col] = pd.to_datetime(trades_df[col]).dt.tz_localize(None)

    trades_csv = TRADES_DIR / f"{htf_timeframe}_trades.csv"
    trades_df.to_csv(trades_csv, index=False)
    print(f"  ✓ CSV: {trades_csv.relative_to(RESULTS_DIR.parent)}")

    # Print summary
    print(f"\n  Results:")
    print(f"    Total Return: {stats['total_return']:+.1f}%")
    print(f"    Sharpe: {stats['sharpe']:.2f}")
    print(f"    Max DD: {stats['max_dd']:.1f}%")
    print(f"    Expectancy: {stats['expectancy']:+.2f}R")
    print(f"    Win Rate: {stats['win_rate']:.1f}%")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main execution - runs all 3 timeframes"""
    start_time = time.time()

    print("\n" + "="*80)
    print("MODEL 3 - COMBINED BACKTEST (W, 3D, M)")
    print("="*80)
    print(f"Pairs: {len(PAIRS)} pairs")
    print(f"Entry: {ENTRY_CONFIRMATION}")
    print(f"Period: {START_DATE} to {END_DATE}")
    print(f"Risk per Trade: {RISK_PER_TRADE*100:.1f}%")
    print(f"Starting Capital: ${STARTING_CAPITAL:,.0f}")
    print(f"\nTimeframes: W, 3D, M")
    print("="*80)

    # Run backtests for all 3 timeframes
    timeframes = ['W', '3D', 'M']

    for htf_tf in timeframes:
        # Run backtest
        trades = run_backtest_for_timeframe(htf_tf)

        # Convert to DataFrame
        trades_df = pd.DataFrame(trades)

        # Generate report
        generate_report_for_timeframe(htf_tf, trades_df)

    # Final summary
    total_time = time.time() - start_time

    print("\n" + "="*80)
    print("ALL BACKTESTS COMPLETE")
    print("="*80)
    print(f"\nTotal Runtime: {total_time:.1f}s ({total_time/60:.1f} minutes)")
    print(f"\nOutput Directory: {RESULTS_DIR}")
    print(f"  - 3 Reports: W_report.txt, 3D_report.txt, M_report.txt")
    print(f"  - 3 CSVs: Trades/W_trades.csv, Trades/3D_trades.csv, Trades/M_trades.csv")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
