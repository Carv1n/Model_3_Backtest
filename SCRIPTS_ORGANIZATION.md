# Script Organization & Usage Guide

## 📁 Aktive Scripts (Für PC Setup)

### **scripts/data_processing/**
Benutze diese Scripts auf deinem PC nach dem Cloud-Download:

1. **0_complete_fresh_download.py** ✓ WICHTIG
   - Lädt alle Daten von Oanda API
   - Erstellt 3D aus Daily
   - Organisiert in UTC/ Ordner
   - Erstellt Parquet files
   - **Verwendung**: `python3 scripts/data_processing/0_complete_fresh_download.py`

---

### **scripts/backtesting/**
Scripts für Backtesting und Analyse:

1. **backtest_modelx.py** ✓ WICHTIG
   - Hauptbacktest für Model X
   - Verwendet UTC/ Daten
   - **Status**: Pfade angepasst auf UTC/

2. **modelx_pivot.py** ✓ WICHTIG
   - Model X mit Pivot-Logik
   - Verwendet UTC/ Daten
   - **Status**: Pfade angepasst auf UTC/

3. **run_all_backtests.py** ✓ WICHTIG
   - Führt alle Backtests aus
   - **Status**: Pfade angepasst auf UTC/

4. **create_summary.py** ✓
   - Erstellt Zusammenfassungen der Ergebnisse

---

## 🗄️ Archivierte Scripts

### **scripts/archive/**
Alte/überholte Scripts - NICHT mehr verwenden:

- `1_download_data.py` - Ersetzt durch 0_complete_fresh_download.py
- `2_convert_csv_to_parquet.py` - Jetzt in 0_complete_fresh_download.py integriert
- `organize_data_step1_raw_to_utc.py` - Ersetzt
- `organize_data_step2_utc_to_utc1.py` - UTC+1 nicht mehr benötigt
- `organize_data_step3_csv_to_parquet.py` - Integriert
- `fix_daily_only.py` - Obsolet (war fehlerhaft)
- `fix_daily_weekly_monthly_timestamps.py` - Obsolet (verursachte Fehler)
- `fix_weekly_monthly_by_trading_day.py` - Obsolet
- `rebuild_weekly_monthly_from_daily.py` - Obsolet
- `rebuild_weekly_monthly_from_daily_both_timezones.py` - Obsolet
- `convert_timezone_to_berlin.py` - UTC+1 nicht mehr benötigt
- `create_tradingview_timestamps.py` - UTC_TradingView nicht verwendet

### **scripts/archive/utility/**
Utility Scripts - bei Bedarf:

- `check_timezones.py` - Timezone-Validierung
- `export_weekly_pivot_gaps.py` - Pivot Gap Export

---

### **validation/archive/**
Debug/Validierungs Scripts - nur für Problemanalyse:

- `check_pivot.py`
- `check_rr.py`
- `debug_*.py` (alle)
- `export_pivot_*.py`
- `gaps_*.csv` (alte Ergebnisse)

---

## 🚀 Workflow für PC Setup

Nach Cloud-Download der UTC Daten:

```bash
# 1. Daten bereits in data/UTC/ vorhanden (aus Cloud)

# 2. Backtest ausführen
python3 scripts/backtesting/backtest_modelx.py

# 3. Alle Backtests ausführen
python3 scripts/backtesting/run_all_backtests.py

# 4. Zusammenfassung erstellen
python3 scripts/backtesting/create_summary.py
```

---

## 📊 Datenstruktur

```
data/
├── UTC/                    ← VERWENDE DIESE
│   ├── H1/ (28 CSVs)
│   ├── H4/ (28 CSVs)
│   ├── D/ (28 CSVs)
│   ├── 3D/ (28 CSVs)
│   ├── W/ (28 CSVs)
│   ├── M/ (28 CSVs)
│   └── *.parquet (6 files)
│
└── UTC_TradingView/        ← NICHT VERWENDET
    └── (kann gelöscht werden)
```

---

## ⚙️ Config Einstellungen

**config.py** ist bereits angepasst:
- Alle Backtest-Scripts verwenden `data/UTC/` Pfade
- OANDA_ACCOUNT_TYPE = "live" (für Daten-Download)
