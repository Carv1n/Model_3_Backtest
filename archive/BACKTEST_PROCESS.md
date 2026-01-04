# Model 3 - Detaillierte Test-Prozedur

**Stand**: 2025-01-04  
**Zweck**: Step-by-Step Anleitung für systematische Optimierung

---

## 📋 ÜBERSICHT

### Aktuelle Phase
✅ **Phase 1**: Validation abgeschlossen  
✅ **Phase 2**: Single TF Default Tests (W, 3D, M) abgeschlossen  
🎯 **Phase 3**: Technische Optimierung (JETZT)

### Test-Philosophie
**NICHT**: Grid Search (alle Kombinationen → Overfit!)  
**SONDERN**: Sequential Optimization (eine Variable nach der anderen)

**Vorteile**:
- Überschaubare Rechenzeit
- Klare Impact-Analyse pro Variable
- Overfitting-Risiko minimiert
- Verständnis wie Variablen wirken

---

## 🎯 PHASE 3: TECHNISCHE OPTIMIERUNG

### Phase 3A: Pivot Quality Filter (ZUERST!)

---

## TEST 1: GAP SIZE FILTER 🔴 **START HERE!**

### Zweck
Filter zu kleine (Noise, schnelle TP/SL) und zu große Gaps (lange Duration, schlecht tradebar)

### Setup
- **HTFs**: W, 3D, M (einzeln testen!)
- **Timeframe**: 2010-2024 (15 Jahre)
- **Settings**: Current Default (direct_touch, Ref all TFs, etc.)
- **Baseline**: NO Filter (current)

---

### Test-Strategie: 2-Phasen-Ansatz

#### **Phase 1A: Grobe Ranges (6-8 Tests)**
Finde beste ungefähre Range

**Test-Runs**:
```
Run 1: NO FILTER (Baseline, current)
       Min: 0 Pips, Max: unlimited
       → Alle Pivots erlaubt

Run 2: VERY WIDE
       Min: 30 Pips, Max: 300 Pips
       → Fast alles erlaubt

Run 3: WIDE
       Min: 50 Pips, Max: 250 Pips

Run 4: BALANCED 1
       Min: 50 Pips, Max: 200 Pips

Run 5: BALANCED 2
       Min: 80 Pips, Max: 250 Pips

Run 6: TIGHT 1
       Min: 80 Pips, Max: 200 Pips

Run 7: TIGHT 2
       Min: 100 Pips, Max: 200 Pips

Run 8: VERY TIGHT
       Min: 100 Pips, Max: 150 Pips
```

**Pro Run**: Full Backtest (W, 3D, M einzeln)

**Metriken vergleichen**:
```
| Run | Min | Max | Trades | Exp(R) | WR(%) | MaxDD(R) | Avg Dur | SQN |
|-----|-----|-----|--------|--------|-------|----------|---------|-----|
| 1   | 0   | ∞   | 5000   | 0.02   | 48%   | -18R     | 22d     | 1.2 |
| 2   | 30  | 300 | 4800   | 0.03   | 49%   | -17R     | 21d     | 1.3 |
| ... | ... | ... | ...    | ...    | ...   | ...      | ...     | ... |
```

**Impact-Analyse**:
- Wie viele Trades gefiltert? (% Reduktion)
- Win Rate der gefilterten Trades? (sind es wirklich schlechte?)
- Duration Distribution Änderung?

**Ergebnis Phase 1A**: Beste Range identifizieren (z.B. "80-250 scheint am besten")

---

#### **Phase 1B: Feine Schritte (25 Tests um beste Range)**

Beispiel: Phase 1A ergab "80-250 ist am besten"

**Jetzt**: 25 Schritte um diese Range testen

**Min Gap - 13 Schritte**:
```
Min 40, 50, 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120 Pips
```

**Max Gap - 12 Schritte**:
```
Max 180, 200, 220, 230, 240, 250, 260, 270, 280, 300, 320, 350 Pips
```

**Test-Runs** (Beispiel: Grid um 80-250):
```
Beste Min bei Max=250 fixed:
Test Min 60-120 in 10er-Schritten (7 Tests)

Beste Max bei Min=80 fixed:
Test Max 200-300 in 20er-Schritten (6 Tests)

Kombinationen um beste Min+Max:
Test beste Min ± 10 mit beste Max ± 20 (4-6 Tests)

Total: ~18-20 Tests
```

**Alternative (noch feiner)**: 
- Vollständiges Grid 13x12 = 156 Kombinationen (nur wenn nötig!)
- Aber: Rechenzeit! Pro HTF ~1h = 156h = 6.5 Tage pro HTF!

**Empfehlung**: 
- Erst Sequential (18-20 Tests)
- Wenn klar → fertig
- Wenn unklar → vollständiges Grid nur um besten Bereich

**Ergebnis Phase 1B**: Optimale Gap Size Range gefunden (z.B. "Min 85, Max 240")

---

### Walk-Forward Validation

**Setup**: 5y IS / 1y OOS rolling

**Prozedur**:
```
Windows:
2005-2009 IS → 2010 OOS
2006-2010 IS → 2011 OOS
2007-2011 IS → 2012 OOS
...
2018-2022 IS → 2023 OOS
2019-2023 IS → 2024 OOS

Total: 14 Windows (2010-2024)
```

**In jedem IS Window**:
- Nehme optimale Gap Range aus Phase 1B
- Teste auf IS: Performance?
- Teste auf OOS: Performance?

**Aggregierte Metriken**:
```
OOS Expectancy:
- Median: 0.08R
- Mean: 0.09R
- Std Dev: 0.03R
- Min: 0.02R (Window 5)
- Max: 0.15R (Window 11)

OOS Win Rate:
- Median: 49%
- Range: 45%-53%

OOS Max DD:
- Median: -12R
- Max: -18R (Window 3)
```

**Bewertung**:
- ✅ **Robust**: Median Exp > 0, kleine Std Dev, keine negativen Windows
- ⚠️ **Unsicher**: Große Varianz, negative Windows, Exp nahe 0
- ❌ **Overfit**: IS gut, OOS schlecht

**Ergebnis**: Gap Size Filter validiert und finalisiert!

---

### Output Dokumentation

**File**: `Gap_Size_Filter_Results.md`

```markdown
# Test 1: Gap Size Filter Results

## Phase 1A: Grobe Ranges
Getestet: 8 Ranges (No Filter bis Very Tight)
Beste Range: 80-250 Pips
Grund: Höchste Expectancy (0.08R), beste Balance Trade Count vs Quality

Gefilterte Trades: 18% (von 5000 → 4100)
Impact: Win Rate +2%, Avg Duration -5 Tage, Max DD -3R

## Phase 1B: Feine Optimierung
Getestet: 18 Kombinationen um 80-250
Optimale Range: Min 85 Pips, Max 240 Pips

## Walk-Forward Validation
14 Windows (2010-2024)
OOS Median Expectancy: 0.08R (stabil)
OOS Win Rate: 48-50% (konsistent)
Bewertung: ✅ ROBUST

## Finale Einstellung
MIN_GAP = 85 Pips
MAX_GAP = 240 Pips

Für alle HTFs (W, 3D, M) gleich.
```

---

## TEST 2: GAP VERSATZ FILTER 🔴

### Zweck
Filter Pivots mit zu starkem Versatz (K1 Close - K2 Open >> Gap)

### Setup
- **Mit Gap Size Filter** aus Test 1!
- HTFs: W, 3D, M einzeln
- Timeframe: 2010-2024

### Versatz Ratio Definition
```python
Versatz = abs(Close_K1 - Open_K2) / Gap

Interpretation:
0.0 = Bodies berühren sich fast (kein Versatz)
0.5 = Moderater Versatz
1.0 = Near liegt auf Pivot (bei Bullish)
1.5 = Near liegt über Pivot
2.0 = Sehr starker Versatz
```

### Test-Runs
```
Run 1: NO FILTER (Baseline)
       Max Versatz: unlimited

Run 2: Max Versatz 2.0
Run 3: Max Versatz 1.5
Run 4: Max Versatz 1.0
Run 5: Max Versatz 0.5
Run 6: Max Versatz 0.3
```

**Metriken vergleichen**: Gleiche wie Test 1

### Walk-Forward
**NEIN** - erst grob beste Range finden

**Wenn klarer Winner** (z.B. "Max 1.5 ist klar besser"):
→ Dann Walk-Forward zur Validierung

**Wenn unklar** (mehrere ähnlich):
→ Konservativer Wert wählen (z.B. 1.5 statt 2.0)

### Erwartung
- Zu hoher Versatz (>1.5): Geometrisch komisch, schlechtere Performance?
- Optimaler Versatz: 0.5-1.5?
- Zu strenger Filter (<0.5): Zu viele gute Trades gefiltert?

---

## TEST 3: WICK ASYMMETRIE FILTER 🟡

### Zweck
Nur Pivots mit klarer Wick-Hierarchie (Extreme deutlich länger als Near)

### Setup
- Mit Gap Size + Versatz Filter!
- HTFs: W, 3D, M einzeln

### Test-Runs
```
Run 1: NO FILTER (current)
       Min Wick Diff: 0% von Gap

Run 2: Min Wick Diff 10%
Run 3: Min Wick Diff 20%
Run 4: Min Wick Diff 30%
Run 5: Min Wick Diff 40%
```

**Bedeutung**:
- 10%: Leichter Filter (Wick Diff muss mind. 10% von Gap sein)
- 30%: Strenger Filter (nur sehr asymmetrische Pivots)

### Walk-Forward
**NEIN** - einfache Metrik, erst grob finden

---

## TEST 4: DOJI FILTER 🟡

### Setup
- Mit allen Filtern aus Test 1-3!

### Test-Runs
```
Run 1: 0% (no filter)
Run 2: 5% (current default)
Run 3: 10% (strenger)
Run 4: 15% (sehr streng)
```

**Erwartung**: 5% ist wahrscheinlich optimal (current default)

### Walk-Forward
**NEIN**

---

## PHASE 3B: ENTRY & REFINEMENT

---

## TEST 5: ENTRY CONFIRMATION TYPE 🔴

### Zweck
Wie wird Entry bestätigt? Touch vs Close?

### Setup
- Mit **allen Filtern aus Phase 3A**!
- HTFs: W, 3D, M einzeln

### Test-Runs
```
Run 1: direct_touch (current)
       Entry sofort bei Touch

Run 2: 1h_close
       Entry erst bei 1H Close jenseits Entry-Level
       Wenn Close schlecht → Verfeinerung löschen

Run 3: 4h_close
       Entry erst bei 4H Close jenseits Entry-Level
       Stärkste Bestätigung
```

### Erwartung
- direct_touch: Mehr Trades, frühere Entries, mehr Fakeouts
- 1h_close: Weniger Trades (-20-30%), bessere Win Rate (+3-5%), bessere Expectancy?
- 4h_close: Noch weniger Trades (-40-50%), beste Win Rate (+5-8%)?

### Walk-Forward
**JA** - Kritische Regel!

14 Windows → OOS Performance vergleichen

### Entscheidung
Beste Entry Type basierend auf:
1. OOS Expectancy
2. Trade Count (nicht zu wenig!)
3. Win Rate
4. Max DD

---

## TEST 6: REFINEMENT TIMEFRAMES 🟡

### Phase 6A: Einzelne TFs testen

### Setup
- Mit Entry Type aus Test 5!

### Test-Runs (Einzeln)
```
Run 1: H1 only
Run 2: H4 only
Run 3: D only
Run 4: 3D only
Run 5: W only (max TF)
```

**Metriken**: Pro TF → Trade Count, Expectancy, Win Rate

### Phase 6B: Beste TFs kombinieren

**Beispiel**: H4 und D waren beste einzeln

**Test-Runs**:
```
Run 6: H4 + D
Run 7: H4 + D + 3D
Run 8: D + 3D + W
...
```

### Walk-Forward
**JA** - Bei finaler Kombination!

---

## TEST 7: REFINEMENT MAX SIZE 🟡

### Setup
- Mit besten Ref TFs aus Test 6!

### Test-Runs
```
Run 1: 10% (sehr streng)
Run 2: 15%
Run 3: 20% (current)
Run 4: 25%
Run 5: 30% (locker)
```

### Walk-Forward
**NEIN**

---

## PHASE 3C: RISK MANAGEMENT

---

## TEST 8: MINIMUM RR 🔴

### Setup
- Mit allen Settings aus Phase 3A + 3B!

### Test-Runs
```
Run 1: 1.0 (current)
Run 2: 1.1
Run 3: 1.2
Run 4: 1.5
```

### Erwartung
- Höhere Min RR: Weniger Trades, bessere Quality?

### Walk-Forward
**JA**

---

## TEST 9: SL MINIMUM DISTANCE 🔴

### Setup
- Mit Min RR aus Test 8!

### Test-Runs
```
Run 1: 40 Pips
Run 2: 50 Pips
Run 3: 60 Pips (current)
Run 4: 70 Pips
Run 5: 80 Pips
Run 6: 100 Pips
```

### Walk-Forward
**JA**

---

## TEST 10: TP FIB LEVEL 🟡

### Setup
- Mit SL Distance aus Test 9!

### Test-Runs
```
Run 1: Fib -0.618 (konservativ)
Run 2: Fib -1.0 (current)
Run 3: Fib -1.5 (aggressiv)
Run 4: Fib -2.0 (sehr aggressiv)
```

### Walk-Forward
**JA** - TP beeinflusst Win Rate stark!

---

## TEST 11: MAX RR 🟡

### Setup
- Mit TP Level aus Test 10!

### Test-Runs
```
Run 1: 1.5 (current)
Run 2: 2.0
Run 3: 2.5
Run 4: 3.0 (unlimited)
```

### Walk-Forward
**NEIN** - Sekundär

---

## PHASE 3D: FINAL CROSS-CHECK ✅

---

## TEST 12: WALK-FORWARD VALIDATION (ALLE PARAMETER)

### Zweck
Finale Validierung: Alle optimierten Parameter zusammen testen

### Setup
**ALLE** optimalen Parameter aus Test 1-11:
```python
# Beispiel-Config (hypothetisch!)
MIN_GAP = 85
MAX_GAP = 240
MAX_VERSATZ = 1.5
MIN_WICK_DIFF = 20
DOJI_FILTER = 5
ENTRY_TYPE = "1h_close"
REF_TFS = ["H4", "D", "3D"]
REF_MAX_SIZE = 20
MIN_RR = 1.1
SL_MIN_PIPS = 60
TP_FIB = -1.0
MAX_RR = 1.5
```

### Walk-Forward (14 Windows)

**In jedem IS Window**:
1. Optimiere Top 3 Parameter-Sets (kleine Variationen um beste Settings)
2. Teste auf korrespondierendem OOS

**Beispiel IS Variations**:
```
Set 1: Exact optimale Settings
Set 2: Min Gap +5, Max Gap -10
Set 3: Min RR 1.0 statt 1.1
```

### Aggregierte OOS Performance

**Metriken**:
```
OOS Expectancy (Median): 0.12R
OOS Win Rate (Median): 51%
OOS Max DD (Median): -9R
OOS SQN (Median): 1.8

Stability:
- Positive in 13/14 Windows (93%)
- Std Dev: 0.04R (niedrig = gut)
- Worst Window: 0.01R (Window 7)
- Best Window: 0.22R (Window 11)
```

### Bewertung

✅ **ROBUST & READY**:
- OOS Median Exp > 0.10R
- Positive in >90% Windows
- Kleine Std Dev (<0.05R)
- Max DD < 10R
- SQN > 1.6

⚠️ **UNSICHER**:
- OOS Median Exp 0.05-0.10R
- Positive in 70-90% Windows
- Moderate Std Dev (0.05-0.10R)
→ Mehr Daten sammeln oder Parameter adjustieren

❌ **OVERFIT / NICHT BEREIT**:
- OOS Median Exp < 0.05R
- Negative Windows
- Große Varianz
→ Zurück zu Test X, Parameter überdenken

---

## RECHENZEIT-SCHÄTZUNG

### Pro Test (ohne Walk-Forward)
- W Backtest: ~30-45 min
- 3D Backtest: ~30-45 min
- M Backtest: ~20-30 min
- **Total pro Run**: ~1.5-2h

### Pro Test (mit Walk-Forward)
- 14 Windows × 3 HTFs × 1.5h = ~63h
- **Mit Parallelisierung** (3 HTFs parallel): ~21h

### Gesamte Phase 3 (geschätzt)

**Phase 3A** (Filter):
- Test 1: Gap Size (25 Runs × 2h) = 50h + WF (21h) = **71h**
- Test 2: Versatz (6 Runs × 2h) = 12h (kein WF) = **12h**
- Test 3: Wick (5 Runs × 2h) = 10h (kein WF) = **10h**
- Test 4: Doji (4 Runs × 2h) = 8h (kein WF) = **8h**

**Phase 3B** (Entry):
- Test 5: Entry Type (3 Runs × 2h) = 6h + WF (21h) = **27h**
- Test 6: Ref TFs (10 Runs × 2h) = 20h + WF (21h) = **41h**
- Test 7: Ref Size (5 Runs × 2h) = 10h (kein WF) = **10h**

**Phase 3C** (Risk):
- Test 8: Min RR (4 Runs × 2h) = 8h + WF (21h) = **29h**
- Test 9: SL Distance (6 Runs × 2h) = 12h + WF (21h) = **33h**
- Test 10: TP Level (4 Runs × 2h) = 8h + WF (21h) = **29h**
- Test 11: Max RR (4 Runs × 2h) = 8h (kein WF) = **8h**

**Phase 3D**:
- Test 12: Final Cross-Check (WF only) = **21h**

**TOTAL**: ~299h ≈ **12.5 Tage continuous runtime**

**Mit Parallelisierung** (z.B. 4 Cores):
- ~75h ≈ **3 Tage**

---

## DOKUMENTATIONS-TEMPLATE

### Pro Test

**File**: `Test_X_[Name]_Results.md`

```markdown
# Test X: [Variable Name]

## Setup
- HTF: W, 3D, M
- Timeframe: 2010-2024
- Config: [vorherige optimale Settings]

## Test-Runs
| Run | Setting | Trades | Exp(R) | WR(%) | MaxDD(R) | Avg Dur | SQN |
|-----|---------|--------|--------|-------|----------|---------|-----|
| 1   | ...     | 4100   | 0.08   | 49%   | -12R     | 18d     | 1.6 |
| 2   | ...     | 3900   | 0.10   | 51%   | -11R     | 17d     | 1.7 |
| ... | ...     | ...    | ...    | ...   | ...      | ...     | ... |

## Impact-Analyse
- Gefilterte Trades: 15% (von 4100 → 3485)
- Win Rate Änderung: +2% (49% → 51%)
- Expectancy Änderung: +0.02R (0.08R → 0.10R)
- Duration Änderung: -1 Tag (18d → 17d)
- Max DD Änderung: -1R (-12R → -11R)

Gefilterte Trades Performance:
- Separate Analyse der entfernten Trades
- Win Rate: 42% (deutlich schlechter als kept 51%)
- Expectancy: -0.05R (negativ!)
→ Filter ist sinnvoll!

## Walk-Forward (wenn applicable)
- 14 Windows
- OOS Median Exp: 0.09R (stabil)
- OOS Win Rate: 50-52% (konsistent)
- Negative Windows: 1/14 (7%)

Bewertung: ✅ ROBUST

## Entscheidung
**Gewählte Einstellung**: [Setting X]

**Begründung**:
- Beste Balance zwischen Trade Count und Quality
- OOS Performance stabil
- Logisch sinnvoll (nicht nur statistisch)
- Robustheit über alle HTFs

## Nächster Schritt
→ Test X+1 mit dieser neuen Einstellung
```

---

## OVERFITTING CHECKLISTE

Vor jedem Test-Abschluss prüfen:

### 1. Parameter-Anzahl
- ✅ Nur 1 Variable optimiert
- ❌ Mehrere gleichzeitig

### 2. Trade Count
- ✅ Genug Trades (>200 pro HTF)
- ⚠️ Weniger Trades, aber bessere Quality?
- ❌ Zu wenig Trades (<100)

### 3. Logische Plausibilität
- ✅ Parameter macht inhaltlich Sinn
- ❌ Nur statistischer Zufall

### 4. Robustheit über Pairs
- ✅ Profitabel über viele Pairs (>60%)
- ⚠️ Nur 2-3 Pairs tragen Performance
- ❌ 1 Pair dominiert

### 5. Cliff-Effekte
- ✅ Smooth Performance-Kurve (Parameter ändern = kleine Änderung)
- ❌ Cliff (Parameter 59→60 = 50% Performance-Drop)

### 6. OOS Performance
- ✅ OOS ähnlich wie IS (Diff <20%)
- ⚠️ OOS schlechter aber positiv (Diff 20-40%)
- ❌ OOS negativ oder sehr verschieden (Diff >50%)

### 7. Stabilität über Zeit
- ✅ Walk-Forward: >90% positive Windows
- ⚠️ Walk-Forward: 70-90% positive
- ❌ Walk-Forward: <70% positive

### 8. Vergleich mit Baseline
- ✅ Deutliche Verbesserung vs Baseline (>20%)
- ⚠️ Moderate Verbesserung (10-20%)
- ❌ Marginale Verbesserung (<10%) → evtl. Noise

---

## FINALE PHASE 4: COMBINED PORTFOLIO

**Nach Phase 3D abgeschlossen**:

### Test 13: HTF Combinations
- 3D + W
- 3D + M
- W + M
- 3D + W + M (alle)

Mit Deduplicate Logic:
- 1 Trade pro Pivot (wenn mehrere HTFs gleichen Pivot erkennen)
- Priorität: M > W > 3D

### Test 14: Portfolio Constraints
- Max Concurrent Trades: 4, 5, 6, 8, 10
- Max per Pair: 1, 2
- Correlation Filter

Walk-Forward: **JA** (finales Portfolio-Setup!)

---

*Last Updated: 2025-01-04*