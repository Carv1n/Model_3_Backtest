"""
Create summary from already generated backtest results.
Now generates:
1. Overall stats across all pairs combined
2. Per-pair stats summary (stats only, no trade data)
"""

from pathlib import Path
import pandas as pd

RESULTS_DIR = Path(__file__).parent.parent / 'results'

# Load all individual backtest files
all_files = list(RESULTS_DIR.glob('backtest_*.csv'))
all_files = [f for f in all_files if f.stem != 'backtest_summary_by_pair' 
             and f.stem != 'backtest_overall_stats'
             and f.stem != 'backtest_all_pairs_combined' 
             and f.stem != 'backtest_direct_touch_fixed']

print(f"Found {len(all_files)} backtest result files")

# We need to re-run stats calculation since we only have trade data
import sys
sys.path.insert(0, str(Path(__file__).parent))
from backtest_modelx import BacktestEngine, Trade

# Collect all trades from all pairs
all_trades = []
per_pair_results = []

for f in all_files:
    pair = f.stem.replace('backtest_', '')
    print(f"Processing {pair}...")
    
    # Load trades
    df = pd.read_csv(f)
    
    if len(df) == 0:
        continue
    
    # Create Trade objects
    pair_trades = []
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
        pair_trades.append(trade)
        all_trades.append(trade)
    
    # Get per-pair stats
    engine = BacktestEngine()
    engine.trades = pair_trades
    stats = engine.get_performance_stats()
    if 'error' not in stats:
        stats['pair'] = pair
        per_pair_results.append(stats)

# Save per-pair summary (stats only, no trade data)
per_pair_df = pd.DataFrame(per_pair_results)
per_pair_df = per_pair_df.sort_values('total_return_pct', ascending=False)
summary_path = RESULTS_DIR / 'backtest_summary_by_pair.csv'
per_pair_df.to_csv(summary_path, index=False)

# Get top 5 pairs
top5_pairs = per_pair_df.head(5)['pair'].tolist()

# Calculate OVERALL stats (all pairs combined)
print("\nCalculating overall stats across all pairs...")
overall_engine = BacktestEngine()
overall_engine.trades = all_trades
overall_stats = overall_engine.get_performance_stats()

# Calculate TOP 5 stats
print("Calculating top 5 pairs stats...")
top5_trades = [t for t in all_trades if t.pair in top5_pairs]
top5_engine = BacktestEngine()
top5_engine.trades = top5_trades
top5_stats = top5_engine.get_performance_stats()

# Save overall stats
overall_stats_path = RESULTS_DIR / 'backtest_overall_stats.csv'
overall_df = pd.DataFrame([overall_stats])
overall_df.to_csv(overall_stats_path, index=False)

# Save top 5 stats
top5_stats_path = RESULTS_DIR / 'backtest_top5_stats.csv'
top5_df = pd.DataFrame([top5_stats])
top5_df.to_csv(top5_stats_path, index=False)

# Display overall stats
print("\n" + "="*80)
print("OVERALL STATS (ALL 28 PAIRS COMBINED)")
print("="*80)
print(f"Total Trades:            {overall_stats['total_trades']}")
print(f"Win Rate:                {overall_stats['win_rate']:.2f}%")
print(f"Expectancy (R):          {overall_stats['expectancy_r']:.6f}R")
print(f"Total Return:            {overall_stats['total_return_pct']:.2f}%")
print(f"Return/Year:             {overall_stats['return_per_year_pct']:.2f}%")
print(f"Return/Month:            {overall_stats['return_per_month_pct']:.2f}%")
print(f"Sharpe Ratio:            {overall_stats['sharpe_ratio']:.3f}")
print(f"Sortino Ratio:           {overall_stats['sortino_ratio']:.3f}")
print(f"Calmar Ratio:            {overall_stats['calmar_ratio']:.3f}")
print(f"Profit Factor:           {overall_stats['profit_factor']:.3f}")
print(f"Max Drawdown:            {overall_stats['max_drawdown_pct']:.2f}%")
print(f"Max Drawdown (R):        {overall_stats['max_drawdown_r']:.2f}R")
print(f"Recovery Factor:         {overall_stats['recovery_factor']:.3f}")
print(f"Win/Loss Ratio:          {overall_stats['win_loss_ratio']:.3f}")
print(f"Avg Win:                 {overall_stats['avg_win_r']:.2f}R ({overall_stats['avg_win_pips']:.1f} pips)")
print(f"Avg Loss:                {overall_stats['avg_loss_r']:.2f}R ({overall_stats['avg_loss_pips']:.1f} pips)")
print(f"Max Consecutive Wins:    {overall_stats['max_consecutive_wins']}")
print(f"Max Consecutive Losses:  {overall_stats['max_consecutive_losses']}")
print(f"Avg Trade Duration:      {overall_stats['avg_trade_duration_days']:.1f} days")
print(f"R-Squared:               {overall_stats['r_squared']:.3f}")
print("="*80)

# Display top 5 stats
print("\n" + "="*80)
print(f"TOP 5 PAIRS STATS ({', '.join(top5_pairs)})")
print("="*80)
print(f"Total Trades:            {top5_stats['total_trades']}")
print(f"Win Rate:                {top5_stats['win_rate']:.2f}%")
print(f"Expectancy (R):          {top5_stats['expectancy_r']:.6f}R")
print(f"Total Return:            {top5_stats['total_return_pct']:.2f}%")
print(f"Return/Year:             {top5_stats['return_per_year_pct']:.2f}%")
print(f"Return/Month:            {top5_stats['return_per_month_pct']:.2f}%")
print(f"Sharpe Ratio:            {top5_stats['sharpe_ratio']:.3f}")
print(f"Sortino Ratio:           {top5_stats['sortino_ratio']:.3f}")
print(f"Calmar Ratio:            {top5_stats['calmar_ratio']:.3f}")
print(f"Profit Factor:           {top5_stats['profit_factor']:.3f}")
print(f"Max Drawdown:            {top5_stats['max_drawdown_pct']:.2f}%")
print(f"Max Drawdown (R):        {top5_stats['max_drawdown_r']:.2f}R")
print(f"Recovery Factor:         {top5_stats['recovery_factor']:.3f}")
print(f"Win/Loss Ratio:          {top5_stats['win_loss_ratio']:.3f}")
print(f"Avg Win:                 {top5_stats['avg_win_r']:.2f}R ({top5_stats['avg_win_pips']:.1f} pips)")
print(f"Avg Loss:                {top5_stats['avg_loss_r']:.2f}R ({top5_stats['avg_loss_pips']:.1f} pips)")
print(f"Max Consecutive Wins:    {top5_stats['max_consecutive_wins']}")
print(f"Max Consecutive Losses:  {top5_stats['max_consecutive_losses']}")
print(f"Avg Trade Duration:      {top5_stats['avg_trade_duration_days']:.1f} days")
print(f"R-Squared:               {top5_stats['r_squared']:.3f}")
print("="*80)

# Display per-pair summary
display_cols = ['pair', 'total_trades', 'win_rate', 'expectancy_r', 'total_return_pct', 
               'return_per_year_pct', 'sharpe_ratio', 'max_drawdown_pct', 'profit_factor',
               'max_consecutive_losses']

print("\n" + "="*80)
print("SUMMARY BY PAIR (Top 10 by Return %)")
print("="*80)
print(per_pair_df[display_cols].head(10).to_string(index=False))
print("\n" + "="*80)
print("BOTTOM 5 by Return %")
print("="*80)
print(per_pair_df[display_cols].tail(5).to_string(index=False))
print(f"\n✓ Overall stats saved to {overall_stats_path}")
print(f"✓ Top 5 stats saved to {top5_stats_path}")
print(f"✓ Per-pair summary saved to {summary_path}")
print(f"✓ Total pairs: {len(per_pair_df)}")
print(f"✓ Total trades: {len(all_trades)}")
print("="*80)
