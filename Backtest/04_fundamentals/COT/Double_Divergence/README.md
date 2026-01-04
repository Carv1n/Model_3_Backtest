# COT Double Divergence Filter - Model 3 Phase 3

**Status**: ⚠️ Implementiert, aber BUGS GEFUNDEN - Fixes benötigt

**Stand**: 31.12.2025

---

## ⚠️ BEKANNTE BUGS (31.12.2025)

### Bug 1: Falsche CSV-Speicherung ❌

**Problem**:
- CSVs werden nur 1x gespeichert (für Bias_8W Mode)
- Aber 18 Reports werden generiert (3 Modi × 6 Files)
- Alle Reports nutzen die GLEICHE falsche CSV (nur Bias_8W trades)
- Reports zeigen falsche Trade-Counts die nicht zur CSV passen

**Beispiel**:
- Bias_8W Report: "308 trades" ✓ (korrekt)
- Bias_to_Bias Report: "1317 trades" ✗ (aber CSV hat nur 308!)
- Bias_fix_0 Report: "1389 trades" ✗ (aber CSV hat nur 308!)

**Root Cause**:
- Line 340 in `apply_cot_filter.py` hat `if mode == 'Bias_8W':` Condition
- Dadurch werden Bias_to_Bias und Bias_fix_0 CSVs nicht gespeichert

**Fix Needed**:
```python
# In apply_cot_filter.py, line 339-345:
# Remove "if mode == 'Bias_8W'" condition
# Save CSVs for ALL modes in separate folders

# CURRENT (WRONG):
if mode == 'Bias_8W':
    trades_csv_dir = output_dir / 'Single_TF' / 'Trades'

# CORRECT (TO DO):
trades_csv_dir = output_dir / 'Single_TF' / 'Trades' / mode
trades_csv_dir.mkdir(parents=True, exist_ok=True)
```

**Status**: 🔴 NICHT GEFIXT - Wartet auf Code-Update

---

### Bug 2: Fehlende Report-Statistiken ❌

**Problem**:
- Phase 3 Reports fehlen VIELE Stats die in Phase 2 Reports vorhanden sind
- Nutzer kann Performance nicht vollständig beurteilen

**Konkret fehlende Stats**:
1. Long/Short Breakdown (Count, Ratio, Win Rates)
2. Payoff Ratio, Max Winner/Loser
3. Trade Duration, Trades per Month
4. Average Drawdown, Recovery Factor
5. Max Consecutive Wins/Losses
6. Concurrent Trades (Avg & Max)
7. MFE/MAE Winners vs. Losers (separate)
8. Funded Account Viability Checks

**Root Cause**:
- `generate_reports.py` berechnet nur minimale Stats
- Phase 2 `report_helpers.py` hat vollständige `calc_stats()` Funktion

**Fix Needed**:
- Erweitere `calculate_statistics()` in `generate_reports.py`
- Erweitere `calculate_portfolio_metrics()` mit Concurrent Trades, Avg DD, etc.
- Erweitere `calculate_mfe_mae()` mit Winners/Losers Breakdown
- Erweitere `format_report()` mit allen fehlenden Sections
- Nutze Phase 2 `report_helpers.py` als Referenz

**Status**: 🔴 NICHT GEFIXT - Wartet auf Code-Update

---

### Bug 3: Katastrophale Performance trotz Filter ❌

**Problem**:
- Filter entfernt 88% der Trades (2608 → 308 bei Bias_8W)
- Aber Win Rate verbessert sich nur um +0.9% (40.3% → 41.2%)
- Expectancy kaum verändert: -0.02 R → 0.00 R
- Profit Factor: 0.97 → 1.01 (+0.04)
- **Das ist VIEL zu wenig Verbesserung!**

**Hypothesen**:
1. Bias-Berechnung invertiert? (Commercial ↔ Retail vertauscht?)
2. Filter-Logik invertiert? (Falsche Trades genommen?)
3. Look-Ahead Bias? (Timing-Logik falsch?)
4. COT-Bias selbst ist ineffektiv für diese Strategie?

**Debug-Steps**:
1. Checke 10 Sample Trades manuell (Direction, COT Bias, Alignment)
2. Vergleiche mit TradingView Indikator
3. Prüfe ob Filter-Logik korrekt (aligned = keep, nicht-aligned = remove)

**Status**: 🟡 UNTER INVESTIGATION - Erst nach Bugs 1+2 fixen

---

## ✅ FIX PRIORITY

1. **Bug 1** (CSV Struktur) → HÖCHSTE PRIORITÄT - Korrekte Daten benötigt
2. **Bug 2** (Fehlende Stats) → HOHE PRIORITÄT - Vollständige Reports benötigt
3. **Bug 3** (Performance) → MEDIUM PRIORITÄT - Erst nach 1+2 debuggen

**Hinweis**: Bug 3 kann erst NACH Bugs 1+2 richtig untersucht werden!

---

## Übersicht

Dieser Filter wendet **COT (Commitment of Traders) Double Divergence** auf die Phase 2 Trade-Ergebnisse an.

**Zweck**: Nur Trades handeln, die mit dem COT-Bias aligned sind → Höhere Win Rate & Expectancy

---

## Technische Details

### COT Double Divergence Berechnung

**Formel**:
```
1. Net Positions:
   - CommNet = CommLong - CommShort (Commercial Hedgers)
   - RetailNet = RetailLong - RetailShort (Small Speculators)

2. WillCo Index (26 Wochen):
   - CommIdx = 100 * (CommNet - min_26w) / (max_26w - min_26w)
   - RetailIdx = 100 * (RetailNet - min_26w) / (max_26w - min_26w)

3. Divergenzen:
   - Div_base = CommIdx_base - RetailIdx_base
   - Div_quote = CommIdx_quote - RetailIdx_quote

4. Double Divergence:
   - DoubleDivergence = Div_base - Div_quote
   - Range: -200 bis +200
```

**Bias-Bestimmung**:
- **Long Bias**: DoubleDivergence >= Threshold (pair-spezifisch)
- **Short Bias**: DoubleDivergence <= -Threshold
- **Neutral**: |DoubleDivergence| < Threshold

**Thresholds** (aus Bias_Zone_Pine):
```
EURUSD: 160    GBPUSD: 180    AUDUSD: 120
EURAUD: 150    GBPAUD: 100    AUDCAD: 140
EURCAD: 180    GBPCAD: 190    AUDCHF: 110
EURCHF: 150    GBPCHF: 160    AUDJPY: 130
EURGBP: 170    GBPJPY: 170    AUDNZD: 130
EURJPY: 170    GBPNZD: 140    CADCHF: 120
EURNZD: 140    NZDCAD: 110    CADJPY: 130
USDCAD: 150    NZDCHF: 150    CHFJPY: 130
USDCHF: 170    NZDJPY: 130
USDJPY: 190    NZDUSD: 190
```

---

## 3 Bias-Modi

### Modus 1: Bias_8W (8-Wochen-Countdown)

**Logik**:
- Signal-Trigger: Divergence >= Threshold (long) oder <= -Threshold (short)
- Countdown: 8 Wochen ab Signal-Start
- Neues Signal: NUR wenn Countdown = 0
- Countdown: Jede Woche -1

**Beispiel**:
```
Woche 1: Div = 165 (>= 160) → Bias = long, Countdown = 8
Woche 2: Div = 140 (< 160)  → Bias = long, Countdown = 7
Woche 3: Div = 120          → Bias = long, Countdown = 6
...
Woche 9: Countdown = 0      → Bias = neutral
Woche 10: Div = 170         → NEUES Signal → Bias = long, Countdown = 8
```

**Charakteristik**: Konservativ - Signal muss "abkühlen" bevor neues starten kann

---

### Modus 2: Bias_to_Bias (Signal-zu-Signal)

**Logik**:
- Long Bias: Startet bei Div >= Threshold
- Long Bias: Bleibt bis Div <= -Threshold (Short-Signal)
- Short Bias: Startet bei Div <= -Threshold
- Short Bias: Bleibt bis Div >= Threshold (Long-Signal)
- Forward-Fill: Bias bleibt bis zum GEGENTEILIGEN Signal

**Beispiel**:
```
Woche 1: Div = 165          → Bias = long
Woche 2: Div = 140          → Bias = long (forward-fill)
Woche 3: Div = 80           → Bias = long (forward-fill)
...
Woche 10: Div = -165        → Bias = short (Umkehr!)
Woche 11: Div = -120        → Bias = short (forward-fill)
```

**Charakteristik**: Aggressiv - Bias bleibt bis zur Umkehr

---

### Modus 3: Bias_fix_0 (Null-Exit)

**Logik**:
- Long Bias: Startet bei Div >= Threshold
- Long Bias: Endet bei Null-Kreuzung (Div < 0)
- Short Bias: Startet bei Div <= -Threshold
- Short Bias: Endet bei Null-Kreuzung (Div > 0)
- Neutral: Nach jeder Null-Kreuzung

**Beispiel**:
```
Woche 1: Div = 165          → Bias = long
Woche 2: Div = 140          → Bias = long
Woche 3: Div = 80           → Bias = long
Woche 4: Div = 30           → Bias = long
Woche 5: Div = -10          → Bias = neutral (Null-Kreuzung!)
Woche 6: Div = -170         → Bias = short
Woche 7: Div = 5            → Bias = neutral (Null-Kreuzung!)
```

**Charakteristik**: Dynamisch - Bias endet bei Momentum-Verlust (Null-Kreuzung)

---

## Trade-Filter-Logik

### Wann wird geprüft?
- **NUR beim Entry**: COT-Bias wird NUR zum Zeitpunkt `entry_time` geprüft
- **NICHT während Trade**: Laufende Trades bleiben offen, egal wie sich COT ändert

### Was wird geprüft?
- **Long Trade**: Benötigt COT Bias = 'long'
- **Short Trade**: Benötigt COT Bias = 'short'
- **Neutral**: Trade wird NICHT genommen

### Timing (Look-Ahead Prevention)
```
COT-Daten: Dienstag gesammelt → Freitag veröffentlicht (+3 Tage)
Signal verfügbar: Ab nächstem Montag

Entry am Montag 9. Dez   → Nutze COT bis Freitag 6. Dez
Entry am Dienstag 10. Dez → Nutze COT bis Freitag 6. Dez
Entry am Freitag 13. Dez  → Nutze COT bis Freitag 6. Dez
Entry am Montag 16. Dez   → Nutze COT bis Freitag 13. Dez (neue Woche!)
```

**Regel**: COT-Daten <= Entry-Date (inclusive) → Kein Look-Ahead Bias

---

## Ordnerstruktur

```
COT/Double_Divergence/
├── scripts/
│   ├── cot_double_divergence.py   # COT Indikator (26W WillCo)
│   ├── apply_cot_filter.py        # Trade Filter (Main Script)
│   ├── generate_reports.py        # Report Generator
│   ├── Indikator_Pine             # TradingView Referenz
│   └── Bias_Zone_Pine             # TradingView Referenz
│
└── 01_default/
    └── Single_TF/
        ├── Trades/                        # Gefilterte Trade-CSVs
        │   ├── W_pure.csv                 # W Pure + COT
        │   ├── W_conservative.csv         # W Conservative + COT
        │   ├── 3D_pure.csv                # 3D Pure + COT
        │   ├── 3D_conservative.csv        # 3D Conservative + COT
        │   ├── M_pure.csv                 # M Pure + COT
        │   └── M_conservative.csv         # M Conservative + COT
        │
        └── results/
            ├── Bias_8W/                   # 8-Wochen-Countdown
            │   ├── W_pure.txt
            │   ├── W_conservative.txt
            │   ├── 3D_pure.txt
            │   ├── 3D_conservative.txt
            │   ├── M_pure.txt
            │   └── M_conservative.txt
            │
            ├── Bias_to_Bias/              # Signal-zu-Signal
            │   ├── W_pure.txt
            │   ├── W_conservative.txt
            │   ├── 3D_pure.txt
            │   ├── 3D_conservative.txt
            │   ├── M_pure.txt
            │   └── M_conservative.txt
            │
            └── Bias_fix_0/                # Null-Exit
                ├── W_pure.txt
                ├── W_conservative.txt
                ├── 3D_pure.txt
                ├── 3D_conservative.txt
                ├── M_pure.txt
                └── M_conservative.txt
```

**Total Output**:
- **18 TXT-Reports**: 3 Modi × 3 Timeframes × 2 Typen
- **6 Trade-CSVs**: W/3D/M × pure/conservative (basierend auf Bias_8W)

---

## Nutzung

### Script ausführen

```bash
cd "05_Model 3/Backtest/03_fundamentals/COT/Double_Divergence/scripts/"
python apply_cot_filter.py
```

**Output**:
```
=== COT DOUBLE DIVERGENCE FILTER - PHASE 3 ===

Processing Timeframe: W
  PURE Strategy:
    Original Trades (Phase 2): 2634

    Bias_8W:
      Filtered Trades: 1245
      Filter Rate: 52.7% removed
      ✓ Report: Single_TF/results/Bias_8W/W_pure.txt

    Bias_to_Bias:
      Filtered Trades: 1567
      Filter Rate: 40.5% removed
      ✓ Report: Single_TF/results/Bias_to_Bias/W_pure.txt

    Bias_fix_0:
      Filtered Trades: 1389
      Filter Rate: 47.3% removed
      ✓ Report: Single_TF/results/Bias_fix_0/W_pure.txt

  CONSERVATIVE Strategy:
    ...

Processing Timeframe: 3D
  ...

Processing Timeframe: M
  ...

=== ALL REPORTS GENERATED ===
```

---

## Report-Format

Jeder Report enthält:

### COT Filter Info
```
=== COT FILTER INFO ===
Original Trades (Phase 2): 2634
Filtered Trades (with COT): 1245
Filter Rate: 52.7% removed
Trades Removed: 1389
```

### Performance Summary
```
=== PERFORMANCE SUMMARY ===
Total Trades: 1245
Winning Trades: 684 (54.9%)
Losing Trades: 561 (45.1%)
Win Rate: 54.9%
Average Win: 1.32 R
Average Loss: -0.98 R
Expectancy: 2.15 R
Profit Factor: 1.85
```

### Portfolio Metrics
```
=== PORTFOLIO METRICS ===
Starting Capital: $100,000
Final Balance: $267,500
Total Return: 167.5%
CAGR: 11.2%
Max Drawdown: 18.3%
Max Drawdown Duration: 23 trades
```

### Risk-Adjusted Returns
```
=== RISK-ADJUSTED RETURNS ===
Sharpe Ratio: 1.85
Sortino Ratio: 2.34
Calmar Ratio: 0.61
Volatility (Annual): 15.8%
```

### MFE/MAE Analysis
```
=== MFE/MAE ANALYSIS ===
Average MFE: 78.5 pips
Average MAE: -32.1 pips
MFE/MAE Ratio: 2.44
```

---

## Erwartete Performance

**Phase 2 Baseline** (Technical only):
- Win Rate: ~40%
- Expectancy: -0.02 to 0 R
- Profit Factor: 0.9 - 1.0
- Total Trades: ~2600 (W), ~1900 (3D), ~1000 (M)

**Phase 3 Target** (Technical + COT):
- Win Rate: 50-60% (+10-20%)
- Expectancy: 2-4 R (+2-4 R improvement)
- Profit Factor: 1.5 - 2.0 (+50-100%)
- Total Trades: ~1000-1500 (W), ~800-1100 (3D), ~400-600 (M)

**Trade-Off**:
- **Weniger Trades**: Filter reduziert Setups um 40-60%
- **Höhere Qualität**: Bessere Win Rate & Expectancy
- **Stabilere Drawdowns**: Weniger False Signals

---

## Dependencies

**Python Packages**:
```
pandas
numpy
```

**Data Sources**:
- **COT Data**: `Data/Cot/Legacy_Reports/Forex/*.csv` (8 Währungen)
- **Phase 2 Trades**: `02_technical/01_DEFAULT/01_Single_TF/results/Trades/*.csv`

**Reference**:
- `Indikator_Pine`: TradingView Double Divergence Indikator
- `Bias_Zone_Pine`: TradingView Bias Zone Indikator (Thresholds)

---

## Validierung

### Vergleich mit TradingView

**Test-Script**:
```bash
cd scripts/
python cot_double_divergence.py
```

**Output**: `EURUSD_test.csv` (alle Wochen seit 2003)

**Vergleichen mit**:
- TradingView → EURUSD Chart
- Indikator "COT Double Divergence" anwenden
- Werte manuell vergleichen

**User-Validierung**: ✅ "die werte passen alle"

---

## Implementierungs-Details

### 1. COT-Indikator (`cot_double_divergence.py`)

**Klasse**: `COTDoubleDivergence`

**Methoden**:
- `load_currency_cot()`: Lädt COT-Daten für einzelne Währung
- `calculate_willco_index()`: Berechnet 26-Wochen WillCo Index
- `calculate_double_divergence()`: Berechnet Double Divergence + Bias (8W default)
- `generate_all_pairs()`: Berechnet alle 28 Pairs

**Output**: DataFrame mit `Date, Pair, DoubleDivergence, Threshold, Bias, Countdown`

---

### 2. Trade-Filter (`apply_cot_filter.py`)

**Klasse**: `COTTradeFilter`

**Methoden**:
- `load_cot_data_all_modes()`: Lädt COT-Daten mit allen 3 Bias-Modi
- `_calculate_bias_8w()`: 8-Wochen-Countdown Logik
- `_calculate_bias_to_bias()`: Signal-zu-Signal Logik
- `_calculate_bias_fix_0()`: Null-Exit Logik
- `get_cot_bias_at_entry()`: Holt COT-Bias zum Entry-Zeitpunkt (Look-Ahead Prevention)
- `filter_trades()`: Filtert Trades basierend auf Bias-Alignment
- `process_all_timeframes()`: Orchestriert W/3D/M × pure/con × 3 Modi

**Main-Funktion**: `main()` - Lädt Phase 2 Trades, filtert mit COT, generiert Reports

---

### 3. Report-Generator (`generate_reports.py`)

**Funktionen**:
- `calculate_statistics()`: Performance-Statistiken (Win Rate, Expectancy, etc.)
- `calculate_portfolio_metrics()`: Portfolio-Metriken (CAGR, Drawdown, Sharpe, etc.)
- `calculate_mfe_mae()`: MFE/MAE Analyse
- `format_report()`: Formatiert Report-Text
- `generate_report()`: Main-Funktion - Berechnet & speichert Report

**Format**: Identisch zu Phase 2 Reports + COT Filter Info

---

## Nächste Schritte

**Nach Script-Ausführung**:

1. **Reports analysieren**:
   - Vergleich: Phase 2 (Technical) vs. Phase 3 (Technical + COT)
   - Welcher Bias-Modus performt am besten?
   - Welcher Timeframe profitiert am meisten?

2. **Best Bias-Modus identifizieren**:
   - Bias_8W: Konservativ, weniger Trades
   - Bias_to_Bias: Aggressiv, mehr Trades
   - Bias_fix_0: Dynamisch, mittlere Trade-Anzahl

3. **Performance-Metriken**:
   - Win Rate: +10-20%? ✓
   - Expectancy: +2-4 R? ✓
   - Profit Factor: 1.5-2.0? ✓

4. **Dokumentation**:
   - Findings in README eintragen
   - CHANGELOG aktualisieren
   - Best Settings dokumentieren

---

*Last Updated: 31.12.2025*
