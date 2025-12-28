# Model 3 - Strategie & Settings

## 🎯 Was macht die Strategie?

**2-stufiges Pivot-System mit Verfeinerungen**

### Ablauf:

1. **HTF-Pivot finden** (3D, W, M)
   - 2-Kerzen-Muster: rot→grün (bullish) ODER grün→rot (bearish)
   - Pivot = Open der 2. Kerze (Standard: OHNE Versatz-Regel)
   - Extreme = Ende der längeren Wick (tiefster Low bei bullish / höchster High bei bearish)
   - Pivot Gap = von Pivot bis Extreme

2. **Wick Difference** = Bereich zwischen den beiden Dochten
   - Near = Ende der kürzeren Wick
   - Wick Diff = von Near bis Extreme

3. **Verfeinerung suchen** (1H, 4H, D, 3D, W)
   - Innerhalb der Wick Difference
   - Kleinerer 2-Kerzen-Pivot (gleiche Regel wie HTF-Pivot)
   - Max. 20% der HTF-Pivot-Gap
   - Priorität: Höchster TF zuerst (W > 3D > D > H4 > H1)
   - **WICHTIG**: Höchster TF für Verfeinerungen ist **Weekly**!

4. **Entry**
   - ERST muss HTF-Pivot-Gap berührt werden
   - DANN Preis berührt Verfeinerung (= Wick Diff der Verfeinerung)
   - Entry: Sofort bei Touch (direct_touch)

5. **Exit**
   - SL: Min. 60 Pips von Entry UND unter/über Fib 1.1
   - TP: Fib -1 (1× Gap jenseits Pivot)
   - RR: 1.0 - 1.5 (SL wird angepasst wenn > 1.5)

---

## ⚙️ Standard-Einstellungen

```python
# HTF-Pivots
HTF_TIMEFRAMES = ["3D", "W", "M"]
DOJI_FILTER = 5.0  # Body >= 5% der Candle Range
VERSATZ_REGEL = False  # Standard: AUS (zum Backtesten aktivierbar)

# Verfeinerungen
REFINEMENT_TIMEFRAMES = ["1H", "4H", "D", "3D", "W"]  # Max = Weekly!
REFINEMENT_MAX_SIZE = 20.0  # Max. 20% der Pivot Gap
REFINEMENT_DOJI_FILTER = 5.0

# Entry
ENTRY_CONFIRMATION = "direct_touch"  # Sofort bei Touch

# Exit
MIN_SL_DISTANCE = 60  # Min. 60 Pips von Entry
FIB_SL_LEVEL = 1.1
FIB_TP_LEVEL = -1
MIN_RR = 1.0
MAX_RR = 1.5

# Backtest
START_DATE = None  # Max verfügbare Daten pro Asset nutzen
END_DATE = None    # Bis aktuell
PAIRS = 28  # Alle Forex Pairs
```

---

## 🧪 Variable Settings (zu testen)

### Entry-Varianten
- `direct_touch` (Standard) - Sofort bei Touch der Verfeinerung
- `1h_close` - Entry bei Open nach 1H Close ÜBER (bullish) / UNTER (bearish) dem NEAR
- `4h_close` - Entry bei Open nach 4H Close ÜBER (bullish) / UNTER (bearish) dem NEAR
  - **Wichtig**: Close muss jenseits NEAR sein, nur Wick in Verfeinerung = nicht der Körper!

### HTF-Kombinationen
- Nur W
- Nur 3D
- Nur M
- 3D + W
- W + M
- Alle (3D + W + M)

### Parameter
- Doji-Filter: 3%, 5%, 7%, 10%
- Verfeinerungsgröße: 10%, 15%, 20%, 25%
- Versatz-Regel: AUS (Standard), EIN (zum Backtesten)

---

## 📊 Test-Phasen

### Phase 1: Validation (01_test)
**Ziel**: Logik prüfen
- 2 Pairs, 6 Sample-Trades
- Manuell validieren: Pivot, Verfeinerung, Entry, SL/TP korrekt?

### Phase 2: Baseline (02_W_test)
**Ziel**: Performance-Baseline
- Alle 28 Pairs
- Nur Weekly Pivots
- Standard-Settings
- **Stats**: Win Rate, Total R, Expectancy, Max DD, Profit Factor

### Phase 3: Entry-Varianten
- Vergleich: direct_touch vs 1h_close vs 4h_close

### Phase 4: HTF-Varianten
- Vergleich: Nur W vs. 3D+W+M

### Phase 5: Fundamentals
- COT, Seasonality, Valuation, Bonds

---

## 📐 Wichtige Regeln

### Pivot-Struktur (IMMER)
- **Pivot** = Open K2
- **Extreme** = Ende längere Wick (tiefster Low / höchster High)
- **Near** = Ende kürzere Wick
- **Gap** = Pivot bis Extreme
- **Wick Diff** = Near bis Extreme

### SL-Berechnung
- **Min. 60 Pips von Entry** (nicht von Extreme!)
- **UND** unter/über Fib 1.1
- Wenn beide nicht erfüllbar → Setup ungültig

### Verfeinerungs-Bedingungen (ALLE müssen erfüllt sein)
- Größe <= 20% der Pivot Gap
- Innerhalb Wick Difference (Ausnahme: exakt auf Near)
- **Unberührt während HTF-Pivot-Entstehung**: Open K2 der Verfeinerung darf nicht berührt werden bis HTF-Pivot valide ist
- Doji-Filter (5%)
- Standard: OHNE Versatz-Regel (zum Backtesten aktivierbar)

---

*Last Updated: 28.12.2025*
