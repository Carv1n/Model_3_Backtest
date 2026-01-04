"""
Report Helpers - REPORT1 Format (Optimization-Focused)
--------------------------------------------------------

Statistics & Report Generation for Model 3 Backtest
Implements REPORT1 format - simpler, focused on optimization metrics
"""

import pandas as pd
import numpy as np


def calc_stats(trades_df, start_cap=100000, risk=0.01):
    """
    Calculate comprehensive statistics from trades DataFrame (REPORT1 style)

    Args:
        trades_df: DataFrame with trade data
        start_cap: Starting capital
        risk: Risk per trade (as decimal, e.g. 0.01 = 1%)

    Returns:
        Dictionary with all statistics including:
        - Basic stats (win rate, expectancy, etc.)
        - SQN (System Quality Number)
        - Win Rate by RR Target (cumulative)
        - Pair Breakdown (Top 5 + Bottom 5 by Expectancy)
        - Long/Short breakdown
        - Drawdown & Streaks
        - Time-based performance (monthly/yearly)
    """
    if len(trades_df) == 0:
        return None

    tdf = trades_df.copy()

    # ========== BASIC METRICS ==========
    total_trades = len(tdf)
    winners = tdf[tdf["pnl_r"] > 0]
    losers = tdf[tdf["pnl_r"] <= 0]

    win_count = len(winners)
    loss_count = len(losers)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0

    # Win/Loss R-multiples
    avg_winner = winners["pnl_r"].mean() if len(winners) > 0 else 0
    avg_loser = losers["pnl_r"].mean() if len(losers) > 0 else 0
    max_winner = winners["pnl_r"].max() if len(winners) > 0 else 0
    max_loser = losers["pnl_r"].min() if len(losers) > 0 else 0
    median_r = tdf["pnl_r"].median()

    # Expectancy & Performance
    cumulative_r = tdf["pnl_r"].sum()
    expectancy = tdf["pnl_r"].mean()
    std_r = tdf["pnl_r"].std(ddof=1) if len(tdf) > 1 else 0

    # SQN (System Quality Number)
    sqn = (expectancy / std_r) * np.sqrt(total_trades) if std_r > 0 else 0

    # Profit Factor & Payoff Ratio
    sum_wins = winners["pnl_r"].sum() if len(winners) > 0 else 0
    sum_losses = abs(losers["pnl_r"].sum()) if len(losers) > 0 else 0
    profit_factor = (sum_wins / sum_losses) if sum_losses > 0 else 0
    payoff_ratio = (avg_winner / abs(avg_loser)) if avg_loser != 0 else 0

    # ========== LONG/SHORT BREAKDOWN ==========
    longs = tdf[tdf["direction"] == "bullish"]
    shorts = tdf[tdf["direction"] == "bearish"]
    long_count = len(longs)
    short_count = len(shorts)

    long_winners = longs[longs["pnl_r"] > 0]
    short_winners = shorts[shorts["pnl_r"] > 0]

    long_win_rate = (len(long_winners) / long_count * 100) if long_count > 0 else 0
    short_win_rate = (len(short_winners) / short_count * 100) if short_count > 0 else 0
    long_short_ratio = (long_count / short_count) if short_count > 0 else 0

    # ========== TIME-BASED STATS ==========
    tdf['entry_dt'] = pd.to_datetime(tdf['entry_time'])
    tdf['exit_dt'] = pd.to_datetime(tdf['exit_time'])

    start_date = tdf['entry_dt'].min()
    end_date = tdf['entry_dt'].max()
    years = (end_date - start_date).days / 365.25 if (end_date - start_date).days > 0 else 1

    # Monthly stats
    tdf['month'] = tdf['entry_dt'].dt.to_period('M')
    monthly_r = tdf.groupby('month')['pnl_r'].sum()

    total_months = len(monthly_r)
    profitable_months = (monthly_r > 0).sum()
    profitable_months_pct = (profitable_months / total_months * 100) if total_months > 0 else 0

    best_month = monthly_r.max() if len(monthly_r) > 0 else 0
    worst_month = monthly_r.min() if len(monthly_r) > 0 else 0
    avg_r_per_month = monthly_r.mean() if len(monthly_r) > 0 else 0

    # Yearly stats
    tdf['year'] = tdf['entry_dt'].dt.year
    yearly_r = tdf.groupby('year')['pnl_r'].sum()

    total_years = len(yearly_r)
    profitable_years = (yearly_r > 0).sum()
    profitable_years_pct = (profitable_years / total_years * 100) if total_years > 0 else 0

    best_year = yearly_r.max() if len(yearly_r) > 0 else 0
    worst_year = yearly_r.min() if len(yearly_r) > 0 else 0
    avg_r_per_year = cumulative_r / years if years > 0 else 0

    # ========== TRADE CHARACTERISTICS ==========
    tdf['duration_hours'] = (tdf['exit_dt'] - tdf['entry_dt']).dt.total_seconds() / 3600
    avg_duration_days = tdf['duration_hours'].mean() / 24
    min_duration_days = tdf['duration_hours'].min() / 24
    max_duration_days = tdf['duration_hours'].max() / 24

    trades_per_year = total_trades / years if years > 0 else 0
    trades_per_month = total_trades / total_months if total_months > 0 else 0
    trades_per_week = trades_per_year / 52 if trades_per_year > 0 else 0

    # Concurrent trades (optimized)
    concurrent_counts = []
    for idx, trade in tdf.iterrows():
        entry_t = trade['entry_dt']
        exit_t = trade['exit_dt']

        # Count overlapping trades
        overlaps = (
            (tdf['entry_dt'] <= entry_t) & (tdf['exit_dt'] >= entry_t) & (tdf.index != idx)
        ).sum()
        concurrent_counts.append(overlaps)

    avg_concurrent = np.mean(concurrent_counts) if len(concurrent_counts) > 0 else 0
    max_concurrent = max(concurrent_counts) if len(concurrent_counts) > 0 else 0

    # ========== DRAWDOWN & STREAKS (VECTORIZED) ==========
    equity = start_cap
    equity_curve = [equity]

    for pnl_r in tdf['pnl_r'].values:
        equity += pnl_r * start_cap * risk
        equity_curve.append(equity)

    equity_array = np.array(equity_curve)
    peak_array = np.maximum.accumulate(equity_array)
    drawdown_pct = ((equity_array - peak_array) / peak_array * 100)

    max_dd = drawdown_pct.min()
    avg_dd = drawdown_pct[drawdown_pct < 0].mean() if (drawdown_pct < 0).any() else 0

    # Max DD Duration (in trades)
    in_dd = drawdown_pct < 0
    dd_durations = []
    curr_duration = 0

    for is_dd in in_dd:
        if is_dd:
            curr_duration += 1
        else:
            if curr_duration > 0:
                dd_durations.append(curr_duration)
            curr_duration = 0
    if curr_duration > 0:
        dd_durations.append(curr_duration)

    max_dd_duration_trades = max(dd_durations) if len(dd_durations) > 0 else 0

    # Find max DD period details
    if max_dd_duration_trades > 0:
        # Find where max DD occurred
        max_dd_idx = np.argmin(drawdown_pct)

        # Calculate days for max DD period
        dd_start_idx = max(0, max_dd_idx - max_dd_duration_trades)
        dd_end_idx = max_dd_idx

        if dd_start_idx < len(tdf) and dd_end_idx < len(tdf):
            dd_start_date = tdf.iloc[dd_start_idx]['entry_dt']
            dd_end_date = tdf.iloc[dd_end_idx]['entry_dt']
            max_dd_duration_days = (dd_end_date - dd_start_date).days
        else:
            max_dd_duration_days = 0
    else:
        max_dd_duration_days = 0

    # Check if recovered from max DD
    final_dd = drawdown_pct[-1]
    recovered = abs(final_dd) < 0.01  # Within 0.01% of peak

    # Consecutive Wins/Losses (vectorized)
    is_winner = (tdf['pnl_r'] > 0).astype(int)

    # Find streaks
    streak_changes = np.diff(is_winner, prepend=is_winner.iloc[0])
    streak_starts = np.where(streak_changes != 0)[0]
    streak_lengths = np.diff(streak_starts, append=len(is_winner))

    win_streaks = streak_lengths[is_winner.iloc[streak_starts] == 1]
    loss_streaks = streak_lengths[is_winner.iloc[streak_starts] == 0]

    max_consec_wins = win_streaks.max() if len(win_streaks) > 0 else 0
    avg_consec_wins = win_streaks.mean() if len(win_streaks) > 0 else 0
    median_consec_wins = np.median(win_streaks) if len(win_streaks) > 0 else 0

    max_consec_losses = loss_streaks.max() if len(loss_streaks) > 0 else 0
    avg_consec_losses = loss_streaks.mean() if len(loss_streaks) > 0 else 0
    median_consec_losses = np.median(loss_streaks) if len(loss_streaks) > 0 else 0

    # ========== PORTFOLIO METRICS ==========
    ending_capital = equity_curve[-1]
    total_return = ((ending_capital - start_cap) / start_cap) * 100

    # CAGR
    if years > 0 and ending_capital > 0:
        cagr = (((ending_capital / start_cap) ** (1 / years)) - 1) * 100
    else:
        cagr = 0

    # Risk-adjusted metrics
    sharpe = (expectancy / std_r) * np.sqrt(trades_per_year) if std_r > 0 else 0

    downside_returns = tdf[tdf['pnl_r'] < 0]['pnl_r']
    downside_std = downside_returns.std(ddof=1) if len(downside_returns) > 1 else 0
    sortino = (expectancy / downside_std) * np.sqrt(trades_per_year) if downside_std > 0 else 0


    # ========== PAIR BREAKDOWN (TOP 5 + BOTTOM 5 BY EXPECTANCY) ==========
    pair_groups = tdf.groupby('pair')
    pair_stats = []

    for pair, group in pair_groups:
        pair_total = len(group)
        pair_winners = group[group['pnl_r'] > 0]
        pair_losers = group[group['pnl_r'] <= 0]

        pair_win_pct = (len(pair_winners) / pair_total * 100) if pair_total > 0 else 0
        pair_expectancy = group['pnl_r'].mean()

        pair_sum_wins = pair_winners['pnl_r'].sum() if len(pair_winners) > 0 else 0
        pair_sum_losses = abs(pair_losers['pnl_r'].sum()) if len(pair_losers) > 0 else 0
        pair_pf = (pair_sum_wins / pair_sum_losses) if pair_sum_losses > 0 else 0

        pair_avg_win = pair_winners['pnl_r'].mean() if len(pair_winners) > 0 else 0
        pair_avg_loss = pair_losers['pnl_r'].mean() if len(pair_losers) > 0 else 0
        pair_total_r = group['pnl_r'].sum()

        pair_stats.append({
            'pair': pair,
            'trades': pair_total,
            'win_pct': pair_win_pct,
            'expectancy': pair_expectancy,
            'profit_factor': pair_pf,
            'avg_win': pair_avg_win,
            'avg_loss': pair_avg_loss,
            'total_r': pair_total_r
        })

    # Sort by expectancy
    pair_stats_sorted = sorted(pair_stats, key=lambda x: x['expectancy'], reverse=True)

    top_5_pairs = pair_stats_sorted[:5] if len(pair_stats_sorted) >= 5 else pair_stats_sorted
    bottom_5_pairs = pair_stats_sorted[-5:] if len(pair_stats_sorted) >= 5 else []

    # ========== RETURN STATS DICTIONARY ==========
    return {
        # Basic stats
        'total_trades': total_trades,
        'winning_trades': win_count,
        'losing_trades': loss_count,
        'win_rate': win_rate,

        # R-multiples
        'avg_winner': avg_winner,
        'avg_loser': avg_loser,
        'max_winner': max_winner,
        'max_loser': max_loser,
        'median_r': median_r,
        'cumulative_r': cumulative_r,
        'expectancy': expectancy,
        'std_r': std_r,

        # Performance metrics
        'profit_factor': profit_factor,
        'payoff_ratio': payoff_ratio,
        'sqn': sqn,

        # Long/Short
        'long_trades': long_count,
        'short_trades': short_count,
        'long_short_ratio': long_short_ratio,
        'long_win_rate': long_win_rate,
        'short_win_rate': short_win_rate,

        # Portfolio
        'starting_capital': start_cap,
        'ending_capital': ending_capital,
        'total_return': total_return,
        'cagr': cagr,

        # Drawdown
        'max_dd': max_dd,
        'avg_dd': avg_dd,
        'max_dd_duration_trades': max_dd_duration_trades,
        'max_dd_duration_days': max_dd_duration_days,
        'recovered': recovered,

        # Streaks
        'max_consec_wins': int(max_consec_wins),
        'avg_consec_wins': avg_consec_wins,
        'median_consec_wins': int(median_consec_wins),
        'max_consec_losses': int(max_consec_losses),
        'avg_consec_losses': avg_consec_losses,
        'median_consec_losses': int(median_consec_losses),

        # Time-based
        'start_date': start_date,
        'end_date': end_date,
        'years': years,
        'total_months': total_months,
        'profitable_months': profitable_months,
        'profitable_months_pct': profitable_months_pct,
        'best_month': best_month,
        'worst_month': worst_month,
        'avg_r_per_month': avg_r_per_month,
        'total_years': total_years,
        'profitable_years': profitable_years,
        'profitable_years_pct': profitable_years_pct,
        'best_year': best_year,
        'worst_year': worst_year,
        'avg_r_per_year': avg_r_per_year,

        # Trade characteristics
        'avg_duration_days': avg_duration_days,
        'min_duration_days': min_duration_days,
        'max_duration_days': max_duration_days,
        'trades_per_year': trades_per_year,
        'trades_per_month': trades_per_month,
        'trades_per_week': trades_per_week,
        'avg_concurrent': avg_concurrent,
        'max_concurrent': int(max_concurrent),

        # Risk metrics
        'sharpe': sharpe,
        'sortino': sortino,

        # Pair breakdown
        'top_5_pairs': top_5_pairs,
        'bottom_5_pairs': bottom_5_pairs,
    }


def format_report(stats, htf_timeframe, config):
    """
    Format statistics into REPORT1 style text report

    Args:
        stats: Statistics dictionary from calc_stats()
        htf_timeframe: Higher timeframe (e.g., "Weekly", "3-Day", "Monthly")
        config: Dict with START_DATE, END_DATE, PAIRS, etc.

    Returns:
        Formatted report string
    """
    lines = []

    # ========== HEADER ==========
    lines.append("=" * 80)
    lines.append("MODEL 3 BACKTEST REPORT")
    lines.append("=" * 80)
    lines.append(f"HTF: {htf_timeframe} | Entry: {config.get('ENTRY_CONFIRMATION', 'Direct Touch')} | Pairs: {', '.join(config['PAIRS'][:2])}")
    lines.append("")

    # ========== QUICK OVERVIEW ==========
    lines.append("=" * 80)
    lines.append("QUICK OVERVIEW")
    lines.append("=" * 80)

    start_year = stats['start_date'].year
    end_year = stats['end_date'].year
    lines.append(f"Total Trades: {stats['total_trades']} (over {int(stats['years'])} years: {start_year}-{end_year})")
    lines.append("")
    lines.append(f"Win Rate: {stats['win_rate']:.1f}%")
    lines.append(f"Expectancy: {stats['expectancy']:+.2f}R")
    lines.append(f"Cumulative R: {stats['cumulative_r']:+.1f}R")
    lines.append(f"R per Year: {stats['avg_r_per_year']:+.1f}R")
    lines.append(f"Max Drawdown: {stats['max_dd']:.1f}R")
    lines.append(f"Profit Factor: {stats['profit_factor']:.2f}")
    lines.append(f"SQN: {stats['sqn']:.2f}")

    # Verdict
    viable = (
        stats['total_trades'] >= 200 and
        stats['expectancy'] > 0 and
        abs(stats['max_dd']) < 10 and
        stats['sqn'] > 1.6 and
        stats['win_rate'] > 35 and
        stats['profit_factor'] > 1.3
    )
    verdict = "VIABLE" if viable else "NOT VIABLE"
    lines.append(f"\n→ VERDICT: {verdict}")
    lines.append("=" * 80)
    lines.append("")

    # ========== R-PERFORMANCE ==========
    lines.append("=" * 80)
    lines.append("R-PERFORMANCE")
    lines.append("=" * 80)
    lines.append(f"Cumulative R: {stats['cumulative_r']:+.1f}R")
    lines.append(f"Expectancy: {stats['expectancy']:+.2f}R per trade")
    lines.append(f"  • Average Winner: +{stats['avg_winner']:.2f}R")
    lines.append(f"  • Average Loser: {stats['avg_loser']:.2f}R")
    lines.append(f"  • Median R: {stats['median_r']:+.2f}R")
    lines.append("")

    # SQN with bracket
    sqn_val = stats['sqn']
    if sqn_val < 1.6:
        sqn_label = "Below Average"
    elif sqn_val < 2.0:
        sqn_label = "Average"
    elif sqn_val < 2.5:
        sqn_label = "Good"
    elif sqn_val < 3.0:
        sqn_label = "Very Good"
    else:
        sqn_label = "Excellent"

    lines.append(f"System Quality Number: {sqn_val:.2f} [{sqn_label}]")
    lines.append(f"Profit Factor: {stats['profit_factor']:.2f}")
    lines.append(f"Payoff Ratio: {stats['payoff_ratio']:.2f}")
    lines.append("")
    lines.append(f"Sharpe Ratio: {stats['sharpe']:.2f}")
    lines.append(f"Sortino Ratio: {stats['sortino']:.2f}")
    lines.append("")

    # ========== TRADE STATISTICS ==========
    lines.append("=" * 80)
    lines.append("TRADE STATISTICS")
    lines.append("=" * 80)
    lines.append(f"Win Rate: {stats['win_rate']:.1f}%")
    lines.append(f"Long/Short: {stats['long_short_ratio']:.2f}:1 ({stats['long_trades']}L / {stats['short_trades']}S)")
    lines.append(f"  • Long WR: {stats['long_win_rate']:.1f}%")
    lines.append(f"  • Short WR: {stats['short_win_rate']:.1f}%")
    lines.append("")
    lines.append(f"Winners: {stats['winning_trades']} | Losers: {stats['losing_trades']}")
    lines.append("")

    # ========== DRAWDOWN & STREAKS ==========
    lines.append("=" * 80)
    lines.append("DRAWDOWN & STREAKS")
    lines.append("=" * 80)
    lines.append(f"Maximum Drawdown: {stats['max_dd']:.1f}R")
    lines.append(f"  • Duration: {stats['max_dd_duration_trades']} trades ({stats['max_dd_duration_days']} days / {stats['max_dd_duration_days']/30:.1f} months)")

    recovery_status = "Recovered" if stats['recovered'] else "Not recovered"
    lines.append(f"  • Recovery: {recovery_status}")
    lines.append("")
    lines.append(f"Average Drawdown: {stats['avg_dd']:.1f}R")
    lines.append("")
    lines.append(f"Consecutive Wins: Max {stats['max_consec_wins']} | Avg {stats['avg_consec_wins']:.1f} | Median {stats['median_consec_wins']}")
    lines.append(f"Consecutive Losses: Max {stats['max_consec_losses']} | Avg {stats['avg_consec_losses']:.1f} | Median {stats['median_consec_losses']}")
    lines.append("")

    # ========== TIME-BASED PERFORMANCE ==========
    lines.append("=" * 80)
    lines.append("TIME-BASED PERFORMANCE")
    lines.append("=" * 80)
    lines.append(f"R per Month: {stats['avg_r_per_month']:+.1f}R avg")
    lines.append(f"R per Year: {stats['avg_r_per_year']:+.1f}R avg")
    lines.append("")
    lines.append("Monthly:")
    lines.append(f"  • Best: {stats['best_month']:+.1f}R | Worst: {stats['worst_month']:+.1f}R")
    lines.append(f"  • Profitable: {stats['profitable_months_pct']:.0f}% ({stats['profitable_months']}/{stats['total_months']} months)")
    lines.append("")
    lines.append("Yearly:")
    lines.append(f"  • Best: {stats['best_year']:+.1f}R | Worst: {stats['worst_year']:+.1f}R")
    lines.append(f"  • Profitable: {stats['profitable_years_pct']:.0f}% ({stats['profitable_years']}/{stats['total_years']} years)")
    lines.append("")

    # ========== TRADE CHARACTERISTICS ==========
    lines.append("=" * 80)
    lines.append("TRADE CHARACTERISTICS")
    lines.append("=" * 80)
    lines.append(f"Duration: Min {stats['min_duration_days']:.1f}d | Avg {stats['avg_duration_days']:.1f}d | Max {stats['max_duration_days']:.0f}d")
    lines.append(f"Frequency: {stats['trades_per_year']:.1f}/year | {stats['trades_per_month']:.1f}/month | {stats['trades_per_week']:.2f}/week")
    lines.append(f"Concurrent: Avg {stats['avg_concurrent']:.1f} | Max {stats['max_concurrent']}")
    lines.append("")

    # ========== FUNDED ACCOUNT VIABILITY ==========
    lines.append("=" * 80)
    lines.append("FUNDED ACCOUNT VIABILITY (@ 1% risk)")
    lines.append("=" * 80)

    chk_trades = stats['total_trades'] >= 200
    chk_exp = stats['expectancy'] > 0
    chk_dd = abs(stats['max_dd']) < 10
    chk_sqn = stats['sqn'] > 1.6
    chk_wr = stats['win_rate'] > 35
    chk_pf = stats['profit_factor'] > 1.3

    lines.append(f"[{'✓' if chk_trades else '✗'}] Min 200 Trades: {'PASS' if chk_trades else 'FAIL'} ({stats['total_trades']})")
    lines.append(f"[{'✓' if chk_exp else '✗'}] Positive Expectancy: {'PASS' if chk_exp else 'FAIL'} ({stats['expectancy']:+.2f}R)")
    lines.append(f"[{'✓' if chk_dd else '✗'}] Max DD < 10R: {'PASS' if chk_dd else 'FAIL'} ({stats['max_dd']:.1f}R)")
    lines.append(f"[{'✓' if chk_sqn else '✗'}] SQN > 1.6: {'PASS' if chk_sqn else 'FAIL'} ({stats['sqn']:.2f})")
    lines.append(f"[{'✓' if chk_wr else '✗'}] Win Rate > 35%: {'PASS' if chk_wr else 'FAIL'} ({stats['win_rate']:.1f}%)")
    lines.append(f"[{'✓' if chk_pf else '✗'}] Profit Factor > 1.3: {'PASS' if chk_pf else 'FAIL'} ({stats['profit_factor']:.2f})")

    overall = all([chk_trades, chk_exp, chk_dd, chk_sqn, chk_wr, chk_pf])
    lines.append(f"\n→ {'VIABLE' if overall else 'NOT VIABLE'} FOR FUNDED ACCOUNT")
    lines.append("=" * 80)
    lines.append("")

    # ========== PAIR BREAKDOWN ==========
    lines.append("=" * 80)
    lines.append("PAIR BREAKDOWN (BY EXPECTANCY)")
    lines.append("=" * 80)
    lines.append("")
    lines.append("TOP 5 BEST PAIRS:")
    lines.append(f"{'Pair':<8} {'Trades':>7} {'Win%':>7} {'Exp':>7} {'PF':>7} {'AvgW':>7} {'AvgL':>7} {'Total R':>9}")
    lines.append("-" * 80)

    for p in stats['top_5_pairs']:
        lines.append(
            f"{p['pair']:<8} {p['trades']:>7} {p['win_pct']:>6.1f}% "
            f"{p['expectancy']:>+6.2f}R {p['profit_factor']:>6.2f} "
            f"{p['avg_win']:>+6.2f}R {p['avg_loss']:>+6.2f}R {p['total_r']:>+8.1f}R"
        )

    if len(stats['bottom_5_pairs']) > 0:
        lines.append("")
        lines.append("BOTTOM 5 WORST PAIRS:")
        lines.append(f"{'Pair':<8} {'Trades':>7} {'Win%':>7} {'Exp':>7} {'PF':>7} {'AvgW':>7} {'AvgL':>7} {'Total R':>9}")
        lines.append("-" * 80)

        for p in stats['bottom_5_pairs']:
            lines.append(
                f"{p['pair']:<8} {p['trades']:>7} {p['win_pct']:>6.1f}% "
                f"{p['expectancy']:>+6.2f}R {p['profit_factor']:>6.2f} "
                f"{p['avg_win']:>+6.2f}R {p['avg_loss']:>+6.2f}R {p['total_r']:>+8.1f}R"
            )

    lines.append("")

    # ========== FOOTER ==========
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    return "\n".join(lines)
