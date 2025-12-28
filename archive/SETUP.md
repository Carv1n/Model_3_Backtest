# 🚀 Model 3 - Setup & Installation

## Schnellstart nach Cloud-Download

### 1. Zum Projekt navigieren
```bash
cd "/Users/carvin/Documents/Trading Backtests/05_Model 3"
```

### 2. Python Environment erstellen
```bash
# Virtual Environment erstellen
python3 -m venv .venv

# Aktivieren
source .venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

### 3. Daten-Struktur überprüfen
```bash
# Zentrale Datenquelle muss existieren
ls -la "/Users/carvin/Documents/Trading Backtests/Data/Chartdata/Forex/Parquet/"

# Erwartete Files:
# - All_Pairs_H1_UTC.parquet
# - All_Pairs_H4_UTC.parquet
# - All_Pairs_D_UTC.parquet
# - All_Pairs_3D_UTC.parquet
# - All_Pairs_W_UTC.parquet
# - All_Pairs_M_UTC.parquet
```

### 4. Config prüfen
```bash
# Öffne config.py und prüfe:
cat config.py | grep DATA_PATH

# Sollte zeigen:
# DATA_PATH = BACKTEST_ROOT / "Data" / "Chartdata" / "Forex"
```

### 5. Test-Run durchführen
```bash
# Einzelner Pair-Test (schnell)
python scripts/backtesting/backtest_model3.py \
    --pairs EURUSD \
    --start-date 2020-01-01

# Mit Entry-Varianten testen
python scripts/backtesting/backtest_model3.py \
    --pairs EURUSD \
    --entry-confirmation 1h_close \
    --start-date 2020-01-01

# Alle 28 Pairs
python scripts/backtesting/backtest_model3.py \
    --start-date 2015-01-01 \
    --output results/trades/model3_all.csv
```

---

## 📦 Daten neu downloaden (optional)

Falls du komplett frische Daten von Oanda laden willst:

```bash
# WARNUNG: Überschreibt existierende Daten!
python3 scripts/data_processing/0_complete_fresh_download.py
```

Dies führt aus:
1. Download H1, H4, D, W, M von Oanda API
2. Erstellt 3D aus Daily
3. Organisiert in zentrale Chartdata/Forex/ Struktur
4. Erstellt kombinierte Parquet-Files

**Wichtig:** Benötigt Oanda API Key in `config.py`

---

## 🔧 Backtest-Befehle

### Einzelner Backtest
```bash
python scripts/backtesting/backtest_model3.py \
    --pairs EURUSD GBPUSD \
    --start-date 2015-01-01
```

### Mit verschiedenen Entry-Modi
```bash
# 1H Close Bestätigung (Standard)
python scripts/backtesting/backtest_model3.py --entry-confirmation 1h_close

# Direkter Touch (ohne Close)
python scripts/backtesting/backtest_model3.py --entry-confirmation direct_touch

# 4H Close Bestätigung
python scripts/backtesting/backtest_model3.py --entry-confirmation 4h_close
```

### Nur bestimmte HTF-Timeframes
```bash
# Nur Weekly Pivots
python scripts/backtesting/backtest_model3.py --htf-timeframes W

# 3D und W
python scripts/backtesting/backtest_model3.py --htf-timeframes 3D W
```

### Ergebnisse anzeigen
```bash
# Vollständiger Report
python3 scripts/backtesting/view_results.py \
    -i results/trades/all_trades_chronological.csv

# Charts generieren
python3 scripts/backtesting/visualizations.py \
    -i results/trades/all_trades_chronological.csv

# Monte Carlo Simulation
python3 scripts/backtesting/monte_carlo.py \
    -i results/trades/all_trades_chronological.csv \
    -n 1000 -p 100
```

---

## 📊 Pivot Quality Test

Testet verschiedene TP/SL Kombinationen:

```bash
cd pivot_analysis
python3 pivot_quality_test.py

# Ergebnisse in:
# pivot_analysis/results/PIVOT_QUALITY_REPORT_*.txt
```

---

## 🗂️ Projekt-Struktur

```
05_Model 3/
├── config.py                    # Basis-Config (API, Pairs, Pfade)
├── backtest_config.py           # Backtest-Regeln (für Model X, Model 3 nutzt eigene Parameter)
├── requirements.txt             # Python Dependencies
├── PROJECT_README.md            # Hauptdokumentation
├── SETUP.md                     # Diese Datei
├── claude.md                    # Claude AI Kontext-Datei
├── MODEL 3 KOMMPLETT            # Vollständige Strategie-Dokumentation
├── Model 3 Regeln übersicht     # Kurzübersicht Regeln
│
├── scripts/
│   ├── data_processing/         # Daten-Download & Processing
│   │   └── 0_complete_fresh_download.py
│   │
│   └── backtesting/             # Backtest-System
│       ├── backtest_model3.py       (Main Engine - Model 3) ✅
│       ├── run_all_backtests.py     (Batch Runner)
│       ├── backtest_ui.py           (Interactive UI)
│       ├── view_results.py          (Results Viewer)
│       ├── visualizations.py        (Charts)
│       ├── monte_carlo.py           (MC Simulation)
│       └── create_summary.py        (Summary Reports)
│
├── pivot_analysis/              # Pivot Quality Tests
│   ├── pivot_quality_test.py
│   └── results/
│
└── results/                     # Backtest Outputs
    ├── trades/                  (Trade CSVs)
    ├── charts/                  (Visualisierungen)
    └── reports/                 (Summary Reports)
```

---

## 🐛 Troubleshooting

### Problem: "FileNotFoundError: Parquet file not found"
```bash
# Prüfe ob zentrale Daten existieren
ls -la "/Users/carvin/Documents/Trading Backtests/Data/Chartdata/Forex/Parquet/"

# Falls nicht → Download durchführen
python3 scripts/data_processing/0_complete_fresh_download.py
```

### Problem: "ModuleNotFoundError"
```bash
# Virtual Environment aktivieren
source .venv/bin/activate

# Dependencies neu installieren
pip install -r requirements.txt
```

### Problem: "KeyError: 'pair'"
```bash
# Parquet-Files müssen MultiIndex haben
# Neu generieren mit data_processing script
python3 scripts/data_processing/0_complete_fresh_download.py
```

### Problem: Import-Fehler
```bash
# Prüfe ob du im richtigen Ordner bist
pwd
# Sollte sein: /Users/carvin/Documents/Trading Backtests/03_Model X

# Virtual Environment aktiviert?
which python3
# Sollte zeigen: .../03_Model X/.venv/bin/python3
```

---

## 📝 Wichtige Dateien

### config.py
- API Credentials (Oanda)
- 28 Forex Pairs
- Timeframes (H1, H4, D, 3D, W, M)
- **Pfade werden automatisch gesetzt** - NICHT manuell ändern!

### backtest_config.py
- Pivot Timeframes (3D, W, M)
- Entry/Exit Typen
- Gap-Größen-Filter
- Multiple-Timeframe-Strategie
- Position-Limits
- **HIER** Backtest-Regeln anpassen!

### requirements.txt
- pandas, numpy (Daten)
- matplotlib, seaborn (Visualisierung)
- oandapyV20 (Oanda API)
- pytz (Timezone Handling)

---

## ⚠️ Wichtige Hinweise

1. **Daten-Pfad:** Zentrale Quelle in `Data/Chartdata/Forex/` - **NICHT** im Projekt-Ordner!
2. **Timestamps:** Alle UTC (ohne TZ-Info im Parquet)
3. **Virtual Environment:** Immer aktivieren vor Ausführung!
4. **Model 3 spezifisch:**
   - Verwendet `backtest_model3.py` (nicht modelx!)
   - Entry-Bestätigung: 1h_close (Standard), direct_touch, 4h_close
   - HTF-Timeframes: 3D, W, M (alle drei per default)
   - Doji-Filter: 5%
   - Verfeinerungen: max 20% der Pivot Gap

---

*Last Updated: 28.12.2025*
