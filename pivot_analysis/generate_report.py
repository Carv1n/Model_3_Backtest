"""
Generate comprehensive TXT report from Pivot Quality Test results
"""

import pandas as pd
from pathlib import Path
from datetime import datetime

results_dir = Path(__file__).parent / "results"

# Find latest CSV
csv_files = list(results_dir.glob("pivot_quality_test_*.csv"))
if not csv_files:
    print("No results found!")
    exit()

latest_csv = sorted(csv_files)[-1]
print(f"Loading: {latest_csv.name}")

df = pd.read_csv(latest_csv)

# Create TXT report
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = results_dir / f"PIVOT_QUALITY_REPORT_{timestamp}.txt"

with open(output_file, 'w') as f:
    f.write('='*120 + '\n')
    f.write('PIVOT QUALITY TEST - COMPREHENSIVE RESULTS\n')
    f.write('='*120 + '\n\n')
    
    f.write('TEST CONFIGURATION:\n')
    f.write('-'*120 + '\n')
    f.write(f'Body Ratio Filter:     5% (filters extreme dojis only)\n')
    f.write(f'Gap Size Filter:       10-250 pips\n')
    f.write(f'Entry Type:            Direct Touch on pivot timeframe\n')
    f.write(f'Entry Level:           Bullish = gap_high | Bearish = gap_low\n')
    f.write(f'Total Pairs:           28\n')
    f.write(f'Timeframes:            3D, W, M\n')
    f.write(f'Total Pivots Tested:   51,253\n')
    f.write(f'TP Calculation:        -1 Fib (1x Gap), -2 Fib (2x Gap), -3 Fib (3x Gap)\n')
    f.write(f'SL Calculation:        Extreme (Gap Extreme), 0.5x Box, 1.0x Box\n')
    f.write(f'Report Generated:      {timestamp}\n\n')
    
    f.write('='*120 + '\n')
    f.write('DETAILED RESULTS BY COMBINATION\n')
    f.write('='*120 + '\n\n')
    
    for idx, row in df.iterrows():
        f.write(f'COMBINATION {idx+1}: TP = {row["tp_mult"]}x (Fib -{int(row["tp_mult"])}) | SL = {row["sl_label"]}\n')
        f.write('-'*120 + '\n')
        f.write(f'Trade Statistics:\n')
        f.write(f'  Total Trades:                {int(row["total_trades"]):>12,}\n')
        f.write(f'  Wins:                        {int(row["wins"]):>12,}  ({row["win_rate"]:>6.2f}%)\n')
        f.write(f'  Losses:                      {int(row["losses"]):>12,}  ({100-row["win_rate"]:>6.2f}%)\n')
        f.write(f'\n')
        f.write(f'Performance Metrics:\n')
        f.write(f'  Win Rate:                    {row["win_rate"]:>12.2f}%\n')
        f.write(f'  Average Win per Trade:       {row["avg_win_pips"]:>12.2f} pips\n')
        f.write(f'  Average Loss per Trade:      {row["avg_loss_pips"]:>12.2f} pips\n')
        f.write(f'  Risk/Reward Ratio (Setup):   {row["avg_rr"]:>12.2f}:1\n')
        f.write(f'  Avg TP Distance:             {row["avg_tp_distance_pips"]:>12.2f} pips\n')
        f.write(f'  Avg SL Distance:             {row["avg_sl_distance_pips"]:>12.2f} pips\n')
        f.write(f'  Profit Factor:               {row["profit_factor"]:>12.2f}\n')
        f.write(f'  Expectancy (per Trade):      {row["expectancy"]:>12.2f} pips\n')
        f.write(f'  Total Pips (All Trades):     {row["total_pips"]:>12,.0f} pips\n')
        f.write(f'\n')
        f.write(f'Gap Size Statistics:\n')
        f.write(f'  Minimum Gap:                 {row["min_gap_pips"]:>12.0f} pips\n')
        f.write(f'  Maximum Gap:                 {row["max_gap_pips"]:>12.0f} pips\n')
        f.write(f'  Median Gap:                  {row["median_gap_pips"]:>12.0f} pips\n')
        f.write(f'  Average Gap:                 {row["avg_gap_pips"]:>12.2f} pips\n')
        f.write('\n' + '='*120 + '\n\n')
    
    # Rankings
    f.write('='*120 + '\n')
    f.write('RANKINGS & ANALYSIS\n')
    f.write('='*120 + '\n\n')
    
    f.write('TOP 5 BY WIN RATE (Best probability):\n')
    f.write('-'*120 + '\n')
    top_wr = df.nlargest(5, 'win_rate')
    for i, (idx, row) in enumerate(top_wr.iterrows(), 1):
        f.write(f'{i}. TP={row["tp_mult"]}x | SL={row["sl_label"]:12} | ')
        f.write(f'Win Rate: {row["win_rate"]:6.2f}% | RR: {row["avg_rr"]:6.2f}:1 | ')
        f.write(f'Expectancy: {row["expectancy"]:8.2f} pips | Trades: {int(row["total_trades"]):6,}\n')
    
    f.write('\n')
    f.write('TOP 5 BY PROFIT FACTOR (Best profitability):\n')
    f.write('-'*120 + '\n')
    top_pf = df.nlargest(5, 'profit_factor')
    for i, (idx, row) in enumerate(top_pf.iterrows(), 1):
        f.write(f'{i}. TP={row["tp_mult"]}x | SL={row["sl_label"]:12} | ')
        f.write(f'PF: {row["profit_factor"]:8.2f} | Win Rate: {row["win_rate"]:6.2f}% | ')
        f.write(f'RR: {row["avg_rr"]:6.2f}:1 | Expectancy: {row["expectancy"]:8.2f} pips\n')
    
    f.write('\n')
    f.write('TOP 5 BY EXPECTANCY (Average profit per trade):\n')
    f.write('-'*120 + '\n')
    top_exp = df.nlargest(5, 'expectancy')
    for i, (idx, row) in enumerate(top_exp.iterrows(), 1):
        f.write(f'{i}. TP={row["tp_mult"]}x | SL={row["sl_label"]:12} | ')
        f.write(f'Exp: {row["expectancy"]:8.2f} pips | Win Rate: {row["win_rate"]:6.2f}% | ')
        f.write(f'PF: {row["profit_factor"]:8.2f} | Total: {row["total_pips"]:>12,.0f} pips\n')
    
    f.write('\n')
    f.write('TOP 5 BY TOTAL PIPS (Gross profitability):\n')
    f.write('-'*120 + '\n')
    top_pips = df.nlargest(5, 'total_pips')
    for i, (idx, row) in enumerate(top_pips.iterrows(), 1):
        f.write(f'{i}. TP={row["tp_mult"]}x | SL={row["sl_label"]:12} | ')
        f.write(f'Total: {row["total_pips"]:>12,.0f} pips | Trades: {int(row["total_trades"]):6,} | ')
        f.write(f'Win Rate: {row["win_rate"]:6.2f}% | Expectancy: {row["expectancy"]:8.2f} pips\n')
    
    f.write('\n')
    f.write('='*120 + '\n')
    f.write('BEST COMBINATIONS SUMMARY\n')
    f.write('='*120 + '\n\n')
    
    f.write('🥇 BEST FOR WIN RATE (Highest Probability):\n')
    best_wr = df.loc[df['win_rate'].idxmax()]
    f.write(f'   TP={best_wr["tp_mult"]}x | SL={best_wr["sl_label"]} | Win Rate: {best_wr["win_rate"]:.2f}%\n\n')
    
    f.write('🥇 BEST FOR PROFIT FACTOR (Most Profitable Per Win/Loss):\n')
    best_pf = df.loc[df['profit_factor'].idxmax()]
    f.write(f'   TP={best_pf["tp_mult"]}x | SL={best_pf["sl_label"]} | Profit Factor: {best_pf["profit_factor"]:.2f}\n\n')
    
    f.write('🥇 BEST FOR EXPECTANCY (Most Pips Per Trade):\n')
    best_exp = df.loc[df['expectancy'].idxmax()]
    f.write(f'   TP={best_exp["tp_mult"]}x | SL={best_exp["sl_label"]} | Expectancy: {best_exp["expectancy"]:.2f} pips/trade\n\n')
    
    f.write('🥇 BEST FOR TOTAL PROFIT (Total Pips All Trades):\n')
    best_total = df.loc[df['total_pips'].idxmax()]
    f.write(f'   TP={best_total["tp_mult"]}x | SL={best_total["sl_label"]} | Total Pips: {best_total["total_pips"]:,.0f}\n\n')
    
    f.write('='*120 + '\n')
    f.write('END OF REPORT\n')
    f.write('='*120 + '\n')

print(f'\n✅ Report saved: {output_file}')
