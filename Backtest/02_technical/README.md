# 02_technical - Technische Backtests (ohne Fundamentals)

## Ziel
Performance-Analyse der technischen Model 3 Strategie OHNE fundamentale Filter.

---

## Test-Kategorien

### 1. Entry-Varianten-Vergleich

**Ziel**: Welche Entry-Bestätigung ist optimal?

#### Tests
- **1H Close** (Standard): 1H Close über/unter Level → Entry bei Open nächster Candle
- **Direct Touch**: Sofortiger Entry bei Berührung (kein Close)
- **4H Close**: 4H Close Bestätigung

#### Befehle
```bash
# Direct Touch (Standard)
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation direct_touch \
    --output Backtest/02_technical/entry_direct_touch.csv

# 1H Close
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --output Backtest/02_technical/entry_1h_close.csv

# 4H Close
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 4h_close \
    --output Backtest/02_technical/entry_4h_close.csv
```

**WICHTIG**: START_DATE = None (nutzt alle verfügbaren Daten pro Asset!)

#### Vergleichs-Metriken
- **Total Trades**: Mehr bei Direct Touch?
- **Win Rate**: Höher bei 1H/4H Close?
- **Expectancy (R)**: Welche Methode profitabler?
- **Max DD**: Welche Methode sicherer?

---

### 2. HTF-Timeframe-Varianten

**Ziel**: Optimale HTF-Kombination finden.

#### Tests
- **Nur W**: Weekly allein
- **Nur 3D**: 3D allein
- **Nur M**: Monthly allein
- **3D + W**: Kombination
- **W + M**: Kombination
- **Alle (3D+W+M)**: Alle drei HTF-TFs

#### Befehle
```bash
# Nur W
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --output Backtest/02_technical/htf_W.csv

# Nur 3D
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes 3D \
    --output Backtest/02_technical/htf_3D.csv

# Alle (3D+W+M)
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes 3D W M \
    --output Backtest/02_technical/htf_all.csv
```

**WICHTIG**: Alle verfügbaren Daten werden genutzt (kein fixer Start!)

#### Vergleichs-Metriken
- **Total Trades**: Mehr Setups = besser?
- **Expectancy**: Qualität vs. Quantität?
- **Max gleichzeitig offen**: Overlap-Problem?

---

### 3. Parameter-Variationen

**Ziel**: Optimale Parameter finden.

#### 3.1 Doji-Filter
```bash
# Doji 3%
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --start-date 2010-01-01 \
    --output Backtest/02_technical/doji_3pct.csv
# TODO: Doji-Parameter als CLI-Argument hinzufügen

# Doji 5% (Standard)
# Doji 7%
# Doji 10%
```

#### 3.2 Verfeinerungsgröße
```bash
# Refinement 10%
# Refinement 15%
# Refinement 20% (Standard)
# Refinement 25%
# TODO: Refinement-Size-Parameter als CLI-Argument hinzufügen
```

---

## Output-Dateien

```
02_technical/
├── entry_1h_close.csv
├── entry_direct_touch.csv
├── entry_4h_close.csv
├── htf_W.csv
├── htf_3D.csv
├── htf_M.csv
├── htf_all.csv
└── README.md (diese Datei)
```

---

## Erwartete Erkenntnisse

### Entry-Varianten
- **Direct Touch** (Standard): Sofort bei Touch, mehr Setups
- **1H Close**: Höhere Win Rate, weniger Setups
- **4H Close**: Höchste Win Rate, wenigste Setups

### HTF-Timeframes
- **Nur W**: Mittlere Anzahl Setups, gute Qualität
- **Nur M**: Wenige Setups, hohe Qualität?
- **Alle**: Viele Setups, aber Overlap-Risiko

---

## Performance-Ziele

**Ohne Fundamentals erwarten wir**:
- Win Rate: 40-50% (bei direct_touch)
- Expectancy: 0-2 R (neutral bis leicht positiv)
- Profit Factor: 0.9-1.2

**Mit Fundamentals sollte sich verbessern auf**:
- Win Rate: 50-60%
- Expectancy: 2-4 R
- Profit Factor: 1.5-2.0

**Neue Regeln implementiert**:
- Gap Touch auf Daily-Daten (auch bei W/M!)
- TP-Check vor Entry (Setup ungültig wenn TP berührt)
- Wick Diff Entry bei < 20%
- RR-Check für alle Entries

---

## Nächste Schritte

Nach Abschluss 02_technical:
1. **Beste Kombination** identifizieren (Entry + HTF)
2. **Baseline dokumentieren**: Performance ohne Fundamentals
3. **Weiter zu 03_fundamentals**: COT, Seasonality hinzufügen

**WICHTIG**: Siehe `STRATEGIE_REGELN.md` für alle technischen Regeln!

---

*Last Updated: 29.12.2025*
