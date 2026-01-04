# Model 3 - Multi-Timeframe Pivot Trading System

## 📁 Projekt-Struktur (AKTUALISIERT 04.01.2026)

```
05_Model 3/
├── README.md                    ← DIESE DATEI (Projekt-Übersicht)
├── BACKTEST_PROCESS.md          ← OPTIMIERUNGS-PROZEDUR (Phase 2)
├── STRATEGIE_VARIABLES.md       ← VARIABLEN FÜR OPTIMIERUNG
├── STRATEGIE_REGELN.md          ← KOMPLETTE TECHNISCHE REGELN
├── claude.md                    ← Claude Kontext
├── CHANGELOG.md                 ← Änderungshistorie
│
├── Backtest/
│   ├── 01_test/                 ← ABGESCHLOSSEN ✅
│   │   ├── 01_Validation/       ← 6 Sample Trades (Validierung)
│   │   └── 02_W_test/           ← Weekly Tests (OLD STRUCTURE)
│   │
│   ├── 02_technical/            ← ABGESCHLOSSEN ✅
│   │   └── 01_Single_TF/        ← Einzelne Timeframes (W, 3D, M)
│   │       ├── scripts/
│   │       │   ├── backtest_all.py      ← Main Script (W, 3D, M)
│   │       │   └── report_helpers.py
│   │       └── results/
│   │           ├── Trades/
│   │           │   ├── W_trades.csv
│   │           │   ├── 3D_trades.csv
│   │           │   └── M_trades.csv
│   │           ├── W_report.txt
│   │           ├── 3D_report.txt
│   │           └── M_report.txt
│   │
│   ├── 03_optimization/         ← AKTUELL 🎯
│   │   └── 01_Single_TF/
│   │       ├── scripts/
│   │       │   └── optimize_gap_size.py
│   │       └── 01_Gap_Size/
│   │           ├── A_Coarse_Ranges/
│   │           └── B_Fine_Steps/
│   │
│   └── 04_fundamentals/         ← SPÄTER (COT, Seasonality)
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

### Phase 2: Single Timeframe Tests ✅ ABGESCHLOSSEN

**Alle Timeframes:**
```bash
cd "05_Model 3/Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_all.py
```

**Output:**
- `results/Trades/{TF}_trades.csv` - Trade-Liste mit allen Details
- `results/{TF}_report.txt` - Vollständiger Report (REPORT1 Format)
- Timeframes: W, 3D, M

---

## 📊 Test-Phasen

### Phase 1: Validation ✅ ABGESCHLOSSEN
- **Ordner**: `Backtest/01_test/01_Validation/`
- **Zweck**: Logik validieren mit 6 Sample-Trades
- **Status**: ✅ Alle Regeln korrekt implementiert

### Phase 2: Technical Backtests ✅ ABGESCHLOSSEN
- **Ordner**: `Backtest/02_technical/01_DEFAULT/01_Single_TF/`
- **Zweck**: Separate Backtests für W, 3D, M
- **Config**: Einzelne Timeframes, 28 Pairs (alphabetisch), direct_touch, 2010-2024
- **Output**: TXT Reports (REPORT1 Format) + CSV Exports
- **Report Features**: SQN, Pair Breakdown, Funded Account Viability
- **Status**: W, 3D, M Backtests durchgeführt (04.01.2026)

### Phase 3: Technische Optimierung 🎯 AKTUELL
- **Ordner**: `Backtest/02_technical/01_DEFAULT/01_Single_TF/`
- **Zweck**: CSV-basierte Optimierung der Strategie-Parameter
- **Methode**: Sequential Optimization (eine Variable nach der anderen)
- **Prozedur**: Siehe `BACKTEST_PROCESS.md`
- **Variablen**: Siehe `STRATEGIE_VARIABLES.md`
- **Startpunkt**: Gap Size Filter (Phase A & B)

### Phase 4: Portfolio & COT Integration (SPÄTER)
- **Ordner**: `Backtest/04_fundamentals/COT/`
- **Zweck**: COT Index filtering auf W, 3D, M Tests anwenden
- **Filter**: Commercial vs Retail positioning

---

## 📂 Aktueller Status (04.01.2026)

### Phase 2 ✅ ABGESCHLOSSEN (04.01.2026)

**Backtests durchgeführt:**
- Weekly (W) - 28 Pairs, 2010-2024
- 3-Day (3D) - 28 Pairs, 2010-2024
- Monthly (M) - 28 Pairs, 2010-2024

**Ergebnisse verfügbar:**
- `results/W_trades.csv` + `W_report.txt`
- `results/3D_trades.csv` + `3D_report.txt`
- `results/M_trades.csv` + `M_report.txt`

### Phase 3 🎯 JETZT: Optimierung

**Fokus**: CSV-basierte Optimierung (schnell & effizient)

**Nächste Schritte:**
1. Gap Size Filter (Phase A: Grobe Ranges)
2. Gap Size Filter (Phase B: Feine Schritte)
3. Walk-Forward Validation
4. Weitere Filter (Versatz, Wick Asymmetrie)

**Prozedur**: Siehe `BACKTEST_PROCESS.md`

---

## 📂 Changelog-Zusammenfassung

### 03.01.2026 - Kritische Fixes
- ✅ K1 Zeitfenster-Check: K1 UND K2 müssen im HTF-Zeitfenster liegen
- ✅ Trade ohne Exit: Wird gelöscht (nicht als "manual" gespeichert)
- ✅ Unberührt-Check: NEAR ist Default (K2 OPEN war zu streng)

### 31.12.2025 - REPORT1 Format Einführung
- Pure/Conservative Trennung entfernt (vereinfacht)
- REPORT1 Format: Optimierungs-fokussiert, schnellere Generierung
- Neue Features: SQN, Pair Breakdown
- PAIRS jetzt alphabetisch sortiert (AUDCAD → USDJPY)

### 30.12.2025 - Strukturänderung
- `02_technical/01_DEFAULT/01_Single_TF/` für alle 3 Timeframes
- Konsolidierung auf ein einziges Script: `backtest_all.py`
- Keine Zeitstempel mehr in Dateinamen

### Ausgabe-Dateien

**CSV Trades:**
- `results/Trades/W_trades.csv`
- `results/Trades/3D_trades.csv`
- `results/Trades/M_trades.csv`

**TXT Reports (REPORT1 Format):**
- `results/W_report.txt`
- `results/3D_report.txt`
- `results/M_report.txt`
- Enthält: SQN, Top/Bottom 5 Pairs, Funded Account Viability

---

## 🔧 Scripts

### backtest_all.py (Main Script)

**Verwendung:**
```bash
cd "Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_all.py
```

**Funktionsweise:**
- Führt W, 3D, M Backtests nacheinander aus
- Nutzt `report_helpers.py` für Statistik-Berechnung
- Generiert REPORT1-Format Reports

**Settings (in Script):**
- `TIMEFRAMES`: ["W", "3D", "M"]
- `PAIRS`: 28 Major/Cross Pairs (alphabetisch sortiert)
- `START_DATE`: "2010-01-01"
- `END_DATE`: "2024-12-31"
- `ENTRY_CONFIRMATION`: "direct_touch"
- `DOJI_FILTER`: 5.0
- `REFINEMENT_MAX_SIZE`: 0.20 (20%)
- `MIN_SL_DISTANCE`: 60 Pips
- `MIN_RR`: 1.0
- `MAX_RR`: 1.5

**Output:**
- Automatische Ordner-Erstellung
- CSV Exports (W_trades.csv, 3D_trades.csv, M_trades.csv)
- TXT Reports (W_report.txt, 3D_report.txt, M_report.txt)

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
- TP-Check: TP nicht berührt **zwischen Gap Touch und Entry**
  - Check-Fenster: `Gap Touch Time` bis `Entry Time`
  - Prüfung auf H1 für Präzision
- Wick Diff Entry bei < 20% (außer Verfeinerung näher)
- RR-Check: >= 1 RR erforderlich
- **Unberührt-Check (Verfeinerung)**: NEAR darf nicht berührt werden zwischen Creation und HTF Valid Time

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
6. **Trade Characteristics**: Duration, Frequency, Concurrent Trades
7. **Funded Account Viability**: 6 Checks (Trades, Exp, DD, SQN, WR, PF)
8. **Pair Breakdown**: Top 5 Best + Bottom 5 Worst by Expectancy

### Key Features:
- **SQN (System Quality Number)**: Qualitäts-Rating des Systems
  - Classification: Excellent > 3.0 > Very Good > 2.5 > Good > 2.0 > Average > 1.6 > Below Average
- **Pair Analysis**: Welche Pairs performen am besten/schlechtesten
- **Vectorized Calculations**: Schnellere Generierung
- **Trade ohne Exit**: Wird NICHT gespeichert (korrekte Datenqualität)

### CSV Spalten (für Optimierung):
- **Gap/Pivot**: `gap_pips`, `wick_diff_pips`, `wick_diff_pct`
- **Entry/Exit**: `entry_price`, `sl_price`, `tp_price`, `final_rr`
- **Performance**: `pnl_r`, `win_loss`, `duration_days`, `mfe_pips`, `mae_pips`
- **Meta**: `pair`, `htf_timeframe`, `direction`, `priority_refinement_tf`

---

## 📝 Wichtige Dateien

- **README.md** ⭐ - Diese Datei (Projekt-Übersicht)
- **BACKTEST_PROCESS.md** ⭐ - Optimierungs-Prozedur (Phase 3)
- **STRATEGIE_VARIABLES.md** ⭐ - Alle test-relevanten Variablen
- **STRATEGIE_REGELN.md** - ALLE technischen Regeln kompakt
- **CHANGELOG.md** - Änderungshistorie
- **claude.md** - Claude Kontext & Implementierungsstatus
- **scripts/backtest_all.py** - Main Backtest Script
- **scripts/report_helpers.py** - Report-Generierung & Statistiken

---

## 🎯 Nächste Schritte

### Phase 3: Technische Optimierung (JETZT)

1. 🎯 **Gap Size Filter** - START HERE!
   - Phase A: Grobe Ranges (8 Tests)
   - Phase B: Feine Schritte (~20 Tests)
   - Walk-Forward Validation (14 Windows)
   - **Methode**: CSV-basiert (schnell!)
   - **Zeit**: ~3h

2. ⏳ **CSV erweitern** (~4h)
   - Neue Spalten: `k1_close`, `k2_open`, `versatz_ratio`, `k1_body_pct`, `k2_body_pct`
   - Re-Run W, 3D, M (~1h pro TF)
   - Dann: Gap Versatz Filter, Doji Filter Impact

3. ⏳ **Kritische Backtests** (~15h)
   - Entry Confirmation (3 Runs: direct_touch, 1h_close, 4h_close)
   - Refinement TFs Phase A (5 Runs)
   - Walk-Forward

4. ⏳ **Final Cross-Check** (~20h)
   - Alle optimalen Parameter kombiniert
   - Walk-Forward: 14 Windows (5y IS / 1y OOS)
   - OOS Stabilität prüfen

### Phase 4: Portfolio & COT (SPÄTER)

5. ⏳ Combined Portfolio Tests (W+3D+M zusammen)
6. ⏳ COT Integration vorbereiten
7. ⏳ Max Concurrent Trades optimieren

---

## ⚠️ Wichtige Updates (04.01.2026)

**Phase 2 ABGESCHLOSSEN:**
- ✅ W, 3D, M Backtests durchgeführt
- ✅ REPORT1 Format Reports generiert
- ✅ CSV Trades für Optimierung verfügbar

**Bug Fixes angewendet (03.01.2026):**
1. ✅ **K1 Zeitfenster-Check**: K1 UND K2 müssen im HTF-Zeitfenster liegen
2. ✅ **Trade ohne Exit**: Wird gelöscht (nicht als "manual" gespeichert)
3. ✅ **Unberührt-Check**: NEAR ist Default (K2 OPEN war zu streng)

**Bug Fixes (01.01.2026):**
1. ✅ **3D Zero Trades Fix**: Dynamic LTF list (excludes HTF itself)
2. ✅ **Chronological Entry Logic**: Korrekte Touch-basierte Reihenfolge
3. ✅ **RR Fallback**: Höchste Prio < 1 RR → Delete, nächste wird aktiv

**Nächster Schritt**: Phase 3 - Technische Optimierung (Gap Size Filter)

Details siehe [CHANGELOG.md](CHANGELOG.md)

---

*Last Updated: 04.01.2026*
