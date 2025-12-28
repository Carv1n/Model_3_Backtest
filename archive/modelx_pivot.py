import pandas as pd
import numpy as np
from typing import List, Dict

# --- Model X Pivot-Logik ---
# Diese Datei enthält die Kernfunktionen zur Pivot-Erkennung und Entry/Exit-Logik für Model X.
# Es werden ausschließlich die UTC Parquet Dateien verwendet (data/UTC/).

class Pivot:
    def __init__(self, timeframe, pair, pivot_level, pivot_extreme, pivot_near, is_bullish, is_valid, entry_zone, sl_level, tp_level, index):
        self.timeframe = timeframe
        self.pair = pair
        self.pivot_level = pivot_level
        self.pivot_extreme = pivot_extreme
        self.pivot_near = pivot_near
        self.is_bullish = is_bullish
        self.is_valid = is_valid
        self.entry_zone = entry_zone
        self.sl_level = sl_level
        self.tp_level = tp_level
        self.index = index  # Index der Pivot-Kerze

class Trade:
    def __init__(self, pair, entry_idx, entry_price, sl, tp, direction, result=None, exit_idx=None, exit_price=None):
        self.pair = pair
        self.entry_idx = entry_idx
        self.entry_price = entry_price
        self.sl = sl
        self.tp = tp
        self.direction = direction  # 'long' oder 'short'
        self.result = result  # 'win', 'loss', 'open'
        self.exit_idx = exit_idx
        self.exit_price = exit_price


def load_data(timeframe: str) -> pd.DataFrame:
    """Lädt die Parquet-Datei für das gegebene Timeframe (z.B. 'D', 'H1', 'H4', 'W', 'M', '3D')."""
    from pathlib import Path
    base_path = Path(__file__).parent.parent.parent.parent / "Data" / "Chartdata" / "Forex" / "Parquet"
    fname = base_path / f"All_Pairs_{timeframe}_UTC.parquet"
    return pd.read_parquet(fname)
def detect_pivots(df: pd.DataFrame, timeframe: str, pair: str) -> List[Pivot]:
    """Erkennt alle validen Pivots für ein Währungspaar in einem DataFrame."""
    pivots = []
    pair_df = df[df['pair'] == pair].reset_index(drop=True)
    for i in range(1, len(pair_df)):
        k1 = pair_df.iloc[i-1]
        k2 = pair_df.iloc[i]
        # Doji-Filter
        def is_doji(row):
            body = abs(row['close'] - row['open'])
            rng = row['high'] - row['low']
            return rng > 0 and (body / rng) < 0.05
        if is_doji(k1) or is_doji(k2):
            continue
        # Pivot-Erkennung
        if k1['close'] < k1['open'] and k2['close'] > k2['open']:
            is_bullish = True
        elif k1['close'] > k1['open'] and k2['close'] < k2['open']:
            is_bullish = False
        else:
            continue
        # Versatz-Handling
        close_k1 = k1['close']
        open_k2 = k2['open']
        if is_bullish:
            extreme = min(k1['low'], k2['low'])
            near = max(k1['low'], k2['low'])
        else:
            extreme = max(k1['high'], k2['high'])
            near = min(k1['high'], k2['high'])
        gap_a = abs(close_k1 - extreme)
        gap_b = abs(open_k2 - extreme)
        # Größere Box wählen
        if gap_a >= gap_b:
            pivot = close_k1
            gap = gap_a
        else:
            pivot = open_k2
            gap = gap_b
        # Versatz-Filter
        if min(gap_a, gap_b) > 0 and (max(gap_a, gap_b) / min(gap_a, gap_b)) >= 2:
            continue
        # Entry/SL/TP
        if is_bullish:
            sl = extreme - 1.5 * gap
            tp = pivot + 3.0 * gap
        else:
            sl = extreme + 1.5 * gap
            tp = pivot - 3.0 * gap
        pivots.append(Pivot(
            timeframe, pair, pivot, extreme, near, is_bullish, True, (pivot, extreme), sl, tp, i
        ))
    return pivots

def run_backtest(df: pd.DataFrame, pivots: List[Pivot], pair: str) -> List[Trade]:
    """Führt den Backtest für ein Paar und eine Liste von Pivots aus (direkter Touch, SL 1.5, TP -3)."""
    trades = []
    pair_df = df[df['pair'] == pair].reset_index(drop=True)
    for pivot in pivots:
        # Suche nach Entry nach Pivot-Entstehung
        for j in range(pivot.index+1, len(pair_df)):
            row = pair_df.iloc[j]
            # Entry-Logik: Preis berührt die Pivot Gap (zwischen pivot_level und pivot_extreme)
            if pivot.is_bullish:
                gap_top = max(pivot.pivot_level, pivot.pivot_extreme)
                gap_bot = min(pivot.pivot_level, pivot.pivot_extreme)
                in_gap = (row['low'] <= gap_top) and (row['high'] >= gap_bot)
                entry_price = gap_bot if row['low'] <= gap_bot else gap_top if row['high'] >= gap_top else row['open']
                sl = pivot.sl_level
                tp = pivot.tp_level
            else:
                gap_top = max(pivot.pivot_level, pivot.pivot_extreme)
                gap_bot = min(pivot.pivot_level, pivot.pivot_extreme)
                in_gap = (row['high'] >= gap_bot) and (row['low'] <= gap_top)
                entry_price = gap_top if row['high'] >= gap_top else gap_bot if row['low'] <= gap_bot else row['open']
                sl = pivot.sl_level
                tp = pivot.tp_level
            if in_gap:
                # Trade ausführen, bis SL oder TP erreicht wird
                direction = 'long' if pivot.is_bullish else 'short'
                for k in range(j+1, len(pair_df)):
                    r = pair_df.iloc[k]
                    if direction == 'long':
                        if r['low'] <= sl:
                            trades.append(Trade(pair, j, entry_price, sl, tp, direction, 'loss', k, sl))
                            break
                        if r['high'] >= tp:
                            trades.append(Trade(pair, j, entry_price, sl, tp, direction, 'win', k, tp))
                            break
                    else:
                        if r['high'] >= sl:
                            trades.append(Trade(pair, j, entry_price, sl, tp, direction, 'loss', k, sl))
                            break
                        if r['low'] <= tp:
                            trades.append(Trade(pair, j, entry_price, sl, tp, direction, 'win', k, tp))
                            break
                break  # Nur ein Trade pro Pivot
    return trades

# Beispiel für die Anwendung:
if __name__ == "__main__":
    df = load_data('D')
    pairs = df['pair'].unique()
    all_results = {}
    for pair in pairs:
        pivots = detect_pivots(df, 'D', pair)
        trades = run_backtest(df, pivots, pair)
        all_results[pair] = trades
        print(f"{pair}: {len(trades)} Trades, {sum(1 for t in trades if t.result == 'win')} Wins, {sum(1 for t in trades if t.result == 'loss')} Losses")
    # Optional: Ergebnisse speichern oder weiter auswerten
