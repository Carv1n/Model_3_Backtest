import pandas as pd

df = pd.read_csv('gaps_GBPUSD_W.csv').head(3)

for idx, row in df.iterrows():
    gap_high = float(row['gap_high'])
    gap_low = float(row['gap_low'])
    tp = float(row['tp_level'])
    sl = float(row['sl_level'])
    rr_csv = float(row['rr'])
    gap_size = gap_high - gap_low
    
    if row['direction'] == 'bullish':
        entry = gap_low
        tp_dist_actual = tp - entry
        sl_dist_actual = entry - sl
    else:
        entry = gap_high
        tp_dist_actual = entry - tp
        sl_dist_actual = sl - entry
    
    # Was sollte es sein?
    tp_dist_expected = 3.0 * gap_size
    sl_dist_expected = 1.5 * gap_size
    
    calc_rr = tp_dist_actual / sl_dist_actual if sl_dist_actual != 0 else 0
    expected_rr = tp_dist_expected / sl_dist_expected
    
    print(f"Direction: {row['direction']}")
    print(f"  Gap size: {gap_size:.5f}")
    print(f"  TP_dist actual: {tp_dist_actual:.5f}, expected: {tp_dist_expected:.5f} (ratio: {tp_dist_actual/tp_dist_expected if tp_dist_expected != 0 else 0:.2f})")
    print(f"  SL_dist actual: {sl_dist_actual:.5f}, expected: {sl_dist_expected:.5f} (ratio: {sl_dist_actual/sl_dist_expected if sl_dist_expected != 0 else 0:.2f})")
    print(f"  CSV RR: {rr_csv:.2f} | Calculated: {calc_rr:.2f} | Expected: {expected_rr:.2f}")
    print()

