# 02_technical - Technische Backtests (ohne Fundamentals)

## Ziel
Performance-Analyse der technischen Model 3 Strategie OHNE fundamentale Filter.

## Status
**Phase 2 - AKTUELL 🎯** (seit 30.12.2025)

---

## Aktuelle Struktur

### 01_DEFAULT/01_Single_TF/
**Einzelne Timeframe Tests (W, 3D, M separat)**

**Scripts:**
- `scripts/backtest_W.py` - Weekly Backtest
- `scripts/backtest_3D.py` - 3-Day Backtest
- `scripts/backtest_M.py` - Monthly Backtest

**Ausführung (seriell):**
```bash
cd "05_Model 3/Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_W.py   # Weekly
python scripts/backtest_3D.py  # 3-Day
python scripts/backtest_M.py   # Monthly
```

**Ausführung (parallel - alle 3 gleichzeitig):**
```bash
# Terminal 1:
cd "05_Model 3/Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_W.py

# Terminal 2 (neues Terminal):
cd "05_Model 3/Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_3D.py

# Terminal 3 (neues Terminal):
cd "05_Model 3/Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_M.py
```

**ODER (Windows - alle 3 in einem Befehl starten):**
```bash
cd "05_Model 3/Backtest/02_technical/01_DEFAULT/01_Single_TF"
start python scripts/backtest_W.py & start python scripts/backtest_3D.py & start python scripts/backtest_M.py
```

**Output:**
- `results/Trades/{TF}_pure.csv`, `{TF}_conservative.csv`
- `results/Pure_Strategy/{TF}_pure.txt`
- `results/Conservative/{TF}_conservative.txt`

**Settings:**
- Entry: `direct_touch` (Standard)
- Doji Filter: 5%
- Refinement Max Size: 20%
- Min RR: 1.0, Max RR: 1.5
- Risk per Trade: 1%
- Start: 2010-01-01, End: 2024-12-31
- Pairs: Alle 28 Major/Cross Pairs

---

## Geplante Tests (Zukünftig)

### 1. Entry-Varianten-Vergleich

**Ziel**: Welche Entry-Bestätigung ist optimal?

#### Tests
- **Direct Touch** (aktuell): Sofortiger Entry bei Berührung
- **1H Close**: 1H Close über/unter Level → Entry bei Open nächster Candle
- **4H Close**: 4H Close Bestätigung

#### Vergleichs-Metriken
- **Total Trades**: Mehr bei Direct Touch?
- **Win Rate**: Höher bei 1H/4H Close?
- **Expectancy (R)**: Welche Methode profitabler?
- **Max DD**: Welche Methode sicherer?

---

### 2. HTF-Timeframe-Varianten

**Ziel**: Optimale HTF-Kombination finden.

#### Tests (bereits getrennt!)
- ✅ **Nur W**: Weekly allein - `backtest_W.py`
- ✅ **Nur 3D**: 3D allein - `backtest_3D.py`
- ✅ **Nur M**: Monthly allein - `backtest_M.py`
- ⏳ **3D + W**: Kombination (geplant)
- ⏳ **W + M**: Kombination (geplant)
- ⏳ **Alle (3D+W+M)**: Alle drei HTF-TFs (geplant)

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

*Last Updated: 30.12.2025*
