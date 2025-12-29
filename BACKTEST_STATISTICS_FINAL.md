# Model 3 - Backtest Statistics (Final)

## Zweck
Finale Liste aller Metriken für Portfolio-Backtest Reports.

**Wichtig**: Nur ECHTE Trades (Entry erfolgt) in Statistiken!

**Output**: TXT Report + HTML Report (QuantStats)

---

## 📊 TXT REPORT STRUCTURE

### 1. Header (Metadata)
```
================================================================================
MODEL 3 - BACKTEST REPORT
================================================================================
Report Generated: 2025-12-29 18:30:00
Test Period: 2010-01-01 to 2024-12-31 (15 years)
Pairs Tested: 28
HTF Timeframe: W (Weekly)
Entry Type: direct_touch
Risk per Trade: 1.0%
Starting Capital: $100,000
================================================================================
```

---

### 2. Performance Summary (12 Metriken)
```
--- PERFORMANCE SUMMARY ---
Total Trades: 247
Winning Trades: 130 (52.6%)
Losing Trades: 117 (47.4%)

Average Winner: +1.38R
Average Loser: -0.98R
Largest Winner: +1.50R
Largest Loser: -1.00R

Profit Factor: 1.89
Payoff Ratio: 1.41
Expectancy: +0.43R per trade

Average Trade Duration: 12.3 days
Trades per Month: 1.4
```

**Metriken**:
1. Total Trades
2. Winning Trades (count + %)
3. Losing Trades (count + %)
4. Average Winner (R)
5. Average Loser (R)
6. Largest Winner (R)
7. Largest Loser (R)
8. Profit Factor
9. Payoff Ratio
10. Expectancy (R)
11. Average Trade Duration (days)
12. Trades per Month

---

### 3. Portfolio Metrics (13 Metriken)
```
--- PORTFOLIO METRICS ---
Starting Capital: $100,000
Ending Capital: $243,200
Total Return: +143.2%
CAGR: 12.4%

Maximum Drawdown: -14.8%
Max DD Duration: 89 days
Average Drawdown: -6.2%
Recovery Factor: 9.68
Calmar Ratio: 2.54

Max Consecutive Wins: 7
Max Consecutive Losses: 5

Average Concurrent Trades: 2.3
Max Concurrent Trades: 8
```

**Metriken**:
1. Starting Capital
2. Ending Capital
3. Total Return (%)
4. CAGR (%)
5. Maximum Drawdown (%)
6. Max DD Duration (days)
7. Average Drawdown (%)
8. Recovery Factor
9. Calmar Ratio
10. Max Consecutive Wins
11. Max Consecutive Losses
12. Average Concurrent Trades
13. Max Concurrent Trades

---

### 4. Risk-Adjusted Returns (3 Metriken)
```
--- RISK-ADJUSTED RETURNS ---
Sharpe Ratio: 1.82 ✅ (>1.5 target)
Sortino Ratio: 2.31 ✅ (>2.0 target)
Annualized Volatility: 18.3%
```

**Metriken**:
1. Sharpe Ratio (mit Check)
2. Sortino Ratio (mit Check)
3. Annualized Volatility (%)

---

### 5. Funded Account Viability Check (5 Checks)
```
--- FUNDED ACCOUNT VIABILITY ---
✅ Max Drawdown < 20%: PASS (14.8%)
✅ Worst Day Loss < 4%: PASS (3.2% on 2020-03-12)
✅ Sharpe Ratio > 1.5: PASS (1.82)
✅ Calmar Ratio > 2.0: PASS (2.54)
✅ Min. 200 Trades: PASS (247)

OVERALL VERDICT: ✅ FUNDED ACCOUNT VIABLE
```

**Checks**:
1. Max DD < 20%
2. Worst Day < 4%
3. Sharpe > 1.5
4. Calmar > 2.0
5. Min. 200 Trades
6. Overall Verdict (Pass/Fail)

---

### 6. HTF Timeframe Breakdown
```
--- HTF TIMEFRAME BREAKDOWN ---
Timeframe | Trades | Win% | Avg PnL | Profit Factor | Expectancy
----------|--------|------|---------|---------------|------------
Weekly    |   247  | 52.6 |  +0.43R |      1.89     |   +0.43R
```

**Für Baseline (nur W)**: 1 Zeile
**Für Full Backtest**: 3 Zeilen (3D, W, M)

**Columns**:
- Timeframe, Trades, Win%, Avg PnL (R), Profit Factor, Expectancy (R)

---

### 7. Top/Bottom 5 Pairs
```
--- TOP 5 PAIRS (by Expectancy) ---
Rank | Pair   | Trades | Win%  | Profit Factor | Expectancy
-----|--------|--------|-------|---------------|------------
  1  | EURUSD |   18   | 61.1% |      2.34     |   +0.78R
  2  | GBPUSD |   15   | 60.0% |      2.12     |   +0.71R
  3  | USDJPY |   12   | 58.3% |      2.01     |   +0.65R
  4  | AUDUSD |   10   | 60.0% |      1.95     |   +0.62R
  5  | NZDUSD |    9   | 55.6% |      1.87     |   +0.55R

--- BOTTOM 5 PAIRS (by Expectancy) ---
Rank | Pair   | Trades | Win%  | Profit Factor | Expectancy
-----|--------|--------|-------|---------------|------------
  1  | GBPJPY |    7   | 28.6% |      0.78     |   -0.32R
  2  | CHFJPY |    5   | 40.0% |      0.85     |   -0.18R
  3  | AUDCAD |    6   | 33.3% |      0.92     |   -0.12R
  4  | NZDCAD |    4   | 50.0% |      0.98     |   -0.05R
  5  | EURAUD |    8   | 50.0% |      1.05     |   +0.08R
```

**2 Tabellen**: Top 5 + Bottom 5

**Columns**: Rank, Pair, Trades, Win%, Profit Factor, Expectancy (R)

---

### 8. Direction Breakdown
```
--- DIRECTION BREAKDOWN ---
Direction | Trades | Win%  | Avg PnL | Profit Factor | Expectancy
----------|--------|-------|---------|---------------|------------
Bullish   |  124   | 53.2% |  +0.46R |      1.92     |   +0.46R
Bearish   |  123   | 52.0% |  +0.40R |      1.86     |   +0.40R
```

**Columns**: Direction, Trades, Win%, Avg PnL (R), Profit Factor, Expectancy (R)

---

### 9. Yearly Performance
```
--- YEARLY PERFORMANCE ---
Year | Trades | Win%  | Total PnL | Return | Max DD | Sharpe | Best Mo | Worst Mo
-----|--------|-------|-----------|--------|--------|--------|---------|----------
2010 |   12   | 50.0% |   +5.1R   |  +8.2% |  -5.3% |  1.42  |  Mar    | Sep
2011 |   15   | 53.3% |   +7.4R   | +12.1% |  -7.8% |  1.55  |  Jun    | Nov
2012 |   18   | 55.6% |   +9.3R   | +15.3% |  -6.2% |  1.89  |  Feb    | Aug
...
2024 |   19   | 57.9% |  +11.2R   | +18.7% |  -8.1% |  2.12  |  Oct    | Mar

Best Year: 2022 (+24.3%, +14.6R, 21 trades)
Worst Year: 2015 (-4.2%, -2.5R, 10 trades)
```

**Columns**: Year, Trades, Win%, Total PnL (R), Return (%), Max DD (%), Sharpe, Best Month, Worst Month

**Summary**: Best/Worst Year

---

### 10. Monthly Distribution
```
--- MONTHLY TRADE DISTRIBUTION ---
Jan: 23  Feb: 19  Mar: 21  Apr: 18  May: 20  Jun: 17
Jul: 15  Aug: 16  Sep: 22  Oct: 24  Nov: 19  Dec: 18

Most Active: October (24 trades)
Least Active: July (15 trades)
Average: 18.9 trades/month
```

**Info**: Trade-Count pro Monat (1-12), Most/Least Active, Average

---

### 11. Setup Conversion Stats
```
--- SETUP CONVERSION ---
Total HTF Pivots Found: 1,247
Pivots with Gap Touch: 843 (67.6%)
Pivots with Valid Entry: 247 (19.8%)

Conversion Rate: 19.8% (Valid Entry / Total Pivots)

--- REJECTION REASONS ---
Reason                      | Count | Percentage
----------------------------|-------|------------
No Gap Touch                |   404 |    32.4%
TP Touched Before Entry     |   198 |    15.9%
No Valid Refinement         |   287 |    23.0%
RR < 1.0                    |    89 |     7.1%
Failed Entry Confirmation   |    22 |     1.8%
```

**Metriken**:
1. Total HTF Pivots
2. Pivots with Gap Touch (count + %)
3. Pivots with Valid Entry (count + %)
4. Conversion Rate (%)
5. Rejection Reasons (5 rows mit count + %)

---

### 12. MFE/MAE Analysis
```
--- MAX FAVORABLE/ADVERSE EXCURSION ---
Average MFE (All): +0.82R (82% of TP distance)
Average MFE (Winners): +1.38R (reached TP)
Average MFE (Losers): +0.68R (came 68% toward TP)

Average MAE (All): -0.48R (48% of SL distance)
Average MAE (Winners): -0.42R (went 42% against before TP)
Average MAE (Losers): -0.98R (hit SL)

Interpretation:
- Losers came within 68% of TP on average (close calls!)
- Winners went 42% against you before hitting TP (patience required)
```

**Metriken**:
1. Average MFE (All)
2. Average MFE (Winners)
3. Average MFE (Losers) ⭐ (USER REQUEST!)
4. Average MAE (All)
5. Average MAE (Winners) ⭐ (Important for funded!)
6. Average MAE (Losers)
7. Interpretation (2-3 sentences)

---

### 13. Footer
```
================================================================================
END OF REPORT
Report Location: Backtest/02_W_test/baseline_report.txt
Trade Details: Backtest/02_W_test/trades.csv
HTML Report: Backtest/02_W_test/baseline_report.html
================================================================================
```

---

## 📈 HTML REPORT (QuantStats)

**Generiert automatisch via:**
```python
import quantstats as qs

# Returns Series aus Equity Curve
returns = equity_curve["value"].pct_change().dropna()

# HTML Report
qs.reports.html(
    returns,
    output='baseline_report.html',
    title='Model 3 - Weekly Baseline Backtest'
)
```

**Enthält automatisch:**
1. **Cumulative Returns Chart** (Equity Curve)
2. **Drawdown Chart** (über Zeit)
3. **Monthly Returns Heatmap** (Jahr vs Monat)
4. **Distribution of Returns** (Histogramm)
5. **Rolling Sharpe** (6-Monats-Fenster)
6. **Rolling Volatility** (6-Monats-Fenster)
7. **Alle Metriken in Tabellen**:
   - Sharpe, Sortino, Calmar
   - Max DD, Avg DD, Recovery Factor
   - Best/Worst Day/Week/Month/Year
   - Win Rate, Profit Factor, etc.

**Vorteil**: Alle professionellen Metriken + Charts automatisch ohne manuelles Coding!

---

## 📁 CSV EXPORTS (für Detail-Analyse)

### 1. trades.csv (alle Trade-Details)
**Columns** (28 Felder):
```
trade_id, pair, htf_timeframe, direction, entry_type,
pivot_time, valid_time, gap_touch_time, entry_time, exit_time, duration_days,
pivot_price, extreme_price, near_price, gap_pips, wick_diff_pips, wick_diff_pct,
total_refinements, priority_refinement_tf,
entry_price, sl_price, tp_price, exit_price,
final_rr, sl_distance_pips, tp_distance_pips,
exit_type, pnl_pips, pnl_r, win_loss,
mfe_pips, mfe_pct, mae_pips, mae_pct
```

**Zweck**: Für manuelles Debugging in TradingView

---

### 2. equity_curve.csv
**Columns**:
```
date, portfolio_value, drawdown_pct, open_trades, cumulative_pnl_r
```

**Zweck**: Input für QuantStats, externe Analyse

---

### 3. breakdown_pairs.csv
**Columns**:
```
pair, trades, winning_trades, losing_trades, win_rate_pct,
avg_winner_r, avg_loser_r, largest_winner_r, largest_loser_r,
profit_factor, payoff_ratio, expectancy_r,
avg_duration_days, trades_per_year
```

**Zweck**: Excel Pivot-Tabellen, Pair-Vergleich

---

## 🔢 SUMMARY: Alle Metriken

### TXT Report Sections (13):
1. Header (7 Felder)
2. Performance Summary (12 Metriken)
3. Portfolio Metrics (13 Metriken)
4. Risk-Adjusted Returns (3 Metriken)
5. Funded Account Check (6 Checks)
6. HTF Breakdown (1 Tabelle)
7. Top/Bottom 5 Pairs (2 Tabellen)
8. Direction Breakdown (1 Tabelle)
9. Yearly Performance (1 Tabelle + Summary)
10. Monthly Distribution (1 Übersicht)
11. Setup Conversion (9 Metriken)
12. MFE/MAE Analysis (6 Metriken + Text)
13. Footer (3 Zeilen)

**Total: ~70 Metriken in strukturiertem TXT**

### CSV Exports (3):
1. trades.csv (28 Felder pro Trade)
2. equity_curve.csv (5 Felder pro Tag)
3. breakdown_pairs.csv (13 Felder pro Pair)

### HTML Report:
- Alle QuantStats Charts + Metriken automatisch

---

## ⚙️ Transaktionskosten (MUSS implementiert werden!)

### Spreads
```python
SPREADS = {
    # Majors
    'EURUSD': 0.8, 'GBPUSD': 0.9, 'USDJPY': 0.8, 'USDCHF': 1.0,
    'AUDUSD': 0.9, 'USDCAD': 1.0, 'NZDUSD': 1.2,

    # Crosses
    'EURGBP': 1.2, 'EURJPY': 1.3, 'GBPJPY': 1.8, 'AUDJPY': 1.4,
    'NZDJPY': 1.8, 'EURAUD': 1.5, 'EURCHF': 1.3, 'GBPAUD': 1.8,
    'AUDNZD': 2.0, 'NZDCAD': 2.2, 'AUDCAD': 1.8, 'GBPCAD': 2.0,
    'GBPNZD': 2.5, 'EURNZD': 2.2, 'CHFJPY': 1.8, 'CADJPY': 1.6,
    'AUDCHF': 1.6, 'NZDCHF': 2.0, 'CADCHF': 1.8, 'GBPCHF': 1.9,
    'EURCAD': 1.6
}
```

### Slippage
```python
SLIPPAGE = 0.5  # Pips pro Trade (Standard)
```

### Total Cost per Trade
```python
def calculate_transaction_cost(pair, entry_price):
    """
    Berechnet Transaktionskosten in Pips
    """
    spread = SPREADS.get(pair, 1.5)
    slippage = SLIPPAGE

    total_cost_pips = spread + slippage

    # Von Entry/Exit Preis abziehen
    return total_cost_pips

# Beispiel:
# EURUSD: 0.8 + 0.5 = 1.3 Pips Kosten pro Trade
# Bei 60 Pip SL = 2.2% weniger R
```

**WICHTIG**: Ohne Spreads & Slippage sind Results unrealistisch!

---

## 📋 Implementation Checklist

**Für Weekly Baseline:**
- [ ] TXT Report mit allen 13 Sections
- [ ] HTML Report via QuantStats
- [ ] 3 CSV Exports (trades, equity, breakdown_pairs)
- [ ] Transaktionskosten implementiert
- [ ] MFE/MAE Tracking
- [ ] Funded Account Checks
- [ ] Alle Breakdowns (HTF, Pairs, Direction, Yearly)

**Optional (Nice-to-Have):**
- [ ] Entry Type Breakdown (für später: direct vs 1h vs 4h)
- [ ] Monthly Breakdown (detailliert)
- [ ] Weekday Breakdown
- [ ] Rolling Metrics

---

*Last Updated: 29.12.2025*
