"""
Gap Size Optimization - Phase A: Coarse Ranges
-----------------------------------------------

Tests gap_pips filter in coarse 25-pip steps to identify optimal ranges.

Grid:
- Min: 25, 50, 75, 100, 125, 150 pips
- Max: 100, 125, 150, 175, 200, 225, 250, 275, 300, 325, 350, 375, 400 pips
- Valid combinations: Min < Max (~72 combinations per timeframe)

Output:
- Filtered trade CSVs in A_Coarse_Ranges/Trades/
- Summary reports in A_Coarse_Ranges/ (W, 3D, M)
- Top 3 configurations highlighted in each report
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add Phase 2 scripts to path for report_helpers
BASE_DIR = Path(__file__).resolve().parents[4]
phase2_scripts = BASE_DIR / "Backtest" / "02_technical" / "01_Single_TF" / "scripts"
sys.path.insert(0, str(phase2_scripts))

from report_helpers import calc_stats

# ========== CONFIGURATION ==========
TIMEFRAMES = ["W", "3D", "M"]

# Phase A: Comprehensive Gap Filter Testing
# Strategy: Test all combinations in 25-pip steps
# Goal: Find optimal exclusion thresholds (Min + Max)

# Generate all configurations
def generate_test_configs():
    """Generate comprehensive test configurations."""
    configs = []

    # Baseline (no filter)
    configs.append((0, 9999, "Baseline (no filter)"))

    # Min values: 25-150 in 25-pip steps
    min_values = list(range(25, 175, 25))  # [25, 50, 75, 100, 125, 150]

    # Max values: 200-800 in 25-pip steps
    max_values = list(range(200, 825, 25))  # [200, 225, 250, ..., 775, 800]

    # Min-only filters (exclude small gaps)
    for min_val in min_values:
        configs.append((min_val, 9999, f"Min {min_val} pips"))

    # Max-only filters (exclude huge gaps)
    for max_val in max_values:
        configs.append((0, max_val, f"Max {max_val} pips"))

    # Combined filters (all valid combinations)
    for min_val in min_values:
        for max_val in max_values:
            # Only include if Min < Max and reasonable range
            if min_val < max_val:
                configs.append((min_val, max_val, f"{min_val}-{max_val} pips"))

    return configs

# Generate all test configurations
TEST_CONFIGS = generate_test_configs()

# Paths
TRADES_DIR = BASE_DIR / "Backtest" / "02_technical" / "01_Single_TF" / "results" / "Trades"
OUTPUT_DIR = BASE_DIR / "Backtest" / "03_optimization" / "01_Single_TF" / "01_Gap_Size" / "A_Coarse_Ranges"
OUTPUT_TRADES_DIR = OUTPUT_DIR / "Trades"

# Create output directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_TRADES_DIR.mkdir(parents=True, exist_ok=True)


def filter_by_gap_size(df, min_gap, max_gap):
    """
    Filter trades by gap_pips range.

    Args:
        df: DataFrame with trades
        min_gap: Minimum gap size in pips
        max_gap: Maximum gap size in pips

    Returns:
        Filtered DataFrame
    """
    return df[(df['gap_pips'] >= min_gap) & (df['gap_pips'] <= max_gap)].copy()


def calculate_filtered_pct(original_count, filtered_count):
    """Calculate percentage of trades filtered out."""
    if original_count == 0:
        return 0.0
    return ((original_count - filtered_count) / original_count) * 100


def run_optimization(timeframe):
    """
    Run gap size optimization for a single timeframe.

    Args:
        timeframe: "W", "3D", or "M"

    Returns:
        List of result dictionaries
    """
    print(f"\n{'='*80}")
    print(f"OPTIMIZING GAP SIZE - TIMEFRAME: {timeframe}")
    print(f"{'='*80}\n")

    # Load baseline trades
    trades_file = TRADES_DIR / f"{timeframe}_trades.csv"
    if not trades_file.exists():
        print(f"ERROR: {trades_file} not found!")
        return []

    df_full = pd.read_csv(trades_file)
    original_count = len(df_full)
    print(f"Loaded {original_count} baseline trades from {timeframe}_trades.csv")

    results = []

    # Test all configurations
    for idx, (min_gap, max_gap, description) in enumerate(TEST_CONFIGS, 1):
        # Filter trades
        df_filtered = filter_by_gap_size(df_full, min_gap, max_gap)
        filtered_count = len(df_filtered)
        filtered_pct = calculate_filtered_pct(original_count, filtered_count)

        # Skip if too few trades (< 50)
        if filtered_count < 50:
            print(f"  [{idx:2d}] {description:20s}: {filtered_count:4d} trades ({filtered_pct:5.1f}% filtered) - SKIPPED (too few trades)")
            continue

        # Calculate stats
        stats = calc_stats(df_filtered)

        if stats is None:
            print(f"  [{idx:2d}] {description:20s}: Stats calculation failed - SKIPPED")
            continue

        # Store results
        result = {
            'min': min_gap,
            'max': max_gap,
            'description': description,
            'trades': filtered_count,
            'filtered_pct': filtered_pct,
            'expectancy': stats['expectancy'],
            'win_rate': stats['win_rate'],
            'sqn': stats['sqn'],
            'profit_factor': stats['profit_factor'],
            'max_dd': stats['max_dd'],
            'avg_duration': stats['avg_duration_days'],
            'min_duration': stats['min_duration_days'],
            'max_duration': stats['max_duration_days'],
            'avg_concurrent': stats['avg_concurrent'],
            'max_concurrent': stats['max_concurrent'],
            'cumulative_r': stats['cumulative_r'],
        }
        results.append(result)

        print(f"  [{idx:2d}] {description:20s}: {filtered_count:4d} trades ({filtered_pct:5.1f}% filt) | Exp: {stats['expectancy']:+.3f}R | WR: {stats['win_rate']:5.1f}% | SQN: {stats['sqn']:5.2f}")

    print(f"\nCompleted {len(results)} valid tests for {timeframe}")
    return results


def generate_summary_report(timeframe, results):
    """
    Generate summary report with Top 3 configurations.

    Args:
        timeframe: "W", "3D", or "M"
        results: List of result dictionaries
    """
    if len(results) == 0:
        print(f"No results to report for {timeframe}")
        return

    # Sort by expectancy (descending)
    results_sorted = sorted(results, key=lambda x: x['expectancy'], reverse=True)

    # Get Top 3
    top_3 = results_sorted[:3] if len(results_sorted) >= 3 else results_sorted

    # Generate report
    lines = []
    lines.append("=" * 80)
    lines.append(f"GAP SIZE OPTIMIZATION - PHASE A: SMART EXCLUSION FILTERS")
    lines.append(f"TIMEFRAME: {timeframe}")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"Total Configurations Tested: {len(results)}")
    lines.append(f"Strategy: Test exclusion filters (remove outliers), not tight windows")
    lines.append(f"Goal: Filter 5-20% of trades max (preserve trade count!)")
    lines.append("")
    lines.append("=" * 80)
    lines.append("TOP 3 CONFIGURATIONS (by Expectancy)")
    lines.append("=" * 80)
    lines.append("")

    for i, res in enumerate(top_3, 1):
        lines.append(f"RANK #{i}: {res['description']}")
        lines.append("-" * 80)
        lines.append(f"  Range:            {res['min']}-{res['max']} pips")
        lines.append(f"  Trades:           {res['trades']:4d} ({res['filtered_pct']:5.1f}% filtered)")
        lines.append(f"  Expectancy:       {res['expectancy']:+.3f}R")
        lines.append(f"  Win Rate:         {res['win_rate']:5.1f}%")
        lines.append(f"  SQN:              {res['sqn']:5.2f}")
        lines.append(f"  Profit Factor:    {res['profit_factor']:5.2f}")
        lines.append(f"  Max DD:           {res['max_dd']:+6.1f}R")
        lines.append(f"  Cumulative R:     {res['cumulative_r']:+.1f}R")
        lines.append(f"  Duration (days):  Avg {res['avg_duration']:5.1f} | Min {res['min_duration']:5.1f} | Max {res['max_duration']:6.0f}")
        lines.append(f"  Concurrent:       Avg {res['avg_concurrent']:4.1f} | Max {res['max_concurrent']:3d}")
        lines.append("")

    # Full results table
    lines.append("=" * 80)
    lines.append("ALL CONFIGURATIONS (sorted by Expectancy)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'Description':<25} {'Range':<12} {'Trades':>7} {'Filt%':>7} {'Exp(R)':>8} {'WR(%)':>7} {'SQN':>7} {'PF':>7}")
    lines.append("-" * 80)

    for res in results_sorted:
        range_str = f"{res['min']}-{res['max']}"
        lines.append(
            f"{res['description']:<25} {range_str:<12} {res['trades']:>7} {res['filtered_pct']:>6.1f}% "
            f"{res['expectancy']:>+7.3f}R {res['win_rate']:>6.1f}% "
            f"{res['sqn']:>6.2f} {res['profit_factor']:>6.2f}"
        )

    lines.append("")
    lines.append("=" * 80)
    lines.append("ANALYSIS & INSIGHTS")
    lines.append("=" * 80)
    lines.append("")

    # Find baseline for comparison
    baseline = next((r for r in results if r['min'] == 0 and r['max'] == 9999), None)
    if baseline:
        best = top_3[0]
        exp_improvement = ((best['expectancy'] - baseline['expectancy']) / abs(baseline['expectancy']) * 100) if baseline['expectancy'] != 0 else 0
        wr_improvement = best['win_rate'] - baseline['win_rate']

        lines.append(f"Baseline (no filter): {baseline['trades']} trades | Exp: {baseline['expectancy']:+.3f}R | WR: {baseline['win_rate']:.1f}%")
        lines.append(f"Best Config: {best['description']}")
        lines.append(f"  → Improvement: {exp_improvement:+.1f}% Expectancy | {wr_improvement:+.1f}% Win Rate")
        lines.append(f"  → Trades Lost: {baseline['trades'] - best['trades']} ({best['filtered_pct']:.1f}%)")
        lines.append("")

    lines.append("=" * 80)
    lines.append("NEXT STEPS")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Phase B will refine the Top 3 configurations with finer steps:")
    for i, res in enumerate(top_3, 1):
        # Smart refinement ranges
        if res['max'] >= 9999:
            # Min-only filter: refine Min around ±15 pips
            min_test_start = max(0, res['min'] - 15)
            min_test_end = res['min'] + 15
            lines.append(f"  Rank #{i} ({res['description']}): Test Min {min_test_start}-{min_test_end} pips (5-pip steps)")
        elif res['min'] == 0:
            # Max-only filter: refine Max around ±50 pips
            max_test_start = max(200, res['max'] - 50)
            max_test_end = min(1000, res['max'] + 50)
            lines.append(f"  Rank #{i} ({res['description']}): Test Max {max_test_start}-{max_test_end} pips (10-pip steps)")
        else:
            # Combined filter: refine both
            min_test_start = max(0, res['min'] - 15)
            min_test_end = res['min'] + 15
            max_test_start = max(200, res['max'] - 50)
            max_test_end = min(1000, res['max'] + 50)
            lines.append(f"  Rank #{i} ({res['description']}): Min {min_test_start}-{min_test_end} (5-pip), Max {max_test_start}-{max_test_end} (10-pip)")

    lines.append("")
    lines.append("=" * 80)
    lines.append("END OF REPORT")
    lines.append("=" * 80)

    # Write report
    report_file = OUTPUT_DIR / f"{timeframe}_report.txt"
    with open(report_file, 'w') as f:
        f.write("\n".join(lines))

    print(f"\nReport saved to: {report_file}")


def main():
    """Main execution."""
    print("=" * 80)
    print("GAP SIZE OPTIMIZATION - PHASE A: SMART EXCLUSION FILTERS")
    print("=" * 80)
    print(f"\nStrategy: Test exclusion filters (remove outliers only)")
    print(f"Goal: Filter 5-20% max, improve Expectancy & Win Rate")
    print(f"\nConfigurations: {len(TEST_CONFIGS)} tests per timeframe")
    print(f"Timeframes: {', '.join(TIMEFRAMES)}")
    print(f"Output: {OUTPUT_DIR}")
    print("")

    for tf in TIMEFRAMES:
        results = run_optimization(tf)

        if len(results) > 0:
            generate_summary_report(tf, results)
        else:
            print(f"WARNING: No valid results for {tf}")

    print("\n" + "=" * 80)
    print("PHASE A COMPLETE")
    print("=" * 80)
    print(f"\nReports saved in: {OUTPUT_DIR}")
    print("\nNext: Run optimize_gap_size_B.py to refine Top 3 configurations")


if __name__ == "__main__":
    main()
