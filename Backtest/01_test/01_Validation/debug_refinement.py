"""Debug Script - Warum wird Verfeinerung #6 nicht erkannt?"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.backtesting.backtest_model3 import (
    load_tf_data,
    detect_htf_pivots,
    detect_refinements,
    Pivot,
)

# Lade AUDNZD Weekly
df_w = load_tf_data("W", "AUDNZD")

# Finde HTF Pivot vom 2015-05-25
pivots = detect_htf_pivots(df_w)
target_pivot = None
for p in pivots:
    if p.time == pd.Timestamp("2015-05-25 00:00:00+00:00"):
        target_pivot = p
        break

if target_pivot is None:
    print("FEHLER: Pivot nicht gefunden!")
    sys.exit(1)

print("=" * 80)
print("HTF PIVOT GEFUNDEN:")
print(f"K1 Time: {target_pivot.k1_time}")
print(f"K2 Time: {target_pivot.time}")
print(f"Valid Time: {target_pivot.valid_time}")
print(f"Direction: {target_pivot.direction}")
print(f"Extreme: {target_pivot.extreme:.5f}")
print(f"Near: {target_pivot.near:.5f}")
print(f"Gap: {target_pivot.gap_size:.5f}")
print()

# Lade H4 Daten
df_h4 = load_tf_data("H4", "AUDNZD")

# Filtere Zeitfenster
mask = (df_h4["time"] >= target_pivot.k1_time) & (df_h4["time"] < target_pivot.valid_time)
df_filtered = df_h4[mask].copy().reset_index(drop=True)

print(f"H4 Bars im Zeitfenster: {len(df_filtered)}")
print()

# Erkenne Verfeinerungen mit dem OFFIZIELLEN Code
refinements = detect_refinements(df_h4, target_pivot, "H4")

print("=" * 80)
print(f"OFFIZIELLE VERFEINERUNGEN: {len(refinements)}")
for i, ref in enumerate(refinements, 1):
    print(f"#{i}: {ref.time} | Extreme={ref.extreme:.5f}, Near={ref.near:.5f}, Size={abs(ref.extreme - ref.near):.5f}")
print()

# Jetzt manuell die beiden erwarteten Verfeinerungen prüfen
print("=" * 80)
print("MANUELLE PRÜFUNG DER BEIDEN ERWARTETEN VERFEINERUNGEN:")
print()

expected = [
    {
        "name": "#6: 05:00-09:00",
        "k1_idx": None,
        "k2_time": pd.Timestamp("2015-05-28 09:00:00+00:00"),
    },
    {
        "name": "#7: 17:00-21:00",
        "k2_time": pd.Timestamp("2015-05-28 21:00:00+00:00"),
    },
]

for exp in expected:
    k2_time = exp["k2_time"]

    # Finde K1/K2
    k2_row = df_h4[df_h4["time"] == k2_time]
    if k2_row.empty:
        print(f"{exp['name']}: K2 NICHT GEFUNDEN!")
        continue

    k2_idx = k2_row.index[0]
    k1_idx = k2_idx - 1

    k1 = df_h4.iloc[k1_idx]
    k2 = df_h4.iloc[k2_idx]

    print(f"{exp['name']}: K2 Time = {k2_time}")
    print(f"  K1: {k1['time']} | O={k1['open']:.5f} H={k1['high']:.5f} L={k1['low']:.5f} C={k1['close']:.5f}")
    print(f"  K2: {k2['time']} | O={k2['open']:.5f} H={k2['high']:.5f} L={k2['low']:.5f} C={k2['close']:.5f}")

    # Check 1: Zeitfenster
    in_timeframe = (k2["time"] >= target_pivot.k1_time and k2["time"] < target_pivot.valid_time)
    print(f"  Zeitfenster: {in_timeframe}")

    # Check 2: Doji Filter
    k1_body = abs(k1['close'] - k1['open'])
    k2_body = abs(k2['close'] - k2['open'])
    k1_range = k1['high'] - k1['low']
    k2_range = k2['high'] - k2['low']
    k1_body_pct = (k1_body / k1_range * 100) if k1_range > 0 else 0
    k2_body_pct = (k2_body / k2_range * 100) if k2_range > 0 else 0
    doji_ok = (k1_body_pct >= 5 and k2_body_pct >= 5)
    print(f"  Doji Filter: {doji_ok} (K1={k1_body_pct:.1f}%, K2={k2_body_pct:.1f}%)")

    # Check 3: Bullish
    prev_red = k1["close"] < k1["open"]
    curr_green = k2["close"] > k2["open"]
    is_bullish = prev_red and curr_green
    print(f"  Bullish: {is_bullish}")

    # Check 4: Struktur
    extreme = min(k1["low"], k2["low"])
    near = max(k1["low"], k2["low"])
    size = abs(extreme - near)
    print(f"  Extreme={extreme:.5f}, Near={near:.5f}, Size={size:.5f}")

    # Check 5: Größe
    max_size = target_pivot.gap_size * 0.2
    size_ok = size <= max_size and size > 0
    print(f"  Size Check: {size_ok} (Size={size*10000:.1f} pips, Max={max_size*10000:.1f} pips)")

    # Check 6: Position
    wick_low = target_pivot.extreme
    wick_high = target_pivot.near
    completely_inside = (extreme >= wick_low and near <= wick_high)
    extreme_on_near = np.isclose(extreme, target_pivot.near, atol=0.00001)
    position_ok = completely_inside or extreme_on_near
    print(f"  Position: {position_ok} (Inside={completely_inside}, OnNear={extreme_on_near})")
    print(f"    DEBUG: wick_low={wick_low:.5f}, wick_high={wick_high:.5f}")
    print(f"    DEBUG: extreme={extreme:.5f}, near={near:.5f}")
    print(f"    DEBUG: extreme >= wick_low = {extreme} >= {wick_low} = {extreme >= wick_low}")
    print(f"    DEBUG: near <= wick_high = {near} <= {wick_high} = {near <= wick_high}")

    # Check 7: Unberührt
    touch_window = df_h4[
        (df_h4["time"] > k2["time"]) &
        (df_h4["time"] <= target_pivot.valid_time)
    ]
    was_touched = False
    for _, candle in touch_window.iterrows():
        if candle["low"] <= near:
            was_touched = True
            break
    unberuehrt_ok = not was_touched
    print(f"  Unberuehrt: {unberuehrt_ok}")

    # Finale Antwort
    all_ok = in_timeframe and doji_ok and is_bullish and size_ok and position_ok and unberuehrt_ok
    print(f"  => VALID: {all_ok}")
    print()
