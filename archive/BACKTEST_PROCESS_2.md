# Model 3 - Test-Prozedur (Kompakt)

**Stand**: 2025-01-04  
**Status**: Phase 1+2 abgeschlossen, Phase 3 (Optimierung) JETZT

---

## 🎯 VERFÜGBARE DATEN

**CSV Trades vorhanden**: W_trades.csv, 3D_trades.csv, M_trades.csv

**Wichtigste Spalten**:
- Gap/Pivot: `gap_pips`, `wick_diff_pips`, `wick_diff_pct`
- Entry/Exit: `entry_price`, `sl_price`, `tp_price`, `exit_price`, `final_rr`
- Performance: `pnl_r`, `win_loss`, `duration_days`, `mfe_pips`, `mae_pips`
- Meta: `pair`, `htf_timeframe`, `direction`, `priority_refinement_tf`

**Nicht vorhanden**:
- K1/K2 Details: `k1_close`, `k2_open`, Body %
- Versatz Ratio, Refinement Details

---

## ✅ MIT CSV MÖGLICH (SCHNELL!)

### **1. GAP SIZE FILTER** 🔴 PRIORITÄT 1
**Spalte**: `gap_pips`

**Test**: Filter Trades nach Min/Max Gap
```python
filtered = trades[(trades['gap_pips'] >= MIN) & (trades['gap_pips'] <= MAX)]
```

**Runs**: 
- Phase A: 8 grobe Ranges (0-∞, 30-300, 50-250, 50-200, 80-250, 80-200, 100-200, 100-150)
- Phase B: 25 feine Schritte um beste Range

**Zeit**: < 1h für alle Tests  
**Walk-Forward**: JA (Jahre-basiert)

---

### **2. WICK ASYMMETRIE** 🟡
**Spalten**: `wick_diff_pips`, `gap_pips`

**Test**: Min Wick Diff % von Gap
```python
filtered = trades[(wick_diff / gap * 100) >= MIN_PCT]
```

**Runs**: 0%, 10%, 20%, 30%, 40%  
**Zeit**: < 10 min

---

### **3. DURATION FILTER** 🔵
**Spalte**: `duration_days`

**Test**: Min/Max Trade Duration  
**Runs**: 3-30d, 5-45d, etc.  
**Zeit**: < 10 min

---

### **4. TIME-BASED FILTER** 🔵
**Spalten**: `entry_time`, `pivot_time`

**Test**: Day of Week, Month Analysis
```python
trades['dow'] = pd.to_datetime(trades['entry_time']).dt.dayofweek
filtered = trades[trades['dow'].isin([1,2,3])]  # Tue-Thu
```

**Zeit**: < 10 min

---

### **⚠️ APPROXIMATIONEN (CSV möglich, aber ungenau)**

#### **RR FILTER** 🟡
**Spalte**: `final_rr`

**Problem**: CSV zeigt nur finale Entries
- Bei Min RR 1.2: Andere Refinements würden genutzt werden
- Filter zeigt nur "Performance von Trades mit RR >= X"
- NICHT "Performance wenn Min RR im Code = X"

**Nutzen**: Grobe Tendenz, für finale Entscheidung neuer Backtest nötig

---

#### **TP LEVEL via MFE** 🔵
**Spalten**: `mfe_pips`, `gap_pips`

**Test**: Simuliere alternative TP Levels
```python
tp_618 = gap * 0.618
would_hit = (mfe >= tp_618)  # Approximation!
```

**Problem**: MFE = Maximum (bester Punkt)
- Preis könnte danach wieder runter → SL getroffen
- Nicht alle "MFE-Hits" wären echte TP-Hits

**Nutzen**: Tendenz-Analyse, nicht exakt

---

## ❌ NEUER BACKTEST NÖTIG

### **1. GAP VERSATZ FILTER** 🔴
**Fehlt**: `k1_close`, `k2_open` → Versatz Ratio

**Warum Backtest**: 
- Ändert welche Pivots gefunden werden
- Filter bei Pivot-Detection, nicht Trade-Filter

**Lösung**:
- **SCHNELL**: CSV erweitern (neue Spalten) → dann Filter wie oben
- **LANGSAM**: Neue Backtests mit Versatz-Parameter

**Test-Runs**: Max Versatz 0.5, 1.0, 1.5, 2.0, unlimited  
**Zeit**: ~2h (5 Runs) oder ~10 min (wenn CSV erweitert)

---

### **2. DOJI FILTER ÄNDERN** 🟡
**Fehlt**: `k1_body_pct`, `k2_body_pct`

**Warum Backtest**: 
- Ändert welche Pivots gefunden werden
- Bei 10% Filter: Manche Pivots existieren nicht

**Test-Runs**: 0%, 5% (current), 10%, 15%  
**Zeit**: ~2h (4 Runs) oder ~10 min (wenn CSV erweitert)

---

### **3. ENTRY CONFIRMATION TYPE** 🔴
**Current**: `direct_touch` only

**Warum Backtest**: 
- `1h_close` / `4h_close` = komplett andere Entry-Logik
- Manche Trades existieren nicht (Close zurück → gelöscht)
- Entry Times ändern sich

**Test-Runs**: direct_touch, 1h_close, 4h_close  
**Zeit**: ~6h (3 Runs à ~2h)  
**Walk-Forward**: JA

---

### **4. REFINEMENT TIMEFRAMES** 🟡
**Current**: All TFs (H1, H4, D, 3D, W)

**Warum Backtest**: 
- Andere TF-Kombination = andere Refinements gefunden
- Entry Levels ändern sich

**Test-Runs**:
- Phase A: H1, H4, D, 3D, W (einzeln) - 5 Runs
- Phase B: Kombinationen (H4+D, D+H4+H1, etc.) - ~10 Runs

**Zeit**: ~20-30h (15 Runs)  
**Walk-Forward**: JA (finale Kombination)

---

### **5. REFINEMENT MAX SIZE** 🟡
**Current**: 20% von HTF Gap

**Warum Backtest**: Andere Max Size = andere Refinements

**Test-Runs**: 10%, 15%, 20%, 25%, 30%  
**Zeit**: ~10h (5 Runs)

---

### **6. SL/TP FIB LEVELS** 🟡
**Current**: SL Fib 1.1, TP Fib -1.0

**Warum Backtest**: 
- Andere Fib = andere SL/TP Distanzen
- Win Rate ändert sich

**Test-Runs**:
- TP: -0.618, -1.0, -1.5, -2.0
- SL: 1.0, 1.1, 1.2, 1.5

**Zeit**: ~16h (8 Kombinationen)  
**Walk-Forward**: JA (TP wichtig)

---

### **7. PARTIAL TP / BREAKEVEN / TRAILING** 🔵
**Current**: Fixe Exits nur

**Warum Backtest**: Braucht Tick-by-Tick während Trade läuft

**Zeit**: ~2-3h pro Variante

---

## 🚀 OPTIMALER WORKFLOW

### **TAG 1: CSV-Tests** (~3h)
1. Gap Size Filter (Phase A+B) - **PRIORITÄT 1**
2. Wick Asymmetrie
3. Duration Filter
4. Walk-Forward beste Settings

**Output**: Beste Filter-Ranges identifiziert

---

### **TAG 1-2: CSV Erweitern** (~4h)
1. Erweitere Trade-Dict:
   - `k1_close`, `k2_open`, `versatz_ratio`
   - `k1_body_pct`, `k2_body_pct`
   - `refinement_size_pct`
   - `move_valid_to_entry_pct` (für Impulsive Move später)

2. Re-Run W, 3D, M (~1h pro TF = 3h)

3. Test auf extended CSV:
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
1. ALLE optimalen Parameter kombiniert
2. Walk-Forward 14 Windows (5y IS / 1y OOS)
3. OOS Robustheit-Check

**Bewertung**:
- ✅ ROBUST: OOS Median Exp > 0.10R, >90% positive Windows, Std Dev < 0.05R
- ⚠️ UNSICHER: OOS Median 0.05-0.10R, 70-90% positive
- ❌ OVERFIT: OOS negativ oder sehr variabel

---

## ⏱️ RECHENZEIT-ÜBERSICHT

### **Schneller Weg** (CSV-fokussiert):
```
Tag 1: CSV-Tests             ~  3h
Tag 1-2: CSV erweitern       ~  4h
Tag 2-3: Kritische Tests     ~ 15h
                    TOTAL:   ~ 22h (~1-2 Tage)
```

### **Vollständiger Weg** (alle Backtests):
```
CSV-Tests                    ~  3h
CSV erweitern                ~  4h
Kritische Tests              ~ 15h
Sekundäre Tests (TF/TP/SL)   ~ 30h
Final Cross-Check            ~ 20h
                    TOTAL:   ~ 72h (~3-4 Tage)
```

### **Mit Parallelisierung** (4 Cores):
```
Backtests 4x schneller       ~ 20h (~1 Tag)
```

---

## 📊 TEST-DOKUMENTATION (Template)

```markdown
# Test X: [Variable]

## Setup
HTF: W/3D/M | Period: 2010-2024 | Config: [vorherige Settings]

## Test-Runs
| Setting | Trades | Exp(R) | WR(%) | MaxDD | SQN |
|---------|--------|--------|-------|-------|-----|
| ...     | 4100   | 0.08   | 49%   | -12R  | 1.6 |

## Impact
- Gefiltert: 15% (4100 → 3485)
- WR Change: +2%
- Exp Change: +0.02R

Gefilterte Trades: 42% WR, -0.05R → Filter sinnvoll!

## Walk-Forward (wenn applicable)
OOS Median: 0.09R | Positive: 13/14 (93%) → ✅ ROBUST

## Entscheidung
Setting: [X] | Grund: Beste Balance Count/Quality, OOS stabil
```

---

## ⚠️ WICHTIGE WARNUNGEN

### **Approximations-Risiken**:

1. **RR Filter via CSV**: Nur Tendenz, nicht exakte neue Resultate
2. **TP Level via MFE**: Schätzung, für finale Entscheidung neuer Backtest
3. **SL Distance Filter**: Zeigt nicht "Performance wenn Min SL = X im Code"

### **Overfitting vermeiden**:
- ✅ Max 1 Variable pro Test
- ✅ Walk-Forward bei kritischen Parametern
- ✅ OOS Performance positiv & stabil
- ✅ Parameter logisch sinnvoll (nicht nur statistisch)
- ✅ Robustheit über Pairs (>60% profitabel)
- ✅ Keine Cliff-Effekte (smooth Performance-Kurve)

---

## 🎯 SOFORT STARTEN

**JETZT**:
1. Gap Size Filter CSV-basiert (Phase A)
2. Beste Range identifizieren
3. Phase B: Feine Schritte

**DANN**:
1. Walk-Forward Validation
2. CSV erweitern
3. Weitere CSV-Tests

**SPÄTER**:
1. Entry Confirmation
2. Refinement TFs
3. Final Cross-Check

---

*Last Updated: 2025-01-04*