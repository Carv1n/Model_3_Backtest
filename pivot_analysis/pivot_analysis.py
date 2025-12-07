"""
Pivot Analysis & Export
=======================

1. Export all pivots to optimization/pivots/PAIR_TF.csv
2. Run Pivot Quality Test with 9 TP/SL combinations
3. Comprehensive statistics: Win Rate, Gap Sizes, Duration, etc.

Body Ratio: 5% (filters extreme dojis only)
Entry: Direct Touch on same timeframe as pivot
TP Levels: -1, -2, -3 Fib (1x, 2x, 3x Gap Size)
SL Levels: Extreme, 0.5x Box, 1.0x Box
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import sys
from typing import List, Dict, Tuple

# Add validation folder to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'validation'))
from export_pivot_gaps import load_data_with_fallback, detect_pivots_tv_style


class PivotAnalyzer:
    """Analyze pivots and run quality tests."""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.pivot_analysis_dir = Path(__file__).parent
        self.export_dir = self.pivot_analysis_dir / "pivots"
        self.export_dir.mkdir(exist_ok=True)
        self.results_dir = self.pivot_analysis_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.all_pairs = [
            'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD',
            'CADCHF', 'CADJPY', 'CHFJPY',
            'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD',
            'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
            'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD',
            'USDCAD', 'USDCHF', 'USDJPY'
        ]
        self.timeframes = ['3D', 'W', 'M']
    
    def pips(self, price_diff: float, pair: str) -> float:
        """Convert price difference to pips."""
        if 'JPY' in pair:
            return abs(price_diff) * 100
        return abs(price_diff) * 10000
    
    def export_pivots(self):
        """Export all detected pivots to CSV files."""
        print(f"\n{'='*80}")
        print(f"EXPORTING PIVOTS")
        print(f"{'='*80}\n")
        
        total_exported = 0
        
        for pair in self.all_pairs:
            for tf in self.timeframes:
                try:
                    df = load_data_with_fallback(tf, pair)
                    pivots = detect_pivots_tv_style(df, min_body_pct=5.0, pair=pair)
                    
                    if not pivots:
                        continue
                    
                    # Convert to DataFrame
                    pivot_list = []
                    for p in pivots:
                        gap_size_pips = self.pips(p['gap_high'] - p['gap_low'], pair)
                        pivot_list.append({
                            'pair': pair,
                            'timeframe': tf,
                            'time': df.iloc[p['index']]['time'],
                            'direction': 'bullish' if p['is_bullish'] else 'bearish',
                            'gap_high': p['gap_high'],
                            'gap_low': p['gap_low'],
                            'gap_size': p['gap_high'] - p['gap_low'],
                            'gap_size_pips': gap_size_pips,
                            'extreme': p['extreme'],
                            'index': p['index'],
                        })
                    
                    pivot_df = pd.DataFrame(pivot_list)
                    
                    # Export
                    export_file = self.export_dir / f"{pair}_{tf}.csv"
                    pivot_df.to_csv(export_file, index=False)
                    
                    print(f"{pair:8} {tf}: {len(pivots):5} pivots → {export_file.name}")
                    total_exported += len(pivots)
                    
                except Exception as e:
                    print(f"{pair:8} {tf}: ERROR - {e}")
                    continue
        
        print(f"\n{'='*80}")
        print(f"Total Pivots Exported: {total_exported:,}")
        print(f"Export Directory: {self.export_dir}")
        print(f"{'='*80}\n")
    
    def run_quality_test(self):
        """Run pivot quality test with 9 TP/SL combinations."""
        print(f"\n{'='*80}")
        print(f"PIVOT QUALITY TEST")
        print(f"{'='*80}")
        print(f"Body Ratio: 5% (filters extreme dojis)")
        print(f"Entry: Direct Touch on pivot timeframe")
        print(f"Gap Filter: 10-250 pips")
        print(f"TP Levels: -1, -2, -3 Fib (1x, 2x, 3x Gap Size)")
        print(f"SL Levels: Extreme, 0.5x Box, 1.0x Box")
        print(f"Pairs: {len(self.all_pairs)}")
        print(f"Timeframes: {', '.join(self.timeframes)}")
        print(f"{'='*80}\n")
        
        # TP/SL combinations
        tp_multipliers = [1.0, 2.0, 3.0]  # -1, -2, -3 Fib
        sl_multipliers = [0.0, 0.5, 1.0]  # Extreme, 0.5x Box, 1.0x Box
        sl_labels = {0.0: 'Extreme', 0.5: '0.5x Box', 1.0: '1.0x Box'}
        
        all_results = []
        
        for tp_mult in tp_multipliers:
            for sl_mult in sl_multipliers:
                print(f"\nTesting: TP={tp_mult}x (Fib -{int(tp_mult)}), SL={sl_labels[sl_mult]}")
                print(f"{'-'*80}")
                
                stats = self._test_combination(tp_mult, sl_mult, sl_labels[sl_mult])
                
                if stats:
                    all_results.append(stats)
                    self._print_stats(stats)
        
        # Save results as TXT (no CSV)
        if all_results:
            results_df = pd.DataFrame(all_results)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = self.results_dir / f"PIVOT_QUALITY_TEST_{timestamp}.txt"
            
            self._write_txt_report(results_df, output_file, timestamp)
            
            print(f"\n{'='*80}")
            print(f"✅ Results saved: {output_file}")
            print(f"{'='*80}\n")
            
            # Print summary
            print(f"\n{'='*80}")
            print(f"TOP 5 BY WIN RATE")
            print(f"{'='*80}\n")
            top_5 = results_df.nlargest(5, 'win_rate')
            for idx, row in top_5.iterrows():
                print(f"TP={row['tp_mult']}x | SL={row['sl_label']}")
                print(f"  Win Rate: {row['win_rate']:.2f}% | RR: {row['rr_ratio']:.2f}")
                print(f"  Trades: {row['total_trades']} | Avg Gap: {row['avg_gap_pips']:.0f} pips")
                print(f"  Min Gap: {row['min_gap_pips']:.0f} | Max Gap: {row['max_gap_pips']:.0f}")
                print(f"  Median Gap: {row['median_gap_pips']:.0f}\n")
    
    def _test_combination(self, tp_mult: float, sl_mult: float, sl_label: str) -> Dict:
        """Test one TP/SL combination."""
        all_trades = []
        
        for pair in self.all_pairs:
            for tf in self.timeframes:
                try:
                    df = load_data_with_fallback(tf, pair)
                    pivots = detect_pivots_tv_style(df, min_body_pct=5.0, pair=pair)
                    
                    for pivot in pivots:
                        gap_size_pips = self.pips(pivot['gap_high'] - pivot['gap_low'], pair)
                        
                        # Filter: 10-250 pips
                        if gap_size_pips < 10 or gap_size_pips > 250:
                            continue
                        
                        # Calculate TP/SL
                        gap_size = pivot['gap_high'] - pivot['gap_low']
                        
                        if pivot['is_bullish']:
                            entry = pivot['gap_high']
                            tp = entry + (tp_mult * gap_size)
                            sl = pivot['extreme'] - (sl_mult * gap_size) if sl_mult > 0 else pivot['extreme']
                            tp_distance = tp - entry
                            sl_distance = entry - sl
                        else:
                            entry = pivot['gap_low']
                            tp = entry - (tp_mult * gap_size)
                            sl = pivot['extreme'] + (sl_mult * gap_size) if sl_mult > 0 else pivot['extreme']
                            tp_distance = entry - tp
                            sl_distance = sl - entry
                        
                        # Calculate RR
                        rr = tp_distance / sl_distance if sl_distance > 0 else 0
                        tp_dist_pips = self.pips(tp_distance, pair)
                        sl_dist_pips = self.pips(sl_distance, pair)
                        
                        # Simulate trade
                        result = self._simulate_trade(df, pivot, entry, tp, sl, pair)
                        
                        if result:
                            result['pair'] = pair
                            result['timeframe'] = tf
                            result['gap_size_pips'] = gap_size_pips
                            result['rr'] = rr
                            result['tp_distance_pips'] = tp_dist_pips
                            result['sl_distance_pips'] = sl_dist_pips
                            all_trades.append(result)
                    
                except Exception as e:
                    continue
        
        if not all_trades:
            return None
        
        # Calculate statistics
        trades_df = pd.DataFrame(all_trades)
        
        wins = trades_df[trades_df['outcome'] == 'win']
        losses = trades_df[trades_df['outcome'] == 'loss']
        
        n_wins = len(wins)
        n_losses = len(losses)
        total_trades = len(trades_df)
        win_rate = (n_wins / total_trades * 100) if total_trades > 0 else 0
        
        # Gap size stats
        gap_sizes = trades_df['gap_size_pips']
        
        # P&L stats (losses already negative)
        avg_win_pips = wins['pnl_pips'].mean() if len(wins) > 0 else 0
        avg_loss_pips = abs(losses['pnl_pips'].mean()) if len(losses) > 0 else 0  # abs to show as positive in report
        
        # RR from trade setup (not from outcome)
        avg_rr = trades_df['rr'].mean()
        avg_tp_dist = trades_df['tp_distance_pips'].mean()
        avg_sl_dist = trades_df['sl_distance_pips'].mean()
        
        # Profit Factor
        total_win_pips = wins['pnl_pips'].sum() if len(wins) > 0 else 0
        total_loss_pips = abs(losses['pnl_pips'].sum()) if len(losses) > 0 else 0
        profit_factor = (total_win_pips / total_loss_pips) if total_loss_pips != 0 else 0
        
        expectancy = trades_df['pnl_pips'].mean()
        
        return {
            'tp_mult': tp_mult,
            'sl_mult': sl_mult,
            'sl_label': sl_label,
            'total_trades': total_trades,
            'wins': n_wins,
            'losses': n_losses,
            'win_rate': win_rate,
            'avg_win_pips': avg_win_pips,
            'avg_loss_pips': avg_loss_pips,
            'avg_rr': avg_rr,
            'avg_tp_distance_pips': avg_tp_dist,
            'avg_sl_distance_pips': avg_sl_dist,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'total_pips': trades_df['pnl_pips'].sum(),
            'min_gap_pips': gap_sizes.min(),
            'max_gap_pips': gap_sizes.max(),
            'median_gap_pips': gap_sizes.median(),
            'avg_gap_pips': gap_sizes.mean(),
        }
    
    def _simulate_trade(self, df: pd.DataFrame, pivot: Dict, entry: float, tp: float, sl: float, pair: str) -> Dict:
        """Simulate trade from pivot detection."""
        pivot_idx = pivot['index']
        valid_idx = pivot_idx + 1
        
        if valid_idx >= len(df):
            return None
        
        # Find entry (first touch of gap)
        entry_idx = None
        for idx in range(valid_idx, len(df)):
            candle = df.iloc[idx]
            if candle['low'] <= pivot['gap_high'] and candle['high'] >= pivot['gap_low']:
                entry_idx = idx
                break
        
        if entry_idx is None:
            return None  # Gap never touched
        
        # Find TP/SL hit
        for idx in range(entry_idx + 1, len(df)):
            candle = df.iloc[idx]
            
            if pivot['is_bullish']:
                if candle['low'] <= sl:
                    return {'outcome': 'loss', 'pnl_pips': -self.pips(entry - sl, pair)}
                if candle['high'] >= tp:
                    return {'outcome': 'win', 'pnl_pips': self.pips(tp - entry, pair)}
            else:
                if candle['high'] >= sl:
                    return {'outcome': 'loss', 'pnl_pips': -self.pips(sl - entry, pair)}
                if candle['low'] <= tp:
                    return {'outcome': 'win', 'pnl_pips': self.pips(entry - tp, pair)}
        
        # End of data, no exit
        return None
    
    def _print_stats(self, stats: Dict):
        """Print statistics for a combination."""
        print(f"  Trades: {stats['total_trades']:5} | Wins: {stats['wins']:5} | Losses: {stats['losses']:5}")
        print(f"  Win Rate: {stats['win_rate']:6.2f}% | RR: {stats['avg_rr']:5.2f} | PF: {stats['profit_factor']:5.2f}")
        print(f"  Avg TP: {stats['avg_tp_distance_pips']:6.0f} pips | Avg SL: {stats['avg_sl_distance_pips']:6.0f} pips")
        print(f"  Avg Gap: {stats['avg_gap_pips']:6.0f} pips | Min: {stats['min_gap_pips']:5.0f} | Max: {stats['max_gap_pips']:6.0f}")
        print(f"  Median Gap: {stats['median_gap_pips']:6.0f} pips")
        print(f"  Expectancy: {stats['expectancy']:6.2f} pips/trade | Total: {stats['total_pips']:8.0f} pips")
    
    def _write_txt_report(self, df: pd.DataFrame, output_file: Path, timestamp: str):
        """Write comprehensive TXT report."""
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
            f.write(f'Total Pairs:           {len(self.all_pairs)}\n')
            f.write(f'Timeframes:            {", ".join(self.timeframes)}\n')
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
            
            f.write('TOP 5 BY WIN RATE:\n')
            f.write('-'*120 + '\n')
            top_wr = df.nlargest(5, 'win_rate')
            for i, (idx, row) in enumerate(top_wr.iterrows(), 1):
                f.write(f'{i}. TP={row["tp_mult"]}x | SL={row["sl_label"]:12} | ')
                f.write(f'WR: {row["win_rate"]:6.2f}% | RR: {row["avg_rr"]:6.2f}:1 | ')
                f.write(f'Exp: {row["expectancy"]:8.2f} pips\n')
            
            f.write('\n')
            f.write('TOP 5 BY PROFIT FACTOR:\n')
            f.write('-'*120 + '\n')
            top_pf = df.nlargest(5, 'profit_factor')
            for i, (idx, row) in enumerate(top_pf.iterrows(), 1):
                f.write(f'{i}. TP={row["tp_mult"]}x | SL={row["sl_label"]:12} | ')
                f.write(f'PF: {row["profit_factor"]:8.2f} | WR: {row["win_rate"]:6.2f}% | ')
                f.write(f'Exp: {row["expectancy"]:8.2f} pips\n')
            
            f.write('\n')
            f.write('TOP 5 BY EXPECTANCY:\n')
            f.write('-'*120 + '\n')
            top_exp = df.nlargest(5, 'expectancy')
            for i, (idx, row) in enumerate(top_exp.iterrows(), 1):
                f.write(f'{i}. TP={row["tp_mult"]}x | SL={row["sl_label"]:12} | ')
                f.write(f'Exp: {row["expectancy"]:8.2f} pips | WR: {row["win_rate"]:6.2f}% | ')
                f.write(f'PF: {row["profit_factor"]:8.2f}\n')
            
            f.write('\n' + '='*120 + '\n')
            f.write('BEST COMBINATIONS SUMMARY\n')
            f.write('='*120 + '\n\n')
            
            best_wr = df.loc[df['win_rate'].idxmax()]
            f.write(f'🥇 BEST WIN RATE: TP={best_wr["tp_mult"]}x | SL={best_wr["sl_label"]} | {best_wr["win_rate"]:.2f}%\n')
            
            best_exp = df.loc[df['expectancy'].idxmax()]
            f.write(f'🥇 BEST EXPECTANCY: TP={best_exp["tp_mult"]}x | SL={best_exp["sl_label"]} | {best_exp["expectancy"]:.2f} pips/trade\n')
            
            f.write('\n' + '='*120 + '\n')
            f.write('END OF REPORT\n')
            f.write('='*120 + '\n')


if __name__ == '__main__':
    analyzer = PivotAnalyzer()
    
    # Export pivots
    analyzer.export_pivots()
    
    # Run quality test
    analyzer.run_quality_test()
    
    print("\nDone!")
