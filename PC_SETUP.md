# 🚀 PC Setup nach Cloud-Download

## Schritt 1: Daten aus Cloud laden
```bash
# Lade UTC Ordner aus Cloud
# data/UTC/ mit allen Parquet und CSV Dateien
```

## Schritt 2: Backtest ausführen

### Einzelner Backtest
```bash
cd "/Users/carvin/Documents/Trading Backtests/03_Model X"
python3 scripts/backtesting/backtest_modelx.py
```

### Alle Pairs & Timeframes
```bash
python3 scripts/backtesting/run_all_backtests.py
```

### Mit Pivot-Logik
```bash
python3 scripts/backtesting/modelx_pivot.py
```

## Schritt 3: Ergebnisse ansehen
```bash
# Ergebnisse in results/ Ordner
ls -la results/
```

---

## Datenstruktur

```
data/
└── UTC/                              ← AKTIV
    ├── H1/                          
    │   ├── AUDCAD_H1_UTC.csv        
    │   └── ... (28 Paare)           
    ├── H4/                          
    ├── D/                           
    ├── 3D/                          
    ├── W/                           
    ├── M/                           
    ├── All_Pairs_H1_UTC.parquet     
    ├── All_Pairs_H4_UTC.parquet     
    ├── All_Pairs_D_UTC.parquet      
    ├── All_Pairs_3D_UTC.parquet     
    ├── All_Pairs_W_UTC.parquet      
    └── All_Pairs_M_UTC.parquet      
```

---

## Alle Scripts verwenden UTC Daten

✓ `backtest_modelx.py` - Pfade aktualisiert
✓ `modelx_pivot.py` - Pfade aktualisiert  
✓ `run_all_backtests.py` - Pfade aktualisiert
✓ `validation/export_pivot_gaps.py` - Pfade aktualisiert

---

## Optional: Neue Daten downloaden

Falls du komplett neue Daten von Oanda laden willst:

```bash
python3 scripts/data_processing/0_complete_fresh_download.py
```

Dies lädt:
- H1, H4, D, W, M von Oanda
- Erstellt 3D aus Daily
- Organisiert in UTC/ Ordner
- Erstellt Parquet files
