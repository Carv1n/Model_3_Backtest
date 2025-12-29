# Model 3 - Backtest Statistics Specification

## Zweck
Vollständige Übersicht aller zu trackenden Metriken für Portfolio-Backtest.

**Wichtig**: Nur ECHTE Trades (Entry erfolgt) werden in die Statistiken aufgenommen!

**Basis**: Professionelle Standards aus STRATEGY_STATS + spezifische User-Anforderungen

---

## 1. Trade-Level Statistiken (Pro Trade)

### 1.1 Basis Trade-Info
- **Trade ID** - Eindeutige Nummer
- **Pair** - Währungspaar
- **HTF Timeframe** - 3D, W, M
- **Direction** - bullish/bearish
- **Entry Type** - direct_touch, 1h_close, 4h_close

### 1.2 Timestamps
- **Pivot Time** - K2 Open (HTF Pivot)
- **Valid Time** - K3 Open (Pivot valid)
- **Gap Touch Time** - Erste Gap-Berührung (Daily)
- **Entry Time** - Tatsächlicher Entry
- **Exit Time** - SL oder TP Hit
- **Trade Duration** - Entry bis Exit (in Tagen/Stunden)

### 1.3 Preis-Levels
- **HTF Pivot** - Open K2
- **HTF Extreme** - Extremes Ende längerer Wick
- **HTF Near** - Near Ende kürzerer Wick
- **HTF Gap** - Pivot bis Extreme (Pips)
- **Wick Diff** - Near bis Extreme (Pips & % von Gap)
- **Entry Price** - Tatsächlicher Entry
- **SL Price** - Stop Loss
- **TP Price** - Take Profit (-1 Fib)
- **Exit Price** - Tatsächlicher Exit

### 1.4 Verfeinerungen
- **Total Refinements** - Anzahl gefundener Verfeinerungen
- **Priority Refinement TF** - Timeframe der gewählten Verfeinerung
- **Priority Refinement Near** - Near der gewählten Verfeinerung
- **Entry Level Type** - "refinement" oder "wick_diff"

### 1.5 Trade-Metriken
- **Initial RR** - Risk-Reward vor SL-Anpassung
- **Final RR** - Risk-Reward nach SL-Anpassung
- **SL Distance (Pips)** - Entry bis SL
- **TP Distance (Pips)** - Entry bis TP
- **Exit Type** - "TP", "SL"
- **PnL (Pips)** - Profit/Loss in Pips
- **PnL (R)** - Profit/Loss in R-Multiples
- **Win/Loss** - Boolean
- **Max Favorable Excursion (MFE)** - Max Bewegung in Richtung TP (Pips & %)
- **Max Adverse Excursion (MAE)** - Max Bewegung gegen Position (Pips & %)

---

## 2. Aggregate Trade-Statistiken

### 2.1 Allgemeine Metriken
- **Total Trades** - Gesamtanzahl Trades
- **Winning Trades** - Anzahl Gewinn-Trades
- **Losing Trades** - Anzahl Verlust-Trades
- **Win Rate (%)** - Winning Trades / Total Trades
- **Loss Rate (%)** - Losing Trades / Total Trades

### 2.2 PnL-Metriken
- **Total PnL (R)** - Summe aller PnL in R
- **Average PnL (R)** - Durchschnitt aller Trades (= Average Trade)
- **Average Win (R)** - Durchschnitt Gewinn-Trades (= Average Winner)
- **Average Loss (R)** - Durchschnitt Verlust-Trades (= Average Loser)
- **Largest Win (R)** - Größter Einzelgewinn (= Largest Winner)
- **Largest Loss (R)** - Größter Einzelverlust (= Largest Loser)
- **Average RR** - Durchschnitt Final RR aller Trades
- **Profit Factor** - Gross Profit / Gross Loss (>1.75 gut, >2.0 sehr gut)
- **Payoff Ratio** - Average Win / Average Loss
- **Expectancy** - (Win Rate × Avg Win) - (Loss Rate × Avg Loss)

### 2.3 Duration-Metriken
- **Average Duration (Days)** - Durchschnitt aller Trades
- **Min Duration (Days)** - Kürzester Trade
- **Max Duration (Days)** - Längster Trade
- **Average Duration Winners (Days)** - Nur Gewinn-Trades
- **Average Duration Losers (Days)** - Nur Verlust-Trades

### 2.4 MFE/MAE-Metriken
- **Average MFE (%)** - Durchschnitt Max Favorable Excursion
- **Average MFE Winners (%)** - Nur Gewinn-Trades
- **Average MFE Losers (%)** - Nur Verlust-Trades (wie nah war TP?)
- **Average MAE (%)** - Durchschnitt Max Adverse Excursion
- **Average MAE Winners (%)** - Nur Gewinn-Trades
- **Average MAE Losers (%)** - Nur Verlust-Trades

### 2.5 SL/TP-Metriken
- **Average SL Distance (Pips)** - Durchschnitt
- **Average TP Distance (Pips)** - Durchschnitt
- **Min/Max SL Distance (Pips)** - Range
- **Min/Max TP Distance (Pips)** - Range

---

## 3. Breakdown-Statistiken

### 3.1 Nach HTF Timeframe
Für jeden HTF (3D, W, M):
- Total Trades
- Win Rate
- Average PnL (R)
- Profit Factor
- Average Duration

### 3.2 Nach Currency Pair
Für jedes Pair (28 Majors/Crosses):
- Total Trades
- Win Rate
- Average PnL (R)
- Profit Factor
- Best/Worst Trade

### 3.3 Nach Direction
Für bullish/bearish:
- Total Trades
- Win Rate
- Average PnL (R)
- Profit Factor

### 3.4 Nach Entry Type
Für direct_touch, 1h_close, 4h_close:
- Total Trades
- Win Rate
- Average PnL (R)
- Profit Factor
- Average Duration

### 3.5 Nach Entry Level Type
Für "refinement" vs "wick_diff":
- Total Trades
- Win Rate
- Average PnL (R)
- Profit Factor

### 3.6 Nach Refinement TF
Für H1, H4, D, 3D, W (Verfeinerung):
- Total Trades
- Win Rate
- Average PnL (R)
- Profit Factor

### 3.7 Nach Jahr
Für jedes Jahr:
- Total Trades
- Win Rate
- Total PnL (R)
- Average PnL (R)
- Profit Factor
- Best/Worst Month

### 3.8 Nach Monat
Für jeden Monat (1-12):
- Total Trades
- Win Rate
- Average PnL (R)
- Best/Worst Year für diesen Monat

### 3.9 Nach Wochentag
Für jeden Wochentag (Entry Day):
- Total Trades
- Win Rate
- Average PnL (R)

### 3.10 Nach Trade Frequency
- **Trades per Day** - Durchschnittlich
- **Trades per Week** - Durchschnittlich
- **Trades per Month** - Durchschnittlich
- **Trades per Year** - Durchschnittlich
- **Time in Market (%)** - Prozentsatz mit offenen Positionen (Exposure)
- **Average Bars in Trade** - Durchschnittliche Anzahl Bars/Kerzen

---

## 4. Portfolio-Statistiken

### 4.1 Portfolio-Metriken
- **Starting Capital** - Initial Portfolio-Wert
- **Ending Capital** - Final Portfolio-Wert
- **Total Return (%)** - (Ending - Starting) / Starting
- **CAGR (%)** - Compound Annual Growth Rate
- **Risk Per Trade (%)** - Fixed (z.B. 1%)
- **Max Position Size** - Max Trades gleichzeitig
- **Average Concurrent Trades** - Durchschnittlich gleichzeitige Trades

### 4.2 Drawdown-Metriken
- **Max Drawdown (%)** - Größter Peak-to-Trough Verlust
- **Max Drawdown Duration (Days)** - Längste Drawdown-Phase
- **Average Drawdown (%)** - Durchschnitt aller Drawdowns
- **Recovery Factor** - Net Profit / Max Drawdown
- **Calmar Ratio** - CAGR / Max Drawdown

### 4.3 Risk-Adjusted Returns
- **Sharpe Ratio** - (Return - RiskFree) / Volatility
  - Annahme: RiskFree Rate = 0% oder konfigurierbar
  - >1.0 gut, >2.0 sehr gut, >3.0 exzellent
- **Sortino Ratio** - (Return - RiskFree) / Downside StdDev
  - Nur Downside-Volatilität (besserer Risk-Indikator)
  - >2.0 ist gut
- **Omega Ratio** - Verhältnis Gains zu Losses über Schwellenwert
- **Calmar Ratio** - CAGR / Max Drawdown
  - >3.0 ist exzellent (bereits in 4.2, hier als Referenz)
- **Return/Risk Ratio** - Average Return / Average Risk

### 4.4 Volatilitäts-Metriken
- **Annualized Volatility** - Jährliche Schwankung (Standard Deviation)
- **Downside Deviation** - Nur negative Schwankungen
- **Skewness** - Schiefe der Renditeverteilung (positive/negative Asymmetrie)
- **Kurtosis** - "Fat Tails" der Renditeverteilung (Extremereignisse)
- **Ulcer Index** - Misst Tiefe und Dauer von Drawdowns kombiniert

### 4.5 Expectancy & SQN
- **Expectancy** - (Win Rate × Avg Win) - (Loss Rate × Avg Loss) (bereits in 2.2)
- **System Quality Number (SQN)** - (Expectancy / StdDev) × √n
  - Misst Qualität des Trading-Systems

### 4.6 Consecutive Streaks
- **Max Consecutive Wins** - Längste Gewinnserie
- **Max Consecutive Losses** - Längste Verlustserie
- **Current Streak** - Aktuelle Win/Loss-Serie am Ende

### 4.7 Weitere Portfolio-Metriken (Optional - Später)
- **Portfolio Turnover** - Umschlaghäufigkeit des Portfolios
- **Gross Leverage** - Gesamtes eingesetztes Kapital relativ zu NAV
- **Net Leverage** - Netto-Exposition
- **Position Concentration** - Verteilung auf einzelne Positionen
- **Currency Exposure** - Verteilung nach Währungen (EUR, USD, JPY, etc.)

---

## 5. Zeitreihen-Daten

### 5.1 Equity Curve
- **Date** - Tägliches Datum
- **Portfolio Value** - Kapital nach allen Trades bis Datum
- **Drawdown (%)** - Aktueller Drawdown
- **Open Trades** - Anzahl offener Positionen
- **Cumulative PnL (R)** - Kumulativer Gewinn/Verlust

### 5.2 Monthly Performance
- **Year-Month** - YYYY-MM
- **Trades** - Anzahl Trades in Monat
- **PnL (R)** - Summe PnL
- **Return (%)** - Prozentuale Veränderung
- **Win Rate (%)** - Win Rate für Monat
- **Best Trade** - Bester Trade des Monats
- **Worst Trade** - Schlechtester Trade des Monats

### 5.3 Yearly Performance
- **Year** - YYYY
- **Annual Return (%)** - Jährliche Rendite
- **CAGR (%)** - Compound Annual Growth Rate
- **Trades** - Anzahl Trades
- **Win Rate (%)** - Win Rate für Jahr
- **Best Month** - Bester Monat des Jahres
- **Worst Month** - Schlechtester Monat des Jahres

### 5.4 Best/Worst Performance
- **Best Day** - Bester Tag (Return %)
- **Worst Day** - Schlechtester Tag (Return %)
- **Best Week** - Beste Woche (Return %)
- **Worst Week** - Schlechteste Woche (Return %)
- **Best Month** - Bester Monat (Return %)
- **Worst Month** - Schlechtester Monat (Return %)
- **Best Year** - Bestes Jahr (Return %)
- **Worst Year** - Schlechtestes Jahr (Return %)

### 5.5 Rolling Metrics (Optional - Später)
- **Rolling Win Rate (20 Trades)** - Rollende Win Rate
- **Rolling Profit Factor (20 Trades)** - Rollender Profit Factor
- **Rolling Average PnL (20 Trades)** - Rollender Durchschnitt

---

## 6. Validierungs-Statistiken

### 6.1 Setup-Statistiken (Gesamt)
Diese zeigen ALLE gefundenen Setups (auch ohne Entry):
- **Total HTF Pivots Found** - Alle HTF Pivots
- **Pivots with Gap Touch** - Pivots mit Gap Touch
- **Pivots with Valid Entry** - Pivots mit erfolgreichem Entry
- **Conversion Rate (%)** - Valid Entry / Total Pivots

### 6.2 Filter-Statistiken
Anzahl ausgeschlossener Setups pro Filter:
- **Rejected: No Gap Touch** - Kein Gap Touch
- **Rejected: TP Touched Before Entry** - TP vorher berührt
- **Rejected: No Valid Refinement** - Keine gültige Verfeinerung
- **Rejected: RR < 1.0** - RR zu niedrig
- **Rejected: Failed Entry Confirmation** - Entry-Bestätigung fehlgeschlagen

**Wichtig**: Diese Zähler sind informativ, erscheinen NICHT in Trade-Statistiken!

---

## 7. Export-Formate

### 7.1 CSV-Dateien
1. **trades.csv** - Alle Trade-Details (Abschnitt 1)
2. **aggregate_stats.csv** - Zusammenfassende Metriken (Abschnitt 2)
3. **breakdown_htf.csv** - HTF Breakdown (Abschnitt 3.1)
4. **breakdown_pairs.csv** - Pairs Breakdown (Abschnitt 3.2)
5. **breakdown_direction.csv** - Direction Breakdown (Abschnitt 3.3)
6. **breakdown_entry.csv** - Entry Type Breakdown (Abschnitt 3.4)
7. **breakdown_yearly.csv** - Yearly Performance (Abschnitt 3.7)
8. **breakdown_monthly.csv** - Monthly Performance (Abschnitt 3.8)
9. **equity_curve.csv** - Equity Curve (Abschnitt 5.1)
10. **monthly_performance.csv** - Monthly Returns (Abschnitt 5.2)
11. **validation_stats.csv** - Setup/Filter Statistiken (Abschnitt 6)

### 7.2 Summary Report (TXT/MD)
- Executive Summary mit wichtigsten Metriken
- Tabellen für Breakdowns
- Equity Curve als ASCII-Plot (optional)

### 7.3 JSON (Optional)
- Vollständige Daten für weitere Analyse
- Für quantstats oder custom Tools

---

## 8. Quantstats Integration

### 8.1 Kompatible Metriken
Folgende Metriken sind quantstats-kompatibel:
- Sharpe Ratio
- Sortino Ratio
- Max Drawdown
- CAGR
- Calmar Ratio
- Recovery Factor
- Win Rate
- Profit Factor
- Equity Curve

### 8.2 Quantstats Export
- **Returns Series** - Tägliche/Monatliche Returns für quantstats.reports
- **Benchmark** - Optional: Buy & Hold Benchmark

---

## 9. Visualisierungen (Optional - Später)

Mögliche Plots:
1. **Equity Curve** - Portfolio Value über Zeit
2. **Drawdown Chart** - Drawdowns über Zeit
3. **Monthly Returns Heatmap** - Jahr vs Monat
4. **Win Rate by Pair** - Balkendiagramm
5. **PnL Distribution** - Histogramm
6. **MFE vs MAE Scatter** - Trade-Qualität
7. **Trade Duration Distribution** - Histogramm

---

## 10. Professionelle Minimum-Standards

**Aus STRATEGY_STATS - Minimum für professionelle Bewertung:**
- ✅ **Sharpe Ratio > 1.5** (>1.0 gut, >2.0 sehr gut, >3.0 exzellent)
- ✅ **Calmar Ratio > 2.0** (>3.0 ist exzellent)
- ✅ **Win Rate > 45%** (bei Payoff Ratio > 1.5)
- ✅ **Max DD < 20%** (unter 20% ist gut)
- ✅ **Min. 200 Trades** für statistische Signifikanz
- ✅ **Profitabel in verschiedenen Market Regimes** (Bull/Bear/Sideways)

**Zusätzliche Qualitätskriterien:**
- Profit Factor > 1.75 (>2.0 sehr gut)
- Sortino Ratio > 2.0
- Expectancy positiv
- SQN (System Quality Number) hoch

---

## 11. Priorität für Baseline-Backtest

### Must-Have (Baseline):
- Abschnitt 1: Alle Trade-Details
- Abschnitt 2: Alle Aggregate-Metriken (inkl. neue: Payoff, Expectancy)
- Abschnitt 3.1-3.4: HTF, Pairs, Direction, Entry Type Breakdowns
- Abschnitt 3.7: Yearly Breakdown
- Abschnitt 4.1-4.6: Alle Portfolio-Metriken (inkl. neue: Volatility, Sharpe, Sortino, Omega, Ulcer, SQN)
- Abschnitt 5.1: Equity Curve
- Abschnitt 5.2: Monthly Performance
- Abschnitt 5.3: Yearly Performance
- Abschnitt 6: Validierungs-Statistiken

### Nice-to-Have (Später):
- Abschnitt 3.5-3.10: Weitere Breakdowns (Entry Level, Refinement TF, Month, Weekday, Frequency)
- Abschnitt 4.7: Weitere Portfolio-Metriken (Turnover, Leverage, etc.)
- Abschnitt 5.4: Best/Worst Performance
- Abschnitt 5.5: Rolling Metrics
- Abschnitt 9: Visualisierungen

---

## 12. Transaktionskosten & Realismus (WICHTIG!)

**Aus STRATEGY_STATS - Für realistischen Backtest:**

### Spreads (MUSS implementiert werden!)
- **Major Pairs (EUR/USD, GBP/USD, USD/JPY)**: 0.5-1.0 Pips
- **Minor Pairs (EUR/GBP, AUD/JPY, etc.)**: 1.0-1.5 Pips
- **Exotic Crosses (NZD/CAD, etc.)**: 1.5-2.0 Pips

### Slippage (KRITISCH!)
- **Standard**: 0.5-1.0 Pip pro Trade (realistisch bei Market Orders)
- **Volatile Markets**: 1.0-2.0 Pips
- **Über Nacht/Wochenende**: Höher (2-5 Pips möglich)

### Commission (Falls applicable)
- Bei RAW Spread Accounts
- Typisch: $3-7 per 100k Lot

### Swap/Overnight Financing
- Bei Positionen über Nacht
- Kann positiv oder negativ sein
- Je nach Pair und Richtung

**WICHTIG**: Ohne Spreads & Slippage sind Backtest-Ergebnisse UNREALISTISCH!

---

## 13. Implementierungs-Hinweise

### 13.1 Trade-Tracking
Während Backtest:
```python
trade = {
    "trade_id": int,
    "pair": str,
    "htf_timeframe": str,
    "direction": str,
    "entry_type": str,
    # ... alle anderen Felder aus Abschnitt 1
}
trades.append(trade)
```

### 13.2 Equity Curve Berechnung
```python
capital = starting_capital
for trade in chronological_trades:
    risk_amount = capital * risk_per_trade
    pnl_amount = risk_amount * trade["pnl_r"]
    capital += pnl_amount
    equity_curve.append({"date": trade["exit_time"], "value": capital})
```

### 13.3 Drawdown Berechnung
```python
peak = starting_capital
max_dd = 0
for point in equity_curve:
    if point["value"] > peak:
        peak = point["value"]
    dd = (peak - point["value"]) / peak
    max_dd = max(max_dd, dd)
    point["drawdown"] = dd
```

### 13.4 QuantStats Integration
```python
import quantstats as qs
import pandas as pd

# Returns Series erstellen (aus Equity Curve)
returns = equity_curve["value"].pct_change().dropna()

# Vollständiger HTML Report
qs.reports.html(
    returns,
    output='backtest_report.html',
    title='Model 3 - Weekly Baseline Backtest'
)

# Einzelne Metriken
sharpe = qs.stats.sharpe(returns)
max_dd = qs.stats.max_drawdown(returns)
cagr = qs.stats.cagr(returns)
sortino = qs.stats.sortino(returns)
calmar = qs.stats.calmar(returns)
```

---

## 14. User-Spezifische Anforderungen

### Aus Conversation:
1. **Average RR** ✅ (Abschnitt 2.2)
2. **Average Return, Duration (Avg/Max/Min)** ✅ (Abschnitt 2.2, 2.3)
3. **Average Max Move Richtung TP ohne Hit** ✅ (MFE Losers - Abschnitt 2.4)
4. **Trade Counts (Total, Year, Month, Asset)** ✅ (Abschnitt 2.1, 3.2, 3.7, 3.8)
5. **Average SL/TP Pips** ✅ (Abschnitt 2.5)
6. **Portfolio Metrics (DD, Sharpe, Win Rate, PF, RF)** ✅ (Abschnitt 4)
7. **Equity Curve & Monthly Performance** ✅ (Abschnitt 5)

### Wichtig:
- **Nur ECHTE Trades** (Entry erfolgt) in allen Statistiken!
- Validierungs-Stats (Abschnitt 6) separat - nicht in Trade-Stats!
- Chronologische Portfolio-Simulation (nicht pair-by-pair)

---

## 15. Zusammenfassung: Neue Metriken aus STRATEGY_STATS

**Hinzugefügte professionelle Metriken:**
1. **Payoff Ratio** - Average Win / Average Loss (Abschnitt 2.2)
2. **Expectancy** - Erwarteter Gewinn pro Trade (Abschnitt 2.2 & 4.5)
3. **Omega Ratio** - Gains/Losses über Schwellenwert (Abschnitt 4.3)
4. **Sortino Ratio** - Risk-adjusted mit Downside Volatility (Abschnitt 4.3)
5. **Annualized Volatility** - Jährliche Schwankung (Abschnitt 4.4)
6. **Downside Deviation** - Nur negative Schwankungen (Abschnitt 4.4)
7. **Skewness & Kurtosis** - Verteilungsform (Abschnitt 4.4)
8. **Ulcer Index** - Drawdown Tiefe + Dauer (Abschnitt 4.4)
9. **System Quality Number (SQN)** - System-Qualität (Abschnitt 4.5)
10. **Trade Frequency Metriken** - Per Day/Week/Month/Year (Abschnitt 3.10)
11. **Time in Market %** - Exposure-Zeit (Abschnitt 3.10)
12. **Best/Worst Performance** - Day/Week/Month/Year (Abschnitt 5.4)
13. **Currency Exposure** - Verteilung nach Währungen (Abschnitt 4.7)

**Neue Sections:**
- Abschnitt 10: Professionelle Minimum-Standards (Sharpe > 1.5, Calmar > 2.0, etc.)
- Abschnitt 12: Transaktionskosten & Realismus (Spreads, Slippage)
- Abschnitt 13.4: QuantStats Integration Code

**Priorisierung:**
- Must-Have für Baseline: Alle Core-Metriken (1-6, 10-14)
- Nice-to-Have: Advanced Breakdowns & Visualisierungen (7-9, 15)

**Nächste Schritte:**
1. User-Review dieser kompletten Statistik-Liste
2. Finalisierung der Must-Have vs Nice-to-Have
3. Implementation Planung (Portfolio Backtest Script)

---

*Last Updated: 29.12.2025*
