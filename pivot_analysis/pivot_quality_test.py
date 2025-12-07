"""
Pivot Quality Test - Wie gut werden Pivots respektiert?
========================================================

Testet verschiedene TP/SL Kombinationen um herauszufinden:
- Welche Kombination hat beste Win Rate?
- Wie lange dauert es bis TP/SL erreicht wird?
- Wie groß sind durchschnittliche TP/SL Distanzen?

Test-Matrix:
- TP: -1 Fib, -2 Fib, -3 Fib (1x, 2x, 3x Gap Size)
- SL: Extreme, 0.5x Box, 1.0x Box
- Entry: 1H Timeframe, Direct Touch der Gap Box
- Filter: Min 10 pips, Max 250 pips Gap Size
- Body Ratio: 10% (wie aktuell)

Output: Comprehensive Stats pro Kombination
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))


def load_pivot_data(timeframe, pair, data_dir):
    """Load pivot data from Parquet with proper handling."""
    parquet_path = data_dir / "Parquet" / f"All_Pairs_{timeframe}_UTC.parquet"
    
    if not parquet_path.exists():
        raise FileNotFoundError(f"Parquet file not found: {parquet_path}")
    
    df = pd.read_parquet(parquet_path)
    
    # Handle MultiIndex
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()
    
    # Filter for specific pair
    if 'pair' in df.columns:
        df = df[df['pair'] == pair].copy()
    else:
        raise KeyError(f"No 'pair' column found in {timeframe} data")
    
    # Ensure time column
    time_col = None
    for col in df.columns:
        if col.lower() in ['time', 'timestamp', 'date', 'datetime']:
            time_col = col
            break
    
    if time_col:
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col], utc=True)
        elif df[time_col].dt.tz is None:
            df[time_col] = df[time_col].dt.tz_localize('UTC')
        df = df.rename(columns={time_col: 'time'})
    
    return df.sort_values('time').reset_index(drop=True)


def load_1h_data(pair, data_dir):
    """Load 1H data for entry detection."""
    parquet_path = data_dir / "Parquet" / "All_Pairs_H1_UTC.parquet"
    
    if not parquet_path.exists():
        raise FileNotFoundError(f"1H Parquet file not found: {parquet_path}")
    
    df = pd.read_parquet(parquet_path)
    
    if isinstance(df.index, pd.MultiIndex):
        df = df.reset_index()
    
    if 'pair' in df.columns:
        df = df[df['pair'] == pair].copy()
    else:
        raise KeyError(f"No 'pair' column in 1H data")
    
    time_col = None
    for col in df.columns:
        if col.lower() in ['time', 'timestamp', 'date', 'datetime']:
            time_col = col
            break
    
    if time_col:
        if not pd.api.types.is_datetime64_any_dtype(df[time_col]):
            df[time_col] = pd.to_datetime(df[time_col], utc=True)
        elif df[time_col].dt.tz is None:
            df[time_col] = df[time_col].dt.tz_localize('UTC')
        df = df.rename(columns={time_col: 'time'})
    
    return df.sort_values('time').reset_index(drop=True)


def detect_pivots(df, pair, min_body_pct=10.0, min_gap_pips=10.0, max_gap_pips=250.0):
    """
    Detect pivots with same logic as export_pivot_gaps.py
    Returns list of pivot dicts with gap boundaries.
    """
    pivots = []
    
    def pips(price_diff):
        if 'JPY' in pair:
            return abs(price_diff) * 100
        return abs(price_diff) * 10000
    
    def body_pct(row):
        rng = row['high'] - row['low']
        if rng == 0:
            return 0.0
        body = abs(row['close'] - row['open'])
        return (body / rng) * 100.0
    
    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        
        # Body percentage filter
        if body_pct(prev) < min_body_pct or body_pct(curr) < min_body_pct:
            continue
        
        prev_red = prev['close'] < prev['open']
        curr_green = curr['close'] > curr['open']
        prev_green = prev['close'] > prev['open']
        curr_red = curr['close'] < curr['open']
        
        if prev_red and curr_green:
            # Bullish pivot
            pivot_extreme = min(prev['low'], curr['low'])
            
            # Larger box variant
            variant_close_k1 = prev['close']
            variant_open_k2 = curr['open']
            size_close = variant_close_k1 - pivot_extreme
            size_open = variant_open_k2 - pivot_extreme
            
            pivot_level = variant_close_k1 if size_close > size_open else variant_open_k2
            
            gap_high = pivot_level
            gap_low = pivot_extreme
            gap_size_price = gap_high - gap_low
            gap_size_pips = pips(gap_size_price)
            
            if gap_size_pips < min_gap_pips or gap_size_pips > max_gap_pips:
                continue
            
            pivots.append({
                'index': i,
                'time': df.iloc[i]['time'],
                'is_bullish': True,
                'gap_high': gap_high,
                'gap_low': gap_low,
                'gap_size': gap_size_price,
                'gap_size_pips': gap_size_pips,
                'extreme': pivot_extreme,
            })
            
        elif prev_green and curr_red:
            # Bearish pivot
            pivot_extreme = max(prev['high'], curr['high'])
            
            variant_close_k1 = prev['close']
            variant_open_k2 = curr['open']
            size_close = pivot_extreme - variant_close_k1
            size_open = pivot_extreme - variant_open_k2
            
            pivot_level = variant_close_k1 if size_close > size_open else variant_open_k2
            
            gap_low = pivot_level
            gap_high = pivot_extreme
            gap_size_price = gap_high - gap_low
            gap_size_pips = pips(gap_size_price)
            
            if gap_size_pips < min_gap_pips or gap_size_pips > max_gap_pips:
                continue
            
            pivots.append({
                'index': i,
                'time': df.iloc[i]['time'],
                'is_bullish': False,
                'gap_high': gap_high,
                'gap_low': gap_low,
                'gap_size': gap_size_price,
                'gap_size_pips': gap_size_pips,
                'extreme': pivot_extreme,
            })
    
    return pivots


def calculate_tp_sl(pivot, tp_multiplier, sl_multiplier):
    """
    Calculate TP and SL levels based on multipliers.
    
    TP Multiplier: -1, -2, -3 Fib = 1x, 2x, 3x Gap Size from Pivot
    SL Multiplier: 
        - 0 = Extreme (Gap Low for bullish, Gap High for bearish)
        - 0.5 = Extreme - 0.5x Gap Size
        - 1.0 = Extreme - 1.0x Gap Size
    """
    gap_size = pivot['gap_size']
    
    if pivot['is_bullish']:
        # Entry at gap_high (pivot level)
        entry = pivot['gap_high']
        tp = entry + (tp_multiplier * gap_size)
        
        # SL below extreme
        if sl_multiplier == 0:
            sl = pivot['extreme']
        else:
            sl = pivot['extreme'] - (sl_multiplier * gap_size)
    else:
        # Entry at gap_low (pivot level)
        entry = pivot['gap_low']
        tp = entry - (tp_multiplier * gap_size)
        
        # SL above extreme
        if sl_multiplier == 0:
            sl = pivot['extreme']
        else:
            sl = pivot['extreme'] + (sl_multiplier * gap_size)
    
    return entry, tp, sl


def simulate_trade(pivot, entry, tp, sl, h1_data, pair):
    """
    Simulate trade on 1H data.
    Returns: dict with outcome, exit_time, duration, pnl_pips
    """
    # Find first 1H candle after pivot is valid (pivot complete at close of K2)
    valid_from = pivot['time']
    h1_after_pivot = h1_data[h1_data['time'] > valid_from].copy()
    
    if len(h1_after_pivot) == 0:
        return None
    
    entry_time = None
    entry_price = None
    
    # Find entry (first touch of gap box on 1H)
    for idx, row in h1_after_pivot.iterrows():
        if row['low'] <= pivot['gap_high'] and row['high'] >= pivot['gap_low']:
            entry_time = row['time']
            entry_price = entry  # Use calculated entry price
            break
    
    if entry_time is None:
        return None  # Gap never touched
    
    # Simulate from entry
    h1_from_entry = h1_data[h1_data['time'] >= entry_time].copy()
    
    def pips(price_diff):
        if 'JPY' in pair:
            return price_diff * 100
        return price_diff * 10000
    
    for idx, row in h1_from_entry.iterrows():
        if pivot['is_bullish']:
            # Check TP (above entry)
            if row['high'] >= tp:
                pnl = tp - entry_price
                return {
                    'outcome': 'win',
                    'entry_time': entry_time,
                    'exit_time': row['time'],
                    'duration_hours': (row['time'] - entry_time).total_seconds() / 3600,
                    'pnl_pips': pips(pnl),
                }
            # Check SL (below entry)
            if row['low'] <= sl:
                pnl = sl - entry_price
                return {
                    'outcome': 'loss',
                    'entry_time': entry_time,
                    'exit_time': row['time'],
                    'duration_hours': (row['time'] - entry_time).total_seconds() / 3600,
                    'pnl_pips': pips(pnl),
                }
        else:
            # Bearish: TP below, SL above
            if row['low'] <= tp:
                pnl = entry_price - tp
                return {
                    'outcome': 'win',
                    'entry_time': entry_time,
                    'exit_time': row['time'],
                    'duration_hours': (row['time'] - entry_time).total_seconds() / 3600,
                    'pnl_pips': pips(pnl),
                }
            if row['high'] >= sl:
                pnl = entry_price - sl
                return {
                    'outcome': 'loss',
                    'entry_time': entry_time,
                    'exit_time': row['time'],
                    'duration_hours': (row['time'] - entry_time).total_seconds() / 3600,
                    'pnl_pips': pips(pnl),
                }
    
    # No TP/SL hit (end of data)
    return None


def calculate_statistics(trades, tp_multiplier, sl_multiplier):
    """Calculate comprehensive statistics for trade results."""
    if not trades:
        return None
    
    df = pd.DataFrame(trades)
    
    total_trades = len(df)
    wins = df[df['outcome'] == 'win']
    losses = df[df['outcome'] == 'loss']
    
    n_wins = len(wins)
    n_losses = len(losses)
    win_rate = (n_wins / total_trades * 100) if total_trades > 0 else 0
    
    avg_win_pips = wins['pnl_pips'].mean() if len(wins) > 0 else 0
    avg_loss_pips = losses['pnl_pips'].mean() if len(losses) > 0 else 0
    
    avg_tp_pips = wins['tp_pips'].mean() if len(wins) > 0 else 0
    avg_sl_pips = abs(losses['sl_pips'].mean()) if len(losses) > 0 else 0
    
    # RR calculation
    if avg_loss_pips != 0:
        rr_ratio = abs(avg_win_pips / avg_loss_pips)
    else:
        rr_ratio = 0
    
    # Profit Factor
    total_win_pips = wins['pnl_pips'].sum() if len(wins) > 0 else 0
    total_loss_pips = abs(losses['pnl_pips'].sum()) if len(losses) > 0 else 0
    profit_factor = (total_win_pips / total_loss_pips) if total_loss_pips != 0 else 0
    
    # Duration stats
    avg_duration = df['duration_hours'].mean()
    avg_win_duration = wins['duration_hours'].mean() if len(wins) > 0 else 0
    avg_loss_duration = losses['duration_hours'].mean() if len(losses) > 0 else 0
    max_duration = df['duration_hours'].max()
    
    # Consecutive wins/losses
    outcomes = df['outcome'].values
    max_cons_wins = 0
    max_cons_losses = 0
    current_wins = 0
    current_losses = 0
    
    for outcome in outcomes:
        if outcome == 'win':
            current_wins += 1
            current_losses = 0
            max_cons_wins = max(max_cons_wins, current_wins)
        else:
            current_losses += 1
            current_wins = 0
            max_cons_losses = max(max_cons_losses, current_losses)
    
    # Expectancy (average pips per trade)
    expectancy = df['pnl_pips'].mean()
    
    # Max Drawdown (in pips, cumulative)
    cumulative_pips = df['pnl_pips'].cumsum()
    running_max = cumulative_pips.cummax()
    drawdown = cumulative_pips - running_max
    max_dd_pips = drawdown.min()
    
    return {
        'tp_multiplier': tp_multiplier,
        'sl_multiplier': sl_multiplier,
        'total_trades': total_trades,
        'wins': n_wins,
        'losses': n_losses,
        'win_rate': win_rate,
        'avg_win_pips': avg_win_pips,
        'avg_loss_pips': avg_loss_pips,
        'avg_tp_pips': avg_tp_pips,
        'avg_sl_pips': avg_sl_pips,
        'rr_ratio': rr_ratio,
        'profit_factor': profit_factor,
        'expectancy': expectancy,
        'total_pips': df['pnl_pips'].sum(),
        'avg_duration_hours': avg_duration,
        'avg_win_duration_hours': avg_win_duration,
        'avg_loss_duration_hours': avg_loss_duration,
        'max_duration_hours': max_duration,
        'max_consecutive_wins': max_cons_wins,
        'max_consecutive_losses': max_cons_losses,
        'max_dd_pips': max_dd_pips,
    }


def run_pivot_quality_test(timeframes=['3D', 'W', 'M'], pairs=None):
    """
    Run pivot quality test across all combinations.
    """
    if pairs is None:
        pairs = [
            'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD',
            'CADCHF', 'CADJPY', 'CHFJPY',
            'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD',
            'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
            'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD',
            'USDCAD', 'USDCHF', 'USDJPY'
        ]
    
    data_dir = Path(__file__).parent.parent / "data"
    
    # Test combinations
    tp_multipliers = [1.0, 2.0, 3.0]  # -1, -2, -3 Fib
    sl_multipliers = [0.0, 0.5, 1.0]  # Extreme, 0.5x Box, 1.0x Box
    
    sl_labels = {0.0: 'Extreme', 0.5: '0.5x Box', 1.0: '1.0x Box'}
    
    all_results = []
    
    print(f"\n{'='*100}")
    print(f"PIVOT QUALITY TEST")
    print(f"{'='*100}")
    print(f"Timeframes: {', '.join(timeframes)}")
    print(f"Pairs: {len(pairs)}")
    print(f"TP Levels: -1 Fib, -2 Fib, -3 Fib")
    print(f"SL Levels: Extreme, 0.5x Box, 1.0x Box")
    print(f"Entry: 1H Direct Touch")
    print(f"Gap Filter: 10-250 pips")
    print(f"{'='*100}\n")
    
    for tf in timeframes:
        print(f"\n{'='*100}")
        print(f"Processing Timeframe: {tf}")
        print(f"{'='*100}\n")
        
        for tp_mult in tp_multipliers:
            for sl_mult in sl_multipliers:
                print(f"\nTesting: TP={tp_mult}x (Fib -{int(tp_mult)}), SL={sl_labels[sl_mult]}")
                print(f"{'-'*80}")
                
                all_trades = []
                
                for pair in pairs:
                    try:
                        # Load pivot timeframe data
                        pivot_df = load_pivot_data(tf, pair, data_dir)
                        
                        # Load 1H data for entry
                        h1_df = load_1h_data(pair, data_dir)
                        
                        # Detect pivots
                        pivots = detect_pivots(pivot_df, pair)
                        
                        # Simulate trades
                        for pivot in pivots:
                            entry, tp, sl = calculate_tp_sl(pivot, tp_mult, sl_mult)
                            
                            result = simulate_trade(pivot, entry, tp, sl, h1_df, pair)
                            
                            if result:
                                # Add TP/SL distances for stats
                                def pips(price_diff):
                                    if 'JPY' in pair:
                                        return abs(price_diff) * 100
                                    return abs(price_diff) * 10000
                                
                                result['pair'] = pair
                                result['timeframe'] = tf
                                result['tp_pips'] = pips(abs(tp - entry))
                                result['sl_pips'] = -pips(abs(sl - entry))  # Negative for loss
                                all_trades.append(result)
                        
                        print(f"  {pair}: {len([p for p in pivots if p])} pivots processed")
                        
                    except Exception as e:
                        print(f"  {pair}: Error - {e}")
                        continue
                
                # Calculate statistics
                if all_trades:
                    stats = calculate_statistics(all_trades, tp_mult, sl_mult)
                    stats['timeframe'] = tf
                    stats['sl_label'] = sl_labels[sl_mult]
                    all_results.append(stats)
                    
                    print(f"\n  Results:")
                    print(f"    Total Trades: {stats['total_trades']}")
                    print(f"    Win Rate: {stats['win_rate']:.2f}%")
                    print(f"    Avg Win: {stats['avg_win_pips']:.1f} pips")
                    print(f"    Avg Loss: {stats['avg_loss_pips']:.1f} pips")
                    print(f"    RR Ratio: {stats['rr_ratio']:.2f}")
                    print(f"    Profit Factor: {stats['profit_factor']:.2f}")
                    print(f"    Expectancy: {stats['expectancy']:.2f} pips/trade")
                else:
                    print(f"  No trades found for this combination")
    
    # Create results DataFrame
    results_df = pd.DataFrame(all_results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = Path(__file__).parent / "results"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"pivot_quality_test_{timestamp}.csv"
    results_df.to_csv(output_file, index=False)
    
    print(f"\n{'='*100}")
    print(f"RESULTS SAVED: {output_file}")
    print(f"{'='*100}\n")
    
    # Print summary
    print(f"\n{'='*100}")
    print(f"SUMMARY - TOP 5 BY WIN RATE")
    print(f"{'='*100}\n")
    
    top_5 = results_df.nlargest(5, 'win_rate')
    for idx, row in top_5.iterrows():
        print(f"{row['timeframe']} | TP={row['tp_multiplier']}x | SL={row['sl_label']}")
        print(f"  Win Rate: {row['win_rate']:.2f}% | RR: {row['rr_ratio']:.2f} | PF: {row['profit_factor']:.2f}")
        print(f"  Trades: {row['total_trades']} | Expectancy: {row['expectancy']:.2f} pips")
        print(f"  Avg Duration: {row['avg_duration_hours']:.1f}h | Max DD: {row['max_dd_pips']:.1f} pips\n")
    
    return results_df


if __name__ == '__main__':
    results = run_pivot_quality_test()
    print("\nDone!")
