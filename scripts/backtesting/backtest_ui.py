#!/usr/bin/env python3
"""
Interactive Backtest Configuration UI
Ermöglicht einfache Anpassung von Backtest-Parametern
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from backtest_modelx import BacktestEngine
import pandas as pd
from datetime import datetime

# All 28 major Forex pairs
ALL_PAIRS = [
    'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD',
    'CADCHF', 'CADJPY', 'CHFJPY',
    'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD',
    'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
    'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD',
    'USDCAD', 'USDCHF', 'USDJPY'
]

ALL_TIMEFRAMES = ['H1', 'H4', 'D', '3D', 'W', 'M']


def print_header(title):
    """Druckt formatierten Header"""
    print("\n" + "="*80)
    print(title.center(80))
    print("="*80)


def select_pairs():
    """Interaktive Pair-Auswahl"""
    print_header("📊 PAIR SELECTION")
    
    print("\nOptions:")
    print("  1. All pairs (28)")
    print("  2. Major pairs only (7)")
    print("  3. AUD crosses (7)")
    print("  4. EUR crosses (7)")
    print("  5. GBP crosses (7)")
    print("  6. USD crosses (7)")
    print("  7. Custom selection")
    
    choice = input("\nSelect option [1-7] (default: 1): ").strip() or '1'
    
    if choice == '1':
        return ALL_PAIRS
    elif choice == '2':
        return ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'USDCHF', 'NZDUSD']
    elif choice == '3':
        return [p for p in ALL_PAIRS if p.startswith('AUD')]
    elif choice == '4':
        return [p for p in ALL_PAIRS if p.startswith('EUR')]
    elif choice == '5':
        return [p for p in ALL_PAIRS if p.startswith('GBP')]
    elif choice == '6':
        return [p for p in ALL_PAIRS if p.startswith('USD')]
    elif choice == '7':
        print("\nAvailable pairs:")
        for i, pair in enumerate(ALL_PAIRS, 1):
            print(f"  {i:2d}. {pair}", end="   ")
            if i % 4 == 0:
                print()
        print()
        
        selection = input("\nEnter pair numbers (comma-separated, e.g., 1,5,10): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected = [ALL_PAIRS[i] for i in indices if 0 <= i < len(ALL_PAIRS)]
            return selected if selected else ALL_PAIRS
        except:
            print("Invalid selection, using all pairs")
            return ALL_PAIRS
    else:
        return ALL_PAIRS


def select_timeframes():
    """Interaktive Timeframe-Auswahl"""
    print_header("⏰ TIMEFRAME SELECTION")
    
    print("\nOptions:")
    print("  1. 3D, W, M (default)")
    print("  2. H1, H4 (intraday)")
    print("  3. D, 3D, W, M (swing)")
    print("  4. All timeframes")
    print("  5. Custom selection")
    
    choice = input("\nSelect option [1-5] (default: 1): ").strip() or '1'
    
    if choice == '1':
        return ['3D', 'W', 'M']
    elif choice == '2':
        return ['H1', 'H4']
    elif choice == '3':
        return ['D', '3D', 'W', 'M']
    elif choice == '4':
        return ALL_TIMEFRAMES
    elif choice == '5':
        print("\nAvailable timeframes:")
        for i, tf in enumerate(ALL_TIMEFRAMES, 1):
            print(f"  {i}. {tf}")
        
        selection = input("\nEnter timeframe numbers (comma-separated, e.g., 1,3,5): ").strip()
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected = [ALL_TIMEFRAMES[i] for i in indices if 0 <= i < len(ALL_TIMEFRAMES)]
            return selected if selected else ['3D', 'W', 'M']
        except:
            print("Invalid selection, using default")
            return ['3D', 'W', 'M']
    else:
        return ['3D', 'W', 'M']


def select_entry_type():
    """Interaktive Entry Type Auswahl"""
    print_header("🎯 ENTRY TYPE")
    
    print("\nOptions:")
    print("  1. direct_touch (enter immediately when gap touched)")
    print("  2. retest (wait for pullback and retest)")
    print("  3. candle_close (enter after candle closes in gap)")
    
    choice = input("\nSelect option [1-3] (default: 1): ").strip() or '1'
    
    if choice == '2':
        return 'retest'
    elif choice == '3':
        return 'candle_close'
    else:
        return 'direct_touch'


def select_exit_type():
    """Interaktive Exit Type Auswahl"""
    print_header("🚪 EXIT TYPE")
    
    print("\nOptions:")
    print("  1. fixed (fixed TP/SL levels)")
    print("  2. trailing (trailing stop)")
    print("  3. breakeven (move SL to BE after X%)")
    
    choice = input("\nSelect option [1-3] (default: 1): ").strip() or '1'
    
    if choice == '2':
        return 'trailing'
    elif choice == '3':
        return 'breakeven'
    else:
        return 'fixed'


def confirm_and_run():
    """Zeigt Konfiguration und bestätigt"""
    print_header("✅ CONFIGURATION SUMMARY")
    
    print(f"\nPairs:       {len(pairs)} selected ({', '.join(pairs[:5])}{'...' if len(pairs) > 5 else ''})")
    print(f"Timeframes:  {', '.join(timeframes)}")
    print(f"Entry Type:  {entry_type}")
    print(f"Exit Type:   {exit_type}")
    
    confirm = input("\nRun backtest with this configuration? [Y/n]: ").strip().lower()
    
    return confirm != 'n'


def run_backtest(pairs, timeframes, entry_type, exit_type):
    """Führt Backtest aus"""
    print_header("🚀 RUNNING BACKTEST")
    
    RESULTS_DIR = Path(__file__).parent.parent.parent / 'results'
    TRADES_DIR = RESULTS_DIR / 'trades'
    REPORTS_DIR = RESULTS_DIR / 'reports'
    
    TRADES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\nProcessing {len(pairs)} pairs across {len(timeframes)} timeframes...")
    print("="*80)
    
    all_results = []
    all_trades_dfs = []
    
    for i, pair in enumerate(pairs, 1):
        print(f"\n[{i}/{len(pairs)}] Backtesting {pair}...")
        
        try:
            engine = BacktestEngine(entry_type=entry_type, exit_type=exit_type)
            results_df = engine.run_backtest(pairs=[pair], timeframes=timeframes)
            stats = engine.get_performance_stats()
            
            if 'error' not in stats:
                stats['pair'] = pair
                all_results.append(stats)
                
                results_df = results_df.sort_values('entry_time')
                output_path = TRADES_DIR / f'{pair}.csv'
                results_df.to_csv(output_path, index=False)
                all_trades_dfs.append(results_df)
                
                print(f"  ✓ {stats['total_trades']} trades, {stats['total_return_pct']:.1f}%, Sharpe: {stats['sharpe_ratio']:.2f}")
            else:
                print(f"  ⚠️  {stats['error']}")
        
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            continue
    
    # Combine and save
    if all_trades_dfs:
        print("\n" + "="*80)
        print("COMBINING TRADES CHRONOLOGICALLY...")
        print("="*80)
        
        all_trades_combined = pd.concat(all_trades_dfs, ignore_index=True)
        all_trades_combined = all_trades_combined.sort_values('entry_time')
        
        combined_path = TRADES_DIR / 'all_trades_chronological.csv'
        all_trades_combined.to_csv(combined_path, index=False)
        print(f"✓ Saved {len(all_trades_combined):,} trades")
        
        # Calculate overall stats
        from backtest_modelx import Trade
        all_trades = []
        
        for _, row in all_trades_combined.iterrows():
            trade = Trade(
                trade_id=row['trade_id'],
                pair=row['pair'],
                timeframe=row['timeframe'],
                direction=row['direction'],
                entry_time=pd.Timestamp(row['entry_time']),
                entry_price=row['entry_price'],
                tp_price=row['tp_price'],
                sl_price=row['sl_price'],
                gap_high=row['gap_high'],
                gap_low=row['gap_low'],
                pivot_generated_time=pd.Timestamp(row['pivot_generated_time'])
            )
            trade.exit_time = pd.Timestamp(row['exit_time']) if pd.notna(row['exit_time']) else None
            trade.exit_price = row['exit_price'] if pd.notna(row['exit_price']) else None
            trade.exit_reason = row['exit_reason'] if pd.notna(row['exit_reason']) else None
            trade.pnl_pips = row['pnl_pips'] if pd.notna(row['pnl_pips']) else None
            trade.pnl_r = row['pnl_r'] if pd.notna(row['pnl_r']) else None
            trade.pnl_percent = row['pnl_percent'] if pd.notna(row['pnl_percent']) else None
            trade.status = row['status']
            all_trades.append(trade)
        
        overall_engine = BacktestEngine()
        overall_engine.trades = all_trades
        overall_stats = overall_engine.get_performance_stats()
        
        summary_df = pd.DataFrame(all_results).sort_values('total_return_pct', ascending=False)
        
        # Display results
        print("\n" + "="*80)
        print("OVERALL STATS")
        print("="*80)
        print(f"Total Trades:    {overall_stats['total_trades']}")
        print(f"Win Rate:        {overall_stats['win_rate']:.2f}%")
        print(f"Total Return:    {overall_stats['total_return_pct']:.2f}%")
        print(f"Sharpe Ratio:    {overall_stats['sharpe_ratio']:.3f}")
        print(f"Max Drawdown:    {overall_stats['max_drawdown_pct']:.2f}%")
        print("="*80)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORTS_DIR / f'backtest_{timestamp}.txt'
        
        with open(report_path, 'w') as f:
            f.write("="*80 + "\n")
            f.write("MODEL X BACKTEST REPORT\n")
            f.write("="*80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Pairs: {', '.join(pairs)}\n")
            f.write(f"Timeframes: {', '.join(timeframes)}\n")
            f.write(f"Entry Type: {entry_type}\n")
            f.write(f"Exit Type: {exit_type}\n")
            f.write("="*80 + "\n\n")
            f.write("OVERALL STATS\n")
            f.write("="*80 + "\n")
            f.write(f"Total Trades:    {overall_stats['total_trades']}\n")
            f.write(f"Win Rate:        {overall_stats['win_rate']:.2f}%\n")
            f.write(f"Total Return:    {overall_stats['total_return_pct']:.2f}%\n")
            f.write(f"Sharpe Ratio:    {overall_stats['sharpe_ratio']:.3f}\n")
            f.write(f"Max Drawdown:    {overall_stats['max_drawdown_pct']:.2f}%\n")
            f.write("="*80 + "\n\n")
            f.write("TOP PERFORMERS\n")
            f.write("="*80 + "\n")
            for _, row in summary_df.head(10).iterrows():
                f.write(f"\n{row['pair']}: {row['total_return_pct']:.2f}% ({int(row['total_trades'])} trades)\n")
        
        print(f"\n✓ Report saved: {report_path}")
        print(f"✓ View results: python3 scripts/backtesting/view_results.py")


# Main interactive flow
if __name__ == '__main__':
    print("\n" + "="*80)
    print("MODEL X BACKTEST - INTERACTIVE CONFIGURATION".center(80))
    print("="*80)
    
    pairs = select_pairs()
    timeframes = select_timeframes()
    entry_type = select_entry_type()
    exit_type = select_exit_type()
    
    if confirm_and_run():
        run_backtest(pairs, timeframes, entry_type, exit_type)
    else:
        print("\nBacktest cancelled.")
