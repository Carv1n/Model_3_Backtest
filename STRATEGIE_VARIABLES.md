# Model 3 - Strategie Variablen (Konsolidiert)

**Stand**: 2025-01-04  
**Zweck**: Alle test-relevanten Variablen für Backtesting & Optimierung

---

## ⚠️ OVERFITTING-WARNUNG

### Grundprinzipien
- **NICHT**: Grid Search (alle Kombinationen → Overfit!)
- **SONDERN**: Sequential Optimization (eine Variable nach der anderen)

### Kriterien für robuste Optimierung
- ✅ Max. 4-6 freie Parameter pro Test-Phase
- ✅ Walk-Forward Testing (5y IS / 1y OOS, ~14 Windows)
- ✅ Parameter müssen logisch sinnvoll sein (nicht nur statistisch)
- ✅ Robustheit über allen Pairs prüfen (>60% profitabel)
- ✅ Keine Cliff-Effekte (smooth Performance-Kurve)
- ✅ Trade Count beachten (>200 pro HTF)
- ✅ OOS Performance positiv & stabil

---

## 📊 VARIABLE KATEGORIEN

### TECHNISCHE VARIABLEN (Phase 3 - JETZT)
Beziehen sich auf Pivot-Qualität & Trade-Eigenschaften:
- Optimierung PRO HTF einzeln (W, 3D, M)
- Unabhängig von Portfolio-Zusammensetzung
- Beispiele: Gap Size, Entry Type, SL/TP Levels

### PORTFOLIO VARIABLEN (Phase 4 - SPÄTER)
Beziehen sich auf Combined Portfolio Management:
- Erst NACH technischer Optimierung
- Beispiele: Max Concurrent Trades, HTF Combinations, Correlation

---

## 🔴 PHASE 1: HTF PIVOT CREATION (FIXED)

### 1.1 Pivot Position
**Status**: ✅ FIXED (nicht ändern)

**Aktuelle Regel**:
- Pivot = **Open K2** (Standard)
- Gap gemessen nach K2 Open (nicht Close)

**Alternative Strategien** (für spätere Tests):
- `close_k1` - Pivot = Close K1
- Nach **größter Gap** - Wähle Pivot mit größerer Gap
- Nach **kleinster Gap** - Wähle Pivot mit kleinerer Gap

**Test-Priorität**: 🔵 NIEDRIG - Nur wenn Standard nicht funktioniert

---

### 1.2 Gap Definition
**Status**: ✅ FIXED

**Aktuelle Regel**:
- Größter/kleinster Gap zwischen K1 und K2
- Kein Versatz-Minimum (Bodies können sich berühren)
- Wick Diff = Extreme - Near (längerer - kürzerer Wick)

---

## 🔴 PHASE 2: HTF TIMEFRAME SELECTION

### 2.1 Einzelne Timeframes
**Status**: ✅ Phase 2 abgeschlossen

**Getestet**:
- `W` only ✅ (aktuell)
- `3D` only ✅
- `M` only ✅

**Ergebnisse verfügbar**: W_trades.csv, 3D_trades.csv, M_trades.csv

---

### 2.2 Kombinierte Timeframes
**Status**: 🎯 Phase 4 (nach technischer Optimierung)

**Zu testen**:
- `3D + W`
- `3D + M`
- `W + M`
- `3D + W + M` (alle)

**Deduplicate Logic**:
- 1 Trade pro Pivot (wenn mehrere HTFs gleichen Pivot erkennen)
- Priorität: M > W > 3D

**Test-Priorität**: 🔴 HOCH - Bei Combined Tests

---

## 🎯 PHASE 3: TECHNISCHE OPTIMIERUNG

### 3.1 GAP SIZE FILTER 🔴 **PRIORITÄT 1 - START HERE!**

**Zweck**: Filter zu kleine (Noise) und zu große Gaps (lange Duration)

**Problem**:
- Hohe Gap (>200 Pips) → Lange Duration → schlecht tradebar
- Kleine Gap (<30 Pips) → Zu schnell TP/SL → schlechte Winrate

**Test-Ansatz**: 2-Phasen

#### Phase A - Grobe Ranges (6-8 Tests)
```
1. No Filter (0 - unlimited, Baseline)
2. Very Wide (30-300 Pips)
3. Wide (50-250 Pips)
4. Balanced 1 (50-200 Pips)
5. Balanced 2 (80-250 Pips)
6. Tight 1 (80-200 Pips)
7. Tight 2 (100-200 Pips)
8. Very Tight (100-150 Pips)
```

#### Phase B - Feine Schritte (18-20 Tests)
Nach bester Range aus Phase A:
```
Min Gap: 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120 Pips
Max Gap: 200, 220, 230, 240, 250, 260, 270, 280, 300 Pips
```

**Erwartung**: 
- Optimale Range ~50-250 Pips
- Filtert ~10-20% Trades
- Win Rate +2-3%
- Duration stabiler

**Walk-Forward**: ✅ **JA** (5y/1y rolling, 14 windows)

---

### 3.2 GAP VERSATZ FILTER 🎯 **PRIORITÄT 2**

**Zweck**: Filter Pivots mit zu starkem Versatz zwischen K1 und K2

**Definition**:
```python
Versatz Ratio = abs(Close K1 - Open K2) / Gap

Interpretation:
0.0 = Bodies berühren sich fast (kein Versatz)
0.5 = Moderater Versatz
1.0 = Near liegt auf Pivot (bei Bullish)
1.5 = Near liegt über Pivot
2.0 = Sehr starker Versatz
```

**Problem bei hohem Versatz**:
- Near kann ÜBER Pivot liegen (bei Bullish)
- Wick Diff kann größer als Gap werden
- Geometrisch problematisch

**Optionen**:
```
Max Versatz: 0.5, 1.0, 1.5, 2.0, unlimited
```

**Test-Runs**:
1. No Filter (unlimited) - Baseline
2. Max 2.0 (sehr locker)
3. Max 1.5 (locker)
4. Max 1.0 (streng)
5. Max 0.5 (sehr streng)

**Erwartung**: Optimum ~1.0-1.5

**Walk-Forward**: ❌ **NEIN** (erst grob testen)

---

### 3.3 WICK ASYMMETRIE FILTER 🎯 **PRIORITÄT 3**

**Zweck**: Nur Pivots mit klarer Wick-Hierarchie

**Definition**:
```python
Wick Diff % = (Extreme - Near) / Gap * 100

Beispiel:
Gap = 100 Pips
Extreme Wick = 80 Pips
Near Wick = 20 Pips
Wick Diff = 60 Pips = 60% von Gap
```

**Optionen**:
```
Min Wick Diff: 0% (no filter), 10%, 20%, 30%, 40% von Gap
```

**Test-Runs**:
1. 0% (kein Filter, current)
2. 10% (leichter Filter)
3. 20% (balanced)
4. 30% (streng)
5. 40% (sehr streng)

**Erwartung**: Optimum ~20-30%

**Walk-Forward**: ❌ **NEIN**

---

### 3.4 PIVOT BODY STRENGTH (Doji Filter) 🎯 **PRIORITÄT 4**

**Zweck**: Filter Doji-Kerzen (zu kleine Bodies)

**Current Default**: 5% (K1 und K2 Body >= 5% von Range)

**Optionen**:
```
Doji Filter: 0%, 5%, 10%, 15%
```

**Test-Runs**:
1. 0% (alle Kerzen erlaubt)
2. 5% (current default) ✅
3. 10% (strenger)
4. 15% (sehr streng)

**Erwartung**: 5% ist wahrscheinlich optimal

**Walk-Forward**: ❌ **NEIN**

---

### 3.5 ENTRY CONFIRMATION TYPE 🔴 **PRIORITÄT HOCH**

**Zweck**: Wie wird Entry bestätigt?

**Optionen**:

#### A) direct_touch (current default) ✅
```
- Entry sofort bei Touch des Entry-Levels
- Schnellste Entry, meiste Trades
- Höchstes Fakeout-Risiko
```

#### B) 1h_close
```
- Entry erst bei 1H CLOSE jenseits Entry-Level
- Wenn Close zurück im Gap → Verfeinerung löschen
- Mittlere Bestätigung
- Weniger Trades (-20-30%), bessere Win Rate (+3-5%)
```

#### C) 4h_close
```
- Entry erst bei 4H CLOSE jenseits Entry-Level
- Stärkste Bestätigung
- Noch weniger Trades (-40-50%), beste Win Rate (+5-8%)
```

**Erwartung**:
- direct_touch: Mehr Trades, mehr Fakeouts
- 1h_close: Balance zwischen Count und Quality
- 4h_close: Beste Quality, weniger Trades

**Walk-Forward**: ✅ **JA** (kritische Regel!)

---

## 🔵 PHASE 3: REFINEMENT VARIABLEN

### 4.1 REFINEMENT TIMEFRAMES 🎯 **PRIORITÄT 3**

**Zweck**: Welche Lower TFs für Verfeinerungen nutzen?

**Max TF für Refinements**: W (nicht M!)
- M → W, 3D, D, H4, H1
- W → 3D, D, H4, H1
- 3D → D, H4, H1

**Test-Ansatz**:

#### Phase A - Einzelne TFs
```
1. H1 only
2. H4 only
3. D only
4. 3D only
5. W only (bei M Pivots)
```

#### Phase B - Kombinationen
```
6. H1+H4 (intraday)
7. H4+D (daily+intraday)
8. D+H4+H1 (multi-level)
9. 3D+D+H4 (higher TFs)
10. W+3D+D+H4+H1 (alle) ✅ (current)
```

**Erwartung**: Optimum D+H4 oder D+H4+3D?

**Walk-Forward**: ✅ **JA** (bei finaler Kombination)

---

### 4.2 REFINEMENT MAX SIZE 🎯 **PRIORITÄT 4**

**Zweck**: Wie groß darf Verfeinerung sein relativ zum HTF Pivot?

**Current Default**: 20% (Wick Diff / HTF Gap)

**Optionen**:
```
Max Size: 10%, 15%, 20%, 25%, 30%
```

**Test-Runs**:
1. 10% (sehr streng)
2. 15%
3. 20% (current) ✅
4. 25%
5. 30% (locker)

**Erwartung**: Optimum 20-25%

**Walk-Forward**: ❌ **NEIN**

---

### 4.3 REFINEMENT VALIDATION ✅ **ERLEDIGT**

**Ergebnis**: **Near Touch ist besser!**
- Mehr Trades
- Bessere Win Rate (+1%)
- K2 Open zu streng

**Current Default**: ✅ **Near unberührt** (FINAL)

---

### 4.4 REFINEMENT PRIORITÄT 🎯 **PRIORITÄT LOW**

**Current Default**: Highest TF → Closest to Near ✅

**Alternative**: Always Closest to Near (ignore TF)

**Test-Priorität**: 🔵 NIEDRIG

---

### 4.5 WICK DIFF ENTRY STRATEGY 🟡 **PRIORITÄT MITTEL**

**Zweck**: Wann Wick Diff Entry nutzen vs Verfeinerung?

**Optionen**:
- **Immer Wick Diff** - Bei jedem HTF Pivot (wenn < 20%)
- **Nur unter 20%** - Wick Diff nur wenn klein genug ✅ (Standard)
- **Kombiniert** - Wick Diff + beste Verfeinerungen zusammen

**Test-Priorität**: 🟡 MITTEL - Nach Refinement TF Tests

---

## 🟢 PHASE 3: RISK MANAGEMENT

### 5.1 MINIMUM RR 🔴 **PRIORITÄT HOCH**

**Zweck**: Filter Trades mit zu niedrigem Risk-Reward

**Current Default**: 1.0 ✅

**Optionen**:
```
Min RR: 1.0, 1.1, 1.2, 1.5
```

**Test-Runs**:
1. 1.0 (current, alle Trades)
2. 1.1 (leichter Filter)
3. 1.2 (strenger)
4. 1.5 (sehr streng)

**Erwartung**: Optimum 1.1-1.2

**Walk-Forward**: ✅ **JA**

---

### 5.2 MAXIMUM RR 🟡 **PRIORITÄT MITTEL**

**Zweck**: Erweitere SL bei zu hohem RR

**Current Default**: 1.5 ✅ (wenn RR > 1.5 → SL erweitern)

**Regel**: Bei RR > Max → SL erweitern UND `rr = Max` setzen

**Optionen**:
```
Max RR: 1.5, 2.0, 2.5, 3.0
```

**Test-Runs**:
1. 1.5 (current, conservative) ✅
2. 2.0 (balanced)
3. 2.5 (locker)
4. 3.0 (sehr locker)

**Walk-Forward**: ❌ **NEIN**

---

### 5.3 SL MINIMUM DISTANCE 🟡 **PRIORITÄT MITTEL**

**Zweck**: Minimale SL Distanz in Pips

**Current Default**: 60 Pips ✅

**Optionen**:
```
Min SL: 40, 50, 60, 70, 80, 100 Pips
```

**Test-Runs**:
1. 40 Pips (kleine SLs)
2. 50 Pips
3. 60 Pips (current) ✅
4. 70 Pips
5. 80 Pips
6. 100 Pips (große SLs)

**Erwartung**: Optimum 60-80 Pips

**Walk-Forward**: ✅ **JA**

---

### 5.4 SL FIB LEVEL 🟡 **PRIORITÄT MITTEL**

**Zweck**: Fibonacci Extension für SL Platzierung

**Current Default**: Fib 1.1 ✅ (10% über Extreme)

**Regel**: `SL = Extreme + (Gap * (Fib - 1.0))`

**Optionen**:
```
SL Fib: 1.0, 1.1, 1.2, 1.5
```

**Test-Runs**:
1. 1.0 (direkt bei Extreme)
2. 1.1 (current, 10% Buffer) ✅
3. 1.2 (20% Buffer)
4. 1.5 (50% Buffer)

**Erwartung**: 1.1-1.2 optimal

**Walk-Forward**: ❌ **NEIN**

---

### 5.5 FIXER SL PRO PAIR ⚠️ **OVERFITTING RISIKO!**

**Zweck**: Pair-spezifische SL-Distanz

**⚠️ ACHTUNG**:
- Risiko: 28 Pairs = 28 freie Parameter!
- Nur nutzen wenn statistisch signifikant

**Empfehlung**: 
- Erst globale SL-Regeln optimieren
- Dann prüfen ob einzelne Pairs deutlich abweichen
- Nur bei klarem Grund (z.B. JPY pairs = höhere Volatilität)

**Test-Priorität**: 🔵 NIEDRIG - Viel später, mit Vorsicht

---

## 🟢 PHASE 3: TAKE PROFIT

### 6.1 TP FIB LEVEL 🟡 **PRIORITÄT MITTEL**

**Zweck**: Fibonacci Extension für TP Platzierung

**Current Default**: Fib -1.0 ✅ (Pivot + Gap Extension)

**Regel**: `TP = Pivot - (Gap * abs(Fib))`

**Optionen**:
```
TP Fib: -0.618, -1.0, -1.272, -1.5, -2.0, -2.5
```

**Test-Runs**:
1. -0.618 (konservativ, Golden Ratio)
2. -1.0 (current, symmetrisch) ✅
3. -1.5 (aggressiv)
4. -2.0 (sehr aggressiv)

**Erwartung**: Trade-off Win Rate vs Avg Win Size

**Walk-Forward**: ✅ **JA** (wichtig!)

---

### 6.2 MIN/MAX TP DISTANCE 🔵 **PRIORITÄT NIEDRIG**

**Zweck**: Limitiere TP auf Pips-Basis

**Current Default**:
- Min TP: 30 Pips
- Max TP: 300 Pips

**Optionen**:
```
Min TP: 50, 75, 100 Pips
Max TP: 200, 250, 300 Pips
```

**Erwartung**: Abhängig von Gap Size Filter

**Walk-Forward**: ❌ **NEIN**

---

## 🔵 PHASE 3: ADVANCED EXITS (EXPERIMENTELL)

### 7.1 PARTIAL TP 🔵 **PRIORITÄT LOW**

**Zweck**: Nimm Teil-Gewinne, lasse Rest laufen

**Optionen**:

#### A) 50% bei Fib -0.5
```
Wenn Preis Fib -0.5 erreicht:
- Close 50% Position
- Rest läuft zu TP (Fib -1.0)
- Move SL zu BE nach Partial TP
```

#### B) 50% bei 1R Profit
```
Wenn 1R Profit erreicht:
- Close 50%
- Rest läuft
- SL zu BE
```

**Walk-Forward**: ✅ **JA** (falls implementiert)

---

### 7.2 BREAKEVEN MOVE 🔵 **PRIORITÄT LOW**

**Zweck**: Move SL zu Entry (BE) nach gewissem Profit

**Optionen**:
- Bei Fib -0.5
- Bei 1R Profit
- Bei 50% TP Distanz erreicht

**Walk-Forward**: ✅ **JA** (falls implementiert)

---

### 7.3 TRAILING SL 🔵 **PRIORITÄT LOW**

**Zweck**: Trail SL hinter Preis nach

**Optionen**:

#### A) Nach Fib -0.5
```
Trail SL by Fib steps (-0.25, -0.5, -0.75)
```

#### B) Nach 1R
```
Trail SL by 0.5R steps
```

**Walk-Forward**: ✅ **JA** (falls implementiert)

---

## 🟢 PHASE 4: PORTFOLIO MANAGEMENT

### 8.1 RISK PER TRADE 🔵 **PRIORITÄT NIEDRIG**

**Zweck**: Wie viel % des Kapitals pro Trade riskieren?

**Current Default**: 1.0% ✅

**Optionen**:
```
Risk per Trade: 0.5%, 1.0%, 2.0%
```

**Test-Priorität**: 🔵 NIEDRIG - Portfolio-Level

---

### 8.2 MAX CONCURRENT TRADES 🔴 **PRIORITÄT HOCH - BEI COMBINED**

**Zweck**: Maximale Anzahl gleichzeitiger Trades

**Optionen**:
```
Max Concurrent: 4, 5, 6, 8, 10, unlimited
```

**⚠️ WICHTIG**: Erst bei Combined Portfolio Tests relevant!

**Current für Single-TF**: Unbegrenzt ✅

**Erwartung**: Optimum 5-8

**Walk-Forward**: ✅ **JA**

---

### 8.3 MAX CONCURRENT PER PAIR 🔴 **PRIORITÄT HOCH - BEI COMBINED**

**Zweck**: Max. Trades pro Pair gleichzeitig

**Optionen**:
```
Max per Pair: 1, 2, unlimited
```

**Empfehlung**: 1 (nur ein Trade pro Pair) ✅

**Walk-Forward**: ✅ **JA**

---

### 8.4 CORRELATION FILTER 🟡 **PRIORITÄT MITTEL - BEI COMBINED**

**Zweck**: Vermeide zu viele korrelierte Trades

**Optionen**:

#### A) Max Correlated Pairs
```
Max 2 Pairs mit Correlation > 0.7 gleichzeitig
Beispiel: EUR/USD + GBP/USD = 2 korrelierte EUR Trades
```

#### B) Currency Exposure
```
Max 4 Trades mit USD
Max 3 Trades mit EUR
Max 2 Trades mit JPY
```

**Walk-Forward**: ✅ **JA**

---

## ⚫ PHASE 5: EXPERIMENTELLE VARIABLEN

### 9.1 IMPULSIVE MOVE FILTER 🔵 **EXPERIMENTELL**

**Zweck**: Filtere Entries nach zu impulsivem Move

**Optionen**:

#### A) Move seit Valid Time
```
Max % Move zwischen Valid Time und Entry
Wenn > 5% → skip (zu impulsiv)
```

#### B) Entry Candle Size
```
Wenn Entry Candle Range > 2x ATR → skip
```

#### C) Speed of Approach
```
Anzahl Bars zwischen Valid Time und Entry Touch
Wenn < 5 Bars → zu schnell
```

---

### 9.2 TIME-OF-DAY FILTER 🔵 **OPTIONAL**

**Optionen**:
- London Session only (08:00-17:00 GMT)
- NY Session only (13:00-22:00 GMT)
- London + NY Overlap (13:00-17:00 GMT)
- All Sessions (current) ✅

**Erwartung**: Wahrscheinlich kein großer Effekt

---

### 9.3 DAY-OF-WEEK FILTER 🔵 **OPTIONAL**

**Optionen**:
- Skip Monday
- Skip Friday
- Tuesday-Thursday only
- All Days (current) ✅

**Erwartung**: Evtl. kleine Effekte

---

### 9.4 VOLATILITY (ATR) FILTER 🔵 **EXPERIMENTELL**

**Zweck**: Nur Trades in bestimmter Volatilitäts-Range

**Optionen**:
```
Min ATR: 0.5% Daily Range
Max ATR: 2.0% Daily Range
```

---

### 9.5 DURATION PREDICTION FILTER 🔵 **EXPERIMENTELL**

**Erkenntnis**: Gap Size korreliert mit Duration
- Small Gap (50-100 Pips) → 3-10 Tage
- Medium Gap (100-200 Pips) → 10-30 Tage
- Large Gap (200-300 Pips) → 30-60 Tage

**Optionen**:
```
Max Expected Duration: 30, 45, 60 Tage
Skip wenn predicted Duration > Max
```

---

### 9.6 ENTRY TIMING FILTER 🔵 **EXPERIMENTELL**

**Zweck**: Setup kann "veralten"

**Optionen**:

#### A) Max Time Valid → Entry
```
Wenn > 30 Tage nach Valid Time noch kein Entry → skip
```

#### B) Max Time Gap Touch → Entry
```
Wenn > 14 Tage nach Gap Touch noch kein Entry → skip
```

#### C) Speed Filter
```
Wenn Entry < 3 Bars nach Valid Time → zu schnell
```

---

## 🎯 OPTIMIERUNGS-ZIELE

### Primäre Ziele
- ✅ **Profit Expectancy**: 0.1 - 0.3 R/Trade (ambitioniert)
- ✅ **Win Rate**: 45-50% (realistisch)
- ✅ **Max Duration**: 95% der Trades unter 60 Tagen
- ✅ **Min Duration**: 2-3 Tage (kein TP/SL innerhalb 1-2 Tagen)
- ✅ **SQN**: > 1.6 (gut), > 2.0 (sehr gut)

### Sekundäre Ziele
- **Profit Factor**: > 1.3
- **Max Drawdown**: < 10R (bei 1% Risk/Trade)
- **Sharpe Ratio**: > 1.0
- **Trade Count**: > 200 pro HTF

### Wichtig für Funded Accounts
- Consistent Profitability (über Monate)
- Controlled Drawdown (< 5-10% Max DD)
- Genug Trades (> 200)
- Stabile OOS Performance

---

## 📋 TEST-REIHENFOLGE (EMPFOHLEN)

### ✅ Phase 1: Baseline (ABGESCHLOSSEN)
- W only, direct_touch, Standard-Settings
- Status: Bereit für Re-Run nach Bug Fixes

### ✅ Phase 2: HTF Selection (ABGESCHLOSSEN)
- 3D, W, M einzeln getestet
- CSV Trades vorhanden: W_trades.csv, 3D_trades.csv, M_trades.csv

### 🎯 Phase 3: Technische Optimierung (JETZT)

#### 3.1 Gap Quality Filters (START HERE!)
1. **Gap Size Filter** (Priorität 1)
   - Phase A: Grobe Ranges (6-8 Tests)
   - Phase B: Feine Schritte (18-20 Tests)
   - Walk-Forward: JA

2. **Gap Versatz Filter** (Priorität 2)
   - 5 Tests (0, 0.5, 1.0, 1.5, 2.0)
   - Walk-Forward: NEIN

3. **Wick Asymmetrie Filter** (Priorität 3)
   - 5 Tests (0%, 10%, 20%, 30%, 40%)
   - Walk-Forward: NEIN

4. **Doji Filter** (Priorität 4)
   - 4 Tests (0%, 5%, 10%, 15%)
   - Walk-Forward: NEIN

#### 3.2 Entry & Refinements
5. **Entry Confirmation** (Priorität Hoch)
   - 3 Tests (direct_touch, 1h_close, 4h_close)
   - Walk-Forward: JA

6. **Refinement Timeframes** (Priorität 3)
   - Phase A: Einzelne TFs (5 Tests)
   - Phase B: Kombinationen (5 Tests)
   - Walk-Forward: JA (finale Kombination)

7. **Refinement Max Size** (Priorität 4)
   - 5 Tests (10%, 15%, 20%, 25%, 30%)
   - Walk-Forward: NEIN

#### 3.3 Risk Management
8. **Min RR** (Priorität Hoch)
   - 4 Tests (1.0, 1.1, 1.2, 1.5)
   - Walk-Forward: JA

9. **SL Distance** (Priorität Mittel)
   - 6 Tests (40, 50, 60, 70, 80, 100 Pips)
   - Walk-Forward: JA

10. **Max RR** (Priorität Mittel)
    - 4 Tests (1.5, 2.0, 2.5, 3.0)
    - Walk-Forward: NEIN

11. **SL Fib Level** (Priorität Mittel)
    - 4 Tests (1.0, 1.1, 1.2, 1.5)
    - Walk-Forward: NEIN

#### 3.4 Take Profit
12. **TP Fib Level** (Priorität Mittel)
    - 5 Tests (-0.618, -1.0, -1.5, -2.0, -2.5)
    - Walk-Forward: JA

### 🟢 Phase 4: Combined Portfolio
13. **HTF Combinations**
    - 7 Tests (3D, W, M, 3D+W, 3D+M, W+M, All)
    - Walk-Forward: JA

14. **Portfolio Constraints**
    - Max Concurrent Trades (5 Tests)
    - Max per Pair (3 Tests)
    - Correlation Filter (optional)
    - Walk-Forward: JA

### 🔵 Phase 5: Fine-Tuning & Experimentell
15. **Advanced Exits**
    - Partial TP
    - Breakeven Move
    - Trailing SL

16. **Experimentelle Filter**
    - Impulsive Move
    - Time/Day Filters
    - ATR Filter
    - Duration Prediction

---

## 📊 WALK-FORWARD TESTING

### Setup (Empfohlen)
```
IS (In-Sample): 5 Jahre
OOS (Out-of-Sample): 1 Jahr
Step: 1 Jahr
Windows: ~14 (2005-2024)
```

### Prozedur
1. Optimiere Parameter auf IS
2. Wähle Top 3 Parameter