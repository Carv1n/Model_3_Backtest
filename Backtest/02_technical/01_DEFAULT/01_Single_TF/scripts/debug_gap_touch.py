"""
Debug Gap Touch für CADJPY 3D Pivot 2021-06-10
"""

import sys
from pathlib import Path
import pandas as pd

# Setup path
model3_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(model3_root))

from scripts.backtesting.backtest_model3 import load_tf_data

# Load Daily data
PAIR = "CADJPY"
d_df = load_tf_data("D", PAIR)

# Pivot info
pivot_time = pd.Timestamp("2021-06-10", tz="UTC")
valid_time = pd.Timestamp("2021-06-15", tz="UTC")
direction = "bullish"
pivot_price = 0.7397
extreme = 0.7379
near = 0.73946

gap_low = min(pivot_price, extreme)  # 0.7379
gap_high = max(pivot_price, extreme)  # 0.7397

print(f"Pivot: {pivot_time}")
print(f"Valid Time (K3 Open): {valid_time}")
print(f"Direction: {direction}")
print(f"Gap Range: {gap_low} - {gap_high}")
print(f"Gap Size: {gap_high - gap_low}")

# Check candles after valid_time
df_after = d_df[d_df["time"] >= valid_time].copy()
print(f"\nCandles after valid_time: {len(df_after)}")

# Show first 20 candles
print("\nFirst 20 candles after valid_time:")
print(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10} {'Touches Gap?'}")
print("-" * 70)

for i in range(min(20, len(df_after))):
    row = df_after.iloc[i]
    date = row["time"].strftime("%Y-%m-%d")

    # Check if candle touches gap
    if direction == "bullish":
        touches = (row["low"] <= gap_high) and (row["high"] >= gap_low)
    else:
        touches = (row["high"] >= gap_low) and (row["low"] <= gap_high)

    marker = "✓ YES" if touches else ""

    print(f"{date:<12} {row['open']:>10.5f} {row['high']:>10.5f} {row['low']:>10.5f} {row['close']:>10.5f} {marker}")

    if touches:
        print(f"\n✓ FIRST GAP TOUCH: {date}")
        print(f"  Candle Low: {row['low']}")
        print(f"  Gap High: {gap_high}")
        print(f"  Distance: {row['low'] - gap_high}")
        break
else:
    print("\n❌ NO GAP TOUCH IN FIRST 20 CANDLES!")
