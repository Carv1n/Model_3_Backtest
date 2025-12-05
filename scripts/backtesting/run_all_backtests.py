"""
Run comprehensive backtest across all pairs and timeframes.
Trades are sorted chronologically by entry_time.
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from backtest_modelx import BacktestEngine

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
RESULTS_DIR = Path(__file__).parent.parent.parent / 'results'
TRADES_DIR = RESULTS_DIR / 'trades'
REPORTS_DIR = RESULTS_DIR / 'reports'

# Create directories
TRADES_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

print("="*80)
print("MODEL X - COMPREHENSIVE BACKTEST")
print("="*80)
print(f"Total Pairs: {len(ALL_PAIRS)}")
print(f"Timeframes: {', '.join(TIMEFRAMES)}")
print(f"Trades Directory: {TRADES_DIR}")
print(f"Reports Directory: {REPORTS_DIR}")
print("="*80)

# Run backtest for each pair individually
all_results = []
all_trades_dfs = []

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
            
            # Sort trades by entry_time (chronological)
            results_df = results_df.sort_values('entry_time')
            
            # Save individual pair results
            output_path = TRADES_DIR / f'{pair}.csv'
            results_df.to_csv(output_path, index=False)
            
            # Collect for combined file
            all_trades_dfs.append(results_df)
            
            print(f"  ✓ {stats['total_trades']} trades, "
                  f"{stats['total_return_pct']:.1f}%, "
                  f"Sharpe: {stats['sharpe_ratio']:.2f}")
        else:
            print(f"  ⚠️  {stats['error']}")
    
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        continue

# Combine all trades and sort chronologically
if all_trades_dfs:
    print("\n" + "="*80)
    print("COMBINING ALL TRADES CHRONOLOGICALLY...")
    print("="*80)
    
    all_trades_combined = pd.concat(all_trades_dfs, ignore_index=True)
    all_trades_combined = all_trades_combined.sort_values('entry_time')
    
    # Save combined chronological trades
    combined_path = TRADES_DIR / 'all_trades_chronological.csv'
    all_trades_combined.to_csv(combined_path, index=False)
    print(f"✓ Saved {len(all_trades_combined):,} trades sorted by entry_time")
    print(f"  First trade: {all_trades_combined.iloc[0]['entry_time']}")
    print(f"  Last trade:  {all_trades_combined.iloc[-1]['entry_time']}")

# Calculate overall stats
if all_results:
    print("\n" + "="*80)
    print("CALCULATING OVERALL STATS...")
    print("="*80)
    
    all_trades = []
    from backtest_modelx import Trade
    
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
    
    # Calculate overall stats
    overall_engine = BacktestEngine()
    overall_engine.trades = all_trades
    overall_stats = overall_engine.get_performance_stats()
    
    # Create summary by pair
    summary_df = pd.DataFrame(all_results)
    summary_df = summary_df.sort_values('total_return_pct', ascending=False)
    
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
    print(f"Max Consec. Wins:        {overall_stats['max_consecutive_wins']}")
    print(f"Max Consec. Losses:      {overall_stats['max_consecutive_losses']}")
    print(f"Avg Trades/Month:        {overall_stats['avg_trades_per_month']:.1f}")
    print(f"Max Concurrent Pos:      {overall_stats['concurrent_positions_max']:.0f}")
    print(f"Median Concurrent Pos:   {overall_stats['concurrent_positions_median']:.1f}")
    print("="*80)
    
    # Display per-pair summary
    display_cols = ['pair', 'total_trades', 'win_rate', 'expectancy_r', 'total_return_pct', 
                   'return_per_year_pct', 'sharpe_ratio', 'max_drawdown_pct', 'profit_factor',
                   'max_consecutive_wins', 'max_consecutive_losses', 'avg_trades_per_month']
    
    print("\n" + "="*80)
    print("TOP 10 PERFORMERS (by Return %)")
    print("="*80)
    print(summary_df[display_cols].head(10).to_string(index=False))
    print("="*80)
    
    # Save formatted text report with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f'backtest_{timestamp}.txt'
    
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
        f.write("="*80 + "\n\n")
        
        f.write("--- BASIC STATS ---\n")
        f.write(f"Total Trades:            {overall_stats['total_trades']}\n")
        f.write(f"Winning Trades:          {overall_stats['winning_trades']} ({overall_stats['win_rate']:.2f}%)\n")
        f.write(f"Losing Trades:           {overall_stats['losing_trades']}\n")
        f.write(f"Win Rate:                {overall_stats['win_rate']:.2f}%\n")
        
        f.write(f"\n--- R-MULTIPLE PERFORMANCE ---\n")
        f.write(f"Total R:                 {overall_stats['total_r']:.2f}R\n")
        f.write(f"Expectancy:              {overall_stats['expectancy_r']:.6f}R per trade\n")
        f.write(f"Avg Win:                 {overall_stats['avg_win_r']:.2f}R\n")
        f.write(f"Avg Loss:                {overall_stats['avg_loss_r']:.2f}R\n")
        f.write(f"Win/Loss Ratio:          {overall_stats['win_loss_ratio']:.2f}\n")
        f.write(f"Max Drawdown:            {overall_stats['max_drawdown_r']:.2f}R\n")
        
        f.write(f"\n--- ACCOUNT % (assuming {overall_stats.get('risk_per_trade', 1.0)}% risk/trade) ---\n")
        f.write(f"Total Return:            {overall_stats['total_return_pct']:.2f}%\n")
        f.write(f"Return/Month:            {overall_stats['return_per_month_pct']:.2f}%\n")
        f.write(f"Return/Year:             {overall_stats['return_per_year_pct']:.2f}%\n")
        f.write(f"Max Drawdown:            {overall_stats['max_drawdown_pct']:.2f}%\n")
        
        f.write(f"\n--- RISK METRICS ---\n")
        f.write(f"Profit Factor:           {overall_stats['profit_factor']:.3f}\n")
        f.write(f"Sharpe Ratio:            {overall_stats['sharpe_ratio']:.3f}\n")
        f.write(f"Sortino Ratio:           {overall_stats['sortino_ratio']:.3f}\n")
        f.write(f"Calmar Ratio:            {overall_stats['calmar_ratio']:.3f}\n")
        f.write(f"Recovery Factor:         {overall_stats['recovery_factor']:.3f}\n")
        
        f.write(f"\n--- CONSISTENCY METRICS ---\n")
        f.write(f"Max Consecutive Wins:    {overall_stats['max_consecutive_wins']}\n")
        f.write(f"Max Consecutive Losses:  {overall_stats['max_consecutive_losses']}\n")
        f.write(f"Avg Trade Duration:      {overall_stats['avg_trade_duration_days']:.1f} days\n")
        f.write(f"R-Squared:               {overall_stats['r_squared']:.3f}\n")
        
        f.write(f"\n--- TRADE FREQUENCY ---\n")
        f.write(f"Total Days:              {overall_stats['total_days']:.0f}\n")
        f.write(f"Total Years:             {overall_stats['total_years']:.2f}\n")
        f.write(f"Trades/Year (calc):      {overall_stats['trades_per_year']:.1f}\n")
        f.write(f"Avg Trades/Month:        {overall_stats['avg_trades_per_month']:.1f}\n")
        f.write(f"Max Trades in Month:     {overall_stats['max_trades_in_month']:.0f}\n")
        f.write(f"Min Trades in Month:     {overall_stats['min_trades_in_month']:.0f}\n")
        f.write(f"Avg Trades/Year:         {overall_stats['avg_trades_per_year_actual']:.1f}\n")
        
        f.write(f"\n--- CONCURRENT POSITIONS ---\n")
        f.write(f"Max Concurrent:          {overall_stats['concurrent_positions_max']:.0f}\n")
        f.write(f"Median Concurrent:       {overall_stats['concurrent_positions_median']:.1f}\n")
        f.write(f"Avg Concurrent:          {overall_stats['concurrent_positions_avg']:.2f}\n")
        
        f.write("\n" + "="*80 + "\n\n")
        
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
            f.write(f"  Max Consec. Wins:    {int(row['max_consecutive_wins'])}\n")
            f.write(f"  Max Consec. Losses:  {int(row['max_consecutive_losses'])}\n")
            f.write(f"  Avg Trades/Month:    {row['avg_trades_per_month']:.1f}\n")
        
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
    
    print(f"\n✓ All backtests complete!")
    print(f"✓ Chronological trades: {combined_path}")
    print(f"✓ Individual trades: {TRADES_DIR / '[PAIR].csv'} (28 files)")
    print(f"✓ Report: {report_path}")
