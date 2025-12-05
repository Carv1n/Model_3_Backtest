"""
Model X Backtest Engine
=======================

Backtest pivot-based trading strategy across multiple pairs and timeframes.

Entry Types:
- direct_touch: Enter immediately when gap is touched
- retest: Enter on second touch of gap (after pullback)
- candle_close: Enter after candle closes inside gap

Exit Types:
- fixed: Fixed TP/SL levels (TP = 3x box, SL = 0.5x box from boundaries)
- trailing: Trailing stop
- breakeven: Move SL to breakeven after X% of TP reached

Current Implementation: Direct Touch + Fixed TP/SL
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import argparse
import sys

# Add validation folder to path for pivot detection
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'validation'))
from export_pivot_gaps import detect_pivots_tv_style, load_data_with_fallback


class Trade:
    """Represents a single trade."""
    
    def __init__(self, trade_id, pair, timeframe, direction, entry_time, entry_price, 
                 tp_price, sl_price, gap_high, gap_low, pivot_generated_time):
        self.trade_id = trade_id
        self.pair = pair
        self.timeframe = timeframe
        self.direction = direction  # 'bullish' or 'bearish'
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.tp_price = tp_price
        self.sl_price = sl_price
        self.gap_high = gap_high
        self.gap_low = gap_low
        self.pivot_generated_time = pivot_generated_time
        
        # Trade outcome (filled when closed)
        self.exit_time = None
        self.exit_price = None
        self.exit_reason = None  # 'tp', 'sl', 'manual'
        self.pnl_pips = None
        self.pnl_r = None  # R-multiple (how many times risk won/lost)
        self.pnl_percent = None
        self.status = 'open'  # 'open', 'closed'
        
    def close_trade(self, exit_time, exit_price, exit_reason):
        """Close the trade and calculate P&L in pips and R-multiples."""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = exit_reason
        self.status = 'closed'
        
        # Calculate pips
        if self.direction == 'bullish':
            pips_diff = exit_price - self.entry_price
        else:
            pips_diff = self.entry_price - exit_price
        
        # Convert to pips (JPY pairs: x100, others: x10000)
        if 'JPY' in self.pair:
            self.pnl_pips = pips_diff * 100
        else:
            self.pnl_pips = pips_diff * 10000
        
        # Calculate R-multiple (risk-adjusted return)
        # 1R = distance from entry to SL
        distance_to_sl = abs(self.entry_price - self.sl_price)
        if 'JPY' in self.pair:
            risk_pips = distance_to_sl * 100
        else:
            risk_pips = distance_to_sl * 10000
        
        # R-multiple: how many times our risk did we gain/lose?
        if risk_pips > 0:
            self.pnl_r = self.pnl_pips / risk_pips
        else:
            self.pnl_r = 0
        
        # With 2:1 RR: TP should be +2R, SL should be -1R
        # Percent return (assuming 1% risk per trade)
        self.pnl_percent = self.pnl_r  # If risking 1%, then +2R = +2%, -1R = -1%
    
    def to_dict(self):
        """Convert trade to dictionary for DataFrame."""
        return {
            'trade_id': self.trade_id,
            'pair': self.pair,
            'timeframe': self.timeframe,
            'direction': self.direction,
            'pivot_generated_time': self.pivot_generated_time,
            'entry_time': self.entry_time,
            'entry_price': self.entry_price,
            'tp_price': self.tp_price,
            'sl_price': self.sl_price,
            'gap_high': self.gap_high,
            'gap_low': self.gap_low,
            'exit_time': self.exit_time,
            'exit_price': self.exit_price,
            'exit_reason': self.exit_reason,
            'pnl_pips': self.pnl_pips,
            'pnl_r': self.pnl_r,
            'pnl_percent': self.pnl_percent,
            'status': self.status
        }


class BacktestEngine:
    """Main backtest engine for Model X strategy."""
    
    def __init__(self, entry_type='direct_touch', exit_type='fixed'):
        self.entry_type = entry_type
        self.exit_type = exit_type
        self.trades = []
        self.trade_counter = 0
        
    def run_backtest(self, pairs, timeframes, start_date=None, end_date=None):
        """
        Run backtest across multiple pairs and timeframes.
        
        Args:
            pairs: List of currency pairs (e.g., ['EURUSD', 'GBPUSD'])
            timeframes: List of timeframes (e.g., ['3D', 'W', 'M'])
            start_date: Start date for backtest (optional)
            end_date: End date for backtest (optional)
        """
        print("="*80)
        print(f"MODEL X BACKTEST - {self.entry_type.upper()} ENTRY + {self.exit_type.upper()} EXIT")
        print("="*80)
        
        total_pivots = 0
        
        for timeframe in timeframes:
            for pair in pairs:
                print(f"\nProcessing {pair} {timeframe}...")
                
                # Load data
                df = load_data_with_fallback(timeframe, pair)
                
                if df is None or len(df) == 0:
                    print(f"  ⚠️  No data available for {pair} {timeframe}")
                    continue
                
                # Filter by date range if provided
                if start_date:
                    df = df[df['time'] >= pd.Timestamp(start_date)]
                if end_date:
                    df = df[df['time'] <= pd.Timestamp(end_date)]
                
                # Detect pivots
                pivots = detect_pivots_tv_style(df, pair=pair)
                print(f"  Found {len(pivots)} pivots")
                total_pivots += len(pivots)
                
                # Run trades for each pivot
                trades_opened = self._backtest_pair_timeframe(df, pivots, pair, timeframe)
                print(f"  Opened {trades_opened} trades")
        
        print(f"\n{'='*80}")
        print(f"BACKTEST COMPLETE")
        print(f"Total Pivots: {total_pivots}")
        print(f"Total Trades: {len(self.trades)}")
        print(f"{'='*80}\n")
        
        return self.get_results()
    
    def _backtest_pair_timeframe(self, df, pivots, pair, timeframe):
        """Run backtest for a single pair/timeframe combination."""
        trades_opened = 0
        
        for pivot in pivots:
            # Pivot is complete at index i
            pivot_idx = pivot['index']
            
            # First tradeable candle is at pivot_idx + 1
            valid_idx = pivot_idx + 1
            
            if valid_idx >= len(df):
                continue
            
            # Get pivot details
            direction = 'bullish' if pivot['is_bullish'] else 'bearish'
            gap_high = pivot['gap_high']
            gap_low = pivot['gap_low']
            tp_level = pivot['tp_level']
            sl_level = pivot['sl_level']
            pivot_generated_time = df.iloc[pivot_idx]['time']
            
            # Entry logic based on entry_type
            if self.entry_type == 'direct_touch':
                trade = self._entry_direct_touch(
                    df, valid_idx, pair, timeframe, direction,
                    gap_high, gap_low, tp_level, sl_level, pivot_generated_time
                )
                
                if trade:
                    self.trades.append(trade)
                    trades_opened += 1
        
        return trades_opened
    
    def _entry_direct_touch(self, df, start_idx, pair, timeframe, direction,
                           gap_high, gap_low, tp_level, sl_level, pivot_generated_time):
        """
        Direct Touch Entry: Enter immediately when gap is touched.
        
        Entry Price:
        - Bullish: gap_high (upper boundary)
        - Bearish: gap_low (lower boundary)
        """
        # Search for first candle that touches the gap
        for idx in range(start_idx, len(df)):
            candle = df.iloc[idx]
            
            # Check if gap is touched
            if candle['low'] <= gap_high and candle['high'] >= gap_low:
                # Gap touched! Enter trade
                if direction == 'bullish':
                    entry_price = gap_high
                else:
                    entry_price = gap_low
                
                # Create trade
                self.trade_counter += 1
                trade = Trade(
                    trade_id=self.trade_counter,
                    pair=pair,
                    timeframe=timeframe,
                    direction=direction,
                    entry_time=candle['time'],
                    entry_price=entry_price,
                    tp_price=tp_level,
                    sl_price=sl_level,
                    gap_high=gap_high,
                    gap_low=gap_low,
                    pivot_generated_time=pivot_generated_time
                )
                
                # Simulate trade execution from next candle onwards
                self._simulate_trade(df, idx + 1, trade)
                
                return trade
        
        # Gap never touched
        return None
    
    def _simulate_trade(self, df, start_idx, trade):
        """
        Simulate trade execution and check for TP/SL hits.
        
        Args:
            df: Price data
            start_idx: Index to start simulation from
            trade: Trade object
        """
        for idx in range(start_idx, len(df)):
            candle = df.iloc[idx]
            
            if trade.direction == 'bullish':
                # Check SL first (conservative)
                if candle['low'] <= trade.sl_price:
                    trade.close_trade(candle['time'], trade.sl_price, 'sl')
                    return
                
                # Check TP
                if candle['high'] >= trade.tp_price:
                    trade.close_trade(candle['time'], trade.tp_price, 'tp')
                    return
            
            else:  # bearish
                # Check SL first (conservative)
                if candle['high'] >= trade.sl_price:
                    trade.close_trade(candle['time'], trade.sl_price, 'sl')
                    return
                
                # Check TP
                if candle['low'] <= trade.tp_price:
                    trade.close_trade(candle['time'], trade.tp_price, 'tp')
                    return
        
        # Trade still open at end of data
        # Close at last available price
        last_candle = df.iloc[-1]
        trade.close_trade(last_candle['time'], last_candle['close'], 'manual')
    
    def get_results(self):
        """Get backtest results as DataFrame."""
        if not self.trades:
            return pd.DataFrame()
        
        results_df = pd.DataFrame([t.to_dict() for t in self.trades])
        return results_df
    
    def get_performance_stats(self, risk_per_trade_pct=1.0):
        """
        Calculate performance statistics.
        
        Args:
            risk_per_trade_pct: Risk per trade in percent (default 1%)
                               Used to convert R-multiples to account % returns
        """
        if not self.trades:
            return {}
        
        results_df = self.get_results()
        closed_trades = results_df[results_df['status'] == 'closed']
        
        if len(closed_trades) == 0:
            return {'error': 'No closed trades'}
        
        total_trades = len(closed_trades)
        winning_trades = len(closed_trades[closed_trades['pnl_r'] > 0])
        losing_trades = len(closed_trades[closed_trades['pnl_r'] < 0])
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # R-multiple metrics (TP = +2R, SL = -1R)
        total_r = closed_trades['pnl_r'].sum()
        avg_r_per_trade = total_r / total_trades if total_trades > 0 else 0
        avg_win_r = closed_trades[closed_trades['pnl_r'] > 0]['pnl_r'].mean() if winning_trades > 0 else 0
        avg_loss_r = closed_trades[closed_trades['pnl_r'] < 0]['pnl_r'].mean() if losing_trades > 0 else 0
        
        # Expectancy: average R per trade (should be positive for profitable system)
        expectancy = avg_r_per_trade
        
        # Profit Factor (in R)
        total_wins_r = closed_trades[closed_trades['pnl_r'] > 0]['pnl_r'].sum()
        total_losses_r = abs(closed_trades[closed_trades['pnl_r'] < 0]['pnl_r'].sum())
        profit_factor = total_wins_r / total_losses_r if total_losses_r > 0 else float('inf')
        
        # Time-based metrics
        closed_trades_sorted = closed_trades.sort_values('exit_time')
        first_trade = closed_trades_sorted.iloc[0]['entry_time']
        last_trade = closed_trades_sorted.iloc[-1]['exit_time']
        total_days = (last_trade - first_trade).total_seconds() / 86400
        total_months = total_days / 30.44
        total_years = total_days / 365.25
        trades_per_year = total_trades / total_years if total_years > 0 else 0
        
        # Account % returns (assuming risk_per_trade_pct risk per trade)
        # If risking 1% per trade: +2R = +2%, -1R = -1%
        closed_trades_sorted['account_pct'] = closed_trades_sorted['pnl_r'] * risk_per_trade_pct
        total_return_pct = closed_trades_sorted['account_pct'].sum()
        return_per_month = total_return_pct / total_months if total_months > 0 else 0
        return_per_year = total_return_pct / total_years if total_years > 0 else 0
        
        # Max Drawdown (in R and %)
        equity_curve_r = closed_trades_sorted['pnl_r'].cumsum()
        max_drawdown_r = (equity_curve_r - equity_curve_r.cummax()).min()
        max_drawdown_pct = max_drawdown_r * risk_per_trade_pct
        
        # Sharpe Ratio (based on R-multiples)
        returns_r = closed_trades_sorted['pnl_r']
        avg_r = returns_r.mean()
        std_r = returns_r.std()
        sharpe_ratio = (avg_r * np.sqrt(trades_per_year)) / std_r if std_r > 0 else 0
        
        # Sortino Ratio (only downside deviation)
        downside_returns = returns_r[returns_r < 0]
        downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
        sortino_ratio = (avg_r * np.sqrt(trades_per_year)) / downside_std if downside_std > 0 else 0
        
        # Calmar Ratio (return/max_dd in R)
        calmar_ratio = (avg_r * trades_per_year) / abs(max_drawdown_r) if max_drawdown_r < 0 else 0
        
        # Recovery Factor (total return / max drawdown)
        recovery_factor = total_r / abs(max_drawdown_r) if max_drawdown_r < 0 else 0
        
        # Win/Loss Ratio
        win_loss_ratio = abs(avg_win_r / avg_loss_r) if avg_loss_r != 0 else 0
        
        # Max Consecutive Wins & Losses
        consecutive_wins = []
        consecutive_losses = []
        current_win_streak = 0
        current_loss_streak = 0
        for r in closed_trades_sorted['pnl_r']:
            if r > 0:
                current_win_streak += 1
                if current_loss_streak > 0:
                    consecutive_losses.append(current_loss_streak)
                current_loss_streak = 0
            else:
                current_loss_streak += 1
                if current_win_streak > 0:
                    consecutive_wins.append(current_win_streak)
                current_win_streak = 0
        if current_win_streak > 0:
            consecutive_wins.append(current_win_streak)
        if current_loss_streak > 0:
            consecutive_losses.append(current_loss_streak)
        
        max_consecutive_wins = max(consecutive_wins) if consecutive_wins else 0
        max_consecutive_losses = max(consecutive_losses) if consecutive_losses else 0
        
        # Trades per Month/Year breakdown
        closed_trades_sorted['month'] = pd.to_datetime(closed_trades_sorted['entry_time']).dt.to_period('M')
        closed_trades_sorted['year'] = pd.to_datetime(closed_trades_sorted['entry_time']).dt.to_period('Y')
        
        # Monthly stats
        monthly_trades = closed_trades_sorted.groupby('month').size()
        avg_trades_per_month = monthly_trades.mean() if len(monthly_trades) > 0 else 0
        max_trades_in_month = monthly_trades.max() if len(monthly_trades) > 0 else 0
        min_trades_in_month = monthly_trades.min() if len(monthly_trades) > 0 else 0
        
        # Yearly stats
        yearly_trades = closed_trades_sorted.groupby('year').size()
        avg_trades_per_year_actual = yearly_trades.mean() if len(yearly_trades) > 0 else 0
        
        # Average Trade Duration (in days)
        closed_trades_sorted['duration_days'] = (
            closed_trades_sorted['exit_time'] - closed_trades_sorted['entry_time']
        ).dt.total_seconds() / 86400
        avg_trade_duration_days = closed_trades_sorted['duration_days'].mean()
        
        # R-Squared (equity curve linearity)
        # Linear regression of equity curve vs trade number
        trade_numbers = np.arange(len(equity_curve_r))
        if len(trade_numbers) > 1:
            correlation = np.corrcoef(trade_numbers, equity_curve_r.values)[0, 1]
            r_squared = correlation ** 2
        else:
            r_squared = 0
        
        # Concurrent Positions Analysis
        # Track how many positions were open at each point in time
        concurrent_positions = []
        
        # Create timeline of all entry and exit events
        events = []
        for _, trade in closed_trades_sorted.iterrows():
            events.append(('entry', trade['entry_time']))
            events.append(('exit', trade['exit_time']))
        
        # Sort events by time
        events.sort(key=lambda x: x[1])
        
        # Calculate concurrent positions at each event
        current_open = 0
        for event_type, event_time in events:
            if event_type == 'entry':
                current_open += 1
                concurrent_positions.append(current_open)
            else:  # exit
                current_open -= 1
        
        # Calculate stats
        concurrent_positions_median = np.median(concurrent_positions) if concurrent_positions else 0
        concurrent_positions_max = max(concurrent_positions) if concurrent_positions else 0
        concurrent_positions_avg = np.mean(concurrent_positions) if concurrent_positions else 0
        
        stats = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            # R-multiple stats
            'total_r': total_r,
            'expectancy_r': expectancy,
            'avg_win_r': avg_win_r,
            'avg_loss_r': avg_loss_r,
            'win_loss_ratio': win_loss_ratio,
            'max_drawdown_r': max_drawdown_r,
            # Account % (assuming 1% risk per trade)
            'total_return_pct': total_return_pct,
            'return_per_month_pct': return_per_month,
            'return_per_year_pct': return_per_year,
            'max_drawdown_pct': max_drawdown_pct,
            # Risk metrics
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'sortino_ratio': sortino_ratio,
            'calmar_ratio': calmar_ratio,
            'recovery_factor': recovery_factor,
            # Consistency metrics
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses,
            'avg_trade_duration_days': avg_trade_duration_days,
            'r_squared': r_squared,
            # Time metrics
            'total_days': total_days,
            'total_years': total_years,
            'trades_per_year': trades_per_year,
            # Monthly/Yearly breakdown
            'avg_trades_per_month': avg_trades_per_month,
            'max_trades_in_month': max_trades_in_month,
            'min_trades_in_month': min_trades_in_month,
            'avg_trades_per_year_actual': avg_trades_per_year_actual,
            # Concurrent positions
            'concurrent_positions_median': concurrent_positions_median,
            'concurrent_positions_max': concurrent_positions_max,
            'concurrent_positions_avg': concurrent_positions_avg
        }
        
        return stats


def print_performance_stats(stats):
    """Print performance statistics in readable format."""
    if 'error' in stats:
        print(f"\n⚠️  {stats['error']}")
        return
    
    print("\n" + "="*80)
    print("PERFORMANCE STATISTICS")
    print("="*80)
    print(f"Total Trades:        {stats['total_trades']}")
    print(f"Winning Trades:      {stats['winning_trades']} ({stats['win_rate']:.2f}%)")
    print(f"Losing Trades:       {stats['losing_trades']}")
    print(f"Period:              {stats['total_years']:.1f} years ({stats['total_days']:.0f} days)")
    print(f"Trades/Year:         {stats['trades_per_year']:.1f}")
    
    print(f"\n--- R-MULTIPLE PERFORMANCE ---")
    print(f"Total R:             {stats['total_r']:.2f}R")
    print(f"Expectancy:          {stats['expectancy_r']:.3f}R per trade")
    print(f"Avg Win:             {stats['avg_win_r']:.2f}R")
    print(f"Avg Loss:            {stats['avg_loss_r']:.2f}R")
    print(f"Max Drawdown:        {stats['max_drawdown_r']:.2f}R")
    
    print(f"\n--- ACCOUNT % (assuming 1% risk/trade) ---")
    print(f"Total Return:        {stats['total_return_pct']:.2f}%")
    print(f"Return/Month:        {stats['return_per_month_pct']:.2f}%")
    print(f"Return/Year:         {stats['return_per_year_pct']:.2f}%")
    print(f"Max Drawdown:        {stats['max_drawdown_pct']:.2f}%")
    
    print(f"\n--- RISK METRICS ---")
    print(f"Profit Factor:       {stats['profit_factor']:.2f}")
    print(f"Win/Loss Ratio:      {stats['win_loss_ratio']:.2f}")
    print(f"Sharpe Ratio:        {stats['sharpe_ratio']:.2f}")
    print(f"Sortino Ratio:       {stats['sortino_ratio']:.2f}")
    print(f"Calmar Ratio:        {stats['calmar_ratio']:.2f}")
    print(f"Recovery Factor:     {stats['recovery_factor']:.2f}")
    
    print(f"\n--- CONSISTENCY METRICS ---")
    print(f"Max Consecutive Wins:   {stats['max_consecutive_wins']}")
    print(f"Max Consecutive Losses: {stats['max_consecutive_losses']}")
    print(f"Avg Trade Duration:     {stats['avg_trade_duration_days']:.1f} days")
    print(f"R-Squared:              {stats['r_squared']:.3f}")
    
    print(f"\n--- TRADE FREQUENCY ---")
    print(f"Avg Trades/Month:       {stats['avg_trades_per_month']:.1f}")
    print(f"Max Trades in Month:    {stats['max_trades_in_month']:.0f}")
    print(f"Min Trades in Month:    {stats['min_trades_in_month']:.0f}")
    print(f"Avg Trades/Year:        {stats['avg_trades_per_year_actual']:.1f}")
    print("="*80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Model X Backtest Engine')
    parser.add_argument('-p', '--pairs', nargs='+', default=['EURUSD', 'GBPUSD'],
                       help='Currency pairs to backtest (default: EURUSD GBPUSD)')
    parser.add_argument('-t', '--timeframes', nargs='+', default=['3D', 'W', 'M'],
                       help='Timeframes to backtest (default: 3D W M)')
    parser.add_argument('-s', '--start-date', type=str, default=None,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('-e', '--end-date', type=str, default=None,
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('-o', '--output', type=str, default=None,
                       help='Output CSV file for results')
    parser.add_argument('--entry-type', type=str, default='direct_touch',
                       choices=['direct_touch', 'retest', 'candle_close'],
                       help='Entry type (default: direct_touch)')
    parser.add_argument('--exit-type', type=str, default='fixed',
                       choices=['fixed', 'trailing', 'breakeven'],
                       help='Exit type (default: fixed)')
    
    args = parser.parse_args()
    
    # Initialize backtest engine
    engine = BacktestEngine(entry_type=args.entry_type, exit_type=args.exit_type)
    
    # Run backtest
    results_df = engine.run_backtest(
        pairs=args.pairs,
        timeframes=args.timeframes,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    # Calculate and print statistics
    stats = engine.get_performance_stats()
    print_performance_stats(stats)
    
    # Save results if output specified
    if args.output:
        output_path = Path(args.output)
        results_df.to_csv(output_path, index=False)
        print(f"✓ Results saved to {output_path}")
    
    # Print sample trades
    if len(results_df) > 0:
        print("\nSample Trades (first 10):")
        print(results_df[['trade_id', 'pair', 'timeframe', 'direction', 'entry_time', 
                         'exit_time', 'exit_reason', 'pnl_pips']].head(10).to_string(index=False))
