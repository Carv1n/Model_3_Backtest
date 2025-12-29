# Weekly Full Test - 28 Pairs

## Zweck
Vollständiger Backtest mit allen 28 Forex Pairs zur Evaluierung der kompletten Strategie.

---

## Configuration

- **Pairs**: Alle 28 Major + Cross Pairs
  - **Majors** (7): EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD
  - **EUR Crosses** (6): EURGBP, EURJPY, EURAUD, EURCHF, EURCAD, EURNZD
  - **GBP Crosses** (5): GBPJPY, GBPAUD, GBPCAD, GBPNZD, GBPCHF
  - **JPY Crosses** (4): AUDJPY, NZDJPY, CHFJPY, CADJPY
  - **Other Crosses** (6): AUDNZD, AUDCAD, AUDCHF, NZDCAD, NZDCHF, CADCHF
- **HTF**: Weekly
- **Entry**: direct_touch
- **Zeitraum**: 2010-2024 (15 Jahre)
- **Risk**: 1% per trade
- **Capital**: $100,000

---

## Performance Optimizations

**Vectorized Functions** (NO LOOPS):
- ✅ Refinement Detection (~100x faster)
- ✅ Gap Touch Detection (vectorized)
- ✅ TP Check (vectorized)
- ✅ Entry/Exit Search (Pandas masking)
- ✅ MFE/MAE Calculation (vectorized)

**NO CACHE NEEDED**:
- 2 Pairs: ~10 Sekunden
- 28 Pairs: ~2-3 Minuten (geschätzt)
- Cache würde nur ~1 Minute sparen

---

## Ausführung

```bash
cd "05_Model 3/Backtest/01_test/02_W_test/02_ALL_PAIRS"
python scripts/backtest_weekly_full.py
```

**Erwartete Runtime**: 2-3 Minuten

---

## Output

**Location**: `results/`

**Files**:
- `baseline_report_TIMESTAMP.txt` - Kompletter Text-Report
- `trades_TIMESTAMP.csv` - Alle Trade-Details (~2000-3000 Trades erwartet)
- `equity_curve_TIMESTAMP.csv` - Portfolio Value über Zeit

**Report Sections**:
1. Performance Summary
   - Total Trades, Win Rate, Profit Factor
   - Average Winner/Loser, Payoff Ratio
   - Expectancy, Trades per Month
2. Portfolio Metrics
   - CAGR, Max Drawdown, Recovery Factor
   - Sharpe, Sortino, Calmar Ratios
   - Consecutive Wins/Losses
3. MFE/MAE Analysis
   - Average MFE/MAE (All, Winners, Losers)
4. Pair Breakdown
   - Top/Bottom 5 Pairs by Expectancy
   - Win Rate, Profit Factor per Pair
5. Direction Breakdown
   - Bullish vs Bearish Performance
6. Timing Summary
   - Data Loading, Pivot Detection, Simulation Time
   - Total Runtime

---

## Erwartete Ergebnisse

**Trades**: ~2000-3000 (basierend auf 2 Pairs × 14)
**Win Rate**: ~40-50% (1.5 RR System)
**Profit Factor**: ~1.0-1.5 (Baseline)
**Max Drawdown**: ~15-25%

---

## Next Steps

**Nach diesem Test**:

1. **Analyse Ergebnisse**:
   - Welche Pairs performen gut/schlecht?
   - Bullish vs Bearish Asymmetrie?
   - Drawdown-Charakteristiken?

2. **Optimierung**:
   - Entry Confirmation (1h_close, 4h_close vs direct_touch)
   - HTF Combinations (W, 3D, M)
   - RR Settings (Min/Max RR)
   - Refinement Settings (Max Size %)

3. **Portfolio-Regeln**:
   - Max Open Positions gleichzeitig
   - Risk per Trade adjustments
   - Pair Selection (nur Top-Performer?)

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

*Baseline Test - Weekly HTF, Direct Touch, 2010-2024*
*Last Updated: 29.12.2025*
