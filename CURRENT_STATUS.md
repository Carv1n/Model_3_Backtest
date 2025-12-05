# 📋 Script Status & Organisation

## ✅ AKTIVE SCRIPTS

### **Data Processing** (`scripts/data_processing/`)
| Script | Status | Zweck | Wann benutzen |
|--------|--------|-------|---------------|
| `0_complete_fresh_download.py` | ✓ Ready | Komplett-Download von Oanda | Nur für Neudownload |

### **Backtesting** (`scripts/backtesting/`)
| Script | Status | Zweck | Verwendung |
|--------|--------|-------|------------|
| `backtest_modelx.py` | ✓ UTC Pfade | Model X Backtest Engine | Haupt-Backtest |
| `modelx_pivot.py` | ✓ UTC Pfade | Pivot-Erkennung & Logik | Pivot-Analyse |
| `run_all_backtests.py` | ✓ UTC Pfade | Alle Pairs backtesten | Vollständiger Test |
| `create_summary.py` | ✓ Ready | Ergebnisse zusammenfassen | Nach Backtests |

### **Validation** (`validation/`)
| Script | Status | Zweck |
|--------|--------|-------|
| `export_pivot_gaps.py` | ✓ UTC Pfade | Pivot-Validierung |

---

## 🗄️ ARCHIVIERTE SCRIPTS (nicht verwenden)

### **Data Processing Archive** (`scripts/archive/`)
❌ `1_download_data.py` - Ersetzt durch 0_complete_fresh_download.py  
❌ `2_convert_csv_to_parquet.py` - Integriert in 0_complete_fresh_download.py  
❌ `organize_data_step1_raw_to_utc.py` - Obsolet  
❌ `organize_data_step2_utc_to_utc1.py` - UTC+1 nicht mehr verwendet  
❌ `organize_data_step3_csv_to_parquet.py` - Integriert  
❌ `fix_*.py` (alle) - Fehlerhaft, nicht verwenden  
❌ `rebuild_*.py` (alle) - Obsolet  
❌ `convert_timezone_to_berlin.py` - UTC+1 nicht verwendet  
❌ `create_tradingview_timestamps.py` - UTC_TradingView nicht verwendet  
❌ `check_timezones.py` - Nur für Debugging  
❌ `export_weekly_pivot_gaps.py` - Veraltet  

### **Validation Archive** (`validation/archive/`)
❌ `check_pivot.py` - Debugging  
❌ `check_rr.py` - Debugging  
❌ `debug_*.py` (alle) - Debugging  
❌ `export_pivot_checks.py` - Obsolet  
❌ `gaps_*.csv` (alle) - Alte Ergebnisse  

---

## 📊 DATENSTRUKTUR

### ✅ Aktiv (verwenden)
```
data/UTC/
├── H1/AUDCAD_H1_UTC.csv ... (28 pairs)
├── H4/AUDCAD_H4_UTC.csv ... (28 pairs)
├── D/AUDCAD_D_UTC.csv ... (28 pairs)
├── 3D/AUDCAD_3D_UTC.csv ... (28 pairs)
├── W/AUDCAD_W_UTC.csv ... (28 pairs)
├── M/AUDCAD_M_UTC.csv ... (28 pairs)
├── All_Pairs_H1_UTC.parquet
├── All_Pairs_H4_UTC.parquet
├── All_Pairs_D_UTC.parquet
├── All_Pairs_3D_UTC.parquet
├── All_Pairs_W_UTC.parquet
└── All_Pairs_M_UTC.parquet
```

### ❌ Nicht verwendet (kann gelöscht werden)
```
data/UTC_TradingView/  → Nicht verwendet
data/*_raw/            → Temporär (nach Parquet-Erstellung)
```

---

## 🔄 WORKFLOW

### Laptop (aktuell)
1. ✓ Daten bereits in UTC/ vorhanden
2. Backtests ausführen: `python3 scripts/backtesting/backtest_modelx.py`
3. Git Push für Code-Änderungen

### PC (nach Sync)
1. Git Pull für Code-Updates
2. Cloud Download: UTC/ Ordner laden
3. Backtests ausführen: `python3 scripts/backtesting/run_all_backtests.py`

---

## 🎯 WICHTIGSTE PFAD-ÄNDERUNGEN

Alle Scripts verwenden jetzt:
- **ALT**: `data/{timeframe}_all_pairs.parquet`
- **NEU**: `data/UTC/All_Pairs_{timeframe}_UTC.parquet`

Geänderte Dateien:
✓ `scripts/backtesting/modelx_pivot.py`
✓ `validation/export_pivot_gaps.py`
✓ `scripts/backtesting/backtest_modelx.py` (via export_pivot_gaps)

---

## 📝 NÄCHSTE SCHRITTE

1. **Auf PC**:
   - Git Pull
   - UTC/ Ordner aus Cloud laden
   - Backtests ausführen

2. **Entwicklung**:
   - Chronologisches Backtest-System implementieren
   - Strategy Variation Framework erstellen
   - Entry/Exit/TP/SL Variationen testen
