"""
Gap Size Optimization - Phase B: Fine Steps
--------------------------------------------

Refines the Top 3 configurations from Phase A with finer 10-pip steps.

For each Top 3 configuration (e.g., 75-200):
- Tests Min: ±25 pips around best (e.g., 50-100) in 10-pip steps
- Tests Max: ±25 pips around best (e.g., 175-225) in 10-pip steps
- Creates wider search range to ensure we capture optimal settings

Output:
- Filtered trade CSVs in B_Fine_Steps/Trades/
- Summary reports in B_Fine_Steps/ (W, 3D, M)
- Top 3 refined configurations highlighted in each report
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import re

# Add Phase 2 scripts to path for report_helpers
BASE_DIR = Path(__file__).resolve().parents[4]
phase2_scripts = BASE_DIR / "Backtest" / "02_technical" / "01_Single_TF" / "scripts"
sys.path.insert(0, str(phase2_scripts))

from report_helpers import calc_stats

# ========== CONFIGURATION ==========
TIMEFRAMES = ["W", "3D", "M"]

# Phase B: Fine steps (10-pip increments)
FINE_STEP = 10

# Paths
TRADES_DIR = BASE_DIR / "Backtest" / "02_technical" / "01_Single_TF" / "results" / "Trades"
PHASE_A_DIR = BASE_DIR / "Backtest" / "03_optimization" / "01_Single_TF" / "01_Gap_Size" / "A_Coarse_Ranges"
OUTPUT_DIR = BASE_DIR / "Backtest" / "03_optimization" / "01_Single_TF" / "01_Gap_Size" / "B_Fine_Steps"
OUTPUT_TRADES_DIR = OUTPUT_DIR / "Trades"

# Create output directories
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_TRADES_DIR.mkdir(parents=True, exist_ok=True)


def parse_phase_a_results(timeframe):
    """
    Parse Phase A report to extract Top 3 configurations.

    Args:
        timeframe: "W", "3D", or "M"

    Returns:
        List of tuples: [(min1, max1, desc1), (min2, max2, desc2), (min3, max3, desc3)]
    """
    report_file = PHASE_A_DIR / f"{timeframe}_report.txt"

    if not report_file.exists():
        print(f"ERROR: Phase A report not found: {report_file}")
        print("Please run optimize_gap_size_A.py first!")
        return []

    with open(report_file, 'r') as f:
        content = f.read()

    # Extract Top 3 from report
    # Pattern: "RANK #1: <description>" followed by "Range: XX-YYYY pips"
    # NEW format after Phase A update
    top_3 = []

    # Try to parse RANK sections
    rank_pattern = r'RANK #(\d+): (.+?)\n.*?Range:\s+(\d+)-(\d+) pips'
    matches = re.findall(rank_pattern, content, re.DOTALL)

    if len(matches) >= 3:
        for rank, desc, min_val, max_val in matches[:3]:
            top_3.append((int(min_val), int(max_val), desc.strip()))
    else:
        # Fallback: try old format
        old_pattern = r'RANK #\d+: (\d+)-(\d+) pips'
        old_matches = re.findall(old_pattern, content)
        if len(old_matches) >= 3:
            for min_val, max_val in old_matches[:3]:
                top_3.append((int(min_val), int(max_val), f"{min_val}-{max_val}"))
        else:
            print(f"ERROR: Could not parse Top 3 from Phase A report for {timeframe}")
            return []

    print(f"Parsed Top 3 from Phase A for {timeframe}:")
    for i, (min_val, max_val, desc) in enumerate(top_3, 1):
        print(f"  Rank #{i}: {desc} ({min_val}-{max_val} pips)")

    return top_3


def generate_test_ranges(min_val, max_val):
    """
    Generate test ranges around a configuration.
    Smart handling for Min-only, Max-only, or Combined filters.

    Args:
        min_val: Best Min from Phase A
        max_val: Best Max from Phase A

    Returns:
        Tuple of (min_values, max_values) to test
    """
    # Detect filter type
    is_min_only = (max_val >= 9999)
    is_max_only = (min_val == 0)

    if is_min_only:
        # Min-only filter: refine Min around ±15 pips (5-pip steps)
        min_start = max(0, min_val - 15)
        min_end = min_val + 15
        min_values = list(range(min_start, min_end + 1, 5))
        max_values = [9999]  # Keep max unlimited

    elif is_max_only:
        # Max-only filter: refine Max around ±50 pips (10-pip steps)
        min_values = [0]  # Keep min at 0
        max_start = max(200, max_val - 50)
        max_end = min(1000, max_val + 50)
        max_values = list(range(max_start, max_end + 1, 10))

    else:
        # Combined filter: refine both
        # Min: ±15 pips (5-pip steps)
        min_start = max(0, min_val - 15)
        min_end = min_val + 15
        min_values = list(range(min_start, min_end + 1, 5))

        # Max: ±50 pips (10-pip steps)
        max_start = max(200, max_val - 50)
        max_end = min(1000, max_val + 50)
        max_values = list(range(max_start, max_end + 1, 10))

    return min_values, max_values


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


def run_refinement(timeframe, config_idx, min_val, max_val, description):
    """
    Refine a single Phase A configuration.

    Args:
        timeframe: "W", "3D", or "M"
        config_idx: Configuration index (1-3)
        min_val: Min value from Phase A
        max_val: Max value from Phase A
        description: Description from Phase A

    Returns:
        List of result dictionaries
    """
    print(f"\n{'='*80}")
    print(f"REFINING CONFIG #{config_idx}: {description} ({min_val}-{max_val} pips)")
    print(f"TIMEFRAME: {timeframe}")
    print(f"{'='*80}\n")

    # Load baseline trades
    trades_file = TRADES_DIR / f"{timeframe}_trades.csv"
    df_full = pd.read_csv(trades_file)
    original_count = len(df_full)

    # Generate test ranges
    min_values, max_values = generate_test_ranges(min_val, max_val)

    print(f"Testing Min: {min_values[0]}-{min_values[-1]} pips (step: {FINE_STEP})")
    print(f"Testing Max: {max_values[0]}-{max_values[-1]} pips (step: {FINE_STEP})")
    print("")

    results = []
    total_tests = 0

    # Test all combinations
    for min_gap in min_values:
        for max_gap in max_values:
            # Skip invalid combinations
            if min_gap >= max_gap:
                continue

            total_tests += 1

            # Filter trades
            df_filtered = filter_by_gap_size(df_full, min_gap, max_gap)
            filtered_count = len(df_filtered)
            filtered_pct = calculate_filtered_pct(original_count, filtered_count)

            # Skip if too few trades
            if filtered_count < 50:
                print(f"  [{total_tests:3d}] {min_gap:3d}-{max_gap:3d}: {filtered_count:4d} trades - SKIPPED (too few)")
                continue

            # Calculate stats
            stats = calc_stats(df_filtered)

            if stats is None:
                print(f"  [{total_tests:3d}] {min_gap:3d}-{max_gap:3d}: Stats failed - SKIPPED")
                continue

            # Store results
            result = {
                'min': min_gap,
                'max': max_gap,
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

            print(f"  [{total_tests:3d}] {min_gap:3d}-{max_gap:3d}: {filtered_count:4d} trades ({filtered_pct:5.1f}% filt) | Exp: {stats['expectancy']:+.3f}R | WR: {stats['win_rate']:5.1f}% | SQN: {stats['sqn']:5.2f}")

    print(f"\nCompleted {len(results)} valid tests for Config #{config_idx}")
    return results


def generate_summary_report(timeframe, all_results):
    """
    Generate summary report combining all refinements.

    Args:
        timeframe: "W", "3D", or "M"
        all_results: Dict mapping config_idx -> results list
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"GAP SIZE OPTIMIZATION - PHASE B: FINE STEPS")
    lines.append(f"TIMEFRAME: {timeframe}")
    lines.append("=" * 80)
    lines.append("")

    # Combine all results and sort
    combined = []
    for config_idx, results in all_results.items():
        for res in results:
            res['config_idx'] = config_idx
            combined.append(res)

    if len(combined) == 0:
        lines.append("ERROR: No valid results!")
        report_file = OUTPUT_DIR / f"{timeframe}_report.txt"
        with open(report_file, 'w') as f:
            f.write("\n".join(lines))
        return

    # Sort by expectancy
    combined_sorted = sorted(combined, key=lambda x: x['expectancy'], reverse=True)

    # Get overall Top 3
    top_3 = combined_sorted[:3] if len(combined_sorted) >= 3 else combined_sorted

    lines.append(f"Total Configurations Tested: {len(combined)}")
    lines.append(f"Refinement Step: {FINE_STEP} pips")
    lines.append("")
    lines.append("=" * 80)
    lines.append("TOP 3 REFINED CONFIGURATIONS (by Expectancy)")
    lines.append("=" * 80)
    lines.append("")

    for i, res in enumerate(top_3, 1):
        lines.append(f"RANK #{i}: {res['min']}-{res['max']} pips (from Phase A Config #{res['config_idx']})")
        lines.append("-" * 80)
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

    # Results by original config
    lines.append("=" * 80)
    lines.append("RESULTS BY PHASE A CONFIGURATION")
    lines.append("=" * 80)
    lines.append("")

    for config_idx in sorted(all_results.keys()):
        results = all_results[config_idx]
        if len(results) == 0:
            continue

        results_sorted = sorted(results, key=lambda x: x['expectancy'], reverse=True)
        best = results_sorted[0]

        lines.append(f"Phase A Config #{config_idx} - Best Refined: {best['min']}-{best['max']} pips")
        lines.append(f"  Exp: {best['expectancy']:+.3f}R | WR: {best['win_rate']:5.1f}% | SQN: {best['sqn']:5.2f} | Trades: {best['trades']}")
        lines.append("")

    # Full results table
    lines.append("=" * 80)
    lines.append("ALL REFINED CONFIGURATIONS (sorted by Expectancy)")
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{'Range':<12} {'From':>6} {'Trades':>7} {'Filt%':>7} {'Exp(R)':>8} {'WR(%)':>7} {'SQN':>7} {'PF':>7} {'MaxDD':>8} {'AvgDur':>8} {'MaxCon':>7}")
    lines.append("-" * 80)

    for res in combined_sorted:
        range_str = f"{res['min']}-{res['max']}"
        from_str = f"Cfg#{res['config_idx']}"
        lines.append(
            f"{range_str:<12} {from_str:>6} {res['trades']:>7} {res['filtered_pct']:>6.1f}% "
            f"{res['expectancy']:>+7.3f}R {res['win_rate']:>6.1f}% "
            f"{res['sqn']:>6.2f} {res['profit_factor']:>6.2f} "
            f"{res['max_dd']:>+7.1f}R {res['avg_duration']:>7.1f}d {res['max_concurrent']:>6d}"
        )

    lines.append("")
    lines.append("=" * 80)
    lines.append("NEXT STEPS")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Phase C: Walk-Forward Validation")
    lines.append(f"  Test the Top 3 refined configurations ({top_3[0]['min']}-{top_3[0]['max']}, etc.)")
    lines.append("  across multiple time windows (5Y IS / 1Y OOS) to verify robustness.")
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
    print("GAP SIZE OPTIMIZATION - PHASE B: FINE STEPS")
    print("=" * 80)
    print(f"\nRefinement Step: {FINE_STEP} pips")
    print(f"Timeframes: {', '.join(TIMEFRAMES)}")
    print(f"Output: {OUTPUT_DIR}")
    print("")

    for tf in TIMEFRAMES:
        # Parse Phase A Top 3
        top_3_configs = parse_phase_a_results(tf)

        if len(top_3_configs) == 0:
            print(f"ERROR: No Phase A results for {tf}. Skipping.")
            continue

        # Refine each config
        all_results = {}
        for i, (min_val, max_val, desc) in enumerate(top_3_configs, 1):
            results = run_refinement(tf, i, min_val, max_val, desc)
            all_results[i] = results

        # Generate summary
        generate_summary_report(tf, all_results)

    print("\n" + "=" * 80)
    print("PHASE B COMPLETE")
    print("=" * 80)
    print(f"\nReports saved in: {OUTPUT_DIR}")
    print("\nNext: Walk-Forward Validation (Phase C)")


if __name__ == "__main__":
    main()
