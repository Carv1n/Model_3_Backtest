"""
Trade Validation - Model 3
---------------------------

Validiert KOMPLETTE Trades (Pivot + Entry + Exit):
- 2 Pairs (AUDNZD, GBPUSD)
- Je 2 zufällige Pivots pro Pair = 4 Trades
- Timeframe: Weekly
- Zeitraum: 2010-2025
- Entry: direct_touch (Standard)

Output: TXT-Datei mit:
- Pivot-Struktur (wie validation_random_pivots.py)
- Trade-Details (Entry, SL, TP, Exit)
- Zur manuellen Validierung in TradingView

Für jedes Setup:
1. Pivot-Struktur
2. Verfeinerungen
3. Gap Touch
4. Entry (Zeit, Preis)
5. SL/TP Levels
6. Exit (Zeit, Preis, Grund)
7. PnL (Pips, R)
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
    compute_sl_tp,
    price_per_pip,
    find_gap_touch_on_daily,
    check_tp_touched_before_entry,
    should_use_wick_diff_entry,
)

# Seed für Reproduzierbarkeit
random.seed(int(datetime.now().timestamp()))

# Config - 6 verschiedene Pivots mit verschiedenen HTF
# Format: (pair, htf_tf)
PIVOT_CONFIGS = [
    ("AUDNZD", "M"),    # Monthly
    ("GBPUSD", "M"),    # Monthly
    ("EURUSD", "W"),    # Weekly
    ("USDJPY", "W"),    # Weekly
    ("NZDCAD", "3D"),   # 3-Day
    ("GBPJPY", "3D"),   # 3-Day
]
START_DATE = "2010-01-01"
END_DATE = "2025-12-31"
PIVOTS_PER_CONFIG = 1  # 1 Pivot pro Config = 6 Trades total
ENTRY_CONFIRMATION = "direct_touch"

# Output
OUTPUT_DIR = Path(__file__).parent / "results"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = OUTPUT_DIR / f"trade_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"


def simulate_trade(pair, pivot, refinements, ltf_cache):
    """
    Simuliert einen Trade für ein Pivot mit Verfeinerungen.

    Neue Regeln:
    1. Gap Touch auf Daily-Daten prüfen
    2. TP-Check: Wenn TP berührt vor Entry → Setup ungültig
    3. Wick Diff Entry bei < 20% (außer Verfeinerung näher)
    4. RR-Check für alle Entry-Levels

    Returns: dict mit Trade-Details oder None wenn kein Trade
    """
    # Lade H1 und D für Checks
    h1_df = ltf_cache["H1"]
    d_df = ltf_cache["D"]

    # 1. Gap Touch auf Daily-Daten prüfen (genaueres Datum)
    gap_touch_time = find_gap_touch_on_daily(d_df, pivot, pivot.valid_time)

    if gap_touch_time is None:
        return None  # Gap nie berührt

    # 2. Berechne TP (-1 Fib) für TP-Check
    gap = pivot.gap_size
    if pivot.direction == "bullish":
        tp_price = pivot.pivot + gap
    else:
        tp_price = pivot.pivot - gap

    # 3. TP-Check: Wurde TP berührt NACH Gap Touch (aber VOR Entry)?
    tp_touched = check_tp_touched_before_entry(h1_df, pivot, gap_touch_time, tp_price)

    if tp_touched:
        return None  # Setup ungültig - TP berührt vor Entry

    # 4. Entry-Level bestimmen
    use_wick_diff, wick_diff_entry = should_use_wick_diff_entry(pivot, refinements)

    # Sortiere Verfeinerungen nach Priorität
    def ref_priority(ref):
        tf_order = {"W": 0, "3D": 1, "D": 2, "H4": 3, "H1": 4}
        tf_prio = tf_order.get(ref.timeframe, 99)
        dist_to_near = abs(ref.near - pivot.near)
        return (tf_prio, dist_to_near)

    refinements_sorted = sorted(refinements, key=ref_priority) if refinements else []

    # Bestimme Entry-Kandidaten (mit RR-Check)
    entry_candidates = []

    # Wick Diff Entry?
    if use_wick_diff and wick_diff_entry is not None:
        sl_tp_result = compute_sl_tp(pivot.direction, wick_diff_entry, pivot, pair)
        if sl_tp_result is not None and sl_tp_result[2] >= 1.0:
            entry_candidates.append(("wick_diff", wick_diff_entry, sl_tp_result, None))

    # Verfeinerungen als Entry
    for ref in refinements_sorted:
        sl_tp_result = compute_sl_tp(pivot.direction, ref.near, pivot, pair)
        if sl_tp_result is not None and sl_tp_result[2] >= 1.0:
            entry_candidates.append((ref.timeframe, ref.near, sl_tp_result, ref))
            break  # Nur die beste Verfeinerung nehmen

    if not entry_candidates:
        return None  # Kein valider Entry mit >= 1 RR

    # Nutze ersten Kandidaten (mit höchster Prio)
    entry_type, entry_price, sl_tp_result, best_ref = entry_candidates[0]
    sl_price, tp_price, rr = sl_tp_result

    # 5. Entry suchen (nach Gap Touch)
    entry_time = None

    entry_window = h1_df[h1_df["time"] >= gap_touch_time].copy()

    for idx, candle in entry_window.iterrows():
        # Direct Touch Entry
        if pivot.direction == "bullish":
            if candle["low"] <= entry_price:
                entry_time = candle["time"]
                break
        else:  # bearish
            if candle["high"] >= entry_price:
                entry_time = candle["time"]
                break

    if entry_time is None:
        return None  # Entry nie erreicht

    # Exit simulieren
    exit_window = h1_df[h1_df["time"] > entry_time].copy()

    exit_time = None
    exit_price = None
    exit_reason = None

    for idx, candle in exit_window.iterrows():
        if pivot.direction == "bullish":
            # Check SL
            if candle["low"] <= sl_price:
                exit_time = candle["time"]
                exit_price = sl_price
                exit_reason = "sl"
                break
            # Check TP
            if candle["high"] >= tp_price:
                exit_time = candle["time"]
                exit_price = tp_price
                exit_reason = "tp"
                break
        else:  # bearish
            # Check SL
            if candle["high"] >= sl_price:
                exit_time = candle["time"]
                exit_price = sl_price
                exit_reason = "sl"
                break
            # Check TP
            if candle["low"] <= tp_price:
                exit_time = candle["time"]
                exit_price = tp_price
                exit_reason = "tp"
                break

    if exit_time is None:
        return None  # Trade noch offen (ignorieren für Validation)

    # PnL berechnen
    pip_value = price_per_pip(pair)

    if pivot.direction == "bullish":
        pnl_price = exit_price - entry_price
    else:
        pnl_price = entry_price - exit_price

    pnl_pips = pnl_price / pip_value

    risk_pips = abs(entry_price - sl_price) / pip_value
    pnl_r = pnl_pips / risk_pips if risk_pips > 0 else 0

    # Trade-Details zusammenstellen
    trade_dict = {
        "gap_touch_time": gap_touch_time,
        "entry_time": entry_time,
        "entry_price": entry_price,
        "entry_type": entry_type,  # "wick_diff" oder TF der Verfeinerung
        "sl_price": sl_price,
        "tp_price": tp_price,
        "rr": rr,
        "exit_time": exit_time,
        "exit_price": exit_price,
        "exit_reason": exit_reason,
        "pnl_pips": pnl_pips,
        "pnl_r": pnl_r,
    }

    # Wenn Verfeinerung genutzt wurde, füge Details hinzu
    if best_ref is not None:
        trade_dict.update({
            "refinement_tf": best_ref.timeframe,
            "refinement_time": best_ref.time,
            "refinement_pivot": best_ref.pivot_level,
            "refinement_extreme": best_ref.extreme,
            "refinement_near": best_ref.near,
            "refinement_size": best_ref.size,
        })
    else:
        # Wick Diff Entry
        trade_dict.update({
            "refinement_tf": "wick_diff",
            "refinement_time": None,
            "refinement_pivot": None,
            "refinement_extreme": pivot.extreme,
            "refinement_near": pivot.near,
            "refinement_size": abs(pivot.near - pivot.extreme),
        })

    return trade_dict


def format_trade_output(f, pair, htf_tf, pivot, refinements, trade):
    """Formatiert Trade für TXT-Datei."""
    f.write("=" * 80 + "\n")
    f.write(f"TRADE: {pair} {htf_tf}\n")
    f.write("=" * 80 + "\n\n")

    # HTF PIVOT
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

    # VERFEINERUNGEN (alle)
    f.write("--- ALLE VERFEINERUNGEN ---\n")
    if not refinements:
        f.write("KEINE gültigen Verfeinerungen!\n\n")
    else:
        by_tf = {}
        for ref in refinements:
            if ref.timeframe not in by_tf:
                by_tf[ref.timeframe] = []
            by_tf[ref.timeframe].append(ref)

        f.write(f"Total: {len(refinements)} Verfeinerung(en)\n\n")

        # Zeige alle TFs in Prioritäts-Reihenfolge (W kann bei M-Pivots vorkommen!)
        for tf in ["W", "3D", "D", "H4", "H1"]:
            if tf not in by_tf:
                continue

            refs = by_tf[tf]
            f.write(f"{tf}: {len(refs)} Verfeinerung(en)\n")

            for i, ref in enumerate(refs, 1):
                f.write(f"  #{i}:\n")
                f.write(f"    Time: {ref.time}\n")
                f.write(f"    Pivot (Open K2): {ref.pivot_level:.5f}\n")
                f.write(f"    Extreme: {ref.extreme:.5f}\n")
                f.write(f"    Near (Entry): {ref.near:.5f}\n")
                ref_pct = (ref.size / pivot.gap_size * 100) if pivot.gap_size > 0 else 0
                f.write(f"    Size: {ref.size:.5f} ({ref.size * 10000:.1f} pips, {ref_pct:.1f}% von HTF Gap)\n")
            f.write("\n")

    # TRADE DETAILS
    if trade is None:
        f.write("--- KEIN TRADE ---\n")
        f.write("Grund: Gap nicht getriggert oder Entry nicht erreicht oder Trade noch offen\n\n")
    else:
        f.write("--- TRADE DETAILS ---\n\n")

        f.write("VERWENDETE VERFEINERUNG:\n")
        f.write(f"  TF: {trade['refinement_tf']}\n")
        f.write(f"  Time: {trade['refinement_time']}\n")
        f.write(f"  Pivot (Open K2): {trade['refinement_pivot']:.5f}\n")
        f.write(f"  Extreme: {trade['refinement_extreme']:.5f}\n")
        f.write(f"  Near (Entry Level): {trade['refinement_near']:.5f}\n")
        f.write(f"  Size: {trade['refinement_size']:.5f} ({trade['refinement_size'] * 10000:.1f} pips)\n\n")

        f.write("GAP TOUCH:\n")
        f.write(f"  Time: {trade['gap_touch_time']}\n\n")

        f.write("ENTRY:\n")
        f.write(f"  Time: {trade['entry_time']}\n")
        f.write(f"  Price: {trade['entry_price']:.5f}\n")
        f.write(f"  Entry Confirmation: {ENTRY_CONFIRMATION}\n\n")

        f.write("SL/TP:\n")
        f.write(f"  SL Price: {trade['sl_price']:.5f}\n")
        f.write(f"  TP Price: {trade['tp_price']:.5f}\n")
        f.write(f"  RR Ratio: {trade['rr']:.2f}\n\n")

        f.write("EXIT:\n")
        f.write(f"  Time: {trade['exit_time']}\n")
        f.write(f"  Price: {trade['exit_price']:.5f}\n")
        f.write(f"  Reason: {trade['exit_reason'].upper()}\n\n")

        f.write("ERGEBNIS:\n")
        f.write(f"  PnL (Pips): {trade['pnl_pips']:.1f}\n")
        f.write(f"  PnL (R): {trade['pnl_r']:.2f}\n")
        f.write(f"  Status: {'WIN' if trade['pnl_r'] > 0 else 'LOSS'}\n")

    f.write("\n" + "=" * 80 + "\n\n\n")


def run_validation():
    """Führt Trade Validation durch."""
    print("=" * 80)
    print("MODEL 3 - TRADE VALIDATION")
    print("=" * 80)
    print(f"Configs: {len(PIVOT_CONFIGS)} verschiedene Pivots")
    for pair, htf in PIVOT_CONFIGS:
        print(f"  - {pair} {htf}")
    print(f"Zeitraum: {START_DATE} bis {END_DATE}")
    print(f"Pivots pro Config: {PIVOTS_PER_CONFIG}")
    print(f"Entry Confirmation: {ENTRY_CONFIRMATION}")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 80)
    print()

    all_trades = []

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("MODEL 3 - TRADE VALIDATION\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Configs: {len(PIVOT_CONFIGS)} verschiedene Pivots\n")
        for pair, htf in PIVOT_CONFIGS:
            f.write(f"  - {pair} {htf}\n")
        f.write(f"Zeitraum: {START_DATE} bis {END_DATE}\n")
        f.write(f"Pivots pro Config: {PIVOTS_PER_CONFIG}\n")
        f.write(f"Entry Confirmation: {ENTRY_CONFIRMATION}\n")
        f.write("\n\n")

        for pair, htf_tf in PIVOT_CONFIGS:
            print(f"{'='*60}")
            print(f"LADE DATEN: {pair} {htf_tf}")
            print(f"{'='*60}")

            try:
                # Lade HTF-Daten
                htf_df = load_tf_data(htf_tf, pair)

                # Filter Zeitraum
                start_ts = pd.Timestamp(START_DATE, tz="UTC")
                end_ts = pd.Timestamp(END_DATE, tz="UTC")
                htf_df = htf_df[(htf_df["time"] >= start_ts) & (htf_df["time"] <= end_ts)].copy()

                print(f"  {htf_tf} Daten: {len(htf_df)} Kerzen")

                # Finde alle Pivots
                pivots = detect_htf_pivots(htf_df, min_body_pct=5.0)
                print(f"  {len(pivots)} Pivots gefunden")

                if len(pivots) == 0:
                    print(f"  [!] Keine Pivots für {pair} {htf_tf}!")
                    continue

                # Wähle zufällige Pivots
                selected_pivots = random.sample(pivots, min(PIVOTS_PER_CONFIG, len(pivots)))
                print(f"  {len(selected_pivots)} zufällig ausgewählt")

                # Lade LTF-Daten (abhängig von HTF!)
                print(f"  Lade LTF-Daten...")
                ltf_cache = {}

                # Bestimme welche LTFs basierend auf HTF
                if htf_tf == "M":
                    ltf_list = ["W", "3D", "D", "H4", "H1"]
                elif htf_tf == "W":
                    ltf_list = ["3D", "D", "H4", "H1"]
                elif htf_tf == "3D":
                    ltf_list = ["D", "H4", "H1"]
                else:
                    ltf_list = ["H4", "H1"]

                for tf in ltf_list:
                    ltf_df = load_tf_data(tf, pair)
                    ltf_df = ltf_df[(ltf_df["time"] >= start_ts) & (ltf_df["time"] <= end_ts)].copy()
                    ltf_cache[tf] = ltf_df

                # Für jeden Pivot: Verfeinerungen + Trade
                for pivot in selected_pivots:
                    refinements = []

                    for tf in ltf_list:
                        ref_list = detect_refinements(
                            ltf_cache[tf],
                            pivot,
                            tf,
                            max_size_frac=0.2,
                            min_body_pct=5.0
                        )
                        refinements.extend(ref_list)

                    # Sortiere nach Priorität
                    def tf_priority(tf: str) -> int:
                        order = {"W": 0, "3D": 1, "D": 2, "H4": 3, "H1": 4}
                        return order.get(tf, 99)

                    refinements.sort(key=lambda r: tf_priority(r.timeframe))

                    # Simuliere Trade
                    trade = simulate_trade(pair, pivot, refinements, ltf_cache)

                    # Ausgabe
                    format_trade_output(f, pair, htf_tf, pivot, refinements, trade)

                    status = "TRADE" if trade else "NO TRADE"
                    pnl_str = f" ({trade['pnl_r']:.2f}R)" if trade else ""
                    print(f"  -> {pivot.time}: {len(refinements)} Verfeinerungen, {status}{pnl_str}")

                    # Speichere für Summary
                    if trade:
                        all_trades.append({
                            "pair": pair,
                            "htf": htf_tf,
                            "pivot_time": pivot.time,
                            "direction": pivot.direction,
                            "entry_time": trade["entry_time"],
                            "exit_reason": trade["exit_reason"],
                            "pnl_pips": trade["pnl_pips"],
                            "pnl_r": trade["pnl_r"],
                        })

            except Exception as e:
                print(f"  [ERROR] {pair} {htf_tf}: {e}")
                import traceback
                traceback.print_exc()
                continue

    # Summary
    if all_trades:
        df = pd.DataFrame(all_trades)
        summary_file = OUTPUT_DIR / f"trade_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(summary_file, index=False)
        print(f"\nTrade Summary CSV: {summary_file}")

        # Stats
        wins = len(df[df["pnl_r"] > 0])
        losses = len(df[df["pnl_r"] < 0])
        win_rate = (wins / len(df) * 100) if len(df) > 0 else 0
        total_r = df["pnl_r"].sum()

        print(f"\nSTATS:")
        print(f"  Total Trades: {len(df)}")
        print(f"  Wins: {wins}, Losses: {losses}")
        print(f"  Win Rate: {win_rate:.1f}%")
        print(f"  Total R: {total_r:.2f}")

    print()
    print("=" * 80)
    print("VALIDATION ABGESCHLOSSEN")
    print("=" * 80)
    print(f"Output: {OUTPUT_FILE}")
    print()


if __name__ == "__main__":
    run_validation()
