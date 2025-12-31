"""
Apply COT Double Divergence Filter to Phase 2 Trades

This script filters Model 3 trades based on COT bias alignment.
Implements 3 bias modes: Bias_8W, Bias_to_Bias, Bias_fix_0

Usage:
    python apply_cot_filter.py

Author: Claude
Date: 2025-12-31
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Tuple
from cot_double_divergence import COTDoubleDivergence


class COTTradeFilter:
    """
    Filter trades based on COT bias alignment

    Implements 3 bias calculation modes:
    - Bias_8W: 8-week countdown logic
    - Bias_to_Bias: Signal-to-signal (forward-fill until opposite)
    - Bias_fix_0: Null-exit (bias ends at zero crossing)
    """

    def __init__(self, cot_data_dir: Path):
        """
        Initialize COT trade filter

        Args:
            cot_data_dir: Path to COT data folder
        """
        self.cot_indicator = COTDoubleDivergence(cot_data_dir, willco_length=26)
        self.cot_data_cache = {}  # Cache for pair COT data

    def load_cot_data_all_modes(self, pair: str) -> Dict[str, pd.DataFrame]:
        """
        Load COT data for a pair with all 3 bias modes

        Args:
            pair: Forex pair (e.g., 'EURUSD')

        Returns:
            Dictionary with 3 DataFrames (one per bias mode)
        """
        if pair in self.cot_data_cache:
            return self.cot_data_cache[pair]

        # Calculate base divergence (without bias)
        df_base = self.cot_indicator.calculate_double_divergence(pair)
        threshold = df_base['Threshold'].iloc[0]

        # Calculate 3 bias modes
        df_8w = self._calculate_bias_8w(df_base.copy(), threshold)
        df_to_bias = self._calculate_bias_to_bias(df_base.copy(), threshold)
        df_fix_0 = self._calculate_bias_fix_0(df_base.copy(), threshold)

        result = {
            'Bias_8W': df_8w,
            'Bias_to_Bias': df_to_bias,
            'Bias_fix_0': df_fix_0
        }

        self.cot_data_cache[pair] = result
        return result

    def _calculate_bias_8w(self, df: pd.DataFrame, threshold: float, duration: int = 8) -> pd.DataFrame:
        """
        Calculate Bias with 8-week countdown

        Logic:
        - When Divergence >= threshold → Start Long Bias (countdown = 8)
        - When Divergence <= -threshold → Start Short Bias (countdown = 8)
        - New signal only when countdown = 0
        - Countdown decreases each week
        """
        df = df.copy()
        df['Bias'] = 'neutral'
        df['Countdown'] = 0

        bias_type = ''
        countdown = 0

        for idx in df.index:
            div = df.loc[idx, 'DoubleDivergence']

            # Skip if divergence is NaN
            if pd.isna(div):
                df.loc[idx, 'Bias'] = 'neutral'
                df.loc[idx, 'Countdown'] = 0
                continue

            # Check for new signal (only when countdown = 0)
            if countdown == 0:
                if div >= threshold:
                    bias_type = 'long'
                    countdown = duration
                elif div <= -threshold:
                    bias_type = 'short'
                    countdown = duration

            # Apply current bias and countdown
            if countdown > 0:
                df.loc[idx, 'Bias'] = bias_type
                df.loc[idx, 'Countdown'] = countdown
                countdown -= 1
            else:
                df.loc[idx, 'Bias'] = 'neutral'
                df.loc[idx, 'Countdown'] = 0

        return df

    def _calculate_bias_to_bias(self, df: pd.DataFrame, threshold: float) -> pd.DataFrame:
        """
        Calculate Bias with signal-to-signal logic

        Logic:
        - Long bias starts when Divergence >= threshold
        - Long bias continues (forward-fill) until Divergence <= -threshold (short signal)
        - Short bias starts when Divergence <= -threshold
        - Short bias continues until Divergence >= threshold (long signal)
        - Neutral only at start before first signal
        """
        df = df.copy()
        df['Bias'] = 'neutral'
        df['Countdown'] = 0  # Not used, but keep for consistency

        current_bias = 'neutral'

        for idx in df.index:
            div = df.loc[idx, 'DoubleDivergence']

            # Skip if divergence is NaN
            if pd.isna(div):
                df.loc[idx, 'Bias'] = current_bias
                continue

            # Check for signal change
            if div >= threshold:
                current_bias = 'long'
            elif div <= -threshold:
                current_bias = 'short'
            # Else: Keep current bias (forward-fill)

            df.loc[idx, 'Bias'] = current_bias

        return df

    def _calculate_bias_fix_0(self, df: pd.DataFrame, threshold: float) -> pd.DataFrame:
        """
        Calculate Bias with null-exit logic

        Logic:
        - Long bias starts when Divergence >= threshold
        - Long bias ends when Divergence crosses below 0
        - Short bias starts when Divergence <= -threshold
        - Short bias ends when Divergence crosses above 0
        - Neutral when no signal or after zero crossing
        """
        df = df.copy()
        df['Bias'] = 'neutral'
        df['Countdown'] = 0  # Not used, but keep for consistency

        current_bias = 'neutral'
        prev_div = None

        for idx in df.index:
            div = df.loc[idx, 'DoubleDivergence']

            # Skip if divergence is NaN
            if pd.isna(div):
                df.loc[idx, 'Bias'] = 'neutral'
                current_bias = 'neutral'
                prev_div = None
                continue

            # Check for zero crossing (bias exit)
            if prev_div is not None:
                if current_bias == 'long' and div < 0:
                    current_bias = 'neutral'
                elif current_bias == 'short' and div > 0:
                    current_bias = 'neutral'

            # Check for new signal (only when neutral)
            if current_bias == 'neutral':
                if div >= threshold:
                    current_bias = 'long'
                elif div <= -threshold:
                    current_bias = 'short'

            df.loc[idx, 'Bias'] = current_bias
            prev_div = div

        return df

    def get_cot_bias_at_entry(self, pair: str, entry_time: pd.Timestamp, bias_mode: str) -> str:
        """
        Get COT bias at trade entry time (with look-ahead prevention)

        Logic:
        - Entry date → Find previous Friday or earlier
        - Use COT data up to that Friday (inclusive)
        - Prevent look-ahead bias

        Args:
            pair: Forex pair
            entry_time: Trade entry timestamp
            bias_mode: 'Bias_8W', 'Bias_to_Bias', or 'Bias_fix_0'

        Returns:
            Bias string: 'long', 'short', or 'neutral'
        """
        # Load COT data for this pair (all modes)
        cot_data_all = self.load_cot_data_all_modes(pair)
        cot_data = cot_data_all[bias_mode]

        # Convert entry_time to date (ignore time)
        entry_date = pd.to_datetime(entry_time).normalize()

        # Find COT data up to entry_date (inclusive)
        # COT dates are already shifted to Friday (+3 days from Tuesday)
        available_cot = cot_data[cot_data['Date'] <= entry_date]

        if len(available_cot) == 0:
            # No COT data available before entry → neutral
            return 'neutral'

        # Get most recent COT bias
        latest_cot = available_cot.iloc[-1]
        return latest_cot['Bias']

    def filter_trades(self, trades_df: pd.DataFrame, bias_mode: str) -> pd.DataFrame:
        """
        Filter trades based on COT bias alignment

        Logic:
        1. For each trade: Get entry_time
        2. Get COT bias at that entry_time (using look-ahead prevention)
        3. Check alignment:
           - direction == 'long' AND bias == 'long' → KEEP
           - direction == 'short' AND bias == 'short' → KEEP
           - ELSE → REMOVE

        Args:
            trades_df: DataFrame with Phase 2 trades
            bias_mode: 'Bias_8W', 'Bias_to_Bias', or 'Bias_fix_0'

        Returns:
            Filtered DataFrame with only aligned trades
        """
        filtered_trades = []

        for idx, trade in trades_df.iterrows():
            pair = trade['pair']
            direction_raw = trade['direction']
            entry_time = pd.to_datetime(trade['entry_time'])

            # Normalize direction: bullish → long, bearish → short
            if direction_raw == 'bullish':
                direction = 'long'
            elif direction_raw == 'bearish':
                direction = 'short'
            else:
                direction = direction_raw  # already 'long' or 'short'

            # Get COT bias at entry
            cot_bias = self.get_cot_bias_at_entry(pair, entry_time, bias_mode)

            # Check alignment
            is_aligned = (
                (direction == 'long' and cot_bias == 'long') or
                (direction == 'short' and cot_bias == 'short')
            )

            if is_aligned:
                filtered_trades.append(trade)

        return pd.DataFrame(filtered_trades)

    def process_all_timeframes(self, phase2_dir: Path, output_dir: Path):
        """
        Process all timeframes (W, 3D, M) with all 3 bias modes

        Generates:
        - 9 TXT reports (3 modes × 3 TFs)
        - 9 Trade CSVs (3 modes × 3 TFs)

        Args:
            phase2_dir: Path to Phase 2 trade results
            output_dir: Path to output directory
        """
        from generate_reports import generate_report

        timeframes = ['W', '3D', 'M']
        modes = ['Bias_8W', 'Bias_to_Bias', 'Bias_fix_0']

        print("\n" + "="*80)
        print("COT DOUBLE DIVERGENCE FILTER - PHASE 3")
        print("="*80 + "\n")

        # Process each timeframe
        for tf in timeframes:
            print(f"\n{'='*80}")
            print(f"Processing Timeframe: {tf}")
            print(f"{'='*80}\n")

            # Load Phase 2 trades (no longer separate pure/conservative)
            trade_file = phase2_dir / f"{tf}_trades.csv"

            if not trade_file.exists():
                print(f"  ⚠ Warning: {trade_file} not found - skipping")
                continue

            trades_original = pd.read_csv(trade_file)
            original_count = len(trades_original)

            print(f"  Original Trades (Phase 2): {original_count}")

            # Process each bias mode
            for mode in modes:
                print(f"\n  {mode}:")

                # Filter trades
                trades_filtered = self.filter_trades(trades_original, mode)
                filtered_count = len(trades_filtered)
                filter_rate = (1 - filtered_count/original_count) * 100 if original_count > 0 else 0

                print(f"    Filtered Trades: {filtered_count}")
                print(f"    Filter Rate: {filter_rate:.1f}% removed")

                # Save filtered trades CSV for ALL modes
                trades_csv_dir = output_dir / 'Single_TF' / 'Trades' / mode
                trades_csv_dir.mkdir(parents=True, exist_ok=True)
                trades_csv_path = trades_csv_dir / f"{tf}_trades.csv"
                trades_filtered.to_csv(trades_csv_path, index=False)
                print(f"    ✓ Saved: {trades_csv_path.relative_to(output_dir.parent)}")

                # Generate report
                report_dir = output_dir / 'Single_TF' / 'results' / mode
                report_dir.mkdir(parents=True, exist_ok=True)
                report_path = report_dir / f"{tf}_report.txt"

                report_title = f"Model 3 - {tf} + COT Filter ({mode})"
                generate_report(
                    trades_df=trades_filtered,
                    output_path=report_path,
                    title=report_title,
                    original_count=original_count,
                    filter_rate=filter_rate,
                    phase2_trades_df=trades_original
                )

                print(f"    ✓ Report: {report_path.relative_to(output_dir.parent)}")

        print("\n" + "="*80)
        print("ALL REPORTS GENERATED")
        print("="*80)
        print(f"\nOutput Directory: {output_dir}")
        print(f"  - 9 TXT Reports in: Single_TF/results/Bias_*/")
        print(f"  - 9 Trade CSVs in: Single_TF/Trades/Bias_*/")


def main():
    """Main script to apply COT filter to Phase 2 trades"""

    # Configuration
    # Script is in: 05_Model 3/Backtest/03_fundamentals/COT/Double_Divergence/scripts/
    # Need to go up to: Trading Backtests/
    BASE_DIR = Path(__file__).parent.parent.parent.parent.parent.parent.parent
    COT_DATA_DIR = BASE_DIR / "Data" / "Cot" / "Legacy_Reports" / "Forex"
    PHASE2_DIR = BASE_DIR / "05_Model 3" / "Backtest" / "02_technical" / "01_DEFAULT" / "01_Single_TF" / "results" / "Trades"
    OUTPUT_DIR = BASE_DIR / "05_Model 3" / "Backtest" / "03_fundamentals" / "COT" / "Double_Divergence" / "01_default"

    # Verify directories exist
    if not COT_DATA_DIR.exists():
        raise FileNotFoundError(f"COT data directory not found: {COT_DATA_DIR}")

    if not PHASE2_DIR.exists():
        raise FileNotFoundError(f"Phase 2 trade directory not found: {PHASE2_DIR}")

    print(f"\nConfiguration:")
    print(f"  COT Data: {COT_DATA_DIR}")
    print(f"  Phase 2 Trades: {PHASE2_DIR}")
    print(f"  Output: {OUTPUT_DIR}")

    # Initialize filter
    filter_engine = COTTradeFilter(COT_DATA_DIR)

    # Process all timeframes
    filter_engine.process_all_timeframes(PHASE2_DIR, OUTPUT_DIR)

    print("\n✓ Complete!")


if __name__ == "__main__":
    main()
