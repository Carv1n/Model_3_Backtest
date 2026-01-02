"""
Debug CADJPY 3D - Warum 0 Trades bei 619 Pivots?

Checkt speziell Pivot 18.06.2021
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Setup path
model3_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(model3_root))

from scripts.backtesting.backtest_model3 import (
    load_tf_data,
    detect_htf_pivots,
    detect_refinements,
    compute_sl_tp,
    should_use_wick_diff_entry,
)

# Settings
PAIR = "CADJPY"
HTF_TF = "3D"
START_DATE = "2010-01-01"
END_DATE = "2024-12-31"
TARGET_PIVOT_DATE = "2021-06-10"

print("="*80)
print(f"DEBUG: {PAIR} {HTF_TF} - Target Pivot: {TARGET_PIVOT_DATE}")
print("="*80)

# Load HTF data
htf_df = load_tf_data(HTF_TF, PAIR)
start_ts = pd.Timestamp(START_DATE, tz="UTC")
end_ts = pd.Timestamp(END_DATE, tz="UTC")
htf_df = htf_df[(htf_df["time"] >= start_ts) & (htf_df["time"] <= end_ts)].copy()

print(f"\nHTF ({HTF_TF}): {len(htf_df)} candles")

# Detect pivots
pivots = detect_htf_pivots(htf_df, min_body_pct=5.0)
print(f"Total Pivots: {len(pivots)}")

# Find target pivot
target_pivot = None
for pivot in pivots:
    pivot_date = pivot.time.strftime("%Y-%m-%d")
    if pivot_date == TARGET_PIVOT_DATE:
        target_pivot = pivot
        break

if target_pivot is None:
    print(f"\n❌ Pivot {TARGET_PIVOT_DATE} NOT FOUND!")
    print("\nAvailable pivots around that date:")
    for pivot in pivots:
        pivot_date = pivot.time.strftime("%Y-%m-%d")
        if "2021-06" in pivot_date:
            print(f"  - {pivot_date}: {pivot.direction}")
    sys.exit(1)

print(f"\n✓ Found Target Pivot: {target_pivot.time}")
print(f"  Direction: {target_pivot.direction}")
print(f"  Pivot: {target_pivot.pivot}")
print(f"  Extreme: {target_pivot.extreme}")
print(f"  Near: {target_pivot.near}")
print(f"  Gap Size: {target_pivot.gap_size}")
print(f"  Wick Diff: {abs(target_pivot.near - target_pivot.extreme)}")
print(f"  Valid Time (K3 Open): {target_pivot.valid_time}")

# Load LTF data
print("\n" + "="*80)
print("LOADING LTF DATA")
print("="*80)

ltf_list = ["D", "H4", "H1"]
ltf_cache = {}

for tf in ltf_list:
    ltf_df = load_tf_data(tf, PAIR)
    ltf_df = ltf_df[(ltf_df["time"] >= start_ts) & (ltf_df["time"] <= end_ts)].copy()
    ltf_cache[tf] = ltf_df
    print(f"  {tf}: {len(ltf_df)} candles")

# Detect refinements
print("\n" + "="*80)
print("DETECTING REFINEMENTS")
print("="*80)

all_refinements = []
for tf in ltf_list:
    ref_list = detect_refinements(
        ltf_cache[tf],
        target_pivot,
        tf,
        max_size_frac=0.20,
        min_body_pct=5.0
    )
    print(f"\n{tf}: {len(ref_list)} refinements")
    for i, ref in enumerate(ref_list, 1):
        print(f"  {i}. Time: {ref.time}, Near: {ref.near}, Size: {ref.size}")
    all_refinements.extend(ref_list)

print(f"\nTotal Refinements: {len(all_refinements)}")

# Check Wick Diff Entry
use_wick_diff, wick_diff_entry = should_use_wick_diff_entry(target_pivot, all_refinements)
print(f"\nWick Diff Entry:")
print(f"  Use: {use_wick_diff}")
print(f"  Entry Level: {wick_diff_entry}")

# Check Gap Touch
print("\n" + "="*80)
print("CHECKING GAP TOUCH")
print("="*80)

d_df = ltf_cache["D"]
h1_df = ltf_cache["H1"]

# Gap Touch Detection
gap_low = min(target_pivot.pivot, target_pivot.extreme)
gap_high = max(target_pivot.pivot, target_pivot.extreme)

df_after = d_df[d_df["time"] >= target_pivot.valid_time].copy()
if target_pivot.direction == "bullish":
    mask = (df_after["low"] <= gap_high) & (df_after["high"] >= gap_low)
else:
    mask = (df_after["high"] >= gap_low) & (df_after["low"] <= gap_high)

hits = df_after[mask]
if len(hits) > 0:
    daily_gap_touch = hits.iloc[0]["time"]
    print(f"✓ Daily Gap Touch: {daily_gap_touch}")

    # H1 Gap Touch
    df_h1_after = h1_df[h1_df["time"] >= daily_gap_touch].copy()
    if target_pivot.direction == "bullish":
        h1_mask = (df_h1_after["low"] <= gap_high) & (df_h1_after["high"] >= gap_low)
    else:
        h1_mask = (df_h1_after["high"] >= gap_low) & (df_h1_after["low"] <= gap_low)

    h1_hits = df_h1_after[h1_mask]
    if len(h1_hits) > 0:
        gap_touch_time = h1_hits.iloc[0]["time"]
        print(f"✓ H1 Gap Touch: {gap_touch_time}")
    else:
        print(f"❌ H1 Gap Touch NOT FOUND!")
        gap_touch_time = None
else:
    print(f"❌ Daily Gap Touch NOT FOUND!")
    gap_touch_time = None

# If we have gap touch, try to find entry
if gap_touch_time and len(all_refinements) > 0:
    print("\n" + "="*80)
    print("CHECKING ENTRY")
    print("="*80)

    # Sort refinements by priority
    def ref_priority(ref):
        tf_order = {"W": 0, "3D": 1, "D": 2, "H4": 3, "H1": 4}
        tf_prio = tf_order.get(ref.timeframe, 99)
        dist_to_near = abs(ref.near - target_pivot.near)
        return (tf_prio, dist_to_near)

    refinements_sorted = sorted(all_refinements, key=ref_priority)

    print(f"Refinements sorted by priority:")
    for i, ref in enumerate(refinements_sorted, 1):
        prio = ref_priority(ref)
        print(f"  {i}. {ref.timeframe} @ {ref.time}: Near={ref.near}, Priority={prio}")

    # Check highest priority refinement
    highest_ref = refinements_sorted[0]
    print(f"\nHighest Priority: {highest_ref.timeframe} @ {highest_ref.time}")

    # Check RR
    sl_tp_result = compute_sl_tp(target_pivot.direction, highest_ref.near, target_pivot, PAIR)
    if sl_tp_result:
        sl, tp, rr = sl_tp_result
        print(f"  Entry: {highest_ref.near}")
        print(f"  SL: {sl}")
        print(f"  TP: {tp}")
        print(f"  RR: {rr:.2f}")

        if rr >= 1.0:
            print(f"\n✓ VALID ENTRY - RR >= 1.0")
        else:
            print(f"\n❌ INVALID ENTRY - RR < 1.0")
    else:
        print(f"\n❌ SL/TP Calculation FAILED")

print("\n" + "="*80)
print("DEBUG COMPLETE")
print("="*80)
