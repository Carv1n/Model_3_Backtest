# 02_technical - Technische Backtests (ohne Fundamentals)

## Ziel
Performance-Analyse der technischen Model 3 Strategie OHNE fundamentale Filter.

## Status
**Phase 2 - AKTUELL 🎯** (seit 30.12.2025)

## ✅ Bug Fixes (31.12.2025)

### 1. Gap_Pips JPY Pairs Fix ✅

**Problem**: JPY-Pairs hatten 100x zu große gap_pips Werte
- Beispiel: Gap bei CHFJPY zeigte 12420 pips statt 124.20 pips
- Betraf alle JPY-Pairs (AUDJPY, CADJPY, CHFJPY, EURJPY, GBPJPY, NZDJPY, USDJPY)

**Root Cause**:
- JPY-Pairs haben 2 Dezimalstellen (nicht 4 wie andere Pairs)
- Code dividierte immer durch 10000, korrekt wäre 100 für JPY

**Fix Applied** (alle 5 Scripts):
- `scripts/backtest_W.py`
- `scripts/backtest_3D.py`
- `scripts/backtest_M.py`
- `scripts/backtest_W_test.py`
- `scripts/backtest_3D_test.py`

**Code-Änderung** in `calculate_gap_pips()` Funktion:
```python
# OLD (WRONG):
gap_pips = abs(gap_price) / 10000

# NEW (CORRECT):
pip_divisor = 100 if 'JPY' in pair else 10000
gap_pips = abs(gap_price) / pip_divisor
```

**Zusätzlicher Fix**:
- `htf_timeframe` Column zu Trade CSVs hinzugefügt (war vorher gefehlt)

**Status**: ✅ GEFIXT (31.12.2025 vormittags)

---

### 2. H1 Gap Touch Precision ✅

**Problem**: TP-Check nutzte Daily Gap Touch Time (Mitternacht), nicht exakte H1 Zeit
- Führte zu falschen Trade-Rejections bei Szenario: TP VOR Gap Touch (aber selber Tag)
- Beispiel: TP um 09:00, Gap Touch um 14:00 → alte Logik rejected (falsch!)

**Root Cause**:
- Gap Touch wurde nur auf Daily geprüft → returned Mitternacht (00:00)
- TP-Check ab 00:00 → TP um 09:00 fälschlich im Check-Window
- Sollte aber ab 14:00 prüfen (tatsächliche Gap Touch Zeit)

**Fix Applied** (alle Test Scripts):
- `01_test/02_W_test/02_ALL_PAIRS/scripts/backtest_weekly_full.py`
- Analog in anderen Test-Scripts

**Code-Änderung** in `simulate_single_trade()`:
```python
# OLD (WRONG - 2608 trades):
gap_touch_time = find_gap_touch_on_daily_fast(d_df, pivot, pivot.valid_time)
# → returned Mitternacht, nicht exakte Zeit

# NEW (CORRECT - 3986 trades):
daily_gap_touch = find_gap_touch_on_daily_fast(d_df, pivot, pivot.valid_time)
gap_touch_time = find_gap_touch_on_h1_fast(h1_df, pivot, daily_gap_touch)
# → returned exakte H1 Zeit (z.B. 14:00)
```

**TP-Check Regel** (korrekt implementiert):
- Check Window: `gap_touch_time` (H1 exakt) bis `entry_time`
- Regel: TP darf NICHT zwischen Gap Touch und Entry getroffen werden
- ABER: TP VOR Gap Touch ist OKAY (Trade valid!)

**Impact**:
- +1378 Trades (+52.8%): 2608 → 3986
- Diese Trades sind VALIDE (TP vor Gap Touch, aber nach Valid Time)
- Alte Logik hatte sie fälschlich rejected

**Status**: ✅ GEFIXT (31.12.2025 nachmittags)

**Trade Count Evolution**:
- 30.12.2025: 2608 trades (Daily Gap Touch, falsches Reject)
- 31.12.2025: 3986 trades (H1 Gap Touch, korrekt!) ✅

---

## Aktuelle Struktur

### 01_Single_TF/
**Combined Backtest (alle 3 Timeframes in einem Script)**

**Main Script:**
- `scripts/backtest_all.py` - **OPTIMIERT**: Alle 3 Timeframes (W, 3D, M) in einem Lauf

**Ausführung (EMPFOHLEN):**
```bash
cd "05_Model 3/Backtest/02_technical/01_Single_TF"
python scripts/backtest_all.py
```

**Performance-Optimierungen:**
- ✅ **Multiprocessing**: Nutzt alle CPU Cores parallel
- ✅ **Smart Data Loading**: Jedes Parquet nur 1x geladen (nicht 28x pro Pair!)
- ✅ **RAM Caching**: Daten im RAM während Script-Laufzeit
- ✅ **Vektorisierte Operations**: NumPy/Pandas Vectorization
- ✅ **Live Progress Display**: Zeigt aktuell verarbeitetes Pair
- **Runtime**: ~1.5-2 Min für alle 3 Timeframes (2005-2025, 28 Pairs)

**Output:**
- `results/W_report.txt` - Weekly Report
- `results/3D_report.txt` - 3-Day Report
- `results/M_report.txt` - Monthly Report
- `results/Trades/W_trades.csv` - Weekly Trades
- `results/Trades/3D_trades.csv` - 3-Day Trades
- `results/Trades/M_trades.csv` - Monthly Trades

**Settings:**
- Entry: `direct_touch` (Standard)
- Doji Filter: 5%
- Refinement Max Size: 20%
- Min RR: 1.0, Max RR: 1.5
- Risk per Trade: 1%
- **Period: 2005-01-01 to 2025-12-31** (21 Jahre)
- Pairs: Alle 28 Major/Cross Pairs
- **Performance**: ~1.5-2 Min für alle 3 Timeframes (optimiert mit Multiprocessing)

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
3. **Weiter zu 03_optimization**: Parameter-Optimierung
4. **Weiter zu 04_fundamentals**: COT, Seasonality hinzufügen

**WICHTIG**: Siehe `STRATEGIE_REGELN.md` für alle technischen Regeln!

---

*Last Updated: 31.12.2025*
