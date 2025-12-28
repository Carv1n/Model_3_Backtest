"""
Validiert das spezifische AUDNZD Pivot vom 25.05.2015
Dieses Pivot hatte das Floating-Point-Problem
"""

import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.backtesting.backtest_model3 import (
    load_tf_data,
    detect_htf_pivots,
    detect_refinements,
)

# Lade AUDNZD Weekly
df_w = load_tf_data("W", "AUDNZD")

# Finde Pivot vom 2015-05-25
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
print("AUDNZD W - 2015-05-25")
print("=" * 80)
print(f"K1 Time: {target_pivot.k1_time}")
print(f"K2 Time: {target_pivot.time}")
print(f"Valid Time: {target_pivot.valid_time}")
print(f"Direction: {target_pivot.direction}")
print(f"Pivot: {target_pivot.pivot:.5f}")
print(f"Extreme: {target_pivot.extreme:.5f}")
print(f"Near: {target_pivot.near:.5f}")
print(f"Gap: {target_pivot.gap_size:.5f} ({target_pivot.gap_size*10000:.1f} pips)")
print()

# Erkenne Verfeinerungen
df_h4 = load_tf_data("H4", "AUDNZD")
df_h1 = load_tf_data("H1", "AUDNZD")

refinements_h4 = detect_refinements(df_h4, target_pivot, "H4")
refinements_h1 = detect_refinements(df_h1, target_pivot, "H1")

print("VERFEINERUNGEN:")
print(f"H4: {len(refinements_h4)}")
for i, ref in enumerate(refinements_h4, 1):
    size = abs(ref.extreme - ref.near)
    size_pct = (size / target_pivot.gap_size * 100)
    print(f"  #{i}: {ref.time}")
    print(f"      Extreme={ref.extreme:.5f}, Near={ref.near:.5f}")
    print(f"      Size={size:.5f} ({size*10000:.1f} pips, {size_pct:.1f}%)")

print()
print(f"H1: {len(refinements_h1)}")
for i, ref in enumerate(refinements_h1, 1):
    size = abs(ref.extreme - ref.near)
    size_pct = (size / target_pivot.gap_size * 100)
    print(f"  #{i}: {ref.time}")
    print(f"      Extreme={ref.extreme:.5f}, Near={ref.near:.5f}")
    print(f"      Size={size:.5f} ({size*10000:.1f} pips, {size_pct:.1f}%)")

print()
print("=" * 80)
print("ERWARTUNG:")
print("H4: 2 Verfeinerungen")
print("  - 2015-05-28 09:00:00 (Extreme auf HTF Extreme)")
print("  - 2015-05-28 21:00:00")
print("=" * 80)

if len(refinements_h4) == 2:
    print("SUCCESS! Beide H4 Verfeinerungen erkannt!")
else:
    print(f"FEHLER! Erwartet: 2, Gefunden: {len(refinements_h4)}")
