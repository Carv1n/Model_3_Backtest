"""
Random Pivot Validation - Model 3
----------------------------------

Validiert ZUFÄLLIGE Pivots für manuelle Überprüfung:
- 2 Pairs (AUDNZD, GBPUSD)
- Je 1 zufälliger Pivot pro Pair
- Timeframe: Weekly
- Zeitraum: 2010-2025
- Output: TXT-Datei mit allen Details

NUR Pivot-Strukturen, KEINE Trade-Simulation!
"""

import sys
from pathlib import Path
import random
import pandas as pd
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.backtesting.backtest_model3 import (
    load_tf_data,
    detect_htf_pivots,
    detect_refinements,
)

# Seed für Reproduzierbarkeit
random.seed(int(datetime.now().timestamp()))

# Config
PAIRS = ["AUDNZD", "GBPUSD"]
HTF_TF = "W"
START_DATE = "2010-01-01"
END_DATE = "2025-12-31"
PIVOTS_PER_PAIR = 1

# Output
OUTPUT_DIR = Path(__file__).parent / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"random_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"


def format_pivot_output(f, pair, htf_tf, pivot, refinements):
    """Formatiert Pivot-Struktur für TXT-Datei."""
    f.write("=" * 80 + "\n")
    f.write(f"PIVOT: {pair} {htf_tf}\n")
    f.write("=" * 80 + "\n\n")

    f.write("--- HTF PIVOT ---\n")
    f.write(f"K1 Time (Open): {pivot.k1_time}\n")
    f.write(f"K2 Time (Open): {pivot.time}\n")
    f.write(f"Valid Time (K3 Open): {pivot.valid_time}\n")
    f.write(f"Direction: {pivot.direction}\n\n")

    f.write("--- LEVELS ---\n")
    f.write(f"Pivot (Open K2): {pivot.pivot:.5f}\n")
    f.write(f"Extreme: {pivot.extreme:.5f}\n")
    f.write(f"Near: {pivot.near:.5f}\n\n")

    f.write("--- GAPS ---\n")
    gap_pips = pivot.gap_size * 10000
    wick_diff = abs(pivot.near - pivot.extreme)
    wick_diff_pips = wick_diff * 10000
    wick_diff_pct = (wick_diff / pivot.gap_size * 100) if pivot.gap_size > 0 else 0

    f.write(f"Pivot Gap: {pivot.gap_size:.5f} ({gap_pips:.1f} pips)\n")
    f.write(f"Wick Difference: {wick_diff:.5f} ({wick_diff_pips:.1f} pips, {wick_diff_pct:.1f}% von Pivot Gap)\n\n")

    if wick_diff_pct < 20.0:
        f.write("WICHTIG: Wick Diff < 20% -> Wick Diff selbst als Entry-Zone!\n\n")

    f.write("--- VERFEINERUNGEN ---\n")
    if not refinements:
        f.write("KEINE gültigen Verfeinerungen gefunden!\n\n")
    else:
        # Gruppiere nach TF
        by_tf = {}
        for ref in refinements:
            if ref.timeframe not in by_tf:
                by_tf[ref.timeframe] = []
            by_tf[ref.timeframe].append(ref)

        f.write(f"Total: {len(refinements)} Verfeinerung(en)\n\n")

        # Sortiere nach TF-Priorität
        tf_order = ["3D", "D", "H4", "H1"]
        for tf in tf_order:
            if tf not in by_tf:
                continue

            refs = by_tf[tf]
            f.write(f"{tf}: {len(refs)} Verfeinerung(en)\n")

            for i, ref in enumerate(refs, 1):
                f.write(f"  #{i}:\n")
                f.write(f"    Time: {ref.time}\n")
                f.write(f"    Direction: {ref.direction}\n")
                f.write(f"    Pivot (Open K2): {ref.pivot_level:.5f}\n")
                f.write(f"    Extreme: {ref.extreme:.5f}\n")
                f.write(f"    Near (Entry): {ref.near:.5f}\n")
                ref_pct = (ref.size / pivot.gap_size * 100) if pivot.gap_size > 0 else 0
                f.write(f"    Size: {ref.size:.5f} ({ref.size * 10000:.1f} pips, {ref_pct:.1f}% von HTF Gap)\n")
            f.write("\n")

    f.write("=" * 80 + "\n\n\n")


def run_validation():
    """Führt Random Pivot Validation durch."""
    print("=" * 80)
    print("MODEL 3 - RANDOM PIVOT VALIDATION")
    print("=" * 80)
    print(f"Pairs: {PAIRS}")
    print(f"HTF: {HTF_TF}")
    print(f"Zeitraum: {START_DATE} bis {END_DATE}")
    print(f"Pivots pro Pair: {PIVOTS_PER_PAIR}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 80)
    print()

    all_structures = []

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("MODEL 3 - RANDOM PIVOT VALIDATION\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Pairs: {', '.join(PAIRS)}\n")
        f.write(f"HTF: {HTF_TF}\n")
        f.write(f"Zeitraum: {START_DATE} bis {END_DATE}\n")
        f.write(f"Pivots pro Pair: {PIVOTS_PER_PAIR}\n")
        f.write("\n\n")

        for pair in PAIRS:
            print(f"{'='*60}")
            print(f"LADE DATEN: {pair}")
            print(f"{'='*60}")

            try:
                # Lade HTF-Daten
                htf_df = load_tf_data(HTF_TF, pair)

                # Filter Zeitraum
                start_ts = pd.Timestamp(START_DATE, tz="UTC")
                end_ts = pd.Timestamp(END_DATE, tz="UTC")
                htf_df = htf_df[(htf_df["time"] >= start_ts) & (htf_df["time"] <= end_ts)].copy()

                print(f"  {HTF_TF} Daten: {len(htf_df)} Kerzen")

                # Finde alle Pivots
                pivots = detect_htf_pivots(htf_df, min_body_pct=5.0)
                print(f"  {len(pivots)} Pivots gefunden")

                if len(pivots) == 0:
                    print(f"  [!] Keine Pivots für {pair}!")
                    continue

                # Wähle zufällige Pivots
                selected_pivots = random.sample(pivots, min(PIVOTS_PER_PAIR, len(pivots)))
                print(f"  {len(selected_pivots)} zufällig ausgewählt")

                # Lade LTF-Daten
                print(f"  Lade LTF-Daten...")
                ltf_cache = {}
                for tf in ["3D", "D", "H4", "H1"]:
                    ltf_df = load_tf_data(tf, pair)
                    ltf_df = ltf_df[(ltf_df["time"] >= start_ts) & (ltf_df["time"] <= end_ts)].copy()
                    ltf_cache[tf] = ltf_df

                # Für jeden Pivot: Verfeinerungen finden
                for pivot in selected_pivots:
                    refinements = []

                    for tf in ["3D", "D", "H4", "H1"]:
                        ref_list = detect_refinements(
                            ltf_cache[tf],
                            pivot,
                            tf,
                            max_size_frac=0.2,
                            min_body_pct=5.0
                        )
                        refinements.extend(ref_list)

                    # Sortiere nach TF-Priorität
                    def tf_priority(tf: str) -> int:
                        order = {"3D": 0, "D": 1, "H4": 2, "H1": 3}
                        return order.get(tf, 99)

                    refinements.sort(key=lambda r: tf_priority(r.timeframe))

                    # Ausgabe
                    format_pivot_output(f, pair, HTF_TF, pivot, refinements)
                    print(f"  -> {pivot.time}: {len(refinements)} Verfeinerungen")

                    # Speichere für Summary
                    all_structures.append({
                        "pair": pair,
                        "pivot_time": pivot.time,
                        "direction": pivot.direction,
                        "gap_size": pivot.gap_size,
                        "num_refinements": len(refinements),
                    })

            except Exception as e:
                print(f"  [ERROR] {pair}: {e}")
                import traceback
                traceback.print_exc()
                continue

    # Summary
    if all_structures:
        df = pd.DataFrame(all_structures)
        summary_file = OUTPUT_DIR / f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(summary_file, index=False)
        print(f"\nSummary CSV: {summary_file}")

    print()
    print("=" * 80)
    print("VALIDATION ABGESCHLOSSEN")
    print("=" * 80)
    print(f"Output: {OUTPUT_FILE}")
    print()


if __name__ == "__main__":
    run_validation()
