"""
Report Helpers - Statistics & Report Generation
------------------------------------------------

Shared functions for generating Pure Strategy and Conservative reports.
Used by both mini and full backtest scripts.
"""

import pandas as pd
import numpy as np
from datetime import datetime


def price_per_pip(pair: str) -> float:
    """Get pip value for a currency pair"""
    return 0.01 if "JPY" in pair else 0.0001


def calc_stats(trades_df, start_cap=100000, risk=0.01, commission_total=0, avg_spread_pips=0):
    """
    Calculate comprehensive statistics from trades DataFrame

    Args:
        trades_df: DataFrame with trade data
        start_cap: Starting capital
        risk: Risk per trade (as decimal, e.g. 0.01 = 1%)
        commission_total: Total commission paid (for Conservative only)
        avg_spread_pips: Average spread per trade (for Conservative only)

    Returns:
        Dictionary with all statistics
    """
    if len(trades_df) == 0:
        return None

    tdf = trades_df.copy()

    # Separate winners/losers and long/short
    winners = tdf[tdf["pnl_r"] > 0]
    losers = tdf[tdf["pnl_r"] <= 0]
    longs = tdf[tdf["direction"] == "bullish"]
    shorts = tdf[tdf["direction"] == "bearish"]
    long_winners = longs[longs["pnl_r"] > 0]
    short_winners = shorts[shorts["pnl_r"] > 0]

    # Basic metrics
    total_trades = len(tdf)
    win_count = len(winners)
    loss_count = len(losers)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

    # Long/Short breakdown
    long_count = len(longs)
    short_count = len(shorts)
    long_short_ratio = (long_count / short_count) if short_count > 0 else 0
    long_win_rate = (len(long_winners) / long_count * 100) if long_count > 0 else 0
    short_win_rate = (len(short_winners) / short_count * 100) if short_count > 0 else 0

    # Win/Loss stats
    avg_winner = winners["pnl_r"].mean() if len(winners) > 0 else 0
    max_winner = winners["pnl_r"].max() if len(winners) > 0 else 0
    avg_loser = losers["pnl_r"].mean() if len(losers) > 0 else 0
    max_loser = losers["pnl_r"].min() if len(losers) > 0 else 0

    sum_wins = winners["pnl_r"].sum() if len(winners) > 0 else 0
    sum_losses = abs(losers["pnl_r"].sum()) if len(losers) > 0 else 0
    profit_factor = (sum_wins / sum_losses) if sum_losses > 0 else 0

    payoff_ratio = (avg_winner / abs(avg_loser)) if avg_loser != 0 else 0
    expectancy = tdf["pnl_r"].mean()

    # Duration
    tdf['duration_hours'] = (
        pd.to_datetime(tdf['exit_time']) - pd.to_datetime(tdf['entry_time'])
    ).dt.total_seconds() / 3600
    avg_duration_days = tdf['duration_hours'].mean() / 24

    start_date = pd.to_datetime(tdf['entry_time'].min())
    end_date = pd.to_datetime(tdf['entry_time'].max())
    months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    trades_per_month = total_trades / months if months > 0 else 0

    # Portfolio metrics
    equity = start_cap
    peak = start_cap
    drawdowns = []
    cons_wins = []
    cons_losses = []
    curr_win_str = 0
    curr_loss_str = 0
    concurrent = []

    for idx, trade in tdf.iterrows():
        pnl_dollars = trade['pnl_r'] * start_cap * risk
        equity += pnl_dollars
        if equity > peak:
            peak = equity
        dd = (equity - peak) / peak * 100
        drawdowns.append(dd)

        if trade['pnl_r'] > 0:
            curr_win_str += 1
            if curr_loss_str > 0:
                cons_losses.append(curr_loss_str)
                curr_loss_str = 0
        else:
            curr_loss_str += 1
            if curr_win_str > 0:
                cons_wins.append(curr_win_str)
                curr_win_str = 0

        # Concurrent trades
        entry_t = pd.to_datetime(trade['entry_time'])
        exit_t = pd.to_datetime(trade['exit_time'])
        conc_cnt = 0
        for idx2, other in tdf.iterrows():
            if idx == idx2:
                continue
            other_entry = pd.to_datetime(other['entry_time'])
            other_exit = pd.to_datetime(other['exit_time'])
            if other_entry <= entry_t <= other_exit:
                conc_cnt += 1
        concurrent.append(conc_cnt)

    if curr_win_str > 0:
        cons_wins.append(curr_win_str)
    if curr_loss_str > 0:
        cons_losses.append(curr_loss_str)

    ending_capital = equity
    total_return = ((ending_capital - start_cap) / start_cap) * 100
    years = (end_date - start_date).days / 365.25

    # CAGR: Handle negative returns (can't take root of negative)
    if years > 0 and ending_capital > 0:
        cagr = (((ending_capital / start_cap) ** (1 / years)) - 1) * 100
    else:
        cagr = 0

    max_dd = min(drawdowns) if len(drawdowns) > 0 else 0
    avg_dd = np.mean([dd for dd in drawdowns if dd < 0]) if any(dd < 0 for dd in drawdowns) else 0
    max_dd_dur = 0
    curr_dd_dur = 0
    for dd in drawdowns:
        if dd < 0:
            curr_dd_dur += 1
            max_dd_dur = max(max_dd_dur, curr_dd_dur)
        else:
            curr_dd_dur = 0

    recovery_factor = (total_return / abs(max_dd)) if max_dd != 0 else 0
    calmar = (cagr / abs(max_dd)) if max_dd != 0 else 0

    # Risk-adjusted
    returns = tdf['pnl_r'].values
    avg_return = np.mean(returns)
    std_return = np.std(returns, ddof=1) if len(returns) > 1 else 0
    trades_per_year = trades_per_month * 12
    sharpe = (avg_return / std_return) * np.sqrt(trades_per_year) if std_return > 0 else 0

    downside_rets = returns[returns < 0]
    downside_std = np.std(downside_rets, ddof=1) if len(downside_rets) > 1 else 0
    sortino = (avg_return / downside_std) * np.sqrt(trades_per_year) if downside_std > 0 else 0
    annualized_vol = std_return * np.sqrt(trades_per_year) * 100 if std_return > 0 else 0

    max_consec_wins = max(cons_wins) if len(cons_wins) > 0 else 0
    max_consec_losses = max(cons_losses) if len(cons_losses) > 0 else 0
    avg_concurrent = np.mean(concurrent) if len(concurrent) > 0 else 0
    max_concurrent = max(concurrent) if len(concurrent) > 0 else 0

    # MFE/MAE
    mfe_all = tdf['mfe_pips'].mean()
    mae_all = tdf['mae_pips'].mean()
    mfe_winners = winners['mfe_pips'].mean() if len(winners) > 0 else 0
    mfe_losers = losers['mfe_pips'].mean() if len(losers) > 0 else 0
    mae_winners = winners['mae_pips'].mean() if len(winners) > 0 else 0
    mae_losers = losers['mae_pips'].mean() if len(losers) > 0 else 0

    worst_trade_loss = losers['pnl_r'].min() if len(losers) > 0 else 0
    worst_day_loss_pct = abs(worst_trade_loss) * risk * 100

    # Commission stats (for Conservative)
    avg_commission = commission_total / total_trades if total_trades > 0 else 0

    # Avg lots (if available in df)
    avg_lots = tdf['lots'].mean() if 'lots' in tdf.columns else 0

    return {
        'total_trades': total_trades, 'winning_trades': win_count, 'losing_trades': loss_count,
        'win_rate': win_rate, 'avg_winner': avg_winner, 'max_winner': max_winner,
        'avg_loser': avg_loser, 'max_loser': max_loser,
        'profit_factor': profit_factor, 'payoff_ratio': payoff_ratio, 'expectancy': expectancy,
        'avg_duration_days': avg_duration_days, 'trades_per_month': trades_per_month,
        'starting_capital': start_cap, 'ending_capital': ending_capital,
        'total_return': total_return, 'cagr': cagr, 'max_dd': max_dd, 'max_dd_duration': max_dd_dur,
        'avg_dd': avg_dd, 'recovery_factor': recovery_factor, 'calmar': calmar,
        'max_consec_wins': max_consec_wins, 'max_consec_losses': max_consec_losses,
        'avg_concurrent_trades': avg_concurrent, 'max_concurrent_trades': max_concurrent,
        'sharpe': sharpe, 'sortino': sortino, 'annualized_volatility': annualized_vol,
        'mfe_all': mfe_all, 'mae_all': mae_all, 'mfe_winners': mfe_winners,
        'mfe_losers': mfe_losers, 'mae_winners': mae_winners, 'mae_losers': mae_losers,
        'worst_day_loss_pct': worst_day_loss_pct,
        'long_trades': long_count, 'short_trades': short_count,
        'long_short_ratio': long_short_ratio, 'long_win_rate': long_win_rate,
        'short_win_rate': short_win_rate, 'total_commission_paid': commission_total,
        'avg_commission_per_trade': avg_commission, 'avg_spread_pips': avg_spread_pips,
        'avg_lots_per_trade': avg_lots,
    }


def format_report(stats, report_type, config):
    """
    Format statistics into text report

    Args:
        stats: Statistics dictionary from calc_stats()
        report_type: "PURE STRATEGY" or "CONSERVATIVE"
        config: Dict with START_DATE, END_DATE, PAIRS, etc.

    Returns:
        Formatted report string
    """
    lines = ["=" * 80, f"MODEL 3 - BACKTEST REPORT ({report_type})", "=" * 80]
    lines.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Test Period: {config['START_DATE']} to {config['END_DATE']}")
    lines.append(f"Pairs Tested: {len(config['PAIRS'])}")
    lines.append(f"HTF Timeframe: W")
    lines.append(f"Entry Type: {config['ENTRY_CONFIRMATION']}")
    lines.append(f"Risk per Trade: {config['RISK_PER_TRADE']*100:.1f}%")
    lines.append(f"Starting Capital: ${config['STARTING_CAPITAL']:,.0f}")

    if report_type == 'PURE STRATEGY':
        lines.append(f"Transaction Costs: NONE (Pure Strategy)")
    else:
        lines.append(f"Transaction Costs: Variable Spreads (avg {stats['avg_spread_pips']:.2f} pips) + $5/lot Commission")

    lines.append("=" * 80 + "\n")

    lines.append("--- PERFORMANCE SUMMARY ---")
    lines.append(f"Total Trades: {stats['total_trades']}")
    lines.append(f"Long Trades: {stats['long_trades']} ({stats['long_trades']/stats['total_trades']*100:.1f}%)")
    lines.append(f"Short Trades: {stats['short_trades']} ({stats['short_trades']/stats['total_trades']*100:.1f}%)")
    lines.append(f"Long/Short Ratio: {stats['long_short_ratio']:.2f}:1\n")

    lines.append(f"Winning Trades: {stats['winning_trades']} ({stats['win_rate']:.1f}%)")
    lines.append(f"Long Win Rate: {stats['long_win_rate']:.1f}%")
    lines.append(f"Short Win Rate: {stats['short_win_rate']:.1f}%")
    lines.append(f"Losing Trades: {stats['losing_trades']} ({100-stats['win_rate']:.1f}%)\n")

    lines.append(f"Average Winner: +{stats['avg_winner']:.2f}R")
    lines.append(f"Max Winner: +{stats['max_winner']:.2f}R")
    lines.append(f"Average Loser: {stats['avg_loser']:.2f}R")
    lines.append(f"Max Loser: {stats['max_loser']:.2f}R\n")

    lines.append(f"Profit Factor: {stats['profit_factor']:.2f}")
    lines.append(f"Payoff Ratio: {stats['payoff_ratio']:.2f}")
    lines.append(f"Expectancy: {stats['expectancy']:+.2f}R per trade\n")
    lines.append(f"Average Trade Duration: {stats['avg_duration_days']:.1f} days")
    lines.append(f"Trades per Month: {stats['trades_per_month']:.1f}\n")

    if report_type == 'CONSERVATIVE':
        lines.append(f"Total Commission Paid: ${stats['total_commission_paid']:,.2f}")
        lines.append(f"Avg Commission per Trade: ${stats['avg_commission_per_trade']:.2f}")
        lines.append(f"Avg Lots per Trade: {stats['avg_lots_per_trade']:.2f}\n")

    lines.append("--- PORTFOLIO METRICS ---")
    lines.append(f"Starting Capital: ${stats['starting_capital']:,.0f}")
    lines.append(f"Ending Capital: ${stats['ending_capital']:,.0f}")
    lines.append(f"Total Return: {stats['total_return']:+.1f}%")
    lines.append(f"CAGR: {stats['cagr']:.1f}%\n")
    lines.append(f"Maximum Drawdown: {stats['max_dd']:.1f}%")
    lines.append(f"Max DD Duration: {stats['max_dd_duration']} trades")
    lines.append(f"Average Drawdown: {stats['avg_dd']:.1f}%")
    lines.append(f"Recovery Factor: {stats['recovery_factor']:.2f}")
    lines.append(f"Calmar Ratio: {stats['calmar']:.2f}\n")
    lines.append(f"Max Consecutive Wins: {stats['max_consec_wins']}")
    lines.append(f"Max Consecutive Losses: {stats['max_consec_losses']}\n")
    lines.append(f"Average Concurrent Trades: {stats['avg_concurrent_trades']:.1f}")
    lines.append(f"Max Concurrent Trades: {stats['max_concurrent_trades']}\n")

    lines.append("--- RISK-ADJUSTED RETURNS ---")
    sharpe_ok = "[OK]" if stats['sharpe'] > 1.5 else "[FAIL]"
    sortino_ok = "[OK]" if stats['sortino'] > 2.0 else "[FAIL]"
    lines.append(f"Sharpe Ratio: {stats['sharpe']:.2f} {sharpe_ok} (>1.5 target)")
    lines.append(f"Sortino Ratio: {stats['sortino']:.2f} {sortino_ok} (>2.0 target)")
    lines.append(f"Annualized Volatility: {stats['annualized_volatility']:.1f}%\n")

    lines.append("--- FUNDED ACCOUNT VIABILITY ---")
    chk_dd = "[OK]" if abs(stats['max_dd']) < 10 else "[FAIL]"
    chk_avg_dd = "[OK]" if abs(stats['avg_dd']) < 7 else "[FAIL]"
    chk_worst = "[OK]" if stats['worst_day_loss_pct'] < 4 else "[FAIL]"
    chk_sharpe = "[OK]" if stats['sharpe'] > 1.5 else "[FAIL]"
    chk_calmar = "[OK]" if stats['calmar'] > 2.0 else "[FAIL]"
    chk_trades = "[OK]" if stats['total_trades'] >= 200 else "[FAIL]"
    lines.append(f"{chk_dd} Max Drawdown < 10%: {'PASS' if chk_dd == '[OK]' else 'FAIL'} ({abs(stats['max_dd']):.1f}%)")
    lines.append(f"{chk_avg_dd} Avg Drawdown < 7%: {'PASS' if chk_avg_dd == '[OK]' else 'FAIL'} ({abs(stats['avg_dd']):.1f}%)")
    lines.append(f"{chk_worst} Worst Day Loss < 4%: {'PASS' if chk_worst == '[OK]' else 'FAIL'} ({stats['worst_day_loss_pct']:.1f}%)")
    lines.append(f"{chk_sharpe} Sharpe Ratio > 1.5: {'PASS' if chk_sharpe == '[OK]' else 'FAIL'} ({stats['sharpe']:.2f})")
    lines.append(f"{chk_calmar} Calmar Ratio > 2.0: {'PASS' if chk_calmar == '[OK]' else 'FAIL'} ({stats['calmar']:.2f})")
    lines.append(f"{chk_trades} Min. 200 Trades: {'PASS' if chk_trades == '[OK]' else 'FAIL'} ({stats['total_trades']})")
    all_chk = [chk_dd, chk_avg_dd, chk_worst, chk_sharpe, chk_calmar, chk_trades]
    overall = "[OK]" if all(c == "[OK]" for c in all_chk) else "[FAIL]"
    lines.append(f"\nOVERALL VERDICT: {overall} FUNDED ACCOUNT {'VIABLE' if overall == '[OK]' else 'NOT VIABLE'}\n")

    lines.append("--- MAX FAVORABLE/ADVERSE EXCURSION ---")
    lines.append(f"Average MFE (All): {stats['mfe_all']:.1f} pips")
    lines.append(f"Average MFE (Winners): {stats['mfe_winners']:.1f} pips")
    lines.append(f"Average MFE (Losers): {stats['mfe_losers']:.1f} pips\n")
    lines.append(f"Average MAE (All): {stats['mae_all']:.1f} pips")
    lines.append(f"Average MAE (Winners): {stats['mae_winners']:.1f} pips")
    lines.append(f"Average MAE (Losers): {stats['mae_losers']:.1f} pips\n")

    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)
    return "\n".join(lines)


def apply_conservative_costs(trades_pure_df, start_cap=100000, risk=0.01):
    """
    Apply conservative transaction costs to pure strategy trades

    Adds:
    - Variable entry spreads (0.4-2.5 pips, avg ~1.0-1.5)
    - Variable exit spreads (0.4-2.5 pips, avg ~1.0-1.5)
    - Commission ($5 per standard lot)

    Returns:
        DataFrame with conservative trades + new columns:
        - entry_spread_pips, exit_spread_pips, commission_usd, lots
    """
    trades_cons = trades_pure_df.copy()

    # Add new columns
    trades_cons['entry_spread_pips'] = 0.0
    trades_cons['exit_spread_pips'] = 0.0
    trades_cons['commission_usd'] = 0.0
    trades_cons['lots'] = 0.0

    for idx, row in trades_cons.iterrows():
        pip_val = price_per_pip(row['pair'])

        # Variable spreads (random 0.4-2.5 pips, avg ~1.0-1.5)
        entry_spread_pips = np.random.uniform(0.4, 2.5)
        exit_spread_pips = np.random.uniform(0.4, 2.5)

        entry_spread_price = entry_spread_pips * pip_val
        exit_spread_price = exit_spread_pips * pip_val

        # Apply spreads to entry and exit
        if row['direction'] == 'bullish':
            real_entry = row['entry_price'] + entry_spread_price
            real_exit = row['exit_price'] - exit_spread_price
        else:
            real_entry = row['entry_price'] - entry_spread_price
            real_exit = row['exit_price'] + exit_spread_price

        # Calculate position size
        risk_pips = abs(row['entry_price'] - row['sl_price']) / pip_val
        position_dollars = start_cap * risk
        dollars_per_pip = position_dollars / risk_pips if risk_pips > 0 else 0

        # Standard lot pip values
        if 'JPY' in row['pair']:
            standard_lot_pip_value = 1000  # JPY pairs: $1000 per pip per lot
        else:
            standard_lot_pip_value = 10    # Non-JPY: $10 per pip per lot

        lots = dollars_per_pip / standard_lot_pip_value
        commission = lots * 5.0  # $5 per standard lot

        # Recalculate PnL with costs
        if row['direction'] == 'bullish':
            pnl_price = real_exit - real_entry
        else:
            pnl_price = real_entry - real_exit

        pnl_pips = pnl_price / pip_val
        pnl_dollars = pnl_pips * dollars_per_pip
        pnl_dollars_after_commission = pnl_dollars - commission
        pnl_r_conservative = pnl_dollars_after_commission / position_dollars

        # Update row
        trades_cons.at[idx, 'pnl_r'] = pnl_r_conservative
        trades_cons.at[idx, 'pnl_pips'] = pnl_pips
        trades_cons.at[idx, 'entry_spread_pips'] = entry_spread_pips
        trades_cons.at[idx, 'exit_spread_pips'] = exit_spread_pips
        trades_cons.at[idx, 'commission_usd'] = commission
        trades_cons.at[idx, 'lots'] = lots

    return trades_cons
