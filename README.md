# Model 3 - Multi-Timeframe Pivot Trading System

## 📁 Projekt-Struktur

```
05_Model 3/
├── README.md                    ← DIESE DATEI
├── STRATEGIE.md                 ← Strategie & Settings
├── claude.md                    ← Claude Kontext
├── MODEL3_CONFIG.md             ← Detaillierte Konfiguration
│
├── scripts/backtesting/
│   └── backtest_model3.py       ← Haupt-Backtest-Script
│
├── Backtest/
│   ├── 01_test/                 ← Validation
│   │   ├── validation_sampler.py  ← Sample-Script
│   │   └── README.md
│   ├── 02_technical/            ← Technical Tests
│   └── 03_fundamentals/         ← Fundamental Tests (später)
│
└── archive/                     ← Alte/unnötige Dateien
```

---

## 🎯 Strategie (Kurzfassung)

**2-stufiges Pivot-System:**

1. HTF-Pivot finden (3D, W, M) - 2-Kerzen-Muster
2. Verfeinerung suchen (1H-W) - innerhalb Wick Difference, max 20%
3. Entry bei Touch der Verfeinerung (direct_touch)
4. SL: Min. 60 Pips von Entry + Fib 1.1
5. TP: Fib -1, RR: 1.0-1.5

**Details:** Siehe `STRATEGIE.md`

---

## ⚙️ Standard-Einstellungen

```python
HTF_TIMEFRAMES = ["3D", "W", "M"]
ENTRY_CONFIRMATION = "direct_touch"
DOJI_FILTER = 5.0
REFINEMENT_MAX_SIZE = 20.0
MIN_SL_DISTANCE = 60
MIN_RR = 1.0
MAX_RR = 1.5
```

---

## 🚀 Quick Start

### 1. Validation (JETZT)

```bash
cd "05_Model 3"
python Backtest/01_test/validation_sampler.py
```

**Output**: `validation_samples.csv` mit 6 Sample-Trades (2 Pairs × 3 HTF-TFs)

**Manuell validieren**:
- Pivot korrekt?
- Verfeinerung korrekt?
- Entry/SL/TP korrekt?

### 2. Baseline-Backtest (nach Validation)

```bash
# Nur Weekly, alle Pairs
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --output Backtest/02_technical/baseline_W.csv
```

---

## 📊 Test-Phasen

1. **01_test** - Validation (Logik prüfen)
2. **02_technical** - Baseline & Entry-Varianten
3. **03_fundamentals** - COT, Seasonality (später)

---

## 🔧 Wichtige Befehle

```bash
# Standard (alle HTF, direct_touch)
python scripts/backtesting/backtest_model3.py

# Nur Weekly
python scripts/backtesting/backtest_model3.py --htf-timeframes W

# Mit 1H Close Bestätigung
python scripts/backtesting/backtest_model3.py --entry-confirmation 1h_close

# Einzelnes Pair
python scripts/backtesting/backtest_model3.py --pairs EURUSD

# Zeitraum einschränken
python scripts/backtesting/backtest_model3.py --start-date 2020-01-01 --end-date 2023-12-31
```

---

## 📝 Wichtige Dateien

- **STRATEGIE.md** - Strategie-Logik & Settings
- **MODEL3_CONFIG.md** - Detaillierte Konfiguration
- **backtest_model3.py** - Haupt-Script
- **validation_sampler.py** - Sample-Generator für Validation

---

## ⚠️ Wichtige Regeln

### Pivot-Struktur
- **Pivot** = IMMER Open K2
- **Extreme** = IMMER Ende längere Wick
- **Near** = Ende kürzere Wick

### SL-Berechnung
- Min. 60 Pips von **ENTRY** (nicht Extreme!)
- UND unter/über Fib 1.1

---

*Last Updated: 28.12.2025*
