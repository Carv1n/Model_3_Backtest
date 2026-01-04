# Model 3 - Strategie Variablen für Backtesting & Optimierung

**Stand**: 2025-01-04  
**Quelle**: Basierend auf Variablen.md (User-definiert)

---

## ⚠️ WICHTIG: Overfitting vermeiden!

- Nicht zu viele Parameter gleichzeitig optimieren
- Walk-Forward Testing nutzen (5y IS / 1y OOS)
- Parameter müssen logisch sinnvoll sein (nicht nur statistisch)
- Robustheit über allen Pairs prüfen (nicht nur 1-2 Top-Pairs)
- Max. 4-6 freie Parameter pro Test-Phase

---

## 1. HTF PIVOT CREATION

### 1.1 Pivot Position
**Zweck**: Wo wird der Pivot-Level platziert?

**Optionen**:
- `open_k2` - Standard: Pivot = Open K2 ✅
- `close_k1` - Alternativ: Pivot = Close K1

**Zusätzliche Strategien** (für Tests):
- Nach **größter Gap** - Wähle Pivot (Open K2 vs Close K1), der größere Gap ergibt
- Nach **kleinster Gap** - Wähle Pivot mit kleinerer Gap

**Erwartung**:
- Open K2: Klare Regel, konsistent
- Close K1: Könnte bessere Entries geben bei bestimmten Setups
- Größte/Kleinste Gap: Adaptive Strategie, mehr Komplexität

**Test-Priorität**: 🔵 MITTEL - Nach Baseline Tests

---

### 1.2 Timeframe Selection
**Zweck**: Welche HTF-Pivots nutzen?

**Einzeln testen**:
- `3D` only
- `W` only ✅ (aktuell)
- `M` only

**Kombiniert testen**:
- `3D + W`
- `3D + M`
- `W + M`
- `3D + W + M` (alle)

**Erwartung**:
- Einzeln: Klare Statistik pro Timeframe
- Kombiniert: Mehr Trades, aber Korrelation/Concurrency-Risiko

**Test-Priorität**: 🔴 HOCH - Direkt nach Baseline

---

## 2. ENTRY VARIABLEN

### 2.1 Entry Confirmation Type
**Zweck**: Wie wird Entry bestätigt?

**Optionen**:
- `direct_touch` - Entry sofort bei Touch des Entry-Levels ✅ (Standard)
- `1h_close` - Warte auf 1H Close jenseits Entry-Level
- `4h_close` - Warte auf 4H Close jenseits Entry-Level

**Entry-Logik bei Close**:
1. Wenn Close **schlecht** (nicht jenseits Entry) → Verfeinerung löschen
2. Wenn Close **gut**:
   - Option A: Entry bei Close der Candle (H1/H4)
   - Option B: Entry bei Near/Wick Diff wenn wieder berührt wird

**Immer**: Min. 1 RR bei Entry-Zeitpunkt prüfen

**Erwartung**:
- direct_touch: Mehr Trades, frühere Entries, mehr Fakeouts
- 1h_close: Weniger Trades, bessere Qualität, weniger Fakeouts
- 4h_close: Noch weniger Trades, höchste Qualität

**Test-Priorität**: 🔴 HOCH - Nach Baseline

---

## 3. STOP LOSS VARIABLEN

### 3.1 Minimum SL Distance (Pips)
**Zweck**: Mindestabstand Entry → SL

**Optionen**:
- `40` Pips - Enger, höhere RR, mehr SL-Hits
- `60` Pips - Standard ✅
- `80` Pips - Weiter, niedrigere RR, weniger SL-Hits
- `100` Pips - Sehr weit

**Test-Priorität**: 🟡 MITTEL - Nach Entry Tests

---

### 3.2 Fixer SL pro Pair
**Zweck**: Pair-spezifische SL-Distanz

**⚠️ ACHTUNG OVERFITTING!**
- Nur nutzen wenn statistisch signifikant
- Risiko: Zu viele freie Parameter (28 Pairs = 28 Parameter!)

**Empfehlung**: 
- Erst globale SL-Regeln optimieren
- Dann prüfen ob einzelne Pairs deutlich abweichen
- Nur bei klarem Grund (z.B. JPY pairs = höhere Volatilität)

**Test-Priorität**: 🔵 NIEDRIG - Viel später, mit Vorsicht

---

### 3.3 Minimum RR für Trade-Ausführung
**Zweck**: Trades nur ausführen wenn RR hoch genug

**Optionen**:
- `1.0` - Standard ✅ (mindestens 1:1)
- `1.1` - Etwas strenger
- `1.2` - Noch strenger, höhere Qualität

**Erwartung**:
- Höhere Min RR: Weniger Trades, bessere durchschnittliche Qualität
- Niedrigere Min RR: Mehr Trades, schlechtere durchschnittliche Qualität

**Test-Priorität**: 🔴 HOCH - Nach Entry Tests

---

### 3.4 Fixer SL bei Fib Level (unabhängig von RR)
**Zweck**: SL fix bei bestimmtem Fib-Level platzieren

**Optionen**:
- `Fib 1.0` - SL direkt bei Extreme (100%)
- `Fib 1.1` - SL 10% jenseits Extreme ✅ (Standard)
- `Fib 1.2` - SL 20% jenseits Extreme
- `Fib 1.5` - SL 50% jenseits Extreme

**Erwartung**:
- Näher bei Extreme: Engerer SL, mehr Hits, höhere RR
- Weiter von Extreme: Weiterer SL, weniger Hits, niedrigere RR

**Test-Priorität**: 🟡 MITTEL - Nach SL Distance Tests

---

## 4. TAKE PROFIT VARIABLEN

### 4.1 TP Fib Level
**Zweck**: Bei welchem Fib-Level wird TP platziert?

**Optionen**:
- `-1.0` - Standard ✅ (Pivot + Gap Extension)
- `-1.5` - 1.5x Gap Extension (aggressiver)
- `-2.0` - 2x Gap Extension (sehr aggressiv)
- `-2.5` - 2.5x Gap Extension

**Erwartung**:
- Konservativere TP (-1): Höhere Win Rate, kleinere Wins
- Aggressivere TP (-2/-2.5): Niedrigere Win Rate, größere Wins

**Test-Priorität**: 🟡 MITTEL - Nach Entry Tests

---

### 4.2 Min/Max TP Distance (Pips)
**Zweck**: Limitiere TP auf Pips-Basis

**Optionen**:
- Min TP: `50`, `75`, `100` Pips
- Max TP: `200`, `250`, `300` Pips

**Erwartung**:
- Zu enge Limits: Gute Trades werden eingeschränkt
- Zu weite Limits: Unrealistische TPs bei großen Gaps

**Test-Priorität**: 🔵 NIEDRIG - Experimentell

---

## 5. RISK/REWARD VARIABLEN

### 5.1 Maximum RR
**Zweck**: Maximales erlaubtes RR - wenn höher, SL erweitern

**Optionen**:
- `1.5` - Standard ✅
- `2.0` - Erlaubt höhere RR, weiterer SL
- `2.5` - Sehr hohe RR erlaubt
- `3.0` - Keine praktische Begrenzung

**Erwartung**:
- Niedrigere Max RR (1.5): Engere SLs, konsistentere Ergebnisse
- Höhere Max RR (2.5-3.0): Weitere SLs, höhere Wins wenn erfolgreich

**Test-Priorität**: 🟡 MITTEL - Nach SL Tests

---

## 6. VERFEINERUNGS-VARIABLEN

### 6.1 Refinement Timeframes
**Zweck**: Welche Timeframes für Verfeinerungen nutzen?

**Einzeln testen**:
- Nur `H1`
- Nur `H4`
- Nur `D`
- Nur `3D`
- Nur `W` (max TF!)

**Kombiniert testen**:
- `H1 + H4` (Intraday)
- `D + H4` (Daily + Intraday)
- `3D + D + H4` (Multi-Level)
- `W + 3D + D + H4 + H1` (alle) ✅ (Standard)

**Erwartung**:
- Einzelne TFs: Klare Statistik pro Level
- Kombiniert: Mehr Verfeinerungen, bessere Abdeckung

**Test-Priorität**: 🔴 HOCH - Nach Entry Tests

---

### 6.2 Wick Diff Entry Strategy
**Zweck**: Wann Wick Diff Entry nutzen vs Verfeinerung?

**Optionen**:
- **Immer Wick Diff** - Bei jedem HTF Pivot (wenn < 20%)
- **Nur unter 20%** - Wick Diff nur wenn klein genug ✅ (Standard)
- **Kombiniert** - Wick Diff + beste Verfeinerungen zusammen

**Erwartung**:
- Immer Wick Diff: Mehr Entries, aber evtl. schlechtere Qualität
- Nur unter 20%: Qualitätsfilter
- Kombiniert: Best of both worlds?

**Test-Priorität**: 🟡 MITTEL - Nach Refinement TF Tests

---

### 6.3 Refinement Max Size
**Zweck**: Maximale Größe der Verfeinerung (% von HTF Gap)

**Optionen**:
- `10%` - Nur sehr kleine Verfeinerungen
- `20%` - Standard ✅
- `30%` - Größere Verfeinerungen erlaubt

**Erwartung**:
- Kleinere Size: Weniger Verfeinerungen, höhere Qualität
- Größere Size: Mehr Verfeinerungen, evtl. mehr Noise

**Test-Priorität**: 🟡 MITTEL - Nach Entry Tests

---

### 6.4 Doji Filter
**Zweck**: Minimum Body Size (% der Candle Range)

**Optionen**:
- `0%` - Kein Filter (alle Kerzen erlaubt)
- `5%` - Standard ✅ (Body mind. 5%)
- `10%` - Strengerer Filter (nur starke Bodies)

**Erwartung**:
- Kein Filter (0%): Mehr Signale, evtl. Doji-Fakeouts
- Strenger Filter (10%): Weniger Signale, nur Momentum-Kerzen

**Test-Priorität**: 🔵 NIEDRIG - Nach Refinement Tests

---

### 6.5 Refinement Validierungs-Check
**Zweck**: Wann ist Verfeinerung ungültig?

**Optionen**:
- **K2 Touch** - Near darf nicht bei K2 Close berührt werden
- **Near Touch** - Near darf zwischen Creation und Valid Time nicht berührt werden ✅ (Standard)

**Erwartung**:
- K2 Touch: Weniger streng, mehr Verfeinerungen
- Near Touch: Strenger, bessere Qualität

**Test-Priorität**: 🔵 NIEDRIG - Experimentell

---

### 6.6 Refinement Priorität
**Zweck**: Welche Verfeinerung wird gewählt bei mehreren?

**Variante 1 (Standard)** ✅:
- Höchste Prio = Höchstes Timeframe (W > 3D > D > H4 > H1)
- Bei mehreren pro TF: Nächste zu HTF Near

**Variante 2 (Alternative)**:
- IMMER nächste zu HTF Near (unabhängig von TF)

**Erwartung**:
- Variante 1: Bevorzugt höhere TFs (mehr "Gewicht")
- Variante 2: Bevorzugt geometrisch beste Position

**Test-Priorität**: 🔵 NIEDRIG - Nach Refinement Tests

---

## 7. PORTFOLIO & RISK MANAGEMENT

### 7.1 Risk per Trade
**Zweck**: Wie viel % des Kapitals pro Trade riskieren?

**Optionen**:
- `0.5%` - Sehr konservativ
- `1.0%` - Standard ✅
- `2.0%` - Aggressiver

**Test-Priorität**: 🔵 NIEDRIG - Portfolio-Level

---

### 7.2 Max Concurrent Trades
**Zweck**: Maximale Anzahl gleichzeitiger Trades

**Optionen**:
- `Unbegrenzt` - Alle Setups nehmen ✅ (aktuell für Single-TF)
- `5` - Diversifikation erzwingen
- `10` - Balance

**⚠️ WICHTIG**: Erst bei Combined Portfolio Tests relevant!

**Test-Priorität**: 🔴 HOCH - Bei Combined Tests (W+3D+M)

---

### 7.3 Max Concurrent per Pair
**Zweck**: Max. Trades pro Pair gleichzeitig

**Optionen**:
- `1` - Nur ein Trade pro Pair ✅ (empfohlen)
- `2` - Zwei Trades erlaubt (z.B. verschiedene HTFs)
- `Unbegrenzt` - Kein Limit

**Test-Priorität**: 🔴 HOCH - Bei Combined Tests

---

## 8. OPTIMIERUNGS-ZIELE

### Primäre Ziele:
- ✅ **Profit Expectancy**: 0.1 - 0.3 R/Trade (ambitioniert)
- ✅ **Win Rate**: 45-50% (realistisch)
- ✅ **Max Duration**: 95% der Trades unter 60 Tagen
- ✅ **Min Duration**: 2-3 Tage (kein TP/SL innerhalb 1-2 Tagen)

### Sekundäre Ziele:
- SQN: > 1.6 (gut), > 2.0 (sehr gut)
- Profit Factor: > 1.3
- Max Drawdown: < 10R (bei 1% Risk/Trade)
- Sharpe Ratio: > 1.0

### Wichtig für Funded Accounts:
- Consistent Profitability (über Monate)
- Controlled Drawdown (< 5-10% Max DD)
- Genug Trades (> 200)
- Stabile OOS Performance

---

## 10. TEST-REIHENFOLGE (Empfehlung)

### Phase 1: Baseline ✅
- W only, direct_touch, Standard-Settings
- Status: Abgeschlossen, bereit für Re-Run nach Bug Fixes

### Phase 2: HTF Selection 🎯
- 3D, W, M einzeln testen
- Beste Timeframe(s) ermitteln

### Phase 3: Entry & Refinements
- Entry Confirmation (direct_touch vs 1h_close vs 4h_close)
- Refinement Timeframes (einzeln und kombiniert)

### Phase 4: Risk Management
- Min RR Testing (1.0 vs 1.1 vs 1.2)
- SL Distance (40 vs 60 vs 80 Pips)
- Max RR (1.5 vs 2.0 vs 2.5)

### Phase 5: Fine-Tuning
- TP Level (-1 vs -1.5 vs -2)
- Refinement Size (10% vs 20% vs 30%)
- Doji Filter (0% vs 5% vs 10%)

### Phase 6: Combined Portfolio
- HTF Combinations (3D+W, W+M, alle)
- Portfolio Constraints (Max Concurrent, Per-Pair Limits)

---

## 11. WALK-FORWARD TESTING

**Setup (Empfohlen)**:
- IS (In-Sample): 5 Jahre
- OOS (Out-of-Sample): 1 Jahr
- Step: 1 Jahr
- Windows: ~14 (2005-2024)

**Prozedur**:
1. Optimiere Parameter auf IS
2. Wähle Top 3 Parameter-Sets
3. Teste auf OOS
4. Aggregiere OOS-Performance
5. Wenn stabil → robust!

---

*Last Updated: 2025-01-04*