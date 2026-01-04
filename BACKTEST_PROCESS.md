# Model 3 - Backtest Prozedur

**Stand**: 2025-01-04  
**Status**: Phase 1+2 abgeschlossen, Phase 3 (Optimierung) JETZT

---

## 📋 ÜBERSICHT

### Aktuelle Phase
✅ Phase 1: Validation abgeschlossen  
✅ Phase 2: Single TF Tests (W, 3D, M) abgeschlossen  
🎯 Phase 3: Technische Optimierung (JETZT)

### Test-Philosophie
**Sequential Optimization** (eine Variable nach der anderen)  
**NICHT Grid Search** (alle Kombinationen → Overfit!)

**Vorteile**:
- Überschaubare Rechenzeit
- Klare Impact-Analyse pro Variable
- Verständnis wie Variablen wirken
- Overfitting-Risiko minimiert

---

## 🎯 VERFÜGBARE DATEN

**CSV Trades**: W_trades.csv, 3D_trades.csv, M_trades.csv

**Wichtigste Spalten**:
- Gap/Pivot: `gap_pips`, `wick_diff_pips`, `wick_diff_pct`
- Entry/Exit: `entry_price`, `sl_price`, `tp_price`, `final_rr`
- Performance: `pnl_r`, `win_loss`, `duration_days`, `mfe_pips`, `mae_pips`
- Meta: `pair`, `htf_timeframe`, `direction`, `priority_refinement_tf`

**Nicht vorhanden**:
- K1/K2 Details: `k1_close`, `k2_open`, Body %
- Versatz Ratio

---

## ✅ MIT CSV MÖGLICH (SCHNELL!)

### **TEST 1: GAP SIZE FILTER** 🔴 **START HERE!**

**Zweck**: Filter zu kleine (Noise) und zu große Gaps (lange Duration)

**Spalte**: `gap_pips`

**Test-Methode**:
```python
filtered = trades[(trades['gap_pips'] >= MIN) & (trades['gap_pips'] <= MAX)]
```

**Test-Strategie: 2-Phasen-Ansatz**

#### Phase A: Grobe Ranges (8 Tests)
```
Run 1: NO FILTER (0 - ∞, Baseline)
Run 2: VERY WIDE (30-300)
Run 3: WIDE (50-250)
Run 4: BALANCED 1 (50-200)
Run 5: BALANCED 2 (80-250)
Run 6: TIGHT 1 (80-200)
Run 7: TIGHT 2 (100-200)
Run 8: VERY TIGHT (100-150)
```

**Metriken vergleichen**:
```
| Run | Min | Max | Trades | Exp(R) | WR(%) | MaxDD | Avg Dur | SQN |
|-----|-----|-----|--------|--------|-------|-------|---------|-----|
| 1   | 0   | ∞   | 5000   | 0.05   | 47%   | -15R  | 18d     | 1.4 |
| 5   | 80  | 250 | 3800   | 0.10   | 51%   | -10R  | 14d     | 1.8 |
```

**Impact-Analyse**:
- Trades gefiltert: % und absolute Zahl
- Win Rate der gefilterten Trades (sind es wirklich schlechte?)
- Duration Distribution Änderung

**Ergebnis**: Beste Range identifizieren (z.B. "80-250")

#### Phase B: Feine Schritte (~20 Tests)

**Beispiel**: Phase A ergab "80-250 ist am besten"

**Vorgehen**:
```
1. Beste Min bei Max=250 fixed:
   Test Min 60, 70, 75, 80, 85, 90, 95, 100, 110, 120 (10 Tests)

2. Beste Max bei Min=80 fixed:
   Test Max 200, 220, 230, 240, 250, 260, 280, 300 (8 Tests)

3. Kombinationen um beste Min+Max (2-4 Tests)

Total: ~20 Tests
```

**Ergebnis**: Optimale Gap Range (z.B. "Min 85, Max 240")

#### Walk-Forward Validation

**Setup**: 5y IS / 1y OOS rolling, 14 Windows (2010-2024)

**Prozedur**:
```
Window 1: 2005-2009 IS → 2010 OOS
Window 2: 2006-2010 IS → 2011 OOS
...
Window 14: 2019-2023 IS → 2024 OOS
```

**Bewertung**:
- ✅ ROBUST: OOS Median Exp > 0.08R, >90% positive Windows, Std Dev < 0.05R
- ⚠️ UNSICHER: OOS Median 0.05-0.10R, 70-90% positive, Std Dev 0.05-0.10R
- ❌ OVERFIT: OOS negativ oder Std Dev > 0.10R

**Zeit**: Phase A+B < 1h, Walk-Forward ~2h (CSV-basiert)

---

### **TEST 2: WICK ASYMMETRIE** 🟡

**Spalten**: `wick_diff_pips`, `gap_pips`

**Test-Methode**:
```python
wick_pct = (trades['wick_diff_pips'] / trades['gap_pips'] * 100)
filtered = trades[wick_pct >= MIN_PCT]
```

**Test-Runs**: 0%, 10%, 20%, 30%, 40%

**Zeit**: < 10 min

**Walk-Forward**: NEIN

---

### **TEST 3: DURATION FILTER** 🔵

**Spalte**: `duration_days`

**Test-Runs**: Min 3 - Max 30d, Min 5 - Max 45d

**Zeit**: < 10 min

---

### **TEST 4: TIME-BASED FILTER** 🔵

**Test**: Day of Week, Month Analysis

**Zeit**: < 10 min

---

### ⚠️ **APPROXIMATIONEN** (CSV möglich, aber ungenau)

#### **RR Filter**
**Problem**: CSV zeigt nur finale Entries
- Bei Min RR 1.2 würden im Backtest andere Refinements genutzt
- Filter zeigt nur "Performance von Trades mit RR >= X"
- **Nutzen**: Grobe Tendenz, für Finale neuer Backtest nötig

#### **TP Level via MFE**
**Problem**: MFE = Maximum (bester Punkt)
- Preis könnte danach wieder runter → SL getroffen
- Nicht alle "MFE-Hits" wären echte TP-Hits
- **Nutzen**: Tendenz-Analyse, nicht exakt

---

## ❌ NEUER BACKTEST NÖTIG

### **TEST 5: GAP VERSATZ FILTER** 🔴

**Fehlt**: `k1_close`, `k2_open` → Versatz Ratio

**Definition**:
```python
Versatz = abs(Close_K1 - Open_K2) / Gap

0.0 = Bodies berühren sich
0.5 = Moderater Versatz
1.0 = Near auf Pivot
1.5 = Near über Pivot
```

**Lösung**:
- **SCHNELL**: CSV erweitern (neue Spalten) → dann Filter
- **LANGSAM**: 6 neue Backtests mit Versatz-Parameter

**Test-Runs**: Max Versatz unlimited, 2.0, 1.5, 1.0, 0.5, 0.3

**Zeit**: ~2h (6 Runs) ODER ~10 min (wenn CSV erweitert)

**Walk-Forward**: NEIN (erst grob)

---

### **TEST 6: DOJI FILTER** 🟡

**Fehlt**: `k1_body_pct`, `k2_body_pct`

**Warum Backtest**: Ändert welche Pivots gefunden werden

**Test-Runs**: 0%, 5% (current), 10%, 15%

**Zeit**: ~2h (4 Runs) ODER ~10 min (wenn CSV erweitert)

---

### **TEST 7: ENTRY CONFIRMATION** 🔴

**Current**: `direct_touch` only

**Warum Backtest**: Komplett andere Entry-Logik
- `1h_close`: Entry bei 1H Close jenseits Level
- `4h_close`: Stärkste Bestätigung
- Manche Trades existieren nicht (Close zurück → gelöscht)

**Test-Runs**: direct_touch, 1h_close, 4h_close

**Erwartung**:
- direct_touch: Baseline
- 1h_close: -20-30% Trades, +3-5% Win Rate
- 4h_close: -40-50% Trades, +5-8% Win Rate

**Zeit**: ~6h (3 Runs à ~2h)

**Walk-Forward**: JA (kritische Regel!)

---

### **TEST 8: REFINEMENT TIMEFRAMES** 🟡

**Warum Backtest**: Andere TFs = andere Refinements gefunden

**Phase A - Einzeln** (5 Runs):
- H1 only, H4 only, D only, 3D only, W only

**Phase B - Kombinationen** (~10 Runs):
- H4+D, D+H4+H1, 3D+D+H4, All

**Zeit**: ~20-30h (15 Runs)

**Walk-Forward**: JA (finale Kombination)

---

### **TEST 9-11: RISK MANAGEMENT** 🟡

**Min RR**: 1.0, 1.1, 1.2, 1.5 (Walk-Forward: JA)  
**SL Distance**: 40, 50, 60, 70, 80, 100 Pips (Walk-Forward: JA)  
**TP Fib**: -0.618, -1.0, -1.5, -2.0 (Walk-Forward: JA)

**Zeit gesamt**: ~16-20h

---

## 🚀 OPTIMALER WORKFLOW

### **TAG 1: CSV-Tests** (~3h)
1. ✅ Gap Size Filter (Phase A: 8 Tests, Phase B: ~20 Tests)
2. ✅ Wick Asymmetrie (5 Tests)
3. ✅ Duration Filter (experimentell)
4. ✅ Walk-Forward beste Settings

**Output**: Beste Filter-Ranges identifiziert

---

### **TAG 1-2: CSV Erweitern** (~4h)

**Erweitere Trade-Dict**:
```python
{
    # Existing fields...
    
    # NEU:
    "k1_close": k1_close_price,
    "k2_open": k2_open_price,
    "versatz_ratio": abs(k1_close - k2_open) / gap_pips,
    "k1_body_pct": body_pct_k1,
    "k2_body_pct": body_pct_k2,
    "refinement_size_pct": ref_wick_diff / htf_gap * 100,
}
```

**Re-Run W, 3D, M** (~1h pro TF = 3h)

**Dann teste**:
- Gap Versatz Filter (10 min)
- Doji Filter Impact (10 min)

**Output**: Alle CSV-möglichen Tests abgeschlossen

---

### **TAG 2-3: Kritische Backtests** (~15h)
1. Entry Confirmation (3 Runs) - ~6h
2. Refinement TFs Phase A (5 Runs) - ~10h
3. Walk-Forward - ~4h

**Output**: Entry Type & Ref TFs optimiert

---

### **TAG 3-4: Final Cross-Check** (~20h)

**Setup**: ALLE optimalen Parameter kombiniert

**Walk-Forward**: 14 Windows (5y IS / 1y OOS)

**In jedem IS**:
- Top 3 Parameter-Sets (kleine Variationen)
- Teste auf OOS

**Aggregate OOS**:
```
OOS Expectancy (Median): 0.12R
OOS Win Rate (Median): 51%
OOS Max DD (Median): -9R
OOS SQN (Median): 1.8

Stability:
- Positive: 13/14 Windows (93%)
- Std Dev: 0.04R (niedrig = gut)
```

**Bewertung**:
- ✅ ROBUST: Median Exp > 0.10R, >90% positive, Std Dev < 0.05R
- ⚠️ UNSICHER: Median 0.05-0.10R, 70-90% positive
- ❌ OVERFIT: Negativ oder Std Dev > 0.10R

---

## ⏱️ RECHENZEIT-ÜBERSICHT

### **Schneller Weg** (CSV-fokussiert)
```
CSV-Tests              ~  3h
CSV erweitern          ~  4h
Kritische Tests        ~ 15h
TOTAL:                 ~ 22h (~1-2 Tage)
```

### **Vollständiger Weg** (alle Backtests)
```
CSV-Tests              ~  3h
CSV erweitern          ~  4h
Kritische Tests        ~ 15h
Sekundäre Tests        ~ 30h
Final Cross-Check      ~ 20h
TOTAL:                 ~ 72h (~3-4 Tage)
```

### **Mit Parallelisierung** (4 Cores)
```
Backtests 4x schneller
TOTAL:                 ~ 20h (~1 Tag)
```

---

## 📊 DOKUMENTATION (Template)

```markdown
# Test X: [Variable]

## Setup
HTF: W/3D/M | Period: 2010-2024 | Config: [vorherige Settings]

## Test-Runs
| Setting | Trades | Exp(R) | WR(%) | MaxDD | Avg Dur | SQN |
|---------|--------|--------|-------|-------|---------|-----|
| Run 1   | 5000   | 0.05   | 47%   | -15R  | 18d     | 1.4 |
| Run 5   | 3800   | 0.10   | 51%   | -10R  | 14d     | 1.8 |

## Impact-Analyse
- Gefiltert: 1200 Trades (24%)
- WR Change: +4% (47% → 51%)
- Exp Change: +0.05R (100% improvement!)

Gefilterte Trades:
- Win Rate: 38% (deutlich schlechter!)
- Expectancy: -0.08R (negativ!)
→ ✅ Filter sinnvoll!

## Walk-Forward (wenn applicable)
- 14 Windows
- OOS Median: 0.09R (stabil)
- Positive: 13/14 (93%)
→ ✅ ROBUST

## Entscheidung
**Setting**: [X]  
**Grund**: Beste Balance Count/Quality, OOS stabil, logisch sinnvoll
```

---

## ⚠️ OVERFITTING CHECKLISTE

Vor jedem Test-Abschluss prüfen:

- ✅ Nur 1 Variable optimiert
- ✅ Genug Trades (>200 pro HTF)
- ✅ Parameter logisch sinnvoll
- ✅ Robustheit über Pairs (>60% profitabel)
- ✅ Smooth Performance-Kurve (keine Cliffs)
- ✅ OOS ähnlich IS (Diff <20%)
- ✅ Walk-Forward: >90% positive Windows
- ✅ Deutliche Verbesserung vs Baseline (>20%)

---

## 🎯 SOFORT STARTEN

**JETZT**:
1. Gap Size Filter CSV-basiert (Phase A)
2. Beste Range identifizieren (Phase B)
3. Walk-Forward Validation

**DANN**:
1. CSV erweitern (einmalig 4h)
2. Weitere CSV-Tests (Versatz, Doji)
3. Kritische Backtests (Entry, Ref TFs)

**SPÄTER**:
1. Sekundäre Tests (SL/TP Levels)
2. Final Cross-Check (alle Parameter)
3. Combined Portfolio (Phase 4)

---

*Last Updated: 2025-01-04*