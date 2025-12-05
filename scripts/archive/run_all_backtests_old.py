"""
Run comprehensive backtest across all pairs and timeframes.
Each pair is backtested individually for each timeframe.
"""

import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from backtest_modelx import BacktestEngine, print_performance_stats

# All 28 major Forex pairs
ALL_PAIRS = [
    'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD',
    'CADCHF', 'CADJPY', 'CHFJPY',
    'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD',
    'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
    'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD',
    'USDCAD', 'USDCHF', 'USDJPY'
]

TIMEFRAMES = ['3D', 'W', 'M']
RESULTS_DIR = Path(__file__).parent.parent / 'results'
RESULTS_DIR.mkdir(exist_ok=True)

print("="*80)
print("MODEL X - COMPREHENSIVE BACKTEST")
print("="*80)
print(f"Total Pairs: {len(ALL_PAIRS)}")
print(f"Timeframes: {', '.join(TIMEFRAMES)}")
print(f"Results Directory: {RESULTS_DIR}")
print("="*80)

# Run backtest for each pair individually
all_results = []

for i, pair in enumerate(ALL_PAIRS, 1):
    print(f"\n[{i}/{len(ALL_PAIRS)}] Backtesting {pair}...")
    
    try:
        # Create engine
        engine = BacktestEngine(entry_type='direct_touch', exit_type='fixed')
        
        # Run backtest
        results_df = engine.run_backtest(
            pairs=[pair],
            timeframes=TIMEFRAMES
        )
        
        # Get stats
        stats = engine.get_performance_stats()
        
        if 'error' not in stats:
            stats['pair'] = pair
            all_results.append(stats)
            
            # Save individual results
            output_path = RESULTS_DIR / f'backtest_{pair}.csv'
            results_df.to_csv(output_path, index=False)
            
            print(f"  ✓ {stats['total_trades']} trades, "
                  f"{stats['total_return_pct']:.1f}%, "
                  f"Sharpe: {stats['sharpe_ratio']:.2f}")
        else:
            print(f"  ⚠️  {stats['error']}")
    
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        continue

# Save per-pair summary (stats only)
if all_results:
    summary_df = pd.DataFrame(all_results)
    summary_df = summary_df.sort_values('total_return_pct', ascending=False)
    
    # Save per-pair summary (stats only, no trade data)
    summary_path = RESULTS_DIR / 'backtest_summary_by_pair.csv'
    summary_df.to_csv(summary_path, index=False)
    
    # Calculate overall stats by combining all trades
    print("\n" + "="*80)
    print("CALCULATING OVERALL STATS (ALL PAIRS COMBINED)...")
    print("="*80)
    
    all_trades = []
    for pair in ALL_PAIRS:
        result_file = RESULTS_DIR / f'backtest_{pair}.csv'
        if result_file.exists():
            df = pd.read_csv(result_file)
            if len(df) > 0:
                # Create Trade objects
                from backtest_modelx import Trade
                for _, row in df.iterrows():
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
    
    # Calculate overall stats
    overall_engine = BacktestEngine()
    overall_engine.trades = all_trades
    overall_stats = overall_engine.get_performance_stats()
    
    # Save overall stats
    overall_stats_path = RESULTS_DIR / 'backtest_overall_stats.csv'
    overall_df = pd.DataFrame([overall_stats])
    overall_df.to_csv(overall_stats_path, index=False)
    
    # Display overall stats
    print("\n" + "="*80)
    print("OVERALL STATS (ALL PAIRS COMBINED)")
    print("="*80)
    print(f"Total Trades:            {overall_stats['total_trades']}")
    print(f"Win Rate:                {overall_stats['win_rate']:.2f}%")
    print(f"Expectancy (R):          {overall_stats['expectancy_r']:.6f}R")
    print(f"Total Return:            {overall_stats['total_return_pct']:.2f}%")
    print(f"Return/Year:             {overall_stats['return_per_year_pct']:.2f}%")
    print(f"Sharpe Ratio:            {overall_stats['sharpe_ratio']:.3f}")
    print(f"Profit Factor:           {overall_stats['profit_factor']:.3f}")
    print(f"Max Drawdown:            {overall_stats['max_drawdown_pct']:.2f}%")
    print("="*80)
    
    # Display per-pair summary
    display_cols = ['pair', 'total_trades', 'win_rate', 'expectancy_r', 'total_return_pct', 
                   'return_per_year_pct', 'sharpe_ratio', 'max_drawdown_pct', 'profit_factor',
                   'max_consecutive_losses']
    
    print("\n" + "="*80)
    print("SUMMARY BY PAIR (Top 10 by Return %)")
    print("="*80)
    print(summary_df[display_cols].head(10).to_string(index=False))
    print(f"\n✓ Overall stats saved to {overall_stats_path}")
    print(f"✓ Per-pair summary saved to {summary_path} (stats only, {len(summary_df.columns)} columns)")
    print("="*80)

# Save formatted text report with timestamp
from datetime import datetime
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
report_path = RESULTS_DIR / f'backtest_report_{timestamp}.txt'

with open(report_path, 'w') as f:
    f.write("="*80 + "\n")
    f.write("MODEL X BACKTEST REPORT\n")
    f.write("="*80 + "\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Total Pairs: {len(ALL_PAIRS)}\n")
    f.write(f"Timeframes: {', '.join(TIMEFRAMES)}\n")
    f.write(f"Entry Type: direct_touch\n")
    f.write(f"Exit Type: fixed\n")
    f.write("="*80 + "\n\n")
    
    f.write("="*80 + "\n")
    f.write("OVERALL STATS (ALL PAIRS COMBINED)\n")
    f.write("="*80 + "\n")
    f.write(f"Total Trades:            {overall_stats['total_trades']}\n")
    f.write(f"Win Rate:                {overall_stats['win_rate']:.2f}%\n")
    f.write(f"Expectancy (R):          {overall_stats['expectancy_r']:.6f}R\n")
    f.write(f"Total Return:            {overall_stats['total_return_pct']:.2f}%\n")
    f.write(f"Return/Year:             {overall_stats['return_per_year_pct']:.2f}%\n")
    f.write(f"Sharpe Ratio:            {overall_stats['sharpe_ratio']:.3f}\n")
    f.write(f"Profit Factor:           {overall_stats['profit_factor']:.3f}\n")
    f.write(f"Max Drawdown:            {overall_stats['max_drawdown_pct']:.2f}%\n")
    f.write("="*80 + "\n\n")
    
    f.write("="*80 + "\n")
    f.write("TOP 10 PERFORMERS (by Return %)\n")
    f.write("="*80 + "\n")
    top_10 = summary_df.head(10)
    for idx, row in top_10.iterrows():
        f.write(f"\n{row['pair']}:\n")
        f.write(f"  Total Trades:        {int(row['total_trades'])}\n")
        f.write(f"  Win Rate:            {row['win_rate']:.2f}%\n")
        f.write(f"  Expectancy:          {row['expectancy_r']:.6f}R\n")
        f.write(f"  Total Return:        {row['total_return_pct']:.2f}%\n")
        f.write(f"  Return/Year:         {row['return_per_year_pct']:.2f}%\n")
        f.write(f"  Sharpe Ratio:        {row['sharpe_ratio']:.3f}\n")
        f.write(f"  Profit Factor:       {row['profit_factor']:.3f}\n")
        f.write(f"  Max Drawdown:        {row['max_drawdown_pct']:.2f}%\n")
        f.write(f"  Max Consec. Losses:  {int(row['max_consecutive_losses'])}\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("BOTTOM 5 PERFORMERS (by Return %)\n")
    f.write("="*80 + "\n")
    bottom_5 = summary_df.tail(5)
    for idx, row in bottom_5.iterrows():
        f.write(f"\n{row['pair']}:\n")
        f.write(f"  Total Trades:        {int(row['total_trades'])}\n")
        f.write(f"  Win Rate:            {row['win_rate']:.2f}%\n")
        f.write(f"  Total Return:        {row['total_return_pct']:.2f}%\n")
        f.write(f"  Sharpe Ratio:        {row['sharpe_ratio']:.3f}\n")
    
    f.write("\n" + "="*80 + "\n")
    f.write("ALL PAIRS SUMMARY\n")
    f.write("="*80 + "\n")
    f.write(summary_df[display_cols].to_string(index=False))
    f.write("\n" + "="*80 + "\n")

print("\n✓ All backtests complete!")
print(f"✓ Individual trade data: {RESULTS_DIR / 'backtest_*.csv'} (28 files)")
print(f"✓ Overall stats: {RESULTS_DIR / 'backtest_overall_stats.csv'}")
print(f"✓ Per-pair summary: {RESULTS_DIR / 'backtest_summary_by_pair.csv'}")
print(f"✓ Formatted report: {report_path}")
