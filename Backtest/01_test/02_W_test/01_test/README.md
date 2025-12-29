# Weekly Mini Test - 2 Pairs

## Zweck
Performance-Test mit minimaler Pair-Anzahl um Runtime zu messen.

**Entscheidung**: Ob Caching für 28-Pair Full Test nötig ist.

---

## Configuration

- **Pairs**: EURUSD, AUDNZD
- **HTF**: Weekly
- **Entry**: direct_touch
- **Zeitraum**: 2010-2024
- **Risk**: 1% per trade
- **Capital**: $100,000

---

## Ausführung

```bash
cd "05_Model 3/Backtest/01_test/02_W_test/01_test"
python scripts/backtest_weekly_mini.py
```

---

## Output

**Location**: `results/`

**Files**:
- `baseline_report_TIMESTAMP.txt` - Kompletter Text-Report
- `trades_TIMESTAMP.csv` - Alle Trade-Details
- `equity_curve_TIMESTAMP.csv` - Portfolio Value über Zeit

**Report Sections**:
1. Performance Summary (12 Metriken)
2. Portfolio Metrics (10 Metriken)
3. MFE/MAE Analysis (6 Metriken)
4. Pair Breakdown (Tabelle)
5. Direction Breakdown (Tabelle)
6. Timing Summary (Runtime-Analyse)

---

## Timing Tracking

**Das Script misst**:
- Data Loading (pro Pair, pro TF)
- Pivot Detection (pro HTF)
- Trade Simulation (pro Pivot)
- Total Runtime

**Erwartete Runtime**: ~30-60 Sekunden

**Entscheidung danach**:
- Wenn < 1 Minute: Kein Cache für 28 Pairs nötig
- Wenn > 2 Minuten: Cache implementieren für Full Test

---

## Next Steps

**Nach diesem Test**:

1. **Analyse Runtime**:
   - Wie lange dauert es pro Pair?
   - Hochrechnung für 28 Pairs (× 14)
   - Bottleneck identifizieren

2. **Entscheidung**:
   - Runtime < 15 Min → Kein Cache nötig
   - Runtime > 15 Min → Cache für 02_ALL_PAIRS implementieren

3. **Validierung**:
   - Sind Statistiken plausibel?
   - Genug Trades für Aussagekraft?
   - Performance realistisch?

4. **Dann**: Full Test mit 28 Pairs in `02_ALL_PAIRS/`

---

## Recent Fixes (29.12.2025)

### ✅ Bug Fixes Applied:
1. **MFE/MAE Calculation**: Fixed to include entry candle in trade window
   - Was: `df["time"] > entry_time` (excluded entry candle)
   - Now: `df["time"] >= entry_time` (includes entry candle)
   - Impact: More accurate MFE/MAE values

2. **TP Check Logic**: Simplified start time calculation
   - Was: `max(pivot.valid_time, gap_touch_time)`
   - Now: `gap_touch_time` (clearer logic)
   - Impact: No functional change, improved code clarity

3. **Refinement Detection**: Added "Unberührt" check
   - Validates refinement NEAR wasn't touched between creation and valid_time
   - Impact: Correctly filters invalid refinements (matches original function)

### ✅ Verification Completed:
- Entry/Exit detection uses H1 precision ✓
- Transaction costs properly applied (spread + slippage) ✓
- RR calculation and SL adjustment logic verified ✓
- All vectorized functions match original logic ✓

---

*Last Updated: 29.12.2025*
