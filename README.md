# Model 3 - Multi-Timeframe Pivot Trading System

## 📁 Projekt-Struktur (AKTUALISIERT 31.12.2025)

```
05_Model 3/
├── README.md                    ← DIESE DATEI (Projekt-Übersicht)
├── STRATEGIE_REGELN.md          ← KOMPLETTE TECHNISCHE REGELN
├── claude.md                    ← Claude Kontext
├── CHANGELOG.md                 ← Änderungshistorie
│
├── scripts/
│   └── backtesting/
│       └── backtest_model3.py   ← Core-Backtest-Engine
│
├── Backtest/
│   ├── 01_test/                 ← ABGESCHLOSSEN ✅
│   │   ├── 01_Validation/       ← 6 Sample Trades (Validierung)
│   │   └── 02_W_test/           ← Weekly Tests (OLD STRUCTURE)
│   │
│   ├── 02_technical/            ← AKTUELL 🎯
│   │   └── 01_DEFAULT/
│   │       └── 01_Single_TF/    ← Einzelne Timeframes (W, 3D, M)
│   │           ├── scripts/
│   │           │   ├── backtest_W.py
│   │           │   ├── backtest_3D.py
│   │           │   ├── backtest_M.py
│   │           │   └── report_helpers.py
│   │           └── results/
│   │               ├── Trades/
│   │               │   ├── W_trades.csv
│   │               │   ├── 3D_trades.csv
│   │               │   └── M_trades.csv
│   │               ├── W_report.txt
│   │               ├── 3D_report.txt
│   │               └── M_report.txt
│   │
│   └── 03_fundamentals/         ← SPÄTER (COT, Seasonality)
│       └── COT/
│
└── archive/                     ← Archivierte Dateien
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
   - Gap Touch auf H1
   - TP-Check: TP nicht berührt zwischen max(Valid Time, Gap Touch) und Entry
   - RR-Check: >= 1 RR erforderlich
4. Entry: direct_touch (Standard), alternativ 1h_close/4h_close
5. SL: Min. 60 Pips von Entry + jenseits Fib 1.1
6. TP: -1 Fib, RR: 1.0-1.5

**Alle technischen Regeln:** Siehe `STRATEGIE_REGELN.md`

---

## ⚙️ Standard-Einstellungen

```python
HTF_TIMEFRAMES = ["W"]  # oder ["3D"] oder ["M"]
ENTRY_CONFIRMATION = "direct_touch"
DOJI_FILTER = 5.0
REFINEMENT_MAX_SIZE = 0.20  # 20%
MIN_SL_DISTANCE = 60
MIN_RR = 1.0
MAX_RR = 1.5
RISK_PER_TRADE = 0.01  # 1%
STARTING_CAPITAL = 100000  # $100k
```

---

## 🚀 Quick Start

### Phase 1: Validation ✅ ABGESCHLOSSEN

```bash
cd "05_Model 3"
python Backtest/01_test/01_Validation/validation_trades.py
```

**Output**: 6 Sample-Trades validiert
- Alle Regeln korrekt implementiert
- Trade-Flow geprüft

### Phase 2: Single Timeframe Tests 🎯 AKTUELL

**Weekly:**
```bash
cd "05_Model 3/Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_W.py
```

**3-Day:**
```bash
python scripts/backtest_3D.py
```

**Monthly:**
```bash
python scripts/backtest_M.py
```

**Output:**
- `results/Trades/{TF}_trades.csv` - Trade-Liste mit allen Details
- `results/{TF}_report.txt` - Vollständiger Report (REPORT1 Format)

---

## 📊 Test-Phasen

### Phase 1: Validation ✅ ABGESCHLOSSEN
- **Ordner**: `Backtest/01_test/01_Validation/`
- **Zweck**: Logik validieren mit 6 Sample-Trades
- **Status**: ✅ Alle Regeln korrekt implementiert

### Phase 2: Technical Backtests 🎯 AKTUELL
- **Ordner**: `Backtest/02_technical/01_DEFAULT/01_Single_TF/`
- **Zweck**: Separate Backtests für W, 3D, M
- **Config**: Einzelne Timeframes, 28 Pairs (alphabetisch), direct_touch, 2010-2024
- **Output**: TXT Reports (REPORT1 Format) + CSV Exports
- **Report Features**: SQN, Win Rate by Fib TP, Pair Breakdown, Funded Account Viability

### Phase 3: COT Integration (NÄCHSTER SCHRITT)
- **Ordner**: `Backtest/03_fundamentals/COT/`
- **Zweck**: COT Index filtering auf W, 3D, M Tests anwenden
- **Filter**: Commercial vs Retail positioning

---

## 📂 Ordnerstruktur & Report Format (Update 31.12.2025)

### Änderungen:

**31.12.2025 - REPORT1 Format Einführung:**
- Pure/Conservative Trennung entfernt (vereinfacht)
- REPORT1 Format: Optimierungs-fokussiert, schnellere Generierung
- Neue Features: SQN, Win Rate by Fib TP Levels, Pair Breakdown
- PAIRS jetzt alphabetisch sortiert (AUDCAD → USDJPY)
- Schnellere Report-Generierung durch Vectorization

**30.12.2025 - Strukturänderung:**
- `02_technical/01_DEFAULT/01_Single_TF/` für alle 3 Timeframes
- Saubere Trennung: W, 3D, M haben eigene Scripts
- Keine Zeitstempel mehr in Dateinamen

### Ausgabe-Dateien

**CSV Trades (in `/Trades/`):**
- `W_trades.csv`, `3D_trades.csv`, `M_trades.csv`

**TXT Reports (REPORT1 Format):**
- `W_report.txt`, `3D_report.txt`, `M_report.txt`
- Enthält: SQN, Win Rate by Fib TP, Top/Bottom 5 Pairs, Funded Account Viability

---

## 🔧 Scripts

### backtest_W.py / backtest_3D.py / backtest_M.py

**Verwendung:**
```bash
cd "Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_W.py   # Weekly
python scripts/backtest_3D.py  # 3-Day
python scripts/backtest_M.py   # Monthly
```

**Settings (in Script):**
- `TIMEFRAME`: "W", "3D", oder "M"
- `HTF_TIMEFRAMES`: Liste mit einem Timeframe
- `PAIRS`: 28 Major/Cross Pairs
- `START_DATE`: "2010-01-01"
- `END_DATE`: "2024-12-31"

**Output:**
- Automatische Ordner-Erstellung
- Pure + Conservative Reports
- CSV Exports ohne Zeitstempel

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
- Gap Touch auf **H1-Daten** prüfen
- TP-Check: TP nicht berührt **zwischen max(Valid Time, Gap Touch) und Entry**
  - Check-Fenster: `max(Valid Time, Gap Touch)` bis `Entry Time`
  - Prüfung auf H1 für Präzision
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

## 📊 Reports (REPORT1 Format)

### Report Sections:
1. **Quick Overview**: Total Trades, Win Rate, Expectancy, SQN, Verdict
2. **R-Performance**: Cumulative R, SQN Classification, Sharpe/Sortino
3. **Trade Statistics**: Long/Short Breakdown, Win Rates
4. **Drawdown & Streaks**: Max DD, Recovery, Consecutive Wins/Losses
5. **Time-Based Performance**: Monthly/Yearly R, Best/Worst Periods
6. **Funded Account Viability**: 6 Checks (Trades, Exp, DD, SQN, WR, PF)
7. **Win Rate by Fib TP Levels**: Fib -0.5 bis -3.0 (was-wäre-wenn Analyse)
8. **Pair Breakdown**: Top 5 Best + Bottom 5 Worst by Expectancy

### Key Features:
- **Fib -1.0 Win Rate = Overall Win Rate** (korrekt)
- **SQN (System Quality Number)**: Qualitäts-Rating des Systems
- **Pair Analysis**: Welche Pairs performen am besten/schlechtesten
- **Vectorized Calculations**: Schnellere Generierung

---

## 📝 Wichtige Dateien

- **STRATEGIE_REGELN.md** ⭐ - ALLE technischen Regeln kompakt
- **README.md** - Diese Datei (Projekt-Übersicht)
- **CHANGELOG.md** - Änderungshistorie
- **claude.md** - Claude Kontext & Implementierungsstatus
- **backtest_W.py / 3D / M** - Timeframe-spezifische Backtests
- **report_helpers.py** - Report-Generierung (shared)

---

## 🎯 Nächste Schritte

1. ✅ Single Timeframe Tests ausführen (W, 3D, M)
2. ⏳ Ergebnisse analysieren und vergleichen
3. ⏳ COT Integration vorbereiten
4. ⏳ Combined Portfolio Tests (W+3D+M zusammen)

---

*Last Updated: 31.12.2025*
