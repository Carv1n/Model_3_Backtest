# Model 3 - Pivot Validation

Dieser Ordner enthält Scripts zur **manuellen Validierung** von Pivot-Strukturen und Verfeinerungen.

---

## Scripts

### 1. `validation_random_pivots.py` ⭐ HAUPTSCRIPT

**Zweck**: Zufällige Pivot-Auswahl für manuelle Validierung in TradingView

**Config**:
- 2 Pairs: AUDNZD, GBPUSD
- 1 zufälliger Pivot pro Pair
- Timeframe: Weekly
- Zeitraum: 2010-2025

**Output**:
- `results/random_validation_YYYYMMDD_HHMMSS.txt` - Detaillierte Pivot-Strukturen
- `results/summary_YYYYMMDD_HHMMSS.csv` - Zusammenfassung

**Verwendung**:
```bash
python validation_random_pivots.py
```

**Output-Format**:
```
PIVOT: AUDNZD W
================================================================================

--- HTF PIVOT ---
K1 Time (Open): 2022-10-03 00:00:00+00:00
K2 Time (Open): 2022-10-10 00:00:00+00:00
Valid Time (K3 Open): 2022-10-17 00:00:00+00:00
Direction: bullish

--- LEVELS ---
Pivot (Open K2): 0.77008
Extreme: 0.76254
Near: 0.76910

--- GAPS ---
Pivot Gap: 0.00754 (75.4 pips)
Wick Difference: 0.00656 (65.6 pips, 87.0% von Pivot Gap)

--- VERFEINERUNGEN ---
Total: 2 Verfeinerung(en)

H4: 1 Verfeinerung(en)
  #1:
    Time: 2022-10-12 01:00:00+00:00
    Direction: bullish
    Pivot (Open K2): 0.76978
    Extreme: 0.76894
    Near (Entry): 0.76902
    Size: 0.00008 (0.8 pips, 1.1% von HTF Gap)

H1: 1 Verfeinerung(en)
  #1:
    Time: 2022-10-10 16:00:00+00:00
    Direction: bullish
    Pivot (Open K2): 0.76416
    Extreme: 0.76254
    Near (Entry): 0.76379
    Size: 0.00125 (12.5 pips, 16.6% von HTF Gap)
```

---

### 2. `validation_fixed_pivot.py`

**Zweck**: Validierung eines **spezifischen** Pivots (für Debugging)

**Usage**: Script direkt editieren (PAIR, HTF_TF, K2_DATE ändern), dann ausführen

---

## Validierungs-Prozess

### 1. Script ausführen
```bash
python validation_random_pivots.py
```

### 2. TXT-Datei öffnen
- Datei in `results/random_validation_*.txt`
- Enthält alle Pivot-Details

### 3. Manuelle Validierung in TradingView

Für jeden Pivot im TXT:

**a) HTF-Pivot prüfen:**
1. Öffne Pair auf Weekly Chart
2. Navigiere zu K2 Time
3. Prüfe 2-Kerzen-Muster:
   - Bullish: K1 rot → K2 grün
   - Bearish: K1 grün → K2 rot
4. Markiere Levels:
   - Pivot (Open K2)
   - Extreme (längerer Wick)
   - Near (kürzerer Wick)
5. Markiere Gaps:
   - Pivot Gap (Pivot bis Extreme)
   - Wick Diff (Near bis Extreme)

**b) Verfeinerungen prüfen:**

Für jede Verfeinerung im TXT:
1. Wechsle zur Verfeinerungs-TF (3D/D/H4/H1)
2. Navigiere zur Verfeinerungs-Time
3. Prüfe 2-Kerzen-Muster (gleiche Direction wie HTF)
4. Prüfe Position: KOMPLETT innerhalb Wick Diff?
5. Prüfe Size: <= 20% von HTF Gap?
6. Prüfe Unberührt: NEAR nicht berührt bis HTF valid_time?
7. Prüfe Doji-Filter: Body >= 5%?

**c) Ergebnis notieren:**
- ✅ Korrekt = Logik validiert
- ❌ Fehler = Notiere Abweichung

### 4. Bei Abweichungen
- Notiere Details in separater Datei
- Prüfe ob Datenunterschied (Oanda vs TradingView)
- Oder Logik-Fehler im Code

---

## Verfeinerungs-Regeln (Kurzfassung)

✅ **Zeitfenster**: K2 >= HTF K1 OPEN und < HTF K3 OPEN
✅ **Größe**: Size <= 20% HTF Gap
✅ **Position**: KOMPLETT in Wick Diff ODER Extreme exakt auf HTF Near
✅ **Unberührt**: NEAR nicht berührt bis HTF valid_time
✅ **Doji**: Body >= 5%
✅ **Direction**: Gleich wie HTF-Pivot

**Priorität**:
1. Höchster TF (3D > D > H4 > H1)
2. Bei mehreren auf gleichem TF: Am nächsten zu HTF Near

---

## Results

Der `results/` Ordner enthält:
- `random_validation_*.txt` - Detaillierte Pivot-Strukturen
- `summary_*.csv` - CSV mit Übersicht

---

*Last Updated: 28.12.2025*
