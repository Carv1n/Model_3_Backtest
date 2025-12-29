# Model 3 - Trade Validation

## Das einzige aktuelle Script

### `validation_trades.py` ✅
**Nutzt die KOMPLETTE, korrigierte Backtest-Logik!**

**Zweck**:
- Validiert komplette Trades (Pivot → Verfeinerungen → Entry → Exit)
- Testet 6 verschiedene Configs mit random Pivots
- Zur manuellen Überprüfung in TradingView

**Config**:
- **AUDNZD M** (Monthly)
- **GBPUSD M** (Monthly)
- **EURUSD W** (Weekly)
- **USDJPY W** (Weekly)
- **NZDCAD 3D** (3-Day)
- **GBPJPY 3D** (3-Day)
- Je 1 random Pivot pro Config
- Zeitraum: 2005-2025 (alle verfügbaren Daten)

**Ausführung**:
```bash
python validation_trades.py
```

**Implementierte Fixes (29.12.2025)**:
1. ✅ **TP-Check Logik korrigiert**:
   - Check nur zwischen Gap Touch und Entry (nicht danach!)
   - Entry Time Parameter hinzugefügt
   - Reihenfolge: Entry suchen → DANN TP-Check
2. ✅ **RR Berechnung korrigiert**:
   - Nach SL-Erweiterung (RR > 1.5) wird `rr = 1.5` gesetzt
   - Vorher: Return falsches RR (z.B. 1.64)
   - Jetzt: Return korrektes RR (1.50)

**Alle Regeln implementiert**:
1. Gap Touch auf Daily-Daten (auch bei W/M Pivots!)
2. TP-Check: TP nicht berührt zwischen Gap Touch und Entry
3. Wick Diff Entry bei < 20% (außer Verfeinerung näher)
4. RR-Check für alle Entry-Levels (>= 1.0)
5. SL-Erweiterung bei RR > 1.5 (max 1.5)

**Output-Format**:
```
TRADE #1: AUDNZD M
================================================================================

--- HTF PIVOT ---
K1 Time (Open): 2024-07-01 00:00:00+00:00
K2 Time (Open): 2024-08-01 00:00:00+00:00
Valid Time (K3 Open): 2024-09-01 00:00:00+00:00
Direction: bullish
Pivot (Open K2): 1.07538
Extreme: 1.07022
Near: 1.07252
Gap: 51.6 pips
Wick Diff: 23.0 pips (44.6% von Gap)

--- GAP TOUCH ---
Gap Touch Time (Daily): 2024-08-08 00:00:00+00:00

--- TP-CHECK ---
TP (-1 Fib): 1.08054
TP touched before entry: NO ✓

--- VERFEINERUNGEN ---
Total: 6
Priority: W (10.07, Near: 1.07264)

--- ENTRY ---
Entry Level: Verfeinerung W Near
Entry Price: 1.07264
Entry Time: 2024-09-08 08:00:00+00:00

--- EXIT ---
SL: 1.06700 (56.4 pips)
TP: 1.08054 (79.0 pips)
RR: 1.40
Exit: TP HIT at 2024-11-13 15:00:00+00:00
PnL: +79.0 pips (+1.40 R) ✓
```

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

## Wichtige Regeln (Kurzfassung)

**Siehe `STRATEGIE_REGELN.md` für ALLE Details!**

### Verfeinerungen (7 Bedingungen):
1. **Zeitfenster**: K1 UND K2 zwischen HTF K1 Open und K3 Open
2. **Größe**: Wick Diff ≤ 20% HTF Gap
3. **Position**: Zwischen HTF Extreme und Near (mit Daten-Korrektur)
4. **Daten-Korrektur**: Wenn Verf. stärkeres Extreme → Nutze HTF Extreme
5. **Unberührt**: Near nicht berührt bis HTF Valid Time
6. **Doji**: Body >= 5%
7. **Richtung**: Gleich wie HTF

### Entry-Voraussetzungen:
1. **Gap Touch auf Daily** (auch bei W/M!)
2. **TP-Check**: TP nicht berührt vor Entry
3. **Entry-Level**: Verfeinerung ODER Wick Diff (bei < 20%)
4. **RR-Check**: >= 1 RR erforderlich

### Priorität:
1. Höchster TF (W > 3D > D > H4 > H1)
2. Bei mehreren: Am nächsten zu HTF Near

---

## Results

Der `results/` Ordner enthält:
- `trade_validation_*.txt` - Komplette Trade-Simulationen

**Was validiert wird**:
- Pivot-Struktur (K1, K2, Extreme, Near)
- Verfeinerungen (alle 7 Bedingungen)
- Gap Touch (auf Daily!)
- TP-Check (vor Entry)
- Entry-Level (Verfeinerung vs Wick Diff)
- SL/TP Berechnung
- RR-Check
- Trade-Simulation (Entry, Exit, PnL)

---

*Last Updated: 29.12.2025*
