# Model 3 Backtest - Vollständige Übersicht

## 📁 Projekt-Struktur

```
05_Model 3/
├── scripts/
│   └── backtesting/
│       ├── backtest_model3.py       ✅ HAUPT-SCRIPT (Model 3)
│       ├── backtest_modelx.py       ⚠️  Alt (Model X, nicht verwenden!)
│       ├── modelx_pivot.py          ⚠️  Alt (Model X spezifisch)
│       ├── run_all_backtests.py     (Batch Runner)
│       ├── backtest_ui.py           (Interactive UI)
│       ├── view_results.py          (Results Viewer)
│       ├── visualizations.py        (Charts)
│       ├── monte_carlo.py           (MC Simulation)
│       └── create_summary.py        (Summary Reports)
│
├── Backtest/                        📊 BACKTEST-ERGEBNISSE
│   ├── 01_test/                     ← Validation & Test-Runs
│   │   └── kurze übersicht.txt
│   ├── 02_technical/                ← Technische Backtests (ohne Fundamentals)
│   └── 03_fundamentals/             ← Mit Fundamental-Filtern (später)
│
├── config.py                        ⚙️  Basis-Config
├── backtest_config.py               ⚠️  Model X Config (nicht verwendet!)
├── PROJECT_README.md                📖 Hauptdokumentation
├── SETUP.md                         🚀 Setup-Anleitung
├── claude.md                        🤖 Claude Kontext
└── BACKTEST_OVERVIEW.md            📋 DIESE DATEI
```

---

## 🎯 Was testet `backtest_model3.py`?

### Strategie-Logik

Das Script testet **Model 3**, eine komplexe Multi-Timeframe Pivot-Strategie:

#### 1. Pivot-Erkennung (HTF: 3D, W, M)
- **2-Kerzen-Pattern**: Bullish (rot→grün) / Bearish (grün→rot)
- **Pivot-Struktur**:
  - Pivot = Open der 2. Kerze
  - Pivot Extreme = Ende der längeren Wick
  - Pivot Near = Ende der kürzeren Wick
  - Pivot Gap = Box von Pivot bis Extreme
  - Wick Difference = Box von Near bis Extreme

#### 2. Verfeinerungen (LTF: 1H, 4H, D, 3D, W)
- **Suche** innerhalb der Wick Difference des HTF-Pivots
- **Hierarchie**: M → W → 3D → D → H4 → H1 (höchster TF zuerst)
- **Gültigkeitsbedingungen**:
  - Max. 20% der Pivot Gap Größe
  - Innerhalb Wick Difference
  - Vor HTF-Pivot-Entstehung NICHT berührt
  - Doji-Filter (5% Body Minimum)

#### 3. Entry-Mechanismus
- **Gap-Trigger**: Pivot Gap muss ZUERST berührt werden
- **Verfeinerungs-Entry**: An höchster gültiger Verfeinerung
- **Bestätigung** (parametrisierbar):
  - `1h_close` (Standard): 1H Close über/unter Level → Entry bei Open nächster Candle
  - `direct_touch`: Sofortiger Entry bei Berührung
  - `4h_close`: 4H Close Bestätigung

#### 4. Exit-Regeln
- **SL**: Min. 60 Pips + min. über/unter Fib 1.1 (0.1× Gap jenseits Extreme)
- **TP**: Fib -1 (1× Gap jenseits Pivot)
- **RR**: 1.0 - 1.5 (SL wird angepasst wenn RR > 1.5)

---

## ⚙️ Aktuelle Standard-Einstellungen

### HTF-Pivots
```python
htf_timeframes = ["3D", "W", "M"]  # Alle drei per Default
```

### Verfeinerungen
```python
refinement_timeframes = ["1H", "4H", "D", "3D", "W"]  # Automatisch basierend auf HTF
max_refinement_size = 20%  # der Pivot Gap
```

### Filter
```python
doji_filter = 5.0  # Body muss >= 5% der Candle Range sein
versatz_filter = None  # Noch nicht implementiert
```

### Entry
```python
entry_confirmation = "1h_close"  # Standard: 1H Close Bestätigung
# Alternativen: "direct_touch", "4h_close"
```

### Exit
```python
min_sl_distance = 60  # Pips
fib_sl_level = 1.1  # Fib 1.1 (0.1× Gap jenseits Extreme)
fib_tp_level = -1  # Fib -1 (1× Gap jenseits Pivot)
min_rr = 1.0
max_rr = 1.5
```

### Backtest-Modus
```python
portfolio_backtest = True  # Trades chronologisch, Datum-abhängig
pairs = 28  # Alle Major Forex Pairs
start_date = "2010-01-01"  # Default
```

---

## 🧪 Test-Plan (01_test)

Laut `01_test/kurze übersicht.txt`:

### Phase 1: Validation (Sample-Tests)
**Ziel**: Logik-Validierung, Setup-Überprüfung

**6 Test-Setups** (2 Zeiträume × 3 HTF-TFs):
1. **2010-2015** auf W
2. **2010-2015** auf M
3. **2010-2015** auf 3D
4. **2020-2025** auf W
5. **2020-2025** auf M
6. **2020-2025** auf 3D

**Pro Setup**:
- Export von 5-10 Trades mit Details
- Manuell validieren: Sind Pivot/Verfeinerung/Entry/Exit korrekt?

### Phase 2: Vollständiger Backtest
**Ziel**: Performance-Metriken

**Setup**:
- **Alle 28 Pairs**
- **Kompletter Zeitraum** (2010-2025)
- **Nur Weekly** (als Standard)
- **Portfolio-Modus** (chronologisch)

**Stats**:
- Total Trades
- Win Rate
- Total R, Expectancy
- Max DD
- Profit Factor
- Sharpe, Sortino
- Monatliche/Jährliche Returns

---

## 📊 Wichtige Metriken für Validation

### 1. Setup-Validierung
- **Pivot korrekt erkannt?** (2-Kerzen-Pattern, Doji-Filter)
- **Verfeinerung korrekt?** (innerhalb Wick Diff, max 20%, unberührt)
- **Entry korrekt?** (Gap zuerst, dann Verfeinerung, Close-Bestätigung)
- **SL/TP korrekt?** (Min. 60 Pips, Fib 1.1, Fib -1, RR 1-1.5)

### 2. Performance-Metriken
**Basis**:
- Total Trades
- Win Rate (%)
- Winning/Losing Trades

**R-Multiple**:
- Total R
- Expectancy (R)
- Avg Win/Loss (R)
- Max DD (R)

**Account %**:
- Total Return (%)
- Return/Month, Return/Year
- Max DD (%)

**Risk**:
- Profit Factor
- Sharpe Ratio
- Sortino Ratio
- Calmar Ratio

**Konsistenz**:
- Max Consecutive Wins/Losses
- R-Squared (Equity Curve Glattheit)
- Trades/Month (Avg/Max/Min)

**Portfolio**:
- Max gleichzeitige Positionen
- Median/Avg gleichzeitig offen

---

## 🔧 CLI-Befehle

### Standard-Backtest (Weekly, 1H Close)
```bash
python scripts/backtesting/backtest_model3.py \
    --pairs EURUSD \
    --start-date 2020-01-01
```

### Validation-Test (Sample)
```bash
# 2010-2015, Weekly, nur 1 Pair für Validierung
python scripts/backtesting/backtest_model3.py \
    --pairs EURUSD \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --start-date 2010-01-01 \
    --end-date 2015-12-31 \
    --output Backtest/01_test/validation_2010-2015_W_EURUSD.csv
```

### Vollständiger Backtest (Alle Pairs, Weekly)
```bash
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --start-date 2010-01-01 \
    --output Backtest/01_test/full_backtest_W_1h_close.csv
```

### Entry-Varianten vergleichen
```bash
# Direct Touch
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation direct_touch \
    --start-date 2010-01-01 \
    --output Backtest/02_technical/direct_touch.csv

# 1H Close (Standard)
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --start-date 2010-01-01 \
    --output Backtest/02_technical/1h_close.csv
```

### Alle HTF-Timeframes (3D, W, M)
```bash
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes 3D W M \
    --entry-confirmation 1h_close \
    --start-date 2010-01-01 \
    --output Backtest/02_technical/all_htf.csv
```

---

## 🚨 Was NOCH NICHT implementiert ist

### 1. Versatz-Regel
- Erkennung: Close K1 ≠ Open K2
- Größere vs. kleinere Box-Variante
- Versatz-Filter (2x Standard)

### 2. Pivot-Overlap-Regel
- Wenn 2-3 Pivots gleiches Extreme haben
- Nur größere Pivot Gap nutzen

### 3. Fundamentale Filter
- COT-Daten Integration
- Seasonality
- Valuation & Bonds

### 4. Position Management
- Max gleichzeitige Positionen
- Max pro Pair
- Trade-Priorität

### 5. Erweiterte SL/TP
- Trailing Stop
- Breakeven
- Partial TP

---

## 📝 Output-Dateien

### Trade-CSV (Standard)
Spalten:
```
pair, direction, pivot_time, entry_time, entry_price,
tp_price, sl_price, exit_time, exit_price, exit_reason,
pnl_pips, pnl_r
```

### Wichtige Felder
- **pivot_time**: Wann HTF-Pivot entstanden ist
- **entry_time**: Wann Entry erfolgt ist
- **exit_reason**: "tp", "sl", "manual"
- **pnl_pips**: PnL in Pips
- **pnl_r**: PnL in R (Risk-Einheiten)

---

## 🎯 Nächste Schritte

### Sofort (01_test):
1. ✅ Standard-Einstellungen festlegen (siehe oben)
2. ⏳ Validation-Tests durchführen (6 Sample-Tests)
3. ⏳ Manuell validieren: Setup-Logik korrekt?
4. ⏳ Vollständiger Backtest (Weekly, alle Pairs)

### Bald (02_technical):
5. Entry-Varianten vergleichen (1H Close vs Direct Touch)
6. HTF-Varianten testen (nur W vs. 3D+W+M)
7. Parameter-Optimierung (Doji-Filter, Verfeinerungsgröße)

### Später (03_fundamentals):
8. COT-Daten Download & Integration
9. Fundamentale Filter implementieren
10. Vollständiger Backtest mit Fundamentals

---

## ⚙️ Standard-Konfiguration für 01_test

Für **konsistente Tests** verwenden wir:

```python
# HTF-Pivots
htf_timeframes = ["W"]  # NUR Weekly für 01_test

# Entry
entry_confirmation = "1h_close"  # Standard-Modus

# Zeitraum
start_date = "2010-01-01"
end_date = None  # Bis zum Ende der Daten

# Pairs
pairs = alle 28  # Für Volltest, einzeln für Validation

# Output
output_dir = "Backtest/01_test/"
```

---

*Last Updated: 28.12.2025*
