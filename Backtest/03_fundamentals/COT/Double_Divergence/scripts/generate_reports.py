"""
Generate Performance Reports for COT-Filtered Trades (REPORT1 Format)

Uses the same calc_stats() logic as Phase 2, with additional Phase 2 comparison.

Author: Claude
Date: 2025-12-31
"""

import sys
from pathlib import Path

# Add Phase 2 scripts to path to import calc_stats
phase2_scripts = Path(__file__).resolve().parents[4] / "02_technical" / "01_DEFAULT" / "01_Single_TF" / "scripts"
sys.path.insert(0, str(phase2_scripts))

from report_helpers import calc_stats

import pandas as pd
import numpy as np
from datetime import datetime


def format_report_with_comparison(stats: dict, htf_timeframe: str, config: dict,
                                    original_count: int = None, filter_rate: float = None,
                                    phase2_stats: dict = None) -> str:
    """
    Format report in REPORT1 style with Phase 2 comparison.

    Args:
        stats: Phase 3 (COT-filtered) statistics from calc_stats()
        htf_timeframe: Timeframe string (e.g., "Weekly", "3D", "Monthly")
        config: Report configuration dict
        original_count: Original trade count from Phase 2
        filter_rate: Percentage of trades removed by filter
        phase2_stats: Phase 2 statistics from calc_stats() for comparison

    Returns:
        Formatted report text
    """
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append("MODEL 3 BACKTEST REPORT (PHASE 3 - WITH COT FILTER)")
    lines.append("=" * 80)
    lines.append(f"HTF: {htf_timeframe} | Entry: {config.get('entry', 'direct_touch')}")
    lines.append("")

    # COT Filter Info
    if original_count is not None and phase2_stats is not None:
        lines.append("=" * 80)
        lines.append("COT FILTER IMPACT")
        lines.append("=" * 80)
        lines.append(f"Original Trades (Phase 2): {original_count}")
        lines.append(f"Filtered Trades (Phase 3): {stats['total_trades']}")
        lines.append(f"Filter Rate: {filter_rate:.1f}% removed")
        lines.append(f"Trades Removed: {original_count - stats['total_trades']}")
        lines.append("")

    # Quick Overview
    lines.append("=" * 80)
    lines.append("QUICK OVERVIEW")
    lines.append("=" * 80)

    years = stats.get('years', 15)
    lines.append(f"Total Trades: {stats['total_trades']} (over {int(years)} years: {config.get('start_year', '2010')}-{config.get('end_year', '2024')})")
    lines.append("")

    # Phase 2 comparison helper
    def fmt_p2(val, p2_val=None, unit='', is_pct=False):
        if p2_val is None:
            return f"{val:.1f}{unit}" if is_pct else f"{val:.2f}{unit}"
        diff = val - p2_val
        sign = "+" if diff >= 0 else ""
        arrow = "↑" if diff > 0 else "↓" if diff < 0 else "→"
        if is_pct:
            return f"{val:.1f}{unit} (P2: {p2_val:.1f}{unit} {arrow} {sign}{diff:.1f}{unit})"
        else:
            return f"{val:.2f}{unit} (P2: {p2_val:.2f}{unit} {arrow} {sign}{diff:.2f}{unit})"

    p2 = phase2_stats if phase2_stats else {}

    lines.append(f"Win Rate: {fmt_p2(stats['win_rate'], p2.get('win_rate'), '%', True)}")
    lines.append(f"Expectancy: {fmt_p2(stats['expectancy'], p2.get('expectancy'), 'R')}")
    lines.append(f"Cumulative R: {fmt_p2(stats['cumulative_r'], p2.get('cumulative_r'), 'R')}")
    lines.append(f"R per Year: {fmt_p2(stats['avg_r_per_year'], p2.get('avg_r_per_year'), 'R')}")
    lines.append(f"Max Drawdown: {fmt_p2(stats['max_dd'], p2.get('max_dd'), 'R')}")
    lines.append(f"Profit Factor: {fmt_p2(stats['profit_factor'], p2.get('profit_factor'))}")
    lines.append(f"SQN: {fmt_p2(stats['sqn'], p2.get('sqn'))}")
    lines.append("")

    # Verdict
    verdict = "VIABLE" if stats['sqn'] > 1.6 and stats['expectancy'] > 0 and abs(stats['max_dd']) < 10 else "NOT VIABLE"
    lines.append(f"→ VERDICT: {verdict}")
    lines.append("=" * 80)
    lines.append("")

    # R-Performance
    lines.append("=" * 80)
    lines.append("R-PERFORMANCE")
    lines.append("=" * 80)
    lines.append(f"Cumulative R: {stats['cumulative_r']:.1f}R")
    lines.append(f"Expectancy: {stats['expectancy']:.2f}R per trade")
    lines.append(f"  • Average Winner: +{stats['avg_winner']:.2f}R")
    lines.append(f"  • Average Loser: {stats['avg_loser']:.2f}R")
    lines.append(f"  • Median R: {stats['median_r']:.2f}R")
    lines.append("")

    sqn_label = ("Excellent" if stats['sqn'] > 3.0 else
                 "Very Good" if stats['sqn'] > 2.5 else
                 "Good" if stats['sqn'] > 2.0 else
                 "Average" if stats['sqn'] > 1.6 else
                 "Below Average")
    lines.append(f"System Quality Number: {stats['sqn']:.2f} [{sqn_label}]")
    lines.append(f"Profit Factor: {stats['profit_factor']:.2f}")
    lines.append(f"Payoff Ratio: {stats['payoff_ratio']:.2f}")
    lines.append("")
    lines.append(f"Sharpe Ratio: {stats['sharpe']:.2f}")
    lines.append(f"Sortino Ratio: {stats['sortino']:.2f}")
    lines.append("")

    # Trade Statistics
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

    # Drawdown & Streaks
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

    # Time-Based Performance
    lines.append("=" * 80)
    lines.append("TIME-BASED PERFORMANCE")
    lines.append("=" * 80)
    lines.append(f"R per Month: {stats['avg_r_per_month']:.1f}R avg")
    lines.append(f"R per Year: {stats['avg_r_per_year']:.1f}R avg")
    lines.append("")
    lines.append("Monthly:")
    lines.append(f"  • Best: +{stats['best_month']:.1f}R | Worst: {stats['worst_month']:.1f}R")
    lines.append(f"  • Profitable: {stats['profitable_months_pct']:.0f}% ({stats['profitable_months']}/{stats['total_months']} months)")
    lines.append("")
    lines.append("Yearly:")
    lines.append(f"  • Best: +{stats['best_year']:.1f}R | Worst: {stats['worst_year']:.1f}R")
    lines.append(f"  • Profitable: {stats['profitable_years_pct']:.0f}% ({stats['profitable_years']}/{stats['total_years']} years)")
    lines.append("")

    # Trade Characteristics
    lines.append("=" * 80)
    lines.append("TRADE CHARACTERISTICS")
    lines.append("=" * 80)
    lines.append(f"Duration: Min {stats['min_duration_days']:.1f}d | Avg {stats['avg_duration_days']:.1f}d | Max {stats['max_duration_days']:.0f}d")
    lines.append(f"Frequency: {stats['trades_per_year']:.1f}/year | {stats['trades_per_month']:.1f}/month | {stats['trades_per_week']:.2f}/week")
    lines.append(f"Concurrent: Avg {stats['avg_concurrent']:.1f} | Max {stats['max_concurrent']}")
    lines.append("")

    # Funded Account Viability
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

    # Win Rate by Fib TP Levels
    lines.append("=" * 80)
    lines.append("WIN RATE BY FIB TP LEVELS (same SL, TP varies by Fib × Box Size)")
    lines.append("=" * 80)

    fib_data = stats['win_rate_by_fib']
    fib_levels = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]

    for fib in fib_levels:
        data = fib_data[fib]
        win_rate = data['win_rate']
        wins = data['wins']
        losses = data['losses']
        total = wins + losses
        avg_rr = data['avg_rr']

        # Visual bar (each █ = 2.5%)
        bar_length = int(win_rate / 2.5)
        bar = "█" * bar_length

        lines.append(f"Fib -{fib:.1f} (Avg RR {avg_rr:.2f}R): {win_rate:5.1f}% ({wins}W / {losses}L of {total}) {bar}")

    lines.append("")
    lines.append("Note: Each Fib level shows win rate if TP was set at that level (same -1.0R SL)")
    lines.append("")

    # Pair Breakdown
    lines.append("=" * 80)
    lines.append("PAIR BREAKDOWN (BY EXPECTANCY)")
    lines.append("=" * 80)
    lines.append("")
    lines.append("TOP 5 BEST PAIRS:")
    lines.append(f"{'Pair':<8} {'Trades':>7} {'Win%':>7} {'Exp':>7} {'PF':>7} {'AvgW':>7} {'AvgL':>7} {'Total R':>9}")
    lines.append("-" * 80)

    for pair_stat in stats['top_5_pairs']:
        lines.append(
            f"{pair_stat['pair']:<8} "
            f"{pair_stat['trades']:>7} "
            f"{pair_stat['win_pct']:>6.1f}% "
            f"{pair_stat['expectancy']:>6.2f}R "
            f"{pair_stat['profit_factor']:>6.2f} "
            f"{pair_stat['avg_win']:>6.2f}R "
            f"{pair_stat['avg_loss']:>6.2f}R "
            f"{pair_stat['total_r']:>8.1f}R"
        )

    lines.append("")
    lines.append("BOTTOM 5 WORST PAIRS:")
    lines.append(f"{'Pair':<8} {'Trades':>7} {'Win%':>7} {'Exp':>7} {'PF':>7} {'AvgW':>7} {'AvgL':>7} {'Total R':>9}")
    lines.append("-" * 80)

    for pair_stat in stats['bottom_5_pairs']:
        lines.append(
            f"{pair_stat['pair']:<8} "
            f"{pair_stat['trades']:>7} "
            f"{pair_stat['win_pct']:>6.1f}% "
            f"{pair_stat['expectancy']:>6.2f}R "
            f"{pair_stat['profit_factor']:>6.2f} "
            f"{pair_stat['avg_win']:>6.2f}R "
            f"{pair_stat['avg_loss']:>6.2f}R "
            f"{pair_stat['total_r']:>8.1f}R"
        )

    lines.append("")

    # Footer
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    return "\n".join(lines)


def generate_report(trades_df: pd.DataFrame, output_path: Path, title: str,
                    original_count: int = None, filter_rate: float = None,
                    phase2_trades_df: pd.DataFrame = None):
    """
    Generate complete performance report with Phase 2 comparison.

    Args:
        trades_df: Phase 3 (COT-filtered) trades DataFrame
        output_path: Path to save report TXT file
        title: Report title (e.g., "Model 3 - W + COT Filter (Bias_8W)")
        original_count: Original trade count from Phase 2
        filter_rate: Percentage of trades removed by filter
        phase2_trades_df: Phase 2 trades DataFrame for comparison
    """
    # Calculate Phase 3 statistics using shared calc_stats()
    stats = calc_stats(trades_df, start_cap=100000, risk=0.01)

    # Calculate Phase 2 statistics (if provided)
    phase2_stats = None
    if phase2_trades_df is not None and not phase2_trades_df.empty:
        phase2_stats = calc_stats(phase2_trades_df, start_cap=100000, risk=0.01)

    # Report config
    report_config = {
        'entry': 'direct_touch',
        'start_year': '2010',
        'end_year': '2024',
    }

    # Extract timeframe from title (e.g., "Model 3 - W + COT Filter" -> "W")
    htf_timeframe = "Unknown"
    if " - " in title and " +" in title:
        htf_timeframe = title.split(" - ")[1].split(" +")[0].strip()

    # Format report
    report_text = format_report_with_comparison(
        stats=stats,
        htf_timeframe=htf_timeframe,
        config=report_config,
        original_count=original_count,
        filter_rate=filter_rate,
        phase2_stats=phase2_stats
    )

    # Save to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report_text)


if __name__ == "__main__":
    print("This module is meant to be imported, not run directly.")
    print("Use: from generate_reports import generate_report")
