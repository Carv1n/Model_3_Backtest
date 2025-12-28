"""
Fixed Pivot Validation - Model 3
---------------------------------

Validiert einen FIXEN Pivot mit ALLEN Details:
- AUDNZD Weekly, K2 = 16.06.2025
- Pivot-Struktur (Pivot, Extreme, Near, Gap, Wick Diff)
- ALLE gültigen Verfeinerungen mit allen Details
- Wenn Wick Diff < 20% der Pivot Gap → Wick Diff selbst als "Verfeinerung"

NUR Struktur-Output, KEINE Trade-Simulation!
"""

import sys
from pathlib import Path
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.backtesting.backtest_model3 import (
    load_tf_data,
    detect_htf_pivots,
    detect_refinements,
    body_pct,
)

# FIXER PIVOT
PAIR = "AUDNZD"
HTF_TF = "W"
K2_DATE = "2025-06-16"  # K2 Close


def find_pivot_at_date(df, target_date):
    """
    Findet Pivot wo K2 = target_date.
    """
    target = pd.Timestamp(target_date, tz="UTC")

    # Finde K2
    k2_row = df[df["time"] == target]
    if k2_row.empty:
        return None, None

    k2_idx = k2_row.index[0]
    if k2_idx == 0:
        return None, None  # Keine K1

    k1 = df.iloc[k2_idx - 1]
    k2 = df.iloc[k2_idx]

    # Check Pivot Pattern
    k1_red = k1["close"] < k1["open"]
    k1_green = k1["close"] > k1["open"]
    k2_red = k2["close"] < k2["open"]
    k2_green = k2["close"] > k2["open"]

    # Doji-Filter
    if body_pct(k1) < 5.0 or body_pct(k2) < 5.0:
        return None, None

    direction = None
    if k1_red and k2_green:
        direction = "bullish"
    elif k1_green and k2_red:
        direction = "bearish"
    else:
        return None, None

    # Pivot Struktur
    if direction == "bullish":
        extreme = min(k1["low"], k2["low"])
        near = max(k1["low"], k2["low"])
    else:
        extreme = max(k1["high"], k2["high"])
        near = min(k1["high"], k2["high"])

    pivot_level = k2["open"]
    gap_size = abs(pivot_level - extreme)

    # valid_time = K3 start (falls vorhanden)
    if k2_idx + 1 < len(df):
        valid_time = df.iloc[k2_idx + 1]["time"]
    else:
        valid_time = k2["time"]

    return {
        "time": k2["time"],
        "valid_time": valid_time,
        "direction": direction,
        "pivot": pivot_level,
        "extreme": extreme,
        "near": near,
        "gap_size": gap_size,
        "k1_time": k1["time"],
        "k2_time": k2["time"],
    }, (k1, k2)


def run_validation():
    print("=" * 80)
    print("MODEL 3 - FIXED PIVOT VALIDATION")
    print("=" * 80)
    print(f"Pair: {PAIR}")
    print(f"HTF: {HTF_TF}")
    print(f"K2 Date: {K2_DATE}")
    print("=" * 80)
    print()

    # Lade HTF Daten
    print("Lade Weekly Daten...")
    htf_df = load_tf_data(HTF_TF, PAIR)

    # Finde Pivot
    pivot_data, candles = find_pivot_at_date(htf_df, K2_DATE)

    if pivot_data is None:
        print(f"[ERROR] Kein gültiger Pivot an K2={K2_DATE} gefunden!")
        print("Mögliche Gründe:")
        print("  - Datum nicht in Daten vorhanden")
        print("  - Kein 2-Kerzen-Muster (K1 rot→K2 grün ODER K1 grün→K2 rot)")
        print("  - Doji-Filter nicht bestanden (Body < 5%)")
        return

    k1, k2 = candles

    print("=" * 80)
    print("HTF-PIVOT GEFUNDEN")
    print("=" * 80)
    print()

    print(f"--- KERZEN ---")
    print(f"K1 Time: {pivot_data['k1_time']}")
    print(f"  Open: {k1['open']:.5f}")
    print(f"  High: {k1['high']:.5f}")
    print(f"  Low: {k1['low']:.5f}")
    print(f"  Close: {k1['close']:.5f}")
    print(f"  Body %: {body_pct(k1):.1f}%")
    print()
    print(f"K2 Time: {pivot_data['k2_time']}")
    print(f"  Open: {k2['open']:.5f}")
    print(f"  High: {k2['high']:.5f}")
    print(f"  Low: {k2['low']:.5f}")
    print(f"  Close: {k2['close']:.5f}")
    print(f"  Body %: {body_pct(k2):.1f}%")
    print()

    print(f"--- PIVOT STRUKTUR ---")
    print(f"Direction: {pivot_data['direction']}")
    print(f"Pivot (Open K2): {pivot_data['pivot']:.5f}")
    print(f"Extreme: {pivot_data['extreme']:.5f}")
    print(f"Near: {pivot_data['near']:.5f}")
    print(f"Valid Time (nach K2 Close): {pivot_data['valid_time']}")
    print()

    print(f"--- GAPS ---")
    gap_pips = pivot_data['gap_size'] * 10000
    print(f"Pivot Gap: {pivot_data['gap_size']:.5f} ({gap_pips:.1f} pips)")

    wick_diff = abs(pivot_data['near'] - pivot_data['extreme'])
    wick_diff_pips = wick_diff * 10000
    wick_diff_pct = (wick_diff / pivot_data['gap_size'] * 100) if pivot_data['gap_size'] > 0 else 0
    print(f"Wick Difference: {wick_diff:.5f} ({wick_diff_pips:.1f} pips, {wick_diff_pct:.1f}% von Pivot Gap)")
    print()

    # CHECK: Wick Diff < 20%?
    use_wick_diff_as_refinement = wick_diff_pct < 20.0
    if use_wick_diff_as_refinement:
        print("🔔 WICHTIG: Wick Diff < 20% der Pivot Gap!")
        print("   → Wick Diff SELBST wird als 'Verfeinerung' genutzt")
        print(f"   → Entry-Zone: {pivot_data['near']:.5f} bis {pivot_data['extreme']:.5f}")
        print()

    # Lade LTF Daten
    print("=" * 80)
    print("LADE LTF-DATEN FÜR VERFEINERUNGEN")
    print("=" * 80)
    ltf_cache = {}
    for tf in ["3D", "D", "H4", "H1"]:
        print(f"  Lade {tf}...", end="")
        ltf_df = load_tf_data(tf, PAIR)
        ltf_cache[tf] = ltf_df
        print(f" {len(ltf_df)} Kerzen")
    print()

    # Erstelle Pivot-Objekt für detect_refinements
    from dataclasses import dataclass

    @dataclass
    class TempPivot:
        time: pd.Timestamp
        k1_time: pd.Timestamp
        valid_time: pd.Timestamp
        direction: str
        pivot: float
        extreme: float
        near: float
        gap_size: float

    pivot_obj = TempPivot(
        time=pivot_data['time'],
        k1_time=pivot_data['k1_time'],
        valid_time=pivot_data['valid_time'],
        direction=pivot_data['direction'],
        pivot=pivot_data['pivot'],
        extreme=pivot_data['extreme'],
        near=pivot_data['near'],
        gap_size=pivot_data['gap_size'],
    )

    # Suche Verfeinerungen
    print("=" * 80)
    print("SUCHE VERFEINERUNGEN")
    print("=" * 80)
    print(f"Zeitfenster: {pivot_data['k1_time']} bis {pivot_data['valid_time']}")
    print(f"Suche in TFs: 3D, D, H4, H1")
    print()

    all_refinements = []
    for tf in ["3D", "D", "H4", "H1"]:
        print(f"--- {tf} ---")
        ref_list = detect_refinements(
            ltf_cache[tf],
            pivot_obj,
            tf,
            max_size_frac=0.2,
            min_body_pct=5.0
        )
        print(f"  {len(ref_list)} Verfeinerung(en) gefunden")
        all_refinements.extend(ref_list)

        # Detail-Output für JEDE Verfeinerung
        for i, ref in enumerate(ref_list, 1):
            print(f"  #{i}:")
            print(f"    Time: {ref.time}")
            print(f"    Direction: {ref.direction}")
            print(f"    Pivot Level (Open K2): {ref.pivot_level:.5f}")
            print(f"    Extreme: {ref.extreme:.5f}")
            print(f"    Near (Entry-Level): {ref.near:.5f}")
            ref_pct = (ref.size / pivot_data['gap_size'] * 100) if pivot_data['gap_size'] > 0 else 0
            print(f"    Size: {ref.size:.5f} ({ref.size * 10000:.1f} pips, {ref_pct:.1f}% von HTF Gap)")
            print()

    print("=" * 80)
    print("ZUSAMMENFASSUNG")
    print("=" * 80)
    print(f"Total Verfeinerungen: {len(all_refinements)}")

    if use_wick_diff_as_refinement:
        print()
        print("⚠️ Wick Diff < 20% → Nutze Wick Diff selbst als Entry-Zone!")
        print(f"   Entry-Zone: {pivot_data['near']:.5f} bis {pivot_data['extreme']:.5f}")

    if len(all_refinements) == 0 and not use_wick_diff_as_refinement:
        print()
        print("⚠️ KEINE Verfeinerungen gefunden UND Wick Diff >= 20%!")
        print("   → Kein gültiges Setup!")

    print()
    print("=" * 80)
    print("MANUELLE VALIDIERUNG IN TRADINGVIEW")
    print("=" * 80)
    print(f"1. Öffne {PAIR} auf Weekly Chart")
    print(f"2. Navigiere zu K2: {K2_DATE}")
    print(f"3. Prüfe K1 ({pivot_data['k1_time']}): {'rot (bearish)' if pivot_data['direction'] == 'bullish' else 'grün (bullish)'}")
    print(f"4. Prüfe K2 ({pivot_data['k2_time']}): {'grün (bullish)' if pivot_data['direction'] == 'bullish' else 'rot (bearish)'}")
    print(f"5. Markiere Levels:")
    print(f"   - Pivot (Open K2): {pivot_data['pivot']:.5f}")
    print(f"   - Extreme: {pivot_data['extreme']:.5f}")
    print(f"   - Near: {pivot_data['near']:.5f}")
    print(f"6. Markiere Pivot Gap: {pivot_data['pivot']:.5f} bis {pivot_data['extreme']:.5f}")
    print(f"7. Markiere Wick Diff: {pivot_data['near']:.5f} bis {pivot_data['extreme']:.5f}")

    if use_wick_diff_as_refinement:
        print(f"8. ✅ Wick Diff < 20% → Entry-Zone = Wick Diff")
    else:
        print(f"8. Prüfe jede Verfeinerung (siehe oben):")
        print(f"   - Innerhalb Wick Diff?")
        print(f"   - Size <= 20% HTF Gap?")
        print(f"   - Open K2 NICHT berührt bis {pivot_data['valid_time']}?")

    print()


if __name__ == "__main__":
    run_validation()
