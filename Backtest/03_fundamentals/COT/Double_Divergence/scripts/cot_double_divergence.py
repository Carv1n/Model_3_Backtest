"""
COT Double Divergence Indicator

Calculates COT Double Divergence for forex pairs using WillCo Index (26 weeks).
Includes Bias calculation with 8-week countdown (default mode).

Usage:
    from cot_double_divergence import COTDoubleDivergence

    indicator = COTDoubleDivergence(data_dir=Path("path/to/cot/data"))
    eurusd_data = indicator.calculate_double_divergence('EURUSD')

Author: Claude
Date: 2025-12-31
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict


class COTDoubleDivergence:
    """
    COT Double Divergence Calculator

    Calculates Double Divergence indicator for forex pairs based on:
    - Commercial vs Retail net positions
    - WillCo Index normalization (26 weeks default)
    - Pair-specific thresholds
    - 8-week countdown bias logic (default)
    """

    # Pair-specific thresholds (from Bias_Zone_Pine)
    THRESHOLDS = {
        'AUDCAD': 140, 'AUDCHF': 110, 'AUDJPY': 130, 'AUDNZD': 130, 'AUDUSD': 120,
        'CADCHF': 120, 'CADJPY': 130, 'CHFJPY': 130,
        'EURAUD': 150, 'EURCAD': 180, 'EURCHF': 150, 'EURGBP': 170,
        'EURJPY': 170, 'EURNZD': 140, 'EURUSD': 160,
        'GBPAUD': 100, 'GBPCAD': 190, 'GBPCHF': 160, 'GBPJPY': 170,
        'GBPNZD': 140, 'GBPUSD': 180,
        'NZDCAD': 110, 'NZDCHF': 150, 'NZDJPY': 130, 'NZDUSD': 190,
        'USDCAD': 150, 'USDCHF': 170, 'USDJPY': 190
    }

    def __init__(self, data_dir: Path, willco_length: int = 26):
        """
        Initialize COT Double Divergence calculator

        Args:
            data_dir: Path to COT data folder (Data/Cot/Legacy_Reports/Forex/)
            willco_length: WillCo index period in weeks (default: 26)
        """
        self.data_dir = Path(data_dir)
        self.willco_length = willco_length

        if not self.data_dir.exists():
            raise ValueError(f"COT data directory not found: {self.data_dir}")

    def load_currency_cot(self, currency: str) -> pd.DataFrame:
        """
        Load COT data for a single currency

        Args:
            currency: Currency code (e.g., 'EUR', 'USD', 'GBP')

        Returns:
            DataFrame with columns: Date, CommNet, RetailNet
        """
        file_path = self.data_dir / f"{currency}.csv"

        if not file_path.exists():
            raise FileNotFoundError(f"COT data file not found: {file_path}")

        # Load CSV
        df = pd.read_csv(file_path, parse_dates=['Date'])

        # Net positions already calculated in CSV (CommNet, RetailNet)
        # Verify columns exist
        required_cols = ['Date', 'CommNet', 'RetailNet']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns in {currency}.csv: {required_cols}")

        return df[required_cols].copy()

    def calculate_willco_index(self, series: pd.Series) -> pd.Series:
        """
        Calculate WillCo Index (0-100 normalization)

        Formula: 100 * (value - min) / (max - min)

        Args:
            series: Net position series

        Returns:
            WillCo index series (0-100 range)
        """
        rolling_min = series.rolling(window=self.willco_length, min_periods=1).min()
        rolling_max = series.rolling(window=self.willco_length, min_periods=1).max()

        # Avoid division by zero
        value_range = rolling_max - rolling_min
        value_range = value_range.replace(0, 1)

        return (100 * (series - rolling_min) / value_range).round(1)

    def calculate_double_divergence(self, pair: str) -> pd.DataFrame:
        """
        Calculate Double Divergence for a forex pair

        Steps:
        1. Load base + quote currency COT data
        2. Calculate WillCo indices for Comm and Retail (26 weeks)
        3. Calculate divergences: Comm - Retail (for base and quote)
        4. Calculate Double Divergence: Div_base - Div_quote
        5. Apply +3 day shift (Tuesday report → Friday publication)
        6. Calculate Bias with 8-week countdown (default)

        Args:
            pair: Forex pair (e.g., 'EURUSD', 'GBPUSD')

        Returns:
            DataFrame with columns: Date, Pair, DoubleDivergence, Threshold, Bias, Countdown
        """
        if len(pair) != 6:
            raise ValueError(f"Invalid pair format: {pair}. Expected 6 characters (e.g., EURUSD)")

        base_currency = pair[:3]
        quote_currency = pair[3:6]

        print(f"  Loading {base_currency} and {quote_currency} COT data...")

        # Load COT data for both currencies
        df_base = self.load_currency_cot(base_currency)
        df_quote = self.load_currency_cot(quote_currency)

        # Merge on Date
        df = pd.merge(df_base, df_quote, on='Date', suffixes=('_base', '_quote'))

        print(f"  Calculating WillCo indices...")

        # Calculate WillCo Indices for Commercial and Retail
        df['CommIdx_base'] = self.calculate_willco_index(df['CommNet_base'])
        df['RetailIdx_base'] = self.calculate_willco_index(df['RetailNet_base'])
        df['CommIdx_quote'] = self.calculate_willco_index(df['CommNet_quote'])
        df['RetailIdx_quote'] = self.calculate_willco_index(df['RetailNet_quote'])

        # Calculate Divergences (Commercial - Retail)
        df['Div_base'] = df['CommIdx_base'] - df['RetailIdx_base']
        df['Div_quote'] = df['CommIdx_quote'] - df['RetailIdx_quote']

        # Double Divergence = Div_base - Div_quote
        df['DoubleDivergence'] = df['Div_base'] - df['Div_quote']

        print(f"  Applying +3 day shift (Tuesday → Friday publication)...")

        # Apply +3 day shift (Tuesday report → Friday publication)
        df['Date'] = df['Date'] + pd.Timedelta(days=3)

        # Add pair and threshold
        threshold = self.THRESHOLDS.get(pair, 150)
        df['Pair'] = pair
        df['Threshold'] = threshold

        print(f"  Calculating Bias (8-week countdown, threshold={threshold})...")

        # Calculate Bias with 8-week countdown (default mode)
        df = self._calculate_bias_8w(df, threshold)

        # Return final columns
        return df[['Date', 'Pair', 'DoubleDivergence', 'Threshold', 'Bias', 'Countdown']].copy()

    def _calculate_bias_8w(self, df: pd.DataFrame, threshold: float, duration: int = 8) -> pd.DataFrame:
        """
        Calculate Bias with 8-week countdown

        Logic:
        - When Divergence >= threshold → Start Long Bias (countdown = 8)
        - When Divergence <= -threshold → Start Short Bias (countdown = 8)
        - New signal only when countdown = 0
        - Countdown decreases each week

        Args:
            df: DataFrame with DoubleDivergence column
            threshold: Bias threshold value
            duration: Countdown duration in weeks (default: 8)

        Returns:
            DataFrame with added Bias and Countdown columns
        """
        df['Bias'] = 'neutral'
        df['Countdown'] = 0

        bias_type = ''
        countdown = 0

        for i in range(len(df)):
            div = df.loc[df.index[i], 'DoubleDivergence']

            # Skip if divergence is NaN
            if pd.isna(div):
                df.loc[df.index[i], 'Bias'] = 'neutral'
                df.loc[df.index[i], 'Countdown'] = 0
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
                df.loc[df.index[i], 'Bias'] = bias_type
                df.loc[df.index[i], 'Countdown'] = countdown
                countdown -= 1
            else:
                df.loc[df.index[i], 'Bias'] = 'neutral'
                df.loc[df.index[i], 'Countdown'] = 0

        return df

    def generate_all_pairs(self) -> Dict[str, pd.DataFrame]:
        """
        Generate Double Divergence for all 28 forex pairs

        Returns:
            Dictionary mapping pair names to DataFrames
        """
        pairs = list(self.THRESHOLDS.keys())
        result = {}

        print(f"\n=== Generating Double Divergence for {len(pairs)} pairs ===\n")

        for i, pair in enumerate(pairs, 1):
            print(f"[{i}/{len(pairs)}] Processing {pair}...")
            try:
                result[pair] = self.calculate_double_divergence(pair)
                print(f"  ✓ {pair} complete ({len(result[pair])} weeks)\n")
            except Exception as e:
                print(f"  ✗ Error processing {pair}: {e}\n")

        print(f"=== Complete: {len(result)}/{len(pairs)} pairs generated ===\n")

        return result


# Test Script
if __name__ == "__main__":
    from pathlib import Path

    print("=== COT Double Divergence Indicator Test ===\n")

    # Configuration
    data_dir = Path("/Users/carvin/Documents/Trading Backtests/Data/Cot/Legacy_Reports/Forex/")

    # Initialize indicator
    print(f"Initializing with WillCo length: 26 weeks")
    print(f"COT data directory: {data_dir}\n")

    indicator = COTDoubleDivergence(data_dir, willco_length=26)

    # Test single pair (EURUSD)
    print("=" * 60)
    print("Testing single pair: EURUSD")
    print("=" * 60 + "\n")

    eurusd = indicator.calculate_double_divergence('EURUSD')

    print("\n" + "=" * 60)
    print("EURUSD Results - Last 20 weeks:")
    print("=" * 60)
    print(eurusd.tail(20).to_string(index=False))

    # Save to CSV for manual verification
    output_file = Path(__file__).parent / "EURUSD_test.csv"
    eurusd.to_csv(output_file, index=False)
    print(f"\n✓ Full results saved to: {output_file}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("Summary Statistics:")
    print("=" * 60)
    print(f"Total weeks: {len(eurusd)}")
    print(f"Date range: {eurusd['Date'].min()} to {eurusd['Date'].max()}")
    print(f"Divergence range: {eurusd['DoubleDivergence'].min():.1f} to {eurusd['DoubleDivergence'].max():.1f}")
    print(f"Threshold: {eurusd['Threshold'].iloc[0]}")
    print(f"\nBias distribution:")
    print(eurusd['Bias'].value_counts())

    print("\n=== Test Complete ===")
    print("Compare EURUSD_test.csv with TradingView Bias_Zone indicator to verify accuracy.")
