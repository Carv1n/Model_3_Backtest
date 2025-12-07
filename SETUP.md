# 🚀 Model X - Setup & Installation

## Schnellstart nach Cloud-Download

### 1. Repository klonen
```bash
cd "/Users/carvin/Documents/Trading Backtests"
git clone https://github.com/Carv1n/Model_X_Backtest.git "03_Model X"
cd "03_Model X"
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
python3 scripts/backtesting/backtest_modelx.py \
    --pairs EURUSD \
    --timeframes W \
    --start-date 2020-01-01

# Wenn erfolgreich → Alle Pairs
python3 scripts/backtesting/run_all_backtests.py
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
python3 scripts/backtesting/backtest_modelx.py \
    --pairs EURUSD GBPUSD \
    --timeframes 3D W M \
    --start-date 2015-01-01
```

### Alle 28 Pairs
```bash
python3 scripts/backtesting/run_all_backtests.py
```

### Interactive UI
```bash
python3 scripts/backtesting/backtest_ui.py
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
03_Model X/
├── config.py                    # Basis-Config (API, Pairs, Pfade)
├── backtest_config.py           # Backtest-Regeln (HIER anpassen!)
├── requirements.txt             # Python Dependencies
├── PROJECT_README.md            # Hauptdokumentation
├── SETUP.md                     # Diese Datei
│
├── scripts/
│   ├── data_processing/         # Daten-Download & Processing
│   │   └── 0_complete_fresh_download.py
│   │
│   └── backtesting/             # Backtest-System
│       ├── backtest_modelx.py       (Main Engine)
│       ├── modelx_pivot.py          (Pivot Logic)
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
4. **Git:** Nicht pushen ohne Tests!

---

*Last Updated: 07.12.2025*
