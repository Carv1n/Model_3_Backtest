# Model 3 - Changelog

**Letzte Updates**: 03.01.2026

---

## 03.01.2026 - CRITICAL FIXES: Refinement Logic & Trade Handling ✅

### 🔴 Fix 1: K1 Zeitfenster-Check
**Problem:**
- Nur K2 wurde geprüft ob im HTF-Zeitfenster, K1 konnte außerhalb liegen
- Konnte zu falschen Refinements führen

**Fix:**
```python
# OLD (WRONG):
if k2["time"] < htf_pivot.k1_time or k2["time"] >= htf_pivot.valid_time:

# NEW (CORRECT):
if k1["time"] < htf_pivot.k1_time or k2["time"] >= htf_pivot.valid_time:
```

**Impact:**
- K1 UND K2 müssen jetzt beide im HTF-Zeitfenster liegen
- Strengere Validierung von Refinements

### 🔴 Fix 2: Trade ohne Exit
**Problem:**
- Trades ohne Exit (noch offen am Ende) wurden als "manual" exit gespeichert
- Verfälschte Statistiken

**Fix:**
```python
# OLD (WRONG):
# kein Exit -> schließen am letzten Kurs
trade.exit_reason = "manual"
return trade

# NEW (CORRECT):
# kein Exit -> Trade löschen (nicht speichern)
return None
```

**Impact:**
- Nur abgeschlossene Trades werden gespeichert
- Sauberere Datenqualität

### 🔴 Fix 3: Unberührt-Check korrigiert
**Problem:**
- Vectorized Scripts prüften NEAR statt K2 OPEN
- Falsche Refinement-Validierung

**Fix:**
```python
# OLD (WRONG):
near_level = nears_result[i]
was_touched = (touch_window["low"] <= near_level).any()

# NEW (CORRECT):
k2_open_level = pivot_levels_result[i]
was_touched = (touch_window["low"] <= k2_open_level).any()
```

**Impact:**
- Korrekte Unberührt-Prüfung (K2 OPEN statt NEAR)
- Mehr valide Refinements möglich

### 📝 Dokumentation
**Aktualisiert:**
- `STRATEGIE_REGELN.md`: "K2 Open unberührt" statt "Near unberührt"
- `README.md`: Alle 3 Fixes dokumentiert
- Report Format: Winrate by Fib TP Levels entfernt

### 🗑️ Cleanup
**Gelöscht:**
- Unwichtige Scripts aus `/scripts/backtesting/`:
  - `backtest_ui.py`
  - `create_summary.py`
  - `monte_carlo.py`
  - `run_all_backtests.py`
  - `view_results.py`
  - `visualizations.py`
- Nur `backtest_model3.py` wird für Model 3 verwendet

---

## 01.01.2026 - CRITICAL BUG FIXES: Entry Logic & LTF List ✅

### 🔴 Bug Fix 1: 3D Backtest Zero Trades Issue
**Problem:**
- 9 von 28 Pairs hatten 0 Trades trotz 600+ Pivots (CADJPY, GBPJPY, GBPUSD, USDJPY, etc.)
- Root Cause: Hardcoded `ltf_list = ["3D", "D", "H4", "H1"]` in Line 501

**Fix:**
```python
# OLD (WRONG):
ltf_list = ["3D", "D", "H4", "H1"]

# NEW (CORRECT):
all_tfs = ["M", "W", "3D", "D", "H4", "H1"]
htf_idx = all_tfs.index(htf_timeframe)
ltf_list = all_tfs[htf_idx + 1:]  # Dynamic based on HTF
```

**Result:**
- W: `["3D", "D", "H4", "H1"]` ✓
- 3D: `["D", "H4", "H1"]` ✓ (excluded 3D itself!)
- M: `["W", "3D", "D", "H4", "H1"]` ✓ (now includes W!)

**Impact:**
- 3D Backtest sollte jetzt Trades für alle 28 Pairs haben
- M Backtest könnte mehr Trades haben (W Verfeinerungen inkludiert)

### 🔴 Bug Fix 2: Chronological Entry Logic
**Problem:**
- Entry-Kandidaten wurden nur nach Priorität sortiert, NICHT chronologisch
- Niedrigere Prio Verfeinerungen wurden nicht sofort gelöscht wenn berührt
- RR Fallback nicht korrekt implementiert
- Multiple entries möglich (sollte nur EINE Entry pro Pivot sein)

**Korrekte Regeln (aus User-Feedback):**
1. **Nur EINE Entry pro Pivot**
2. **Nur höchste Priorität** refinement bekommt RR-Check
3. **Niedrigere Priorität** refinements → Sofort löschen wenn berührt (KEIN RR-Check!)
4. **Chronologische Reihenfolge** der Touches ist entscheidend
5. **RR Fallback**: Wenn höchste Prio < 1 RR → löschen, nächste wird höchste Prio

**Fix:**
```python
# Neue Funktion:
def find_near_touch_time(near_level, start_time, h1_df, direction):
    """Findet wann near_level zum ersten Mal nach start_time berührt wird"""
    # Vectorized touch detection auf H1 Daten

# Neue Logik in simulate_single_trade():
1. Finde Touch-Zeiten für ALLE Verfeinerungen
2. Sortiere Touches chronologisch
3. Verarbeite in zeitlicher Reihenfolge:
   - Touched Ref = Höchste Prio → RR Check → Entry oder Delete
   - Touched Ref ≠ Höchste Prio → DELETE sofort (kein RR Check)
4. Return erste valide Entry oder None
```

**Impact:**
- Korrekte Entry-Simulation nach tatsächlicher Marktbewegung
- RR Fallback funktioniert richtig
- Keine falschen Entries mehr

### Files Updated
- ✅ `backtest_all.py` - Phase 2 Main Script
- ✅ `backtest_weekly_mini.py` - Test Script
- ✅ `backtest_weekly_full.py` - Test Script (All Pairs)

### Verification
- ✅ Python Syntax Check: Alle 3 Files valid
- ✅ Logic Check gegen STRATEGIE_REGELN.md: Korrekt
- ✅ Refinement Priority: W > 3D > D > H4 > H1 ✓
- ✅ Chronological Processing: Touch-basierte Reihenfolge ✓
- ✅ Single Entry Rule: Nur erste valide Entry ✓
- ✅ RR Fallback: Höchste Prio < 1 RR → Delete, nächste wird aktiv ✓

---

## 31.12.2025 - REPORT1 Format & Improvements ✅

### REPORT1 Format Einführung
- ✅ Pure/Conservative Trennung entfernt (vereinfacht)
- ✅ Neues REPORT1 Format: Optimierungs-fokussiert
- ✅ **Win Rate by Fib TP Levels**: Fib -0.5 bis -3.0 Analyse
  - Fib -1.0 Win Rate = Overall Win Rate (korrekt)
  - Nutzt `exit_type == 'tp'` für Fib -1.0, MFE für andere Levels
- ✅ **SQN (System Quality Number)**: (Expectancy / StdDev) × √N
  - Classification: Excellent > 3.0 > Very Good > 2.5 > Good > 2.0 > Average > 1.6 > Below Average
- ✅ **Pair Breakdown**: Top 5 Best + Bottom 5 Worst by Expectancy
  - 7 Stats: Trades, Win%, Exp, PF, AvgW, AvgL, Total R
- ✅ **Funded Account Viability**: 6 Checks (200 Trades, +Exp, DD<10R, SQN>1.6, WR>35%, PF>1.3)

### Scripts Aktualisiert
- ✅ `report_helpers.py` - Neue calc_stats() mit Fib TP & SQN
- ✅ `backtest_all.py` (Phase 2) - format_report(stats, htf_timeframe, config)
- ✅ `backtest_weekly_full.py` (Test) - format_report(stats, "Weekly", config)
- ✅ `backtest_weekly_mini.py` (Test) - Template für neue Struktur
- ✅ COT `generate_reports.py` - Neues REPORT1 Format mit Phase 2 Vergleich

### Code Improvements
- ✅ Vectorized Calculations: Schnellere DD, Streaks, Concurrent Trades Berechnung
- ✅ PAIRS alphabetisch sortiert (AUDCAD → USDJPY) in allen Scripts
- ✅ Entfernt: commission/spread Parameter aus calc_stats()
- ✅ Vereinfacht: format_report(stats, htf_timeframe, config)

### Bug Fixes
- ✅ **Fib -1.0 Win Rate Korrektur**:
  - Problem: MFE-based Berechnung zeigte 33.8% statt 39.9%
  - Fix: Fib -1.0 nutzt `exit_type == 'tp'` (actual exits)
  - Andere Fib Levels nutzen MFE (hypothetical "what if")
  - 4 Trades hatten MFE >= TP aber SL exit (Preis ging zu TP, kam zurück)

### Output-Dateien (NEU)
**CSV Trades:**
- `results/Trades/W_trades.csv`
- `results/Trades/3D_trades.csv`
- `results/Trades/M_trades.csv`

**TXT Reports (REPORT1 Format):**
- `results/W_report.txt`
- `results/3D_report.txt`
- `results/M_report.txt`

### COT Phase 3 Updates
- ✅ `generate_reports.py` komplett neu im REPORT1-Stil
- ✅ Nutzt calc_stats() aus Phase 2 (via sys.path import)
- ✅ Phase 2 Vergleich beibehalten (mit Pfeilen ↑↓→)
- ✅ Alle REPORT1 Sections + COT Filter Impact Section

---

## 30.12.2025 - Ordnerstruktur Refactoring ✅

### Neue Struktur
- ✅ `Backtest/02_technical/01_DEFAULT/01_Single_TF/` erstellt
- ✅ Separate Scripts für W, 3D, M Timeframes
- ✅ Einheitliche Dateinamenskonvention (ohne Zeitstempel)
- ✅ Pure vs Conservative klar getrennt

### Scripts
- ✅ `backtest_W.py` - Weekly Backtest
- ✅ `backtest_3D.py` - 3-Day Backtest
- ✅ `backtest_M.py` - Monthly Backtest
- ✅ `report_helpers.py` - Shared reporting functions

### Output-Dateien
**CSV Trades:**
- `results/Trades/W_pure.csv`
- `results/Trades/W_conservative.csv`
- `results/Trades/3D_pure.csv`
- `results/Trades/3D_conservative.csv`
- `results/Trades/M_pure.csv`
- `results/Trades/M_conservative.csv`

**TXT Reports:**
- `results/Pure_Strategy/W_pure.txt`
- `results/Pure_Strategy/3D_pure.txt`
- `results/Pure_Strategy/M_pure.txt`
- `results/Conservative/W_conservative.txt`
- `results/Conservative/3D_conservative.txt`
- `results/Conservative/M_conservative.txt`

### Pfad-Anpassungen
- ✅ Alle Scripts verwenden korrekte relative Pfade
- ✅ `model3_root` = 5× parent (scripts → ... → 05_Model 3)
- ✅ `RESULTS_DIR` = parent.parent / "results"
- ✅ Automatische Ordner-Erstellung

### Dokumentation
- ✅ README.md aktualisiert mit neuer Struktur
- ✅ CHANGELOG.md aktualisiert
- ✅ claude.md wird aktualisiert

### Status
- ✅ Phase 1 (01_test/) ABGESCHLOSSEN
- 🎯 Phase 2 (02_technical/) AKTIV
- ⏳ Phase 3 (03_fundamentals/COT) VORBEREITET

---

## Wichtigste Korrekturen (vorherige Updates)

### 1. Verfeinerungen Max TF = Weekly
- Vorher: Dachte M kann Verfeinerung sein
- Jetzt: M → W,3D,D,H4,H1 / W → 3D,D,H4,H1 / 3D → D,H4,H1
- Max TF für Verfeinerungen ist W!

### 2. Unberührt-Check
- Vorher: Near darf nicht berührt werden
- Jetzt: K2 OPEN der Verfeinerung darf nicht berührt werden (bis HTF Valid Time)
- Ab Valid Time: Entry bei Near (K2 Open egal)

### 3. Versatz-Regel
- Standard: OHNE Versatz (weder Pivots noch Verfeinerungen)

### 4. TP-Check Zeitfenster
- Start: `max(Valid Time, Gap Touch)`
- Ende: BEI Entry (nicht danach)
- TP Touch NACH Entry = normaler Trade

### 5. RR-Berechnung
- Bei RR > 1.5: SL erweitern UND `rr = 1.5` setzen

### 6. Gap Touch auf H1
- H1 statt Daily (stunden-genau!)

---

## Code-Fixes (30.12.2025)

1. TP-Check nicht ausgeführt → Jetzt in Trade-Flow eingebaut
2. Unberührt-Check falsch → Jetzt k2 open statt near
3. Variable near_level → Korrigiert zu nears_result[i]
4. CAGR Bug → Check ending_capital > 0
5. Wick Diff Entry → Vollständig implementiert
6. QuantStats HTML Reports → Entfernt (zu kompliziert, nur TXT+CSV)

---

## Nächste Schritte

1. ⏳ W, 3D, M Backtests ausführen
2. ⏳ Ergebnisse vergleichen (Timeframe Performance)
3. ⏳ COT Integration planen
4. ⏳ Combined Portfolio Test (W+3D+M)

---

*Last Updated: 30.12.2025*
