# Model 3 - Strategy Variables für Optimization

## Zweck
Übersicht aller Strategie-Parameter, die für zukünftige Optimierung getestet werden können.

**Status**: Diese Variablen sind NOCH NICHT zu optimieren - erst nach Baseline-Backtest!

---

## 1. Entry-Variablen

### 1.1 Entry Confirmation Type
**Aktuell**: `direct_touch` (Standard)

**Varianten zu testen**:
- `direct_touch` - Entry bei erster Berührung des Entry-Levels
- `1h_close` - Entry bei Close UNTER/ÜBER Entry-Level (1H Bar)
- `4h_close` - Entry bei Close UNTER/ÜBER Entry-Level (4H Bar)

**Erwartung**:
- direct_touch: Mehr Trades, frühere Entries, höheres Risiko von Fakeouts
- 1h_close: Weniger Trades, bestätigte Entries, weniger Fakeouts
- 4h_close: Noch weniger Trades, stärkste Bestätigung, beste Qualität?

**Test-Priority**: **HIGH** - Direkt nach Baseline!

---

## 2. HTF Timeframe Variablen

### 2.1 HTF Timeframe Selection
**Aktuell**: `["3D", "W", "M"]` (alle)


## 3. Risk-Reward Variablen

### 3.1 Minimum RR
**Aktuell**: `1.0` (mindestens 1:1)

**Varianten zu testen**:
- `0.8` - Mehr Trades, niedrigere Qualität
- `1.0` - Standard
- `1.2` - Weniger Trades, höhere Qualität
- `1.5` - Nur beste Setups

**Erwartung**:
- Niedrigere Min RR: Mehr Trades, niedrigerer Avg RR, evtl. schlechtere Win Rate
- Höhere Min RR: Weniger Trades, höherer Avg RR, evtl. bessere Win Rate

**Test-Priority**: **MEDIUM** - Nach Baseline

### 3.2 Maximum RR
**Aktuell**: `1.5` (max 1.5:1, dann SL erweitern)

**Varianten zu testen**:
- `1.5` - Standard
- `2.0` - Höhere RR erlaubt, weiterer SL
- `3.0` - Keine Begrenzung

**Erwartung**:
- Höhere Max RR: Höherer Avg RR, aber evtl. mehr SL Hits (weiterer SL)
- Standard 1.5: Balance zwischen RR und SL Distance

**Test-Priority**: **LOW** - Später

---

## 4. Stop Loss Variablen

### 4.1 Minimum SL Distance
**Aktuell**: `60` Pips (min. 60 Pips von Entry)

**Varianten zu testen**:
- `40` Pips - Engerer SL, höhere RR, mehr SL Hits?
- `60` Pips - Standard
- `80` Pips - Weiterer SL, niedrigere RR, weniger SL Hits?

**Erwartung**:
- Engerer SL: Höhere RR, aber mehr SL Hits (höheres Risiko von Noise)
- Weiterer SL: Niedrigere RR, aber weniger SL Hits (mehr "Raum")

**Test-Priority**: **MEDIUM** - Nach Entry Tests

### 4.2 Fib Level für SL Placement
**Aktuell**: `1.1` (SL jenseits Fib 1.1 = Fib 1 ± 10% Gap)

**Varianten zu testen**:
- `1.0` - SL direkt bei Fib 1 (100%)
- `1.1` - Standard (110%)
- `1.2` - SL bei Fib 1 + 20% Gap

**Erwartung**:
- Fib 1.0: Engerer SL, mehr SL Hits, höhere RR
- Fib 1.2: Weiterer SL, weniger SL Hits, niedrigere RR

**Test-Priority**: **LOW** - Später, nach SL Distance Tests

---

## 5. Verfeinerungs-Variablen

### 5.1 Refinement Max Size
**Aktuell**: `20.0` (max 20% von HTF Gap)

**Varianten zu testen**:
- `10.0` - Nur kleinere Verfeinerungen (höhere Qualität?)
- `20.0` - Standard
- `30.0` - Mehr Verfeinerungen erlaubt (niedrigere Qualität?)

**Erwartung**:
- Kleinere Max Size: Weniger Verfeinerungen, feinere Entries, höhere Qualität?
- Größere Max Size: Mehr Verfeinerungen, mehr Trades, niedrigere Qualität?

**Test-Priority**: **MEDIUM** - Nach Entry Tests

### 5.2 Doji Filter
**Aktuell**: `5.0` (Body mindestens 5% der Range)

**Varianten zu testen**:
- `0.0` - Kein Doji-Filter (alle Kerzen erlaubt)
- `5.0` - Standard
- `10.0` - Strengerer Filter (nur starke Bodies)

**Erwartung**:
- Kein Filter: Mehr Verfeinerungen, evtl. mehr Fakeouts (Dojis)
- Strengerer Filter: Weniger Verfeinerungen, höhere Qualität (nur Momentum)

**Test-Priority**: **LOW** - Später

### 5.3 Refinement Priorität
**Aktuell**: Höchster TF → Am nächsten zu HTF Near

**Varianten zu testen**:
- Höchster TF first (Standard)
- Closest to Near first (unabhängig von TF)
- Smallest Size first (kleinste Verfeinerung = höchste Qualität?)

**Erwartung**:
- Verschiedene Priorisierungen führen zu unterschiedlichen Entry-Levels
- Schwer vorherzusagen ohne Tests

**Test-Priority**: **LOW** - Experimentell, später

---

## 6. Gap Touch Variablen

### 6.1 Gap Touch Timeframe
**Aktuell**: `D` (Daily) - FEST!

**Varianten zu testen**:
- Aktuell NICHT vorgesehen zu ändern
- Daily ist die Regel, sollte konsistent bleiben

**Test-Priority**: **NONE** - Nicht testen (Regel!)

---

## 7. TP-Level Variablen

### 7.1 TP Fib Level
**Aktuell**: `-1.0` (Fib -1 = Pivot - Gap)

**Varianten zu testen**:
- `-0.618` - Konservativeres TP (näher bei Entry)
- `-1.0` - Standard (komplette Gap Extension)
- `-1.272` - Aggressiveres TP (weitere Extension)

**Erwartung**:
- Konservativeres TP: Höhere Win Rate, niedrigerer Avg Win
- Aggressiveres TP: Niedrigere Win Rate, höherer Avg Win

**Test-Priority**: **MEDIUM** - Interessant, aber nach Entry Tests

---

## 8. Daten-Qualität Variablen

### 8.1 H1-H4 Data Source
**Aktuell**: Oanda API (mit Daten-Korrektur)

**Varianten zu testen**:
- Aktuell: Oanda mit Korrektur (Abweichungen möglich)
- Zukünftig: TradingView H1-H4 Daten? (100% exakt)

**Test-Priority**: **NONE** - Abhängig von Datenverfügbarkeit

---

## 9. Portfolio-Variablen

### 9.1 Risk Per Trade
**Aktuell**: `1.0%` (1% des Kapitals pro Trade)

**Varianten zu testen**:
- `0.5%` - Konservativer
- `1.0%` - Standard
- `2.0%` - Aggressiver

**Erwartung**:
- Niedrigeres Risiko: Geringere Returns, geringerer Max DD
- Höheres Risiko: Höhere Returns, höherer Max DD

**Test-Priority**: **LOW** - Portfolio-Level, nach Trade-Level Optimization

### 9.2 Max Concurrent Trades
**Aktuell**: Unbegrenzt (alle Setups nehmen)

**Varianten zu testen**:
- Unbegrenzt - Standard (für Baseline)
- Limit 5 Trades - Diversifikation
- Limit 10 Trades - Balance

**Erwartung**:
- Unbegrenzt: Alle Opportunities, höheres Risiko bei Korrelation
- Limit: Weniger Trades, erzwungene Selektion, Diversifikation

**Test-Priority**: **LOW** - Portfolio-Level, nach Baseline

---

## 10. Weitere Ideen (Ungetestet)

### 10.1 Verfeinerungs-Distanz zu HTF Near
- Nur Verfeinerungen innerhalb X% von HTF Near?
- Beispiel: Nur innerhalb 50% des Wick Diff

### 10.2 HTF Pivot Quality Filter
- Nur Pivots mit bestimmten Eigenschaften?
- Beispiel: Wick Diff > X% von Gap (nur "saubere" Pivots)

### 10.3 Volatility Filter
- Trades nur bei bestimmter ATR/Volatility?
- Beispiel: Keine Trades bei sehr niedriger Volatility

### 10.4 News/Event Filter
- Keine Trades vor/während Major News?
- Erfordert externe Datenquelle

### 10.5 Session Filter
- Nur Trades während bestimmter Sessions?
- Beispiel: Nur während London/NY Session

**Test-Priority für alle**: **VERY LOW** - Experimentell, viel später

---

## 11. Test-Reihenfolge (Empfehlung)

### Phase 1: Baseline (JETZT)
1. **Baseline-Backtest**: W only, direct_touch, Standard-Settings
2. Validierung der Ergebnisse

### Phase 2: Entry & HTF (DANACH)
1. **Entry Confirmation**: direct_touch vs 1h_close vs 4h_close
2. **HTF Timeframes**: 3D, W, M einzeln und Kombinationen
3. Beste Kombination ermitteln

### Phase 3: Risk & Refinements (SPÄTER)
1. **Min RR**: 0.8, 1.0, 1.2, 1.5
2. **Refinement Max Size**: 10%, 20%, 30%
3. **SL Distance**: 40, 60, 80 Pips

### Phase 4: Fine-Tuning (VIEL SPÄTER)
1. **TP Level**: -0.618, -1.0, -1.272
2. **Doji Filter**: 0%, 5%, 10%
3. **Max RR**: 1.5, 2.0, 3.0

### Phase 5: Portfolio (ZULETZT)
1. **Risk Per Trade**: 0.5%, 1%, 2%
2. **Max Concurrent Trades**: Unbegrenzt, 5, 10

---

## 12. Wichtige Hinweise

### Bei Optimierung beachten:
1. **Overfitting vermeiden** - Nicht zu viele Parameter auf gleichen Daten optimieren
2. **Walk-Forward Testing** - Out-of-Sample Validation
3. **Robustheit prüfen** - Parameter sollten stabil sein (keine Cliffs)
4. **Logik vor Profit** - Macht die Änderung logisch Sinn?
5. **Sample Size** - Genug Trades für statistische Signifikanz?

### Dokumentation:
- Jeder Test wird dokumentiert mit:
  - Getestete Parameter
  - Ergebnisse (Key Metrics)
  - Entscheidung (behalten oder verwerfen)
  - Begründung

---

## 13. Parameter-Kombinationen

### Aktuell (Baseline):
```python
HTF_TIMEFRAMES = ["W"]
ENTRY_CONFIRMATION = "direct_touch"
DOJI_FILTER = 5.0
REFINEMENT_MAX_SIZE = 20.0
MIN_SL_DISTANCE = 60
MIN_RR = 1.0
MAX_RR = 1.5
TP_FIB_LEVEL = -1.0
RISK_PER_TRADE = 1.0
```

### Nach Optimization (Hypothetisch):
```python
# Beispiel - NICHT getestet!
HTF_TIMEFRAMES = ["W", "M"]  # Beste Kombination?
ENTRY_CONFIRMATION = "1h_close"  # Bessere Qualität?
DOJI_FILTER = 5.0  # Bleibt gleich?
REFINEMENT_MAX_SIZE = 15.0  # Strengerer Filter?
MIN_SL_DISTANCE = 60  # Bleibt gleich?
MIN_RR = 1.2  # Höhere Qualität?
MAX_RR = 1.5  # Bleibt gleich?
TP_FIB_LEVEL = -1.0  # Bleibt gleich?
RISK_PER_TRADE = 1.0  # Bleibt gleich?
```

**Wichtig**: Alle Änderungen müssen durch Tests begründet sein!

---

*Last Updated: 29.12.2025*
