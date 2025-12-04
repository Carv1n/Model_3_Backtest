import pandas as pd
from pathlib import Path

df = pd.read_parquet(Path(__file__).parent.parent / 'data' / '3D_all_pairs.parquet')
df = df.reset_index()
df = df[df['pair'] == 'GBPUSD'].copy()
df = df.reset_index(drop=True)
df['time'] = pd.to_datetime(df['time'])

# Find rows around 2025-09-26
result = df[(df['time'] >= '2025-09-20') & (df['time'] <= '2025-10-05')]
print('3D CANDLES:')
for idx, row in result.iterrows():
    color = 'GREEN' if row['close'] > row['open'] else 'RED'
    print(f"  {row['time']}: O={row['open']:.5f} H={row['high']:.5f} L={row['low']:.5f} C={row['close']:.5f} [{color}]")

# Check the pivot
k1_idx = result[result['time'] == '2025-09-23'].index[0]
k2_idx = result[result['time'] == '2025-09-26'].index[0]

k1 = df.loc[k1_idx]
k2 = df.loc[k2_idx]

print(f'\nPIVOT ANALYSIS:')
print(f"K1 (23.09): close={k1['close']:.5f} (RED)")
print(f"K2 (26.09): open={k2['open']:.5f} (GREEN)")
print(f"Pivot Extreme (tiefster Low): {min(k1['low'], k2['low']):.5f}")
print(f"\nVariante Close K1: {k1['close']:.5f} - {min(k1['low'], k2['low']):.5f} = {k1['close'] - min(k1['low'], k2['low']):.5f}")
print(f"Variante Open K2: {k2['open']:.5f} - {min(k1['low'], k2['low']):.5f} = {k2['open'] - min(k1['low'], k2['low']):.5f}")

# Which is bigger?
size_close = k1['close'] - min(k1['low'], k2['low'])
size_open = k2['open'] - min(k1['low'], k2['low'])

if size_close > size_open:
    print(f"\n=> Close K1 ist größer ({size_close:.5f} > {size_open:.5f})")
    print(f"=> gap_high sollte sein: {k1['close']:.5f}")
else:
    print(f"\n=> Open K2 ist größer ({size_open:.5f} > {size_close:.5f})")
    print(f"=> gap_high sollte sein: {k2['open']:.5f}")
