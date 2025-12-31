"""
Generate Performance Reports for COT-Filtered Trades

Identical format to Phase 2 reports, with additional COT filter statistics.
Includes comprehensive statistics ported from Phase 2 `report_helpers.py`.

Author: Claude & Gemini
Date: 2025-12-31
"""

import pandas as pd
import numpy as np
from pathlib import Path
import itertools
from typing import Dict
from datetime import datetime


def calculate_statistics(trades_df: pd.DataFrame) -> Dict:
    """
    Calculate performance statistics from trades.
    (Enhanced with metrics from Phase 2)
    """
    if len(trades_df) == 0:
        return {
            'total_trades': 0, 'winning_trades': 0, 'losing_trades': 0, 'breakeven_trades': 0,
            'win_rate': 0, 'avg_win': 0, 'avg_loss': 0, 'expectancy': 0, 'profit_factor': 0,
            'total_pips': 0, 'avg_pips': 0, 'total_r': 0, 'avg_r': 0, 'payoff_ratio': 0,
            'max_winner': 0, 'max_loser': 0, 'long_trades': 0, 'short_trades': 0,
            'long_win_rate': 0, 'short_win_rate': 0, 'long_short_ratio': 0,
            'avg_duration_days': 0, 'trades_per_month': 0
        }

    tdf = trades_df.copy()
    total_trades = len(tdf)

    # Normalize direction column for safety
    tdf['direction'] = tdf['direction'].str.lower()

    # Winners and Losers
    winners = tdf[tdf["pnl_r"] > 0]
    losers = tdf[tdf["pnl_r"] < 0]
    breakeven_trades = tdf[tdf["pnl_r"] == 0]
    winning_trades = len(winners)
    losing_trades = len(losers)
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

    # Long/Short Breakdown
    longs = tdf[tdf["direction"].str.contains('long|bullish')]
    shorts = tdf[tdf["direction"].str.contains('short|bearish')]
    long_winners = longs[longs["pnl_r"] > 0]
    short_winners = shorts[shorts["pnl_r"] > 0]
    long_count = len(longs)
    short_count = len(shorts)
    long_short_ratio = (long_count / short_count) if short_count > 0 else 0
    long_win_rate = (len(long_winners) / long_count * 100) if long_count > 0 else 0
    short_win_rate = (len(short_winners) / short_count * 100) if short_count > 0 else 0

    # Averages
    avg_win = winners["pnl_r"].mean() if winning_trades > 0 else 0
    avg_loss = losers["pnl_r"].mean() if losing_trades > 0 else 0
    max_winner = winners["pnl_r"].max() if winning_trades > 0 else 0
    max_loser = losers["pnl_r"].min() if losing_trades > 0 else 0

    # R-Multiples & Factors
    total_win_r = winners["pnl_r"].sum()
    total_loss_r = abs(losers["pnl_r"].sum())
    profit_factor = (total_win_r / total_loss_r) if total_loss_r > 0 else np.inf
    payoff_ratio = (avg_win / abs(avg_loss)) if avg_loss != 0 else 0
    expectancy = tdf["pnl_r"].mean()
    total_r = tdf["pnl_r"].sum()
    avg_r = expectancy

    # Pips
    total_pips = tdf['pnl_pips'].sum() if 'pnl_pips' in tdf.columns else 0
    avg_pips = tdf['pnl_pips'].mean() if 'pnl_pips' in tdf.columns else 0

    # Duration
    tdf['exit_time'] = pd.to_datetime(tdf['exit_time'])
    tdf['entry_time'] = pd.to_datetime(tdf['entry_time'])
    tdf['duration_hours'] = (tdf['exit_time'] - tdf['entry_time']).dt.total_seconds() / 3600
    avg_duration_days = tdf['duration_hours'].mean() / 24

    start_date = tdf['entry_time'].min()
    end_date = tdf['entry_time'].max()
    months = ((end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1) if not tdf.empty else 1
    trades_per_month = total_trades / months if months > 0 else 0

    return {
        'total_trades': total_trades, 'winning_trades': winning_trades, 'losing_trades': losing_trades,
        'breakeven_trades': len(breakeven_trades), 'win_rate': win_rate, 'avg_win': avg_win,
        'avg_loss': avg_loss, 'expectancy': expectancy, 'profit_factor': profit_factor,
        'total_pips': total_pips, 'avg_pips': avg_pips, 'total_r': total_r, 'avg_r': avg_r,
        'payoff_ratio': payoff_ratio, 'max_winner': max_winner, 'max_loser': max_loser,
        'long_trades': long_count, 'short_trades': short_count, 'long_win_rate': long_win_rate,
        'short_win_rate': short_win_rate, 'long_short_ratio': long_short_ratio,
        'avg_duration_days': avg_duration_days, 'trades_per_month': trades_per_month,
    }

def calculate_portfolio_metrics(trades_df: pd.DataFrame, starting_capital: float = 100000, risk_per_trade: float = 0.01) -> Dict:
    """
    Calculate portfolio-level metrics.
    (Enhanced with metrics from Phase 2)
    """
    if len(trades_df) == 0:
        return {
            'starting_capital': starting_capital, 'final_balance': starting_capital,
            'total_return': 0, 'cagr': 0, 'max_drawdown': 0, 'avg_dd': 0, 'max_dd_duration': 0,
            'recovery_factor': 0, 'calmar_ratio': 0, 'sharpe_ratio': 0, 'sortino_ratio': 0,
            'volatility': 0, 'max_consec_wins': 0, 'max_consec_losses': 0,
            'avg_concurrent_trades': 0, 'max_concurrent_trades': 0
        }

    tdf = trades_df.copy()
    tdf['exit_time'] = pd.to_datetime(tdf['exit_time'])
    tdf['entry_time'] = pd.to_datetime(tdf['entry_time'])
    tdf = tdf.sort_values('entry_time').reset_index(drop=True)

    # Equity Curve, Drawdown, Streaks, Concurrency
    equity = starting_capital
    peak = starting_capital
    equity_curve = [starting_capital]
    drawdowns = []
    cons_wins, cons_losses = [], []
    curr_win_str, curr_loss_str = 0, 0
    concurrent_trades = []

    for i in range(len(tdf)):
        trade = tdf.iloc[i]
        # Use compounding equity for PnL calculation
        pnl_dollars = trade['pnl_r'] * equity * risk_per_trade
        equity += pnl_dollars
        equity_curve.append(equity)

        if equity > peak:
            peak = equity
        dd = (equity - peak) / peak * 100 if peak > 0 else 0
        drawdowns.append(dd)

        if trade['pnl_r'] > 0:
            curr_win_str += 1
            if curr_loss_str > 0:
                cons_losses.append(curr_loss_str)
            curr_loss_str = 0
        else: # includes breakeven
            curr_loss_str += 1
            if curr_win_str > 0:
                cons_wins.append(curr_win_str)
            curr_win_str = 0

        # Concurrency - count how many other trades were open during this one
        overlapping = tdf[
            (tdf['entry_time'] < trade['exit_time']) & (tdf['exit_time'] > trade['entry_time'])
        ]
        concurrent_trades.append(len(overlapping))

    if curr_win_str > 0: cons_wins.append(curr_win_str)
    if curr_loss_str > 0: cons_losses.append(curr_loss_str)

    final_balance = equity
    total_return = (final_balance - starting_capital) / starting_capital * 100

    # Time-based metrics
    days_total = (tdf['exit_time'].max() - tdf['entry_time'].min()).days if not tdf.empty else 0
    years = days_total / 365.25 if days_total > 0 else 1.0
    cagr = ((final_balance / starting_capital) ** (1 / years) - 1) * 100 if years > 0 and final_balance > 0 and starting_capital > 0 else 0

    # Drawdown metrics
    max_drawdown = abs(min(drawdowns)) if drawdowns else 0
    avg_dd = np.mean([d for d in drawdowns if d < 0]) if any(d < 0 for d in drawdowns) else 0

    in_drawdown = np.array(drawdowns) < 0
    dd_durations = [len(list(g)) for k, g in itertools.groupby(in_drawdown) if k]
    max_dd_duration = max(dd_durations) if dd_durations else 0

    # Ratios
    recovery_factor = total_return / max_drawdown if max_drawdown > 0 else 0
    calmar_ratio = cagr / max_drawdown if max_drawdown > 0 else 0

    # Risk-adjusted returns
    returns = tdf['pnl_r'] * risk_per_trade
    mean_return = returns.mean()
    std_return = returns.std()

    trades_per_year = len(tdf) / years if years > 0 else len(tdf)
    sharpe_ratio = (mean_return / std_return) * np.sqrt(trades_per_year) if std_return > 0 else 0
    downside_returns = returns[returns < 0]
    downside_std = downside_returns.std() if len(downside_returns) > 0 else 0
    sortino_ratio = (mean_return / downside_std) * np.sqrt(trades_per_year) if downside_std > 0 else 0
    volatility = std_return * np.sqrt(trades_per_year) * 100

    return {
        'starting_capital': starting_capital, 'final_balance': final_balance,
        'total_return': total_return, 'cagr': cagr, 'max_drawdown': max_drawdown,
        'avg_dd': abs(avg_dd), 'max_dd_duration': max_dd_duration,
        'recovery_factor': recovery_factor, 'calmar_ratio': calmar_ratio,
        'sharpe_ratio': sharpe_ratio, 'sortino_ratio': sortino_ratio, 'volatility': volatility,
        'max_consec_wins': max(cons_wins) if cons_wins else 0,
        'max_consec_losses': max(cons_losses) if cons_losses else 0,
        'avg_concurrent_trades': np.mean(concurrent_trades) if concurrent_trades else 0,
        'max_concurrent_trades': np.max(concurrent_trades) if concurrent_trades else 0,
    }

def calculate_mfe_mae(trades_df: pd.DataFrame) -> Dict:
    """
    Calculate MFE/MAE analysis, including separate stats for winners and losers.
    """
    if len(trades_df) == 0 or 'mfe_pips' not in trades_df.columns:
        return {
            'avg_mfe_pips': 0, 'avg_mae_pips': 0, 'mfe_mae_ratio': 0,
            'mfe_winners': 0, 'mae_winners': 0, 'mfe_losers': 0, 'mae_losers': 0
        }

    winners = trades_df[trades_df['pnl_r'] > 0]
    losers = trades_df[trades_df['pnl_r'] < 0]
    
    mae_mean = trades_df['mae_pips'].mean()

    return {
        'avg_mfe_pips': trades_df['mfe_pips'].mean(),
        'avg_mae_pips': mae_mean,
        'mfe_mae_ratio': trades_df['mfe_pips'].mean() / abs(mae_mean) if mae_mean != 0 else 0,
        'mfe_winners': winners['mfe_pips'].mean() if len(winners) > 0 else 0,
        'mae_winners': winners['mae_pips'].mean() if len(winners) > 0 else 0,
        'mfe_losers': losers['mfe_pips'].mean() if len(losers) > 0 else 0,
        'mae_losers': losers['mae_pips'].mean() if len(losers) > 0 else 0,
    }

def format_report(stats: Dict, portfolio: Dict, mfe_mae: Dict, title: str,
                  original_count: int = None, filter_rate: float = None,
                  phase2_stats: Dict = None, phase2_portfolio: Dict = None) -> str:
    """
    Format statistics into a comprehensive report text.
    (Enhanced with sections from Phase 2)
    """
    def fmt_chg(val, p2_val, unit, is_percent=False):
        diff = val - p2_val
        sign = "+" if diff >= 0 else ""
        if is_percent:
            return f"{val:.1f}{unit} (P2: {p2_val:.1f}{unit}, {sign}{diff:.1f}{unit})"
        else:
            return f"{val:.2f}{unit} (P2: {p2_val:.2f}{unit}, {sign}{diff:.2f}{unit})"

    lines = ["="*80, title, "="*80, ""]

    # Filter Info
    if original_count is not None:
        lines.append("=== COT FILTER INFO ===")
        lines.append(f"Original Trades (Phase 2): {original_count}")
        lines.append(f"Filtered Trades (Phase 3): {stats['total_trades']}")
        lines.append(f"Filter Rate: {filter_rate:.1f}% removed")
        lines.append(f"Trades Removed: {original_count - stats['total_trades']}\n")

    # Summary
    lines.append("--- PERFORMANCE SUMMARY ---")
    p2_mode = phase2_stats is not None
    lines.append(f"Total Trades: {stats['total_trades']}" + (f" (P2: {phase2_stats.get('total_trades', 0)})" if p2_mode else ""))
    lines.append(f"Win Rate: {fmt_chg(stats['win_rate'], phase2_stats.get('win_rate', 0), '%', True) if p2_mode else f'{stats.get("win_rate", 0):.1f}%'}")
    lines.append(f"Profit Factor: {fmt_chg(stats['profit_factor'], phase2_stats.get('profit_factor', 0), '') if p2_mode else f'{stats.get("profit_factor", 0):.2f}'}")
    lines.append(f"Expectancy: {fmt_chg(stats['expectancy'], phase2_stats.get('expectancy', 0), 'R') if p2_mode else f'{stats.get("expectancy", 0):.2f}R'}\n")

    # Long/Short
    lines.append("--- LONG/SHORT BREAKDOWN ---")
    total_trades = stats.get('total_trades', 0)
    long_trades_pct = (stats.get('long_trades', 0) / total_trades * 100) if total_trades > 0 else 0
    short_trades_pct = (stats.get('short_trades', 0) / total_trades * 100) if total_trades > 0 else 0
    lines.append(f"Long Trades: {stats.get('long_trades', 0)} ({long_trades_pct:.1f}%) | Win Rate: {stats.get('long_win_rate', 0):.1f}%")
    lines.append(f"Short Trades: {stats.get('short_trades', 0)} ({short_trades_pct:.1f}%) | Win Rate: {stats.get('short_win_rate', 0):.1f}%")
    lines.append(f"Long/Short Ratio: {stats.get('long_short_ratio', 0):.2f}:1\n")

    # Win/Loss Details
    lines.append("--- WIN/LOSS ANALYSIS ---")
    lines.append(f"Payoff Ratio: {stats.get('payoff_ratio', 0):.2f}")
    lines.append(f"Average Win: {fmt_chg(stats.get('avg_win',0), phase2_stats.get('avg_win', 0), 'R') if p2_mode else f'{stats.get("avg_win", 0):.2f}R'}")
    lines.append(f"Average Loss: {fmt_chg(stats.get('avg_loss',0), phase2_stats.get('avg_loss', 0), 'R') if p2_mode else f'{stats.get("avg_loss", 0):.2f}R'}")
    lines.append(f"Max Winner: {stats.get('max_winner', 0):.2f}R | Max Loser: {stats.get('max_loser', 0):.2f}R\n")

    # Trade Activity
    lines.append("--- TRADE ACTIVITY ---")
    lines.append(f"Average Trade Duration: {stats.get('avg_duration_days', 0):.1f} days")
    lines.append(f"Trades per Month: {stats.get('trades_per_month', 0):.1f}")
    lines.append(f"Max Consecutive Wins: {portfolio.get('max_consec_wins', 0)}")
    lines.append(f"Max Consecutive Losses: {portfolio.get('max_consec_losses', 0)}")
    lines.append(f"Average Concurrent Trades: {portfolio.get('avg_concurrent_trades', 0):.1f}")
    lines.append(f"Max Concurrent Trades: {portfolio.get('max_concurrent_trades', 0)}\n")

    # Portfolio
    lines.append("--- PORTFOLIO & RISK ---")
    p2p_mode = phase2_portfolio is not None
    lines.append(f"Starting Capital: ${portfolio.get('starting_capital', 0):,.0f}")
    lines.append(f"Ending Capital: ${portfolio.get('final_balance', 0):,.0f}" + (f" (P2: ${phase2_portfolio.get('final_balance', 0):,.0f})" if p2p_mode else ""))
    lines.append(f"Total Return: {fmt_chg(portfolio.get('total_return',0), phase2_portfolio.get('total_return', 0), '%', True) if p2p_mode else f'{portfolio.get("total_return", 0):.1f}%'}")
    lines.append(f"CAGR: {fmt_chg(portfolio.get('cagr',0), phase2_portfolio.get('cagr', 0), '%', True) if p2p_mode else f'{portfolio.get("cagr", 0):.1f}%'}\n")

    lines.append(f"Max Drawdown: {fmt_chg(portfolio.get('max_drawdown',0), phase2_portfolio.get('max_drawdown', 0), '%', True) if p2p_mode else f'{portfolio.get("max_drawdown", 0):.1f}%'}")
    lines.append(f"Average Drawdown: {portfolio.get('avg_dd', 0):.1f}%")
    lines.append(f"Max DD Duration: {portfolio.get('max_dd_duration', 0)} trades")
    lines.append(f"Recovery Factor: {portfolio.get('recovery_factor', 0):.2f}")
    lines.append(f"Calmar Ratio: {fmt_chg(portfolio.get('calmar_ratio',0), phase2_portfolio.get('calmar_ratio', 0), '') if p2p_mode else f'{portfolio.get("calmar_ratio", 0):.2f}'}\n")

    # Risk-Adjusted
    lines.append("--- RISK-ADJUSTED RETURNS ---")
    lines.append(f"Sharpe Ratio: {fmt_chg(portfolio.get('sharpe_ratio',0), phase2_portfolio.get('sharpe_ratio', 0), '') if p2p_mode else f'{portfolio.get("sharpe_ratio", 0):.2f}'}")
    lines.append(f"Sortino Ratio: {fmt_chg(portfolio.get('sortino_ratio',0), phase2_portfolio.get('sortino_ratio', 0), '') if p2p_mode else f'{portfolio.get("sortino_ratio", 0):.2f}'}")
    lines.append(f"Annualized Volatility: {portfolio.get('volatility', 0):.1f}%
")

    # MFE/MAE
    if 'mfe_winners' in mfe_mae and mfe_mae['mfe_winners'] is not None:
        lines.append("--- MFE/MAE ANALYSIS (PIPS) ---")
        lines.append(f"Average MFE (Winners): {mfe_mae.get('mfe_winners', 0):.1f} | Average MAE (Winners): {mfe_mae.get('mae_winners', 0):.1f}")
        lines.append(f"Average MFE (Losers): {mfe_mae.get('mfe_losers', 0):.1f} | Average MAE (Losers): {mfe_mae.get('mae_losers', 0):.1f}")
        lines.append(f"Overall MFE/MAE Ratio: {mfe_mae.get('mfe_mae_ratio', 0):.2f}\n")

    # Footer
    lines.append("=" * 80)
    lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 80)
    return "\n".join(lines)


def generate_report(trades_df: pd.DataFrame, output_path: Path, title: str,
                    original_count: int = None, filter_rate: float = None,
                    phase2_trades_df: pd.DataFrame = None):
    """
    Generate complete performance report with enhanced statistics.
    """
    # Calculate Phase 3 statistics
    stats = calculate_statistics(trades_df)
    portfolio = calculate_portfolio_metrics(trades_df)
    mfe_mae = calculate_mfe_mae(trades_df)

    # Calculate Phase 2 statistics (if provided)
    phase2_stats = None
    phase2_portfolio = None
    if phase2_trades_df is not None and not phase2_trades_df.empty:
        phase2_stats = calculate_statistics(phase2_trades_df)
        phase2_portfolio = calculate_portfolio_metrics(phase2_trades_df)

    # Format report
    report_text = format_report(
        stats=stats,
        portfolio=portfolio,
        mfe_mae=mfe_mae,
        title=title,
        original_count=original_count,
        filter_rate=filter_rate,
        phase2_stats=phase2_stats,
        phase2_portfolio=phase2_portfolio
    )

    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)


if __name__ == "__main__":
    print("This module is meant to be imported, not run directly.")
    print("Use: from generate_reports import generate_report")