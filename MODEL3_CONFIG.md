# Model 3 - Standard-Konfiguration

## 📋 Übersicht

Diese Datei definiert die **Standard-Einstellungen** für Model 3 Backtests.

**Für komplette Strategie-Regeln siehe**: `STRATEGIE_REGELN.md`

---

## ⚙️ STANDARD-EINSTELLUNGEN

### 1. HTF-Pivot-Erkennung

```python
# Timeframes für Pivot-Erkennung
HTF_TIMEFRAMES = ["3D", "W", "M"]  # Alle drei HTF-TFs

# Für 01_test: Nur Weekly
HTF_TIMEFRAMES_TEST = ["W"]
```

**Filter**:
```python
DOJI_FILTER_PCT = 5.0  # Body muss >= 5% der Candle Range sein
PIVOT_VALIDATION_CANDLES = 2  # Pivot aus 2 Kerzen
```

**Versatz** (NICHT Standard, zum Backtesten aktivierbar):
```python
VERSATZ_REGEL = False  # Standard: AUS (kein Versatz)
# Wenn aktiviert:
VERSATZ_PLATZIERUNG = "größere_box"  # größere_box, kleinere_box, close_k1, open_k2
VERSATZ_FILTER = 2.0  # Größere Box muss < 2x kleinere Box sein (sonst Pivot ungültig)
```

---

### 2. Verfeinerungen (LTF)

```python
# Timeframes für Verfeinerungen (automatisch basierend auf HTF)
# WICHTIG: Höchster TF für Verfeinerungen ist WEEKLY!
# M → sucht in: W, 3D, D, H4, H1
# W → sucht in: 3D, D, H4, H1
# 3D → sucht in: D, H4, H1

REFINEMENT_MAX_SIZE_PCT = 20.0  # Max. 20% der HTF-Pivot-Gap
REFINEMENT_MIN_BODY_PCT = 5.0  # Doji-Filter: Body >= 5%
REFINEMENT_VERSATZ = False  # Standard: KEINE Versatz-Regel
```

**Priorität**:
```python
# Hierarchie: W > 3D > D > H4 > H1
# Höchster TF hat Priorität (Max = Weekly!)
```

**Precision**:
- Alle Preise werden auf **5 Nachkommastellen** gerundet
- Vergleiche verwenden Tolerance von **0.00001** um Floating-Point-Fehler zu vermeiden
- **Datenqualität**: D-M Daten (TradingView) sind exakt, H1-H4 (Oanda API) können abweichen

---

### 3. Entry-Regeln

```python
# Entry-Bestätigung
ENTRY_CONFIRMATION = "direct_touch"  # Standard: Direkter Entry bei Touch (kein Close)

# Alternativen (für Tests):
# - "1h_close": 1H Close Bestätigung → Entry bei Open nächster Candle
# - "4h_close": 4H Close Bestätigung
```

**Wichtige Hinweise**:
- Gap Touch wird auf **Daily-Daten** geprüft (auch bei W/M Pivots!)
- TP-Check: Wenn TP berührt **zwischen Gap Touch und Entry** → Setup ungültig
  - Check-Fenster: `max(Valid Time, Gap Touch)` **bis** `Entry Time`
  - Check endet BEI Entry, nicht danach!
  - TP Touch NACH Entry = normaler Trade-Verlauf (valide)
- Wick Diff Entry: Bei < 20% Wick Diff → Entry bei HTF Near (außer Verfeinerung näher)
- RR-Check: >= 1 RR erforderlich für alle Entries

---

### 4. Exit-Regeln

#### Stop Loss
```python
MIN_SL_DISTANCE_PIPS = 60  # Min. 60 Pips von Entry
FIB_SL_LEVEL = 1.1  # Fib 1.1 (0.1× Gap jenseits Extreme)

# SL-Berechnung:
# - Bullish: SL = min(Fib 1.1, Entry - 60 Pips)
# - Bearish: SL = max(Fib 1.1, Entry + 60 Pips)
# - Wenn SL zu nah: Setup wird ignoriert
```

#### Take Profit
```python
FIB_TP_LEVEL = -1  # Fib -1 (1× Gap jenseits Pivot)

# TP-Berechnung:
# - Bullish: TP = Pivot + Gap Size
# - Bearish: TP = Pivot - Gap Size
```

#### Risk/Reward
```python
MIN_RR = 1.0  # Setup ignorieren wenn RR < 1.0
MAX_RR = 1.5  # SL vergrößern wenn RR > 1.5

# RR-Anpassung:
# - Wenn RR > 1.5: SL nach außen verschieben bis RR = 1.5
# - Entry und TP bleiben unverändert
# - WICHTIG: Nach SL-Anpassung muss RR = 1.5 gesetzt werden (nicht altes RR returnen!)
```

---

### 5. Backtest-Einstellungen

#### Zeitraum
```python
START_DATE = None  # Max verfügbare Daten pro Asset nutzen (kein fixer Start!)
END_DATE = None  # Bis zum Ende der verfügbaren Daten
```

**WICHTIG - Datum/Zeit-Konvention:**
- **Alle Timestamps in Daten = OPEN-Zeit der Bar!**
- Beispiele:
  - 1H @ 20:00 → Opens 20:00, closes 20:59
  - Daily @ 18.06 → Opens 18.06 00:00, closes 18.06 23:59
  - Weekly @ 16.06 (Montag) → Opens Mo 16.06 00:00, closes Fr 20.06 23:59

#### Pairs
```python
# Alle 28 Major Forex Pairs
PAIRS_ALL = [
    "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "AUDUSD",
    "CADCHF", "CADJPY", "CHFJPY",
    "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "EURUSD",
    "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
    "USDCAD", "USDCHF", "USDJPY"
]

# Für schnelle Tests
PAIRS_TEST = ["EURUSD", "GBPUSD", "USDJPY"]
```

#### Portfolio-Modus
```python
PORTFOLIO_BACKTEST = True  # Trades chronologisch, Datum-abhängig
# - Trades werden in zeitlicher Reihenfolge ausgeführt
# - Mehrere Pairs können gleichzeitig offen sein
# - Simuliert reales Portfolio-Trading
```

#### Position Management (noch nicht implementiert)
```python
MAX_TOTAL_POSITIONS = None  # None = unbegrenzt
MAX_POSITIONS_PER_PAIR = None  # None = unbegrenzt
TRADE_PRIORITY = "timeframe"  # timeframe, alphabetical, gap_size
```

---

## 🧪 Konfigurations-Profile

### Profil 1: VALIDATION (01_test)
**Ziel**: Logik-Validierung, Setup-Überprüfung

```python
HTF_TIMEFRAMES = ["W"]  # NUR Weekly
ENTRY_CONFIRMATION = "direct_touch"  # Standard
START_DATE = None  # Max verfügbare Daten
PAIRS = einzeln (EURUSD, GBPUSD, etc.) für manuelle Validierung
```

**Verwendung**:
```bash
python scripts/backtesting/backtest_model3.py \
    --pairs EURUSD \
    --htf-timeframes W \
    --entry-confirmation direct_touch \
    --output Backtest/01_test/validation_W_EURUSD.csv
```

---

### Profil 2: STANDARD (02_technical)
**Ziel**: Performance-Analyse, Entry-Varianten

```python
HTF_TIMEFRAMES = ["W"]  # Weekly als Standard
ENTRY_CONFIRMATION = "direct_touch"  # Standard-Modus
START_DATE = None  # Max verfügbare Daten
PAIRS = PAIRS_ALL  # Alle 28 Pairs
```

**Verwendung**:
```bash
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --output Backtest/02_technical/standard_W_1h_close.csv
```

---

### Profil 3: ALLE HTF (02_technical)
**Ziel**: Multi-Timeframe Performance

```python
HTF_TIMEFRAMES = ["3D", "W", "M"]  # Alle drei
ENTRY_CONFIRMATION = "1h_close"
START_DATE = None  # Max verfügbare Daten
PAIRS = PAIRS_ALL
```

**Verwendung**:
```bash
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes 3D W M \
    --entry-confirmation 1h_close \
    --output Backtest/02_technical/all_htf_1h_close.csv
```

---

### Profil 4: DIRECT TOUCH (02_technical)
**Ziel**: Entry-Varianten-Vergleich

```python
HTF_TIMEFRAMES = ["W"]
ENTRY_CONFIRMATION = "direct_touch"  # Ohne Close-Bestätigung
START_DATE = None  # Max verfügbare Daten
PAIRS = PAIRS_ALL
```

**Verwendung**:
```bash
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation direct_touch \
    --output Backtest/02_technical/direct_touch.csv
```

---

## 📊 Output-Format

### Trade-CSV Spalten
```
pair              - Forex Pair (z.B. "EURUSD")
direction         - "bullish" oder "bearish"
pivot_time        - Zeitpunkt HTF-Pivot-Entstehung
entry_time        - Zeitpunkt Entry
entry_price       - Entry-Preis
tp_price          - Take Profit Preis
sl_price          - Stop Loss Preis
exit_time         - Zeitpunkt Exit
exit_price        - Exit-Preis
exit_reason       - "tp", "sl", "manual"
pnl_pips          - PnL in Pips
pnl_r             - PnL in R (Risk-Einheiten)
```

### Zusätzliche Infos (für Validierung)
Für detaillierte Validierung könnten wir hinzufügen:
- `htf_timeframe` - Welcher HTF-TF (3D/W/M)
- `refinement_timeframe` - Welcher LTF für Verfeinerung
- `pivot_level` - HTF-Pivot Level
- `pivot_extreme` - HTF-Pivot Extreme
- `refinement_level` - Verfeinerungs-Level
- `gap_size_pips` - HTF-Gap Größe
- `refinement_size_pips` - Verfeinerungs-Größe
- `rr_ratio` - Tatsächliches RR

---

## 🔄 Parameter-Variationen (für späteren Tests)

### Doji-Filter
```python
DOJI_FILTER_VARIATIONS = [3.0, 5.0, 7.0, 10.0]
# Testen: Welcher Filter optimal?
```

### Verfeinerungsgröße
```python
REFINEMENT_SIZE_VARIATIONS = [10.0, 15.0, 20.0, 25.0]
# Testen: Welche Größe optimal?
```

### Entry-Bestätigung
```python
ENTRY_VARIATIONS = ["direct_touch", "1h_close", "4h_close"]
# Vergleich: Welche Bestätigung besser?
```

### HTF-Kombinationen
```python
HTF_VARIATIONS = [
    ["W"],          # Nur Weekly
    ["3D"],         # Nur 3D
    ["M"],          # Nur Monthly
    ["3D", "W"],    # 3D + W
    ["W", "M"],     # W + M
    ["3D", "W", "M"]  # Alle drei
]
# Vergleich: Welche Kombination optimal?
```

---

## 📝 Empfohlene Vorgehensweise

### Phase 1: Validation ✅ JETZT
1. **Profil 1** verwenden (nur W, direct_touch)
2. **6 Sample-Tests** durchführen (siehe `01_test/kurze übersicht.txt`)
3. **Manuell validieren**: Setups korrekt?

### Phase 2: Standard-Backtest
4. **Profil 2** verwenden (W, alle Pairs)
5. **Performance analysieren**: Metriken, Charts
6. **Baseline etablieren**: Standard-Performance dokumentieren

### Phase 3: Entry-Varianten
7. **Profil 4** (direct_touch) vs. **Profil 2** (1h_close)
8. **Vergleich**: Win Rate, Expectancy, Total R
9. **Entscheidung**: Welche Entry-Methode besser?

### Phase 4: HTF-Varianten
10. **Profil 3** (alle HTF) testen
11. **Vergleich**: Nur W vs. 3D+W+M
12. **Analyse**: Mehr Setups = bessere Performance?

### Phase 5: Parameter-Optimierung
13. Doji-Filter-Variationen testen
14. Verfeinerungsgröße-Variationen testen
15. Optimale Kombination finden

---

*Last Updated: 29.12.2025*
