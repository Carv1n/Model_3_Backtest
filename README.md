# Model 3 - Multi-Timeframe Pivot Trading System

## 📁 Projekt-Struktur

```
05_Model 3/
├── README.md                    ← DIESE DATEI (Projekt-Übersicht)
├── STRATEGIE_REGELN.md          ← KOMPLETTE TECHNISCHE REGELN
├── STRATEGIE.md                 ← Strategie-Überblick & Settings
├── MODEL3_CONFIG.md             ← Detaillierte Konfiguration
├── claude.md                    ← Claude Kontext
│
├── scripts/backtesting/
│   └── backtest_model3.py       ← Haupt-Backtest-Script
│
├── Backtest/
│   ├── 01_test/01_Validation/   ← Validation
│   │   ├── validation_trades.py ← Trade-Validierung (6 Pivots)
│   │   └── README.md
│   ├── 02_technical/            ← Technical Tests
│   └── 03_fundamentals/         ← Fundamental Tests (später)
│
└── archive/                     ← Archivierte Dateien
    └── MODEL 3 KOMMPLETT        ← Vollständige Strategie-Doku
```

---

## 🎯 Strategie (Kurzfassung)

**2-stufiges Pivot-System:**

1. HTF-Pivot finden (3D, W, M) - 2-Kerzen-Muster
2. Verfeinerung suchen (H1, H4, D, 3D, W) - max TF = Weekly!
   - Position: Zwischen HTF Extreme und Near
   - Größe: Wick Diff ≤ 20% HTF Gap
   - 7 Gültigkeitsbedingungen
3. Entry-Voraussetzungen:
   - Gap Touch auf Daily (auch bei W/M Pivots!)
   - TP-Check: TP nicht berührt zwischen Gap Touch und Entry
   - RR-Check: >= 1 RR erforderlich
4. Entry: direct_touch (Standard), alternativ 1h_close/4h_close
5. SL: Min. 60 Pips von Entry + jenseits Fib 1.1
6. TP: -1 Fib, RR: 1.0-1.5

**Alle technischen Regeln:** Siehe `STRATEGIE_REGELN.md`
**Übersicht & Settings:** Siehe `STRATEGIE.md`

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

### 1. Validation (JETZT) ✅

```bash
cd "05_Model 3"
python Backtest/01_test/01_Validation/validation_trades.py
```

**Output**: `results/trade_validation_*.txt` mit 6 Sample-Trades
- 6 verschiedene Pivots (M, W, 3D)
- 6 verschiedene Pairs
- Komplette Trade-Simulation mit **korrigierter Logik**:
  - ✅ TP-Check mit Entry Time (nur bis Entry!)
  - ✅ RR Berechnung korrigiert (RR = 1.5 nach SL-Anpassung)

**Manuell validieren**:
- Pivot korrekt? (K1, K2, Extreme, Near)
- Verfeinerungen korrekt? (7 Bedingungen)
- Gap Touch auf Daily?
- TP-Check korrekt?
- Entry/SL/TP korrekt?

### 2. Baseline-Backtest (NÄCHSTER SCHRITT) 🎯

```bash
# Weekly only, alle 28 Pairs, direct_touch
python scripts/backtesting/backtest_weekly_baseline.py
```

**Output**:
- `Backtest/02_W_test/baseline_report.txt` - Kompletter Text-Report
- `Backtest/02_W_test/baseline_report.html` - QuantStats HTML Report mit Charts
- `Backtest/02_W_test/trades.csv` - Alle Trade-Details
- `Backtest/02_W_test/equity_curve.csv` - Portfolio Value über Zeit

**Zweck**: Ersten Überblick bekommen - funktioniert die Strategie?

**Erwartungen**:
- Min. 50-100 Trades für Aussagekraft
- Win Rate ~45-55%
- Profit Factor >1.5
- Max DD <20%
- Sharpe >1.5

---

## 📊 Test-Phasen

### Phase 1: Validation ✅ ABGESCHLOSSEN
- **Ordner**: `Backtest/01_test/01_Validation/`
- **Zweck**: Logik validieren mit 6 Sample-Trades
- **Status**: ✅ Alle Regeln korrekt implementiert

### Phase 2: Weekly Baseline 🎯 AKTUELL
- **Ordner**: `Backtest/02_W_test/`
- **Zweck**: Erster vollständiger Backtest mit Weekly Pivots
- **Config**: W only, alle 28 Pairs, direct_touch, 2010-2024
- **Output**: TXT + HTML Reports, CSV Exports

### Phase 3: Full Backtest (später)
- **Ordner**: `Backtest/03_full/`
- **Zweck**: Alle HTF (3D, W, M), Entry-Varianten testen
- **Config**: Alle Kombinationen, Optimization

### Phase 4: Fundamentals (viel später)
- **Ordner**: `Backtest/04_fundamentals/`
- **Zweck**: COT, Seasonality, Correlation-Filter

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

- **STRATEGIE_REGELN.md** ⭐ - ALLE technischen Regeln kompakt
- **STRATEGIE.md** - Strategie-Überblick & Settings
- **MODEL3_CONFIG.md** - Detaillierte Konfiguration
- **backtest_model3.py** - Haupt-Backtest-Script
- **validation_trades.py** - Trade-Validierung (6 Samples)

---

## ⚠️ Wichtige Regeln

### Pivot-Struktur
- **Pivot** = Open K2 (Standard: OHNE Versatz)
- **Extreme** = Ende längere Wick
  - Bullish: min(K1 Low, K2 Low) - tiefster Punkt
  - Bearish: max(K1 High, K2 High) - höchster Punkt
- **Near** = Ende kürzere Wick
  - Bullish: max(K1 Low, K2 Low) - höherer Low
  - Bearish: min(K1 High, K2 High) - tieferer High
- **Timestamps** = ALLE OPEN-Zeit der Bars!

### Entry-Voraussetzungen
- Gap Touch auf **Daily-Daten** prüfen (auch bei W/M!)
- TP-Check: TP nicht berührt **zwischen Gap Touch und Entry**
  - Check-Fenster: `max(Valid Time, Gap Touch)` bis `Entry Time`
- Wick Diff Entry bei < 20% (außer Verfeinerung näher)
- RR-Check: >= 1 RR erforderlich

### SL-Berechnung
- Min. 60 Pips von **ENTRY** (nicht Extreme!)
- UND jenseits Fib 1.1 (= Fib 1 ± 10% Gap)

### Datenqualität
- **D-M Daten**: TradingView → 100% exakt
- **H1-H4 Daten**: Oanda API → können abweichen
- Daten-Korrektur in Code implementiert

---

*Last Updated: 29.12.2025*
