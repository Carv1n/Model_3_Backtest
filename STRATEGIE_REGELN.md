# Model 3 - Technische Strategie-Regeln

**Stand**: 2025-12-31 (Fixes: JPY Pips, H1 Gap Touch, TP-Check Logik, RR Berechnung)

Dieses Dokument enthält ALLE technischen Regeln der Strategie - kompakt und vollständig.

---

## 1. PIVOT-STRUKTUR

### Pivot-Pattern (2-Kerzen-Regel)

**Bullish Pivot:**
- K1: Rote Kerze (Close < Open)
- K2: Grüne Kerze (Close > Open)
- **Pivot** = Open K2
- **Extreme** = min(K1 Low, K2 Low) - tiefster Punkt
- **Near** = max(K1 Low, K2 Low) - höherer Low (kürzeres Wick!)
- **Gap** = abs(Pivot - Extreme)
- **Wick Diff** = abs(Extreme - Near) - Zone zwischen den Wicks

**Bearish Pivot:**
- K1: Grüne Kerze (Close > Open)
- K2: Rote Kerze (Close < Open)
- **Pivot** = Open K2
- **Extreme** = max(K1 High, K2 High) - höchster Punkt
- **Near** = min(K1 High, K2 High) - tieferer High (kürzeres Wick!)
- **Gap** = abs(Pivot - Extreme)
- **Wick Diff** = abs(Extreme - Near)

### HTF-Pivots

**Timeframes**: 3D, W, M

**Filter:**
- Doji-Filter: Body >= 5% der Candle Range (BEIDE Kerzen)
- Versatz: KEINER (Standard)

**Valid Time:**
- Pivot wird valide NACH Close K2
- Valid Time = K3 Open

**Timestamps:**
- ALLE Timestamps = OPEN-Zeit der Bars (sehr wichtig!)

---

## 2. VERFEINERUNGEN

### Definition
Verfeinerung = Kleinerer Pivot innerhalb HTF Pivot Wick Diff

### Timeframes
**Abhängig von HTF:**
- M-Pivot → Suche in: W, 3D, D, H4, H1
- W-Pivot → Suche in: 3D, D, H4, H1
- 3D-Pivot → Suche in: D, H4, H1

**Max TF = Weekly!**

### Gültigkeitsbedingungen (ALLE müssen erfüllt sein)

**1. Zeitfenster:**
- K1 UND K2 der Verfeinerung müssen zwischen HTF K1 OPEN und HTF K3 OPEN liegen
- Verfeinerung entsteht WÄHREND HTF Pivot-Formation

**2. Größe:**
- Verfeinerung Wick Diff ≤ 20% der HTF Pivot Gap
- Berechnung: abs(Extreme - Near) der Verfeinerung
- Gemessen an: HTF Gap (NICHT Wick Diff!)

**3. Position:**
- **Standard**: Verfeinerung zwischen HTF Extreme und HTF Near
  - Bullish: Verf. Extreme >= HTF Extreme UND Verf. Near <= HTF Near
  - Bearish: Verf. Extreme <= HTF Extreme UND Verf. Near >= HTF Near
- **Ausnahme**: Verfeinerung Extreme EXAKT auf HTF Near
  - Dann: Near darf außerhalb liegen (schneidet sich in einem Punkt)

**4. Daten-Korrektur:**
- **Logik**: Verfeinerung in K1+K2 kann NICHT stärkeres Extreme als HTF haben
- **Wenn doch**: Nutze HTF Extreme (H1/H4 Oanda-Daten können abweichen)
- **Grund**: D-M Daten (TradingView) exakt, H1-H4 (Oanda API) können Abweichungen haben

**5. Unberührt:**
- **OPEN K2** der Verfeinerung darf NICHT berührt werden
- Zeitraum: Zwischen Verfeinerung Entstehung und HTF Valid Time
- Bei Touch → Verfeinerung ungültig
- **WICHTIG**: NICHT Near, sondern k2["open"] (Pivot Level)!
- **Ab Valid Time**: k2 open spielt keine Rolle mehr, nur Near für Entry

**6. Doji-Filter:**
- Body >= 5% (BEIDE Kerzen)
- Gleicher Filter wie HTF-Pivots

**7. Richtung:**
- Verfeinerung muss gleiche Richtung wie HTF haben

### Priorität
Bei mehreren Verfeinerungen:
1. **Höchster Timeframe**: W > 3D > D > H4 > H1
2. **Bei gleichem TF**: Nächste zu HTF Near

### Precision
- Alle Preise: 5 Nachkommastellen
- Vergleiche: Tolerance 0.00001 (Floating-Point-Fehler)
- Position-Check: Mit Tolerance

---

## 3. ENTRY-REGELN

### Voraussetzungen

**1. Gap Touch (auf H1!)**
- HTF Pivot Gap muss ZUERST berührt werden
- **WICHTIG**: Prüfung auf H1-Daten (stunden-genau, nicht nur Datum!)
- Vorteil: H1 gibt exakte Stunde, Daily nur Datum
- Gilt auch bei W/M Pivots - immer auf H1 prüfen!

**2. TP-Check** ✅ (korrigiert 31.12.2025)
- TP (-1 Fib) darf NICHT berührt werden **zwischen Gap Touch und Entry**
- **WICHTIG**: Check-Fenster: `Gap Touch Time` (H1 exakt!) **bis** `Entry Time`
- Check startet AB Gap Touch (nicht ab Valid Time!)
- Warum? TP VOR Gap Touch ist irrelevant (Pivot war noch nicht activated)
- Check endet BEI Entry (nicht danach!)
- **Regel**: Wenn TP zwischen Gap Touch und Entry → Setup **ungültig**
- Wenn TP NACH Entry → egal (normaler Trade-Verlauf)
- Wenn TP VOR Gap Touch → **OKAY** (Trade ist valide!)
- **Multi-TF**: M ungültig → W/3D bleiben valide (wenn deren TPs nicht berührt)
- **Implementation**: `check_tp_touched_before_entry_fast(df, pivot, gap_touch_time, entry_time, tp)`

### Entry-Level bestimmen

**Standard: Verfeinerung**
- Höchste Verfeinerung nach Priorität
- Entry bei: Verfeinerung Near

**Bei Wick Diff < 20%:**
- Entry bei: Wick Diff = HTF Near
- **Ausnahme**: Wenn Verfeinerung mit Extreme auf HTF Near existiert
  - → Diese ist näher am Pivot
  - → Entry bei Verfeinerung Near

**RR-Check:**
- Entry muss >= 1 RR ergeben
- Wenn < 1 RR → Verwerfen, nächste Verfeinerung nehmen

### Entry-Bestätigung

**Standard: direct_touch**
- Entry sofort bei Touch des Entry-Levels
- Keine Close-Bestätigung nötig

**Alternativ (für Tests):**
- 1h_close: Warte auf 1H Close jenseits Near
- 4h_close: Warte auf 4H Close jenseits Near

---

## 4. EXIT-REGELN

### Stop Loss

**Minimum-Anforderungen (BEIDE):**
1. >= 60 Pips von Entry
2. Jenseits Fib 1.1
   - Fib 1.1 = Fib 1 (Extreme) ± 10% Gap
   - Bullish: SL UNTER Fib 1.1
   - Bearish: SL ÜBER Fib 1.1

**SL Position:**
- SL = min(Fib 1.1, Entry - 60 Pips) bei bullish
- SL = max(Fib 1.1, Entry + 60 Pips) bei bearish

### Take Profit

**Fix auf -1 Fib:**
- -1 Fib = Gleiche Distanz wie Gap, in andere Richtung
- Bullish: TP = Pivot + Gap (oberhalb)
- Bearish: TP = Pivot - Gap (unterhalb)

### Risk/Reward

**Minimum: 1 RR**
- Wenn < 1 RR → Setup verwerfen

**Maximum: 1.5 RR**
- Wenn > 1.5 RR → SL vergrößern bis exakt 1.5 RR
- Entry und TP bleiben unverändert
- **WICHTIG**: Nach SL-Anpassung muss RR auf 1.5 gesetzt werden (nicht altes RR returnen!)

---

## 5. FIBONACCI-LEVELS

**Bullish:**
- Fib 0 = Pivot (oben)
- Fib 1 = Extreme (unten, tiefster Punkt)
- Fib 1.1 = Extreme - 10% Gap (noch tiefer)
- Fib -1 = Pivot + Gap (TP, oberhalb)

**Bearish:**
- Fib 0 = Pivot (unten)
- Fib 1 = Extreme (oben, höchster Punkt)
- Fib 1.1 = Extreme + 10% Gap (noch höher)
- Fib -1 = Pivot - Gap (TP, unterhalb)

---

## 6. WICHTIGE HINWEISE

### Timestamps
- **IMMER** OPEN-Zeit der Bars
- Beispiel 1H @ 20:00 → Opens 20:00, closes 20:59
- Beispiel Daily @ 18.06 → Opens 18.06 00:00, closes 18.06 23:59
- Beispiel Weekly @ 16.06 → Opens Monday 00:00, closes Friday 23:59

### Datenqualität
- **D-M Daten**: TradingView → 100% exakt
- **H1-H4 Daten**: Oanda API → Können abweichen
- Daten-Korrektur in Code implementiert

### Multi-Timeframe
Bei gleichzeitigen Pivots (3D, W, M):
- Alle sind unabhängig
- Wenn M ungültig (TP berührt) → W/3D bleiben gültig
- Jedes HTF hat eigenen TP

### Versatz-Regel
- Standard: **OHNE** Versatz
- Weder bei Pivots noch bei Verfeinerungen
- Kann für Tests aktiviert werden

---

## 7. CHECKLISTE FÜR VALIDATION

**HTF Pivot:**
- [ ] K1 + K2 korrekte Richtung?
- [ ] Body >= 5% (beide)?
- [ ] Pivot, Extreme, Near korrekt?
- [ ] Valid Time = K3 Open?

**Verfeinerung:**
- [ ] K1 + K2 zwischen HTF K1-K3?
- [ ] Gleiche Richtung wie HTF?
- [ ] Size <= 20% HTF Gap?
- [ ] Position zwischen Extreme und Near?
- [ ] Near unberührt bis HTF Valid Time?
- [ ] Body >= 5% (beide)?

**Trade:**
- [ ] Gap Touch auf H1?
- [ ] TP nicht berührt zwischen max(Valid Time, Gap Touch) und Entry?
- [ ] Entry-Level korrekt (Verf./Wick Diff)?
- [ ] RR >= 1?
- [ ] SL >= 60 Pips + jenseits Fib 1.1?
- [ ] TP = -1 Fib?
