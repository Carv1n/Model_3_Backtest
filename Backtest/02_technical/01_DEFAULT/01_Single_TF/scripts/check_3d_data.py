"""
Check 3D Data for CADJPY around 2021-06-10
"""

import sys
from pathlib import Path
import pandas as pd

# Setup path
model3_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(model3_root))

from scripts.backtesting.backtest_model3 import load_tf_data

PAIR = "CADJPY"

# Load 3D and Daily data
df_3d = load_tf_data("3D", PAIR)
df_d = load_tf_data("D", PAIR)

# Check around June 2021
start = pd.Timestamp("2021-06-01", tz="UTC")
end = pd.Timestamp("2021-06-30", tz="UTC")

df_3d_june = df_3d[(df_3d["time"] >= start) & (df_3d["time"] <= end)]
df_d_june = df_d[(df_d["time"] >= start) & (df_d["time"] <= end)]

print("="*80)
print("CADJPY - June 2021 Data Check")
print("="*80)

print("\n3D Candles:")
print(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10}")
print("-" * 60)
for i, row in df_3d_june.iterrows():
    date = row["time"].strftime("%Y-%m-%d")
    print(f"{date:<12} {row['open']:>10.5f} {row['high']:>10.5f} {row['low']:>10.5f} {row['close']:>10.5f}")

print("\n\nDaily Candles (first 10):")
print(f"{'Date':<12} {'Open':>10} {'High':>10} {'Low':>10} {'Close':>10}")
print("-" * 60)
for i, row in df_d_june.head(10).iterrows():
    date = row["time"].strftime("%Y-%m-%d")
    print(f"{date:<12} {row['open']:>10.5f} {row['high']:>10.5f} {row['low']:>10.5f} {row['close']:>10.5f}")

print("\n" + "="*80)
print("PROBLEM ANALYSIS:")
print("="*80)
print(f"3D Data Price Range: {df_3d_june['low'].min():.2f} - {df_3d_june['high'].max():.2f}")
print(f"Daily Data Price Range: {df_d_june['low'].min():.2f} - {df_d_june['high'].max():.2f}")

if df_3d_june['low'].min() < 10 and df_d_june['low'].min() > 50:
    print("\n❌ CRITICAL: 3D and Daily data are in DIFFERENT FORMATS!")
    print("   3D uses decimal format (e.g., 0.74 = 74.00 JPY)")
    print("   Daily uses JPY format (e.g., 90.00)")
    print("\n   → Data needs to be converted to same format!")
else:
    print("\n✓ Data formats appear consistent")
