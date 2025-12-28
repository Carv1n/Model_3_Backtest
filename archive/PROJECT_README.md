# Model 3 - Multi-Timeframe Pivot Trading Backtest System

## 📊 Projekt-Übersicht

**Model 3** ist ein komplexes Multi-Timeframe Pivot-Trading-System mit Verfeinerungs-Mechanismus für 28 Forex-Paare über mehrere Timeframes (3D, W, M für Pivots, 1H-W für Verfeinerungen).

### System-Architektur
```
/Users/carvin/Documents/Trading Backtests/
├── Data/Chartdata/Forex/          ← ZENTRALE DATENQUELLE (shared)
│   ├── H1/  (28 CSVs)
│   ├── H4/  (28 CSVs)
│   ├── D/   (28 CSVs)
│   ├── 3D/  (28 CSVs)
│   ├── W/   (28 CSVs)
│   ├── M/   (28 CSVs)
│   └── Parquet/
│       ├── All_Pairs_H1_UTC.parquet
│       ├── All_Pairs_H4_UTC.parquet
│       ├── All_Pairs_D_UTC.parquet
│       ├── All_Pairs_3D_UTC.parquet
│       ├── All_Pairs_W_UTC.parquet
│       └── All_Pairs_M_UTC.parquet
│
└── 05_Model 3/                     ← PROJEKT-ORDNER
    ├── config.py                   ← Basis-Config (API, Pairs, Paths)
    ├── backtest_config.py          ← Backtest-Regeln (variabel)
    ├── PROJECT_README.md           ← DIESE DATEI
    │
    ├── scripts/
    │   ├── data_processing/        ← Daten-Download & Processing
    │   │   └── 0_complete_fresh_download.py
    │   │
    │   ├── backtesting/            ← Backtest-System
    │   │   ├── backtest_model3.py      (Main Engine - Model 3)
    │   │   ├── run_all_backtests.py    (Batch Runner)
    │   │   ├── backtest_ui.py          (Interactive UI)
    │   │   ├── view_results.py         (Results Viewer)
    │   │   ├── visualizations.py       (Charts)
    │   │   ├── monte_carlo.py          (MC Simulation)
    │   │   └── create_summary.py       (Summary Reports)
    │   │
    │   └── archive/                ← Alte/obsolete Scripts (nicht verwenden!)
    │
    ├── pivot_analysis/             ← Pivot Quality Tests
    │   ├── pivot_analysis.py
    │   ├── pivot_quality_test.py
    │   └── results/
    │
    └── results/                    ← Backtest Outputs
        ├── trades/                 (Trade CSVs)
        ├── charts/                 (Visualisierungen)
        └── reports/                (Summary Reports)
```

---

## 🎯 Trading-Strategie

### Pivot-Erkennung (HTF: 3D, W, M)
**Pivot = 2-Candle Pattern:**
- **Bullish Pivot:** Rote Kerze (C<O) → Grüne Kerze (C>O)
- **Bearish Pivot:** Grüne Kerze (C>O) → Rote Kerze (C<O)

**Pivot-Struktur:**
- **Pivot:** Open der zweiten Kerze
- **Pivot Extreme:** Ende der längeren Wick (bullish: tiefster Low, bearish: höchster High)
- **Pivot Near:** Ende der kürzeren Wick (bullish: höherer Low, bearish: niedrigerer High)
- **Pivot Gap:** Box von Pivot bis Pivot Extreme
- **Wick Difference:** Box von Pivot Near bis Pivot Extreme

**Filter:**
- **Doji-Filter:** Kerze ignorieren wenn Body < 5% der Range
- **Validation:** Pivot valid ab **Close der 2. Candle**

### Verfeinerungen (LTF: 1H, 4H, D, 3D, W)

**Such-Prozess:**
- Erst NACH HTF-Pivot-Entstehung (Kerze 2 geschlossen)
- Systematisch von höherem TF nach unten: M→W→3D→D→4H→1H
- Innerhalb der **Wick Difference** des HTF-Pivots suchen

**Gültigkeitsbedingungen:**
- Größe max. **20% der Pivot Gap**
- Position innerhalb Wick Difference (Ausnahme: exakt auf Pivot Near erlaubt)
- **Unberührt-Regel:** Vor HTF-Pivot-Entstehung nicht berührt
- Doji-Filter (5% Body Minimum)

### Entry Rules

**Voraussetzungen:**
1. HTF Pivot muss valide sein
2. **Pivot Gap muss zuerst getriggert werden**
3. Dann wird Verfeinerung relevant

**Entry-Bestätigung (parametrisierbar):**
- **1H Close** (Standard): Warte auf 1H Close über/unter Verfeinerungs-Level, Entry bei Open nächster Candle
- **4H Close**: Warte auf 4H Close Bestätigung
- **Direct Touch**: Sofortiger Entry bei Berührung (kein Close)

**Invalidierung:**
- Wenn Close nicht bestätigt → Verfeinerung gelöscht
- Wenn Verfeinerung durchbrochen wird → nächste Verfeinerung

### Exit Rules

**Fibonacci-Levels:**
- **Fib 0:** Pivot
- **Fib 1:** Pivot Extreme
- **Fib 1.1:** 0.1× Gap jenseits Extreme

**Stop Loss:**
- **Min. 60 Pips** von Entry
- **Min. über/unter Fib 1.1**

**Take Profit:**
- **Fib -1** (1× Gap jenseits Pivot)

**Risk/Reward:** 1.0 - 1.5 (variabel, SL wird angepasst)

---

---

## ⚙️ Konfiguration

### `config.py` (Basis-Einstellungen)
```python
# API
OANDA_API_KEY = "..."
OANDA_ACCOUNT_TYPE = "live"

# 28 Forex Pairs
PAIRS = ['AUDCAD', 'AUDCHF', ..., 'USDJPY']

# Timeframes
TIMEFRAMES = ['H1', 'H4', 'D', '3D', 'W', 'M']

# Paths (automatisch gesetzt)
DATA_PATH = .../Data/Chartdata/Forex/
RESULTS_PATH = .../03_Model X/results/
```

### `backtest_config.py` (Backtest-Regeln)

**FIXIERTE REGELN (nicht variabel):**
```python
PIVOT_TIMEFRAMES = ['3D', 'W', 'M']  # Nur diese für Pivots
PIVOT_VALIDATION_CANDLES = 2         # Pivot braucht 2 Candles
PIVOT_VALID_AFTER_CANDLES = 2        # Valid ab 3. Candle
```

**VARIABLE REGELN (aktuell):**
```python
MULTIPLE_TIMEFRAME_STRATEGY = 'highest'  # Bei Gap auf 3D+W+M: nur M
ENTRY_WITH_OPEN_TRADES = 'always'        # Neue Trades immer nehmen
MAX_TOTAL_POSITIONS = None               # Unbegrenzt
MAX_POSITIONS_PER_PAIR = None            # Unbegrenzt
ENTRY_TYPE = 'direct_touch'
EXIT_TYPE = 'fixed'
MIN_GAP_SIZE_PIPS = 10
MAX_GAP_SIZE_PIPS = 250
```

---

## 🚀 Usage

### 1. Daten-Download (falls nötig)
```bash
python scripts/data_processing/0_complete_fresh_download.py
```
Lädt frische Daten von Oanda API und erstellt Parquet-Files.

### 2. Backtest ausführen

**Single Pair:**
```bash
python scripts/backtesting/backtest_model3.py \
    --pairs EURUSD \
    --start-date 2020-01-01
```

**Mit Entry-Varianten:**
```bash
# 1H Close Bestätigung (Standard)
python scripts/backtesting/backtest_model3.py --pairs EURUSD --entry-confirmation 1h_close

# Direkter Touch (ohne Close)
python scripts/backtesting/backtest_model3.py --pairs EURUSD --entry-confirmation direct_touch

# 4H Close Bestätigung
python scripts/backtesting/backtest_model3.py --pairs EURUSD --entry-confirmation 4h_close
```

**Alle 28 Pairs:**
```bash
python scripts/backtesting/backtest_model3.py \
    --start-date 2015-01-01 \
    --output results/trades/model3_all.csv
```

**Nur bestimmte HTF-Timeframes:**
```bash
# Nur Weekly Pivots
python scripts/backtesting/backtest_model3.py --htf-timeframes W

# Nur 3D und W
python scripts/backtesting/backtest_model3.py --htf-timeframes 3D W
```

### 3. Ergebnisse visualisieren

**Vollständiger Report:**
```bash
python3 scripts/backtesting/view_results.py \
    -i results/trades/all_trades_chronological.csv
```

**Charts erstellen:**
```bash
python3 scripts/backtesting/visualizations.py \
    -i results/trades/all_trades_chronological.csv
```
Erstellt:
- Equity Curve + Drawdown
- R-Multiple Distribution
- Monthly Returns Heatmap
- Win/Loss Analysis

**Monte Carlo Simulation:**
```bash
python3 scripts/backtesting/monte_carlo.py \
    -i results/trades/all_trades_chronological.csv \
    -n 1000 -p 100
```
Simuliert 1000 alternative Equity-Paths durch Trade-Randomisierung.

### 4. Pivot Quality Test
```bash
python3 pivot_analysis/pivot_quality_test.py
```
Testet verschiedene TP/SL-Kombinationen (9 Kombinationen × 28 Pairs × 3 Timeframes).

**Output:** `pivot_analysis/results/PIVOT_QUALITY_REPORT_*.txt`

---

## 📊 Output-Dateien

### Trade CSVs (`results/trades/`)
- `all_trades_chronological.csv` - Alle Trades zeitlich sortiert
- `{PAIR}_{TIMEFRAME}_trades.csv` - Pro Pair/TF

**Spalten:**
```
trade_id, pair, timeframe, direction, entry_time, entry_price,
tp_price, sl_price, exit_time, exit_price, exit_reason,
pnl_pips, pnl_r, gap_size_pips, trade_duration_hours
```

### Summary Reports (`results/reports/`)
- Detaillierte Performance-Metriken
- Pair-by-Pair Breakdown
- Monatliche/Jährliche Returns

### Charts (`results/charts/`)
- `equity_curve.png`
- `drawdown_chart.png`
- `r_multiple_distribution.png`
- `monthly_returns_heatmap.png`
- `win_loss_analysis.png`

---

## 🔍 Wichtige Metriken

### Basis-Stats
- Total Trades, Win Rate, Winning/Losing Trades

### R-Multiple Performance
- Total R, Expectancy, Avg Win/Loss, Win/Loss Ratio, Max DD (R)

### Account % Performance
- Total Return (%), Return/Month, Return/Year, Max DD (%)

### Risk Metriken
- Profit Factor, Sharpe, Sortino, Calmar, Recovery Factor

### Konsistenz
- Max Consecutive Wins/Losses
- Avg Trade Duration
- R-Squared (Equity Curve Glattheit)

### Zeit-Metriken
- Total Days/Years
- Trades/Year, Trades/Month (Avg/Max/Min)

### Concurrent Positions
- Max, Median, Avg gleichzeitig offene Positionen

---

## 🎯 Projektziele & Philosophie

### Was ist Model 3?
Model 3 ist eine **komplexe Multi-Timeframe Pivot-Strategie** mit Verfeinerungen:
- **Multi-TF Verfeinerungen** (systematische Suche von M bis 1H)
- **Entry-Bestätigung** mit 1H Close (parametrisierbar)
- **Dynamisches RR** (1.0-1.5, SL wird angepasst)
- **Präzises Entry-Timing** durch Verfeinerungs-Hierarchie
- **Komplexer** als Model X, dafür präzisere Entries

### Philosophie
⚠️ **WICHTIG:** Die Strategie basiert stark auf **Fundamentals** (COT, Seasonality, Valuation, Bonds)
- **Technisches** dient nur als Entry-Timing
- **Fundamentals** geben Richtung und Bias
- Ohne fundamentale Filter wahrscheinlich **NICHT profitabel**

### Entwicklungsziel
- Systematisches Backtesting zur Validierung der Pivot-Gap-Logik
- Optimierung von Entry/Exit-Varianten
- Spätere Integration mit fundamentalen Indikatoren
- Forward-Testing Vorbereitung

### 💡 Wichtige Erkenntnisse

**Pivot-Validierung:**
- Body-Filter: 5% (Standard für Model 3)
- Pivot valid ab **Close der 2. Candle**
- Wick Difference als Suchbereich für Verfeinerungen

**Verfeinerungen:**
- Max. 20% der Pivot Gap Größe
- Höchster TF hat Priorität (M > W > 3D > D > H4 > H1)
- Unberührt-Regel: Vor HTF-Pivot nicht berührt

**Entry-Bestätigung:**
- **1H Close** (Standard): Bessere Win Rate durch Bestätigung
- **Direct Touch**: Mehr Setups, aber höhere Fehlsignale
- **4H Close**: Noch selektiver, weniger Setups

**Zeitstempel-Handling:**
- Oanda gibt Close-Timestamp → Muss zu Open-Timestamp konvertiert werden
- Weekly: Timestamp +1 Tag für Alignment mit TradingView
- Daily: Timestamp +1 Tag (Oanda Close → TV Open)

**Daten-Organisation:**
- Zentrale Parquet-Files (ein File pro Timeframe, alle Pairs)
- MultiIndex (pair, time) für schnellen Zugriff
- UTC Timestamps ohne TZ-Info (wichtig für Parquet Kompatibilität)

---

## 🛠️ Technische Details

### Dependencies
```bash
pip install -r requirements.txt
```

**Wichtigste Packages:**
- `pandas` - Datenverarbeitung
- `numpy` - Berechnungen
- `matplotlib`, `seaborn` - Visualisierungen
- `oandapyV20` - Oanda API
- `pytz` - Timezone Handling

### Data Format (Parquet)

**MultiIndex:** `(pair, time)`

**Columns:**
```python
['open', 'high', 'low', 'close', 'volume']
```

**Timestamps:** UTC (ohne TZ-Info)

---

## 🔧 Wichtige Hinweise

### Datenstruktur
- **Zentrale Datenquelle:** `/Users/carvin/Documents/Trading Backtests/Data/Chartdata/Forex/`
- **Parquet-Files:** Kombinierte Multi-Pair-Dateien pro Timeframe
- **CSV-Files:** Einzelne Pair-Dateien pro Timeframe
- **Alle Timestamps:** UTC (ohne TZ-Info im Parquet)

### Config-System
- `config.py` - Basis-Config (API, Pairs, Pfade) → **NICHT** ändern
- `backtest_config.py` - Backtest-Regeln → **HIER** Einstellungen anpassen

### Bei Problemen
1. Prüfe Config-Files (`config.py`, `backtest_config.py`)
2. Checke Daten-Verfügbarkeit: `Data/Chartdata/Forex/Parquet/`
3. Lies Error-Messages (meist Pfad- oder Daten-Probleme)
4. Siehe `SETUP.md` für Installation & Environment-Setup

---

## 📋 Nächste Schritte (TODOs)

### Kurzfristig
- [ ] Backtest mit optimierter TP/SL Kombination (3.0x/-Extreme) erneut durchführen
- [ ] Worst Performing Pairs analysieren (CHFJPY, GBPCHF, EURGBP) - eventuell ausschließen
- [ ] Entry-Varianten testen: 1H Close vs Direct Touch
- [ ] Position Sizing implementieren (aktuell: fixed lot size)

### Mittelfristig
- [ ] COT-Daten Integration vorbereiten (fundamentaler Filter)
- [ ] Seasonality-Analyse implementieren
- [ ] Multiple Timeframe Priority testen ('largest_gap' vs 'highest' Strategy)
- [ ] Pair Correlation Analysis durchführen

### Langfristig
- [ ] Valuation & Bonds Indikatoren entwickeln
- [ ] Komplette Fundamental-Integration
- [ ] Forward-Testing Setup
- [ ] Live-Trading Vorbereitung (Risk Management, Position Limits)

---
