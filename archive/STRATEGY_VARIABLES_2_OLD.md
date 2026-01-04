# Model 3 - Strategy Variables

**Stand**: 2025-01-04  
**Zweck**: Alle test-relevanten Variablen systematisch dokumentiert

---

## ⚠️ OVERFITTING-WARNUNG

**NICHT**: Grid Search (alle Kombinationen → Overfit!)  
**SONDERN**: Sequential Optimization (eine Variable nach der anderen)

**Kriterien für robuste Optimierung**:
- ✅ Max 1 Variable pro Test
- ✅ Walk-Forward bei kritischen Parametern
- ✅ OOS Performance positiv & stabil
- ✅ Parameter müssen logisch Sinn machen
- ✅ Robustheit über Pairs (>60% profitabel)
- ✅ Keine Cliff-Effekte (smooth Performance-Kurve)
- ✅ Trade Count beachten (>200 pro HTF)

---

## 📊 VARIABLE KATEGORIEN

### Unterscheidung TECHNISCH vs PORTFOLIO

**TECHNISCHE VARIABLEN** (Phase 3 - JETZT):
- Beziehen sich auf Pivot-Qualität & Trade-Eigenschaften
- Optimierung PRO HTF einzeln (W, 3D, M)
- Unabhängig von Portfolio-Zusammensetzung
- Beispiele: Gap Size, Entry Type, SL/TP Levels

**PORTFOLIO VARIABLEN** (Phase 4 - SPÄTER):
- Beziehen sich auf Combined Portfolio Management
- Erst NACH technischer Optimierung
- Beispiele: Max Concurrent Trades, HTF Combinations, Correlation

---

## 🔴 TECHNISCHE VARIABLEN (Phase 3)

### 1. HTF PIVOT CREATION

**Status**: ✅ FIXED (nicht ändern)

**Regeln**:
- Gap nach K2 OPEN (nicht Close)
- Größter/kleinster Gap zwischen K1 und K2
- Kein Versatz (Standard): Bodies können sich berühren
- Wick Diff = Extreme - Near (längerer - kürzerer Wick)

---

### 2. GAP SIZE FILTER 🎯 **PRIORITÄT 1 - START HERE!**

**Zweck**: Filter zu kleine (Noise, schnelle TP/SL) und zu große Gaps (lange Duration, schlecht tradebar)

**Problem**:
- Hohe Gap (>200 Pips?) → Lange Duration → schlecht tradebar
- Kleine Gap (<30 Pips?) → Zu schnell TP/SL → schlechte Winrate

**Optionen**:
```
Min Gap: 30, 40, 50, 60, 70, 80, 90, 100, 110, 120 Pips
Max Gap: 150, 180, 200, 220, 240, 250, 260, 280, 300 Pips
```

**Test-Ansatz**: 2-Phasen
1. **Phase A - Grobe Ranges** (6-8 Tests):
   - No Filter (0 - unlimited, Baseline)
   - Very Wide (30-300)
   - Wide (50-250)
   - Balanced 1 (50-200)
   - Balanced 2 (80-250)
   - Tight 1 (80-200)
   - Tight 2 (100-200)
   - Very Tight (100-150)

2. **Phase B - Feine Schritte** (25 Tests um beste Range):
   - Beste Range aus Phase A identifizieren (z.B. "80-250")
   - Min Gap: 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120
   - Max Gap: 200, 220, 230, 240, 250, 260, 270, 280, 300
   - Kombinationen um beste Range (~18-20 Tests)

**Erwartung**: 
- Optimale Range ~50-250 Pips? 
- Filtert ~10-20% Trades (zu klein/groß)
- Win Rate +2-3%
- Duration stabiler

**Varianten**:
- Overall (alle Pairs gleich) - **ZUERST!**
- Pro TF unterschiedlich (M > W > 3D)? - Später
- Pro Pair? - Nur wenn sinnvoll, Overfitting-Risiko!
- ATR-normalisiert? - Experimentell, erstmal absolute Pips

**Walk-Forward**: ✅ **JA** (5y/1y rolling, 14 windows)

---

### 3. GAP VERSATZ FILTER 🎯 **PRIORITÄT 2**

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
- Wick Diff kann größer als Gap selbst werden
- Geometrisch "komisch"
- Evtl. schlechtere Performance?

**Optionen**:
```
Max Versatz: 0.5, 1.0, 1.5, 2.0, unlimited
```

**Test-Runs**:
1. No Filter (unlimited)
2. Max 2.0 (sehr locker)
3. Max 1.5 (locker)
4. Max 1.0 (streng)
5. Max 0.5 (sehr streng)

**Erwartung**: 
- Optimum ~1.0-1.5?
- Zu streng (<1.0): Zu viele Trades gefiltert
- Zu locker (>2.0): Geometrisch problematische Pivots

**Walk-Forward**: ❌ **NEIN** (erst grob beste Range finden, dann evtl. Walk-Forward)

---

### 4. WICK ASYMMETRIE FILTER 🎯 **PRIORITÄT 3**

**Zweck**: Nur Pivots mit klarer Wick-Hierarchie (Extreme deutlich länger als Near)

**Optionen**:
```
Min Wick Diff: 0% (no filter), 10%, 20%, 30%, 40% von Gap
```

**Definition**:
```python
Wick Diff % = (Extreme - Near) / Gap * 100

Beispiel:
Gap = 100 Pips
Extreme = 80 Pips (Wick)
Near = 20 Pips (Wick)
Wick Diff = 60 Pips = 60% von Gap
```

**Test-Runs**:
1. 0% (kein Filter, current)
2. 10% (leichter Filter)
3. 20% (balanced)
4. 30% (streng)
5. 40% (sehr streng)

**Erwartung**:
- Filtert symmetrische Pivots (beide Wicks gleich lang)
- Optimum ~20-30%?
- Zu streng (>40%): Zu viele Trades gefiltert

**Varianten**:
- Absolute Min Wick Diff in Pips statt %
- Combined mit Gap Size (große Gaps: Asymmetrie wichtiger?)

**Walk-Forward**: ❌ **NEIN**

---

### 5. PIVOT BODY STRENGTH (Doji Filter) 🎯 **PRIORITÄT 4**

**Zweck**: Filter Doji-Kerzen (zu kleine Bodies)

**Current Default**: 5% (K1 und K2 Body >= 5% von Range)

**Optionen**:
```
Doji Filter: 0% (no filter), 5%, 10%, 15%
```

**Test-Runs**:
1. 0% (alle Kerzen erlaubt)
2. 5% (current default)
3. 10% (strenger)
4. 15% (sehr streng)

**Erwartung**: 
- 5% ist wahrscheinlich optimal (current)
- Zu locker (0%): Dojis = schlechte Pivots
- Zu streng (>10%): Zu viele Trades gefiltert

**Zusätzliche Tests** (später):
- K2 Body wichtiger als K1? (nur K2 >= 10%?)
- Range Balance: K2/K1 Ratio (0.5-2.0 = balanced?)

**Walk-Forward**: ❌ **NEIN**

---

### 6. PIVOT TIMEFRAME 🎯 **PRIORITÄT HIGH**

**Status**: ✅ Phase 2 abgeschlossen (W, 3D, M Default getestet)

**Optionen**:
- W (Weekly)
- 3D (3-Day)
- M (Monthly)

**Nächster Schritt**: 
- Nach Gap Size Filter → Combined Tests (Phase 4)
- 3D+W, 3D+M, W+M, All (3D+W+M)

---

### 7. ENTRY CONFIRMATION TYPE 🎯 **PRIORITÄT 2-3**

**Zweck**: Wie wird Entry bestätigt? Touch vs Close?

**Optionen**:

**A) direct_touch** (current default):
```
Entry sofort bei Touch des Entry-Levels (Near)
Schnellste Entry, meiste Trades
Höchstes Fakeout-Risiko
```

**B) 1h_close**:
```
Entry erst bei 1H CLOSE jenseits Entry-Level
Wenn Close zurück im Gap → Verfeinerung löschen (kein Entry)
Mittlere Bestätigung
Weniger Trades (-20-30%?), bessere Win Rate (+3-5%?)
```

**C) 4h_close**:
```
Entry erst bei 4H CLOSE jenseits Entry-Level
Stärkste Bestätigung
Noch weniger Trades (-40-50%?), beste Win Rate (+5-8%?)
```

**Erwartung**:
- direct_touch: Mehr Trades, mehr Fakeouts
- 1h_close: Balance zwischen Count und Quality
- 4h_close: Beste Quality, aber weniger Trades

**Walk-Forward**: ✅ **JA** (kritische Regel!)

---

### 8. REFINEMENT TIMEFRAMES 🎯 **PRIORITÄT 3-4**

**Zweck**: Welche Lower TFs für Verfeinerungen nutzen?

**Current Default**: Alle verfügbaren (H1, H4, D, 3D, W je nach HTF)

**Max TF für Refinements**: W (nicht M!)
- M → W, 3D, D, H4, H1
- W → 3D, D, H4, H1
- 3D → D, H4, H1

**Test-Ansatz**:

**Phase A - Einzelne TFs**:
1. H1 only
2. H4 only
3. D only
4. 3D only
5. W only (bei M Pivots)

**Phase B - Kombinationen**:
6. H1+H4 (intraday)
7. H4+D (daily+intraday)
8. D+H4+H1 (multi-level, current)
9. 3D+D+H4 (higher TFs)
10. All available (current default)

**Erwartung**:
- Higher TF Refinements (W, 3D) evtl. besser?
- H1 evtl. zu viel Noise?
- Optimum: D+H4 oder D+H4+3D?

**Walk-Forward**: ✅ **JA** (bei finaler Kombination)

---

### 9. REFINEMENT MAX SIZE 🎯 **PRIORITÄT 4**

**Zweck**: Wie groß darf Verfeinerung sein relativ zum HTF Pivot?

**Current Default**: 20% (Wick Diff / HTF Gap)

**Optionen**:
```
Max Size: 10%, 15%, 20%, 25%, 30%
```

**Test-Runs**:
1. 10% (sehr streng, nur kleine Refinements)
2. 15%
3. 20% (current)
4. 25%
5. 30% (locker, größere Refinements erlaubt)

**Erwartung**:
- Zu streng (10%): Weniger Refinements, evtl. wichtige gefiltert
- Zu locker (30%): Refinements zu groß, überdecken HTF Pivot
- Optimum: 20-25%?

**Walk-Forward**: ❌ **NEIN**

---

### 10. REFINEMENT VALIDATION 🎯 **STATUS: ERLEDIGT** ✅

**Zweck**: Was darf nicht berührt werden zwischen Pivot Time und Valid Time?

**Getestet**: Near Touch vs K2 Open Touch

**Ergebnis**: **Near Touch ist besser!**
- Mehr Trades
- Bessere Win Rate (+1%)
- Weniger Max DD
- K2 Open zu streng (wird öfter berührt als Near)

**Current Default**: ✅ **Near unberührt** (FINAL)

---

### 11. REFINEMENT PRIORITÄT 🎯 **PRIORITÄT LOW**

**Current Default**: Highest TF → Closest to Near

**Alternative**: Always Closest to Near (ignore TF)

**Test**: Vergleich beide Varianten

**Walk-Forward**: ❌ **NEIN**

---

### 12. MINIMUM RR 🎯 **PRIORITÄT 2**

**Zweck**: Filter Trades mit zu niedrigem Risk-Reward

**Current Default**: 1.0

**Optionen**:
```
Min RR: 1.0, 1.1, 1.2, 1.5
```

**Test-Runs**:
1. 1.0 (current, alle Trades erlaubt)
2. 1.1 (leichter Filter)
3. 1.2 (strenger)
4. 1.5 (sehr streng)

**Erwartung**:
- Höhere Min RR: Weniger Trades, bessere Quality?
- Optimum: 1.1-1.2?
- Zu streng (1.5): Zu viele Trades gefiltert

**Walk-Forward**: ✅ **JA**

---

### 13. MAXIMUM RR 🎯 **PRIORITÄT 3**

**Zweck**: Erweitere SL bei zu hohem RR

**Current Default**: 1.5 (wenn RR > 1.5 → SL erweitern)

**Regel**: Bei RR > Max → SL erweitern UND `rr = Max` setzen

**Optionen**:
```
Max RR: 1.5, 2.0, 2.5, 3.0 (unlimited)
```

**Test-Runs**:
1. 1.5 (current, conservative)
2. 2.0 (balanced)
3. 2.5 (locker)
4. 3.0 (sehr locker / unlimited)

**Erwartung**:
- Niedrige Max RR (1.5): Größere SLs, weniger SL Hits?
- Höhere Max RR (3.0): Kleinere SLs, mehr Trades verworfen bei Min RR Check?

**Walk-Forward**: ❌ **NEIN** (sekundär)

---

### 14. SL MINIMUM DISTANCE 🎯 **PRIORITÄT 3**

**Zweck**: Minimale SL Distanz in Pips

**Current Default**: 60 Pips

**Optionen**:
```
Min SL: 40, 50, 60, 70, 80, 100 Pips
```

**Test-Runs**:
1. 40 Pips (kleine SLs erlaubt)
2. 50 Pips
3. 60 Pips (current)
4. 70 Pips
5. 80 Pips
6. 100 Pips (große SLs)

**Erwartung**:
- Zu klein (40 Pips): Zu viele SL Hits (Noise)
- Zu groß (100 Pips): Weniger Trades, bessere Hit Rate?
- Optimum: 60-80 Pips?

**Walk-Forward**: ✅ **JA**

---

### 15. SL FIB LEVEL 🎯 **PRIORITÄT 4**

**Zweck**: Fibonacci Extension für SL Platzierung

**Current Default**: Fib 1.1 (10% über Extreme)

**Optionen**:
```
SL Fib: 1.0, 1.1, 1.2, 1.5
```

**Regel**: `SL = Extreme + (Gap * (Fib - 1.0))`

**Test-Runs**:
1. 1.0 (SL direkt bei Extreme, kein Buffer)
2. 1.1 (current, 10% Buffer)
3. 1.2 (20% Buffer)
4. 1.5 (50% Buffer, sehr groß)

**Erwartung**:
- 1.0: Zu nah, viele SL Hits
- 1.1-1.2: Optimum (current wahrscheinlich gut)
- 1.5: Zu weit, zu große SLs

**Walk-Forward**: ❌ **NEIN**

---

### 16. TP FIB LEVEL 🎯 **PRIORITÄT 3**

**Zweck**: Fibonacci Extension für TP Platzierung

**Current Default**: Fib -1.0 (TP auf anderer Seite von Pivot, Gap-Distanz)

**Optionen**:
```
TP Fib: -0.618, -1.0, -1.272, -1.5, -2.0, -2.5
```

**Regel**: `TP = Pivot - (Gap * abs(Fib))`

**Test-Runs**:
1. -0.618 (konservativ, Golden Ratio)
2. -1.0 (current, symmetrisch zu Gap)
3. -1.5 (aggressiv)
4. -2.0 (sehr aggressiv)

**Erwartung**:
- -0.618: Höhere Win Rate, kleinere Gewinne
- -1.0: Balance (current)
- -2.0: Niedrigere Win Rate, größere Gewinne
- Trade-off: Win Rate vs Avg Win Size

**Walk-Forward**: ✅ **JA** (wichtig für Win Rate!)

---

### 17. TP/SL MINIMUM PIPS 🎯 **PRIORITÄT 4**

**Current Default**:
- Min TP: 30 Pips
- Max TP: 300 Pips
- Min SL: 40 Pips
- Max SL: 200 Pips

**Zweck**: Filtere extreme TP/SL Werte

**Test**: Evtl. später anpassen je nach Gap Size Filter Ergebnissen

**Walk-Forward**: ❌ **NEIN**

---

## 🔵 ADVANCED EXIT VARIABLEN (Phase 3+ / Experimentell)

### 18. PARTIAL TP 🎯 **PRIORITÄT LOW**

**Zweck**: Nimm Teil-Gewinne, lasse Rest laufen

**Optionen**:

**A) 50% bei Fib -0.5**:
```
Wenn Preis Fib -0.5 erreicht:
- Close 50% Position
- Rest läuft zu TP (Fib -1.0)
- Move SL zu BE nach Partial TP
```

**B) 50% bei 1R Profit**:
```
Wenn 1R Profit erreicht:
- Close 50%
- Rest läuft
- SL zu BE
```

**Walk-Forward**: ✅ **JA** (falls implementiert)

---

### 19. BREAKEVEN MOVE 🎯 **PRIORITÄT LOW**

**Zweck**: Move SL zu Entry (BE) nach gewissem Profit

**Optionen**:
- Bei Fib -0.5
- Bei 1R Profit
- Bei 50% TP Distanz erreicht

**Walk-Forward**: ✅ **JA** (falls implementiert)

---

### 20. TRAILING SL 🎯 **PRIORITÄT LOW**

**Zweck**: Trail SL hinter Preis nach

**Optionen**:

**A) Nach Fib -0.5**:
```
Trail SL by Fib steps (-0.25, -0.5, -0.75)
```

**B) Nach 1R**:
```
Trail SL by 0.5R steps
```

**Walk-Forward**: ✅ **JA** (falls implementiert)

---

## 🟢 PORTFOLIO VARIABLEN (Phase 4 - Combined Tests)

### 21. HTF COMBINATIONS 🎯 **NACH PHASE 3 ABGESCHLOSSEN**

**Zweck**: Kombiniere verschiedene HTF Pivots im Portfolio

**Optionen**:
- 3D only (single)
- W only (single)
- M only (single)
- 3D + W (combined)
- 3D + M (combined)
- W + M (combined)
- 3D + W + M (all, full portfolio)

**Deduplicate Logic**:
- 1 Trade pro Pivot (wenn mehrere HTFs gleichen Pivot erkennen)
- Priorität: M > W > 3D

**Walk-Forward**: ✅ **JA** (finales Portfolio Setup!)

---

### 22. MAX CONCURRENT TRADES 🎯 **BEI COMBINED**

**Zweck**: Maximale Anzahl gleichzeitiger Trades

**Optionen**:
```
Max Concurrent: 4, 5, 6, 8, 10, unlimited
```

**Erwartung**:
- Zu niedrig (4): Opportunity Cost (gute Setups verpasst)
- Zu hoch (unlimited): Risiko-Cluster, korrelierte Losses
- Optimum: 5-8?

**Walk-Forward**: ✅ **JA**

---

### 23. MAX CONCURRENT PER PAIR 🎯 **BEI COMBINED**

**Zweck**: Max Trades pro Pair gleichzeitig

**Optionen**:
```
Max per Pair: 1, 2, unlimited
```

**Empfehlung**: 1 (sonst mehrere Trades auf gleichem Pair = höheres Risiko)

**Walk-Forward**: ✅ **JA**

---

### 24. CORRELATION FILTER 🎯 **BEI COMBINED**

**Zweck**: Vermeide zu viele korrelierte Trades

**Optionen**:

**A) Max Correlated Pairs**:
```
Max 2 Pairs mit Correlation > 0.7 gleichzeitig
Beispiel: EUR/USD + GBP/USD = 2 korrelierte EUR Trades
```

**B) Currency Exposure**:
```
Max 4 Trades mit USD
Max 3 Trades mit EUR
Max 2 Trades mit JPY
```

**Walk-Forward**: ✅ **JA**

---

## ⚫ EXPERIMENTELLE VARIABLEN (Phase 5+)

### 25. IMPULSIVE MOVE FILTER 🎯 **SPÄTER**

**Zweck**: Filtere Entries nach zu impulsivem Move (schneller SL Risiko)

**Optionen**:

**A) Move seit Valid Time**:
```
Max % Move zwischen Valid Time und Entry
Wenn > 5% → skip (zu impulsiv)
```

**B) Entry Candle Size**:
```
Wenn Entry Candle Range > 2x ATR → skip (zu volatil)
```

**C) Speed of Approach**:
```
Anzahl Bars zwischen Valid Time und Entry Touch
Wenn < 5 Bars → zu schnell (Fakeout Risiko?)
```

---

### 26. TIME-OF-DAY FILTER 🎯 **OPTIONAL**

**Zweck**: Nur bestimmte Handelszeiten

**Optionen**:
- London Session only (08:00-17:00 GMT)
- NY Session only (13:00-22:00 GMT)
- London + NY Overlap (13:00-17:00 GMT)
- All Sessions (current)

**Erwartung**: Wahrscheinlich kein großer Effekt (keine SMC Strategie)

---

### 27. DAY-OF-WEEK FILTER 🎯 **OPTIONAL**

**Zweck**: Filtere bestimmte Wochentage

**Optionen**:
- Skip Monday (wenig Momentum?)
- Skip Friday (Close vor Weekend?)
- Tuesday-Thursday only
- All Days (current)

**Erwartung**: Evtl. kleine Effekte, aber wahrscheinlich nicht signifikant

---

### 28. VOLATILITY (ATR) FILTER 🎯 **EXPERIMENTELL**

**Zweck**: Nur Trades in bestimmter Volatilitäts-Range

**Optionen**:
```
Min ATR: 0.5% Daily Range
Max ATR: 2.0% Daily Range
```

**Zweck**: 
- Zu niedrige ATR: Range-bound Market
- Zu hohe ATR: Chaotischer Market

---

### 29. DURATION PREDICTION FILTER 🎯 **EXPERIMENTELL**

**Zweck**: Filter basierend auf erwarteter Trade Duration

**Erkenntnis**: Gap Size korreliert mit Duration
- Small Gap (50-100 Pips) → 3-10 Tage
- Medium Gap (100-200 Pips) → 10-30 Tage
- Large Gap (200-300 Pips) → 30-60 Tage

**Optionen**:
```
Max Expected Duration: 30 Tage, 45 Tage, 60 Tage
Skip wenn predicted Duration > Max
```

---

### 30. ENTRY TIMING FILTER 🎯 **EXPERIMENTELL**

**Zweck**: Setup kann "veralten"

**Optionen**:

**A) Max Time Valid → Entry**:
```
Wenn > 30 Tage nach Valid Time noch kein Entry → skip (Setup zu alt)
```

**B) Max Time Gap Touch → Entry**:
```
Wenn > 14 Tage nach Gap Touch noch kein Entry → skip
```

**C) Speed Filter**:
```
Wenn Entry < 3 Bars nach Valid Time → zu schnell (Fakeout?)
```

---

## 🎯 OPTIMIERUNGS-ZIELE

### Primary Metrics
- **Expectancy (R)**: Median > 0.10R (OOS)
- **Win Rate**: 45-55%
- **System Quality Number (SQN)**: > 1.6 (tradeable), > 2.5 (good)
- **Max Drawdown**: < 10R (relativ zu Expectancy)

### Secondary Metrics
- **Profit Factor**: > 1.3
- **Trade Count**: > 200 pro HTF (genug Daten)
- **Avg Duration**: 5-40 Tage (tradeable)
- **OOS Stability**: < 90% positive Windows (Walk-Forward)

### Risk Metrics
- **Max DD**: Absolut < 15R
- **Longest Losing Streak**: < 10 Trades
- **Drawdown Recovery**: Schnelle Erholung nach DD

### Portfolio Metrics (Phase 4)
- **Sharpe Ratio**: > 1.0
- **CAGR**: > 15% (bei 2% Risk per Trade)
- **Max Concurrent DD**: < 20R (mehrere HTFs kombiniert)

---

## 📝 NOTES

**Current Status**: 
- ✅ Phase 1 (Validation) abgeschlossen
- ✅ Phase 2 (Single TF Default: W, 3D, M) abgeschlossen
- 🎯 Phase 3 (Technische Optimierung) - **NEXT: Gap Size Filter**

**CSV Trades vorhanden**: 
- W_trades.csv, 3D_trades.csv, M_trades.csv
- Spalten: pair, htf_timeframe, direction, entry_type, pivot_time, valid_time, gap_touch_time, entry_time, exit_time, duration_days, pivot_price, extreme_price, near_price, gap_pips, wick_diff_pips, wick_diff_pct, total_refinements, priority_refinement_tf, entry_price, sl_price, tp_price, exit_price, final_rr, sl_distance_pips, tp_distance_pips, exit_type, pnl_pips, pnl_r, win_loss, mfe_pips, mae_pips, lots

**Wichtigste Erkenntnisse**:
- Near Touch > K2 Open Touch (mehr Trades, bessere WR)
- Gap Size SEHR wichtig (korreliert mit Duration)
- Sequential Optimization > Grid Search
- Walk-Forward nur bei kritischen Parametern

---

*Last Updated: 2025-01-04*