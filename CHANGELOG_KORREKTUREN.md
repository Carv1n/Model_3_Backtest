# Model 3 - Korrekturen & Anpassungen

## 📝 Übersicht

Dieses Dokument listet alle Korrekturen auf, die basierend auf der finalen Klärung der Strategie-Regeln vorgenommen wurden.

**Letzte Updates**:
- 28.12.2025: Initiale Korrekturen
- 29.12.2025: TP-Check Korrektur

---

## ✅ KORREKTUREN

### 1. Höchster TF für Verfeinerungen = Weekly (NICHT Monthly!)

**Vorher**: Dachte M > W > 3D > D > H4 > H1
**Jetzt**: **W > 3D > D > H4 > H1** (Weekly ist Maximum!)

**Betroffen**:
- ✅ `STRATEGIE.md`
- ✅ `MODEL3_CONFIG.md`
- ✅ `archive/MODEL 3 KOMMPLETT`
- ✅ `scripts/backtesting/backtest_model3.py` (Code-Korrektur nötig)

---

### 2. "Unberührt"-Check präzisiert

**Vorher**: Dachte Wick Diff der Verfeinerung darf nicht berührt werden
**Jetzt**: **Open K2 der Verfeinerung** darf nicht berührt werden (nicht erst Wick Diff!)

**Zwei Phasen**:
1. **Während HTF-Pivot-Entstehung** (K1/K2): Open K2 der Verfeinerung darf NICHT berührt werden → sonst ungültig
2. **Nach HTF-Pivot valide**: Entry nur bei Berührung der Wick Diff der Verfeinerung (Open K2 spielt keine Rolle mehr)

**Betroffen**:
- ✅ `STRATEGIE.md`
- ✅ `MODEL3_CONFIG.md`
- ✅ `archive/MODEL 3 KOMMPLETT`
- ✅ `scripts/backtesting/backtest_model3.py` (Code-Korrektur nötig)

---

### 3. Versatz-Regel = NICHT Standard!

**Vorher**: Unklar ob Versatz-Regel Standard ist
**Jetzt**: **Standard = OHNE Versatz-Regel** (weder bei Pivots noch Verfeinerungen)

Versatz-Regel ist:
- Zum Backtesten aktivierbar
- Nicht Teil der Standard-Konfiguration
- Gilt für Pivots UND Verfeinerungen wenn aktiviert

**Betroffen**:
- ✅ `STRATEGIE.md`
- ✅ `MODEL3_CONFIG.md`
- ✅ `archive/MODEL 3 KOMMPLETT`
- ❌ `scripts/backtesting/backtest_model3.py` (noch nicht implementiert, später hinzufügen)

---

### 4. Alternative Entry-Varianten präzisiert

**Vorher**: Close-Modi unklar formuliert
**Jetzt**: **Close muss ÜBER (bullish) / UNTER (bearish) dem NEAR sein**

**Bedeutung**:
- Körper der Kerze muss JENSEITS NEAR schließen
- Nur der Wick darf in der Verfeinerung sein
- NICHT der Körper!

**Beispiel Bullish**:
- Verfeinerung NEAR bei 1.1000
- 1H Kerze: Low 1.0995, Close 1.1005 → ✅ GÜLTIG (Close über NEAR)
- 1H Kerze: Low 1.0995, Close 1.0998 → ❌ UNGÜLTIG (Close unter NEAR, Körper in Verfeinerung)

**Betroffen**:
- ✅ `STRATEGIE.md`
- ✅ `MODEL3_CONFIG.md`
- ✅ `archive/MODEL 3 KOMMPLETT`
- ✅ `scripts/backtesting/backtest_model3.py` (Code-Korrektur nötig)

---

### 5. Daten-Zeitraum präzisiert

**Vorher**: "ab 2010" oder ähnlich
**Jetzt**: **Max verfügbare Daten pro Asset nutzen** (kein fixer Start-Zeitpunkt!)

**Bedeutung**:
- Jedes Pair hat unterschiedlich viel historische Daten
- Wir nutzen ALLE verfügbaren Daten pro Pair
- Kein fixer Start wie "2010-01-01"
- START_DATE = None → nutzt automatisch älteste verfügbare Daten

**Betroffen**:
- ✅ `STRATEGIE.md`
- ✅ `MODEL3_CONFIG.md`
- ✅ `archive/MODEL 3 KOMMPLETT`

---

### 6. Standard Entry-Modus = direct_touch

**Vorher**: Verschiedene Angaben (teils 1h_close als Standard)
**Jetzt**: **direct_touch ist Standard-Einstellung**

**Zu testen**:
- direct_touch (Standard)
- 1h_close (Close ÜBER/UNTER NEAR)
- 4h_close (Close ÜBER/UNTER NEAR)

**Betroffen**:
- ✅ `STRATEGIE.md`
- ✅ `MODEL3_CONFIG.md`
- ✅ `archive/MODEL 3 KOMMPLETT`
- ✅ Alle Beispiel-Commands in Doku

---

### 8. RR Berechnung Bug behoben (29.12.2025) ✅

**Problem**: Nach SL-Anpassung (wenn RR > 1.5) wurde `rr` nicht aktualisiert

**Bug**:
```python
if rr > 1.5:
    sl = entry + reward / 1.5  # SL angepasst
return sl, tp, rr  # ❌ rr ist noch der ALTE Wert!
```

**Fix**:
```python
if rr > 1.5:
    sl = entry + reward / 1.5
    rr = 1.5  # ✅ RR auf 1.5 setzen!
return sl, tp, rr
```

**Beispiel (AUDNZD M Juli 2018)**:
- Entry: 1.09737
- Reward: 98.5 pips (zu TP)
- Risk initial: 59.8 pips → RR = 1.64
- SL erweitert auf 65.7 pips → RR sollte 1.5 sein
- **VORHER**: Return (..., ..., 1.64) ❌
- **JETZT**: Return (..., ..., 1.5) ✅

**Betroffen**:
- ✅ `scripts/backtesting/backtest_model3.py` - `compute_sl_tp()` Zeile 595

---

### 7. TP-Check Logik korrigiert (29.12.2025) ✅ FINAL

**Problem 1 - Zeitpunkt falsch**: TP-Check startete ab Gap Touch
**Lösung 1**: Check startet ab **max(Valid Time, Gap Touch)**

**Problem 2 - Check-Fenster falsch**: TP-Check prüfte die gesamte Zeit nach Gap Touch (ohne Ende)
**Lösung 2**: Check endet **BEI Entry Time** (nicht danach!)

**Problem 3 - Reihenfolge falsch**: TP-Check wurde VOR Entry-Suche durchgeführt
**Lösung 3**: Check wird NACH Entry-Suche durchgeführt (Entry Time muss bekannt sein!)

**FINALE LOGIK**:
1. Gap Touch finden
2. Entry-Kandidaten bestimmen (mit RR-Check)
3. Entry suchen (jetzt kennen wir Entry Time!)
4. TP-Check: Prüfe ob TP berührt zwischen **max(Valid Time, Gap Touch)** und **Entry Time**
5. Wenn TP berührt in diesem Fenster → Setup ungültig
6. Wenn TP berührt NACH Entry → egal (normaler Trade-Verlauf)

**Wichtig**:
- TP darf NICHT berührt werden zwischen Gap Touch und Entry
- Wenn TP vor Gap Touch berührt → egal (irrelevant)
- Wenn TP nach Entry berührt → egal (normaler Trade)
- Check-Fenster: `max(Valid Time, Gap Touch)` bis `Entry Time`

**Beispiel (AUDNZD M Juni/Juli 2018)**:
- Gap Touch: 01.08.2018 00:00
- Entry: 01.08.2018 01:00
- TP berührt: 29.08.2018 14:00 (28 Tage NACH Entry!)
- **VORHER**: Setup ungültig ❌ (falsch - TP-Check hatte kein Ende!)
- **JETZT**: Setup gültig ✅ (TP nach Entry ist ok!)

**Betroffen**:
- ✅ `scripts/backtesting/backtest_model3.py` - Funktion `check_tp_touched_before_entry()` korrigiert (+entry_time Parameter)
- ✅ `Backtest/01_test/01_Validation/validation_trades.py` - Reihenfolge korrigiert (TP-Check nach Entry-Suche)
- ✅ `STRATEGIE_REGELN.md` - TP-Check Beschreibung präzisiert
- ✅ `MODEL3_CONFIG.md` - Entry-Hinweise aktualisiert

---

## 🔧 CODE-KORREKTUREN

### `scripts/backtesting/backtest_model3.py`

#### 0a. RR Berechnung korrigieren (29.12.2025 - ERLEDIGT ✅)
```python
# In compute_sl_tp() Funktion:

# ❌ VORHER (Zeile 586-595):
rr = reward / risk
if rr < 1.0:
    return None
if rr > 1.5:
    if direction == "bullish":
        sl = entry - reward / 1.5
    else:
        sl = entry + reward / 1.5
return sl, tp, rr  # ❌ Bug: rr ist noch alt (z.B. 1.64)!

# ✅ JETZT:
rr = reward / risk
if rr < 1.0:
    return None
if rr > 1.5:
    if direction == "bullish":
        sl = entry - reward / 1.5
    else:
        sl = entry + reward / 1.5
    rr = 1.5  # ✅ Fix: rr auf 1.5 setzen!
return sl, tp, rr
```

#### 0b. TP-Check Logik korrigieren (29.12.2025 - ERLEDIGT ✅)
```python
def check_tp_touched_before_entry(
    df: pd.DataFrame,
    pivot: Pivot,
    gap_touch_time: pd.Timestamp,
    entry_time: pd.Timestamp,  # ✅ NEU: Entry Time hinzugefügt!
    tp: float
) -> bool:
    # ❌ VORHER: Filtere ab Gap Touch (ohne Ende!)
    df_after_gap = df[df["time"] > gap_touch_time].copy()
    # Problem: Prüft ALLE Zeit nach Gap Touch, auch nach Entry!

    # ✅ JETZT: Check-Fenster von max(Valid Time, Gap Touch) BIS Entry
    start_time = max(pivot.valid_time, gap_touch_time)
    df_check_window = df[(df["time"] >= start_time) & (df["time"] < entry_time)].copy()

    # Prüfe ob TP im Check-Fenster berührt wurde
    for _, row in df_check_window.iterrows():
        if pivot.direction == "bullish":
            if row["high"] >= tp:
                return True  # TP vor Entry → ungültig
        else:
            if row["low"] <= tp:
                return True  # TP vor Entry → ungültig

    return False  # TP nicht im Fenster → valide
```

**Zusätzlich in `validation_trades.py`**:
```python
# ❌ VORHER: TP-Check VOR Entry-Suche (Entry Time unbekannt!)
tp_touched = check_tp_touched_before_entry(h1_df, pivot, gap_touch_time, tp_price)
if tp_touched:
    return None

# ... später Entry suchen ...

# ✅ JETZT: TP-Check NACH Entry-Suche (Entry Time bekannt!)
# 1. Entry suchen
for idx, candle in entry_window.iterrows():
    if ...:
        entry_time = candle["time"]
        break

if entry_time is None:
    return None

# 2. JETZT TP-Check mit Entry Time
tp_touched = check_tp_touched_before_entry(h1_df, pivot, gap_touch_time, entry_time, tp_price)
if tp_touched:
    return None  # TP vor Entry berührt → ungültig
```

#### 1. Refinement Dataclass erweitern
```python
@dataclass
class Refinement:
    # ... existing fields ...
    near: float  # ✅ HINZUGEFÜGT
```

#### 2. Entry-Level korrigieren
```python
@property
def entry_level(self) -> float:
    # ❌ VORHER: return self.pivot_level
    # ✅ JETZT: return self.near
    return self.near
```

#### 3. Wick Difference Berechnung korrigieren
```python
# ❌ VORHER:
wick_low = min(htf_pivot.extreme, htf_pivot.near)
wick_high = max(htf_pivot.extreme, htf_pivot.near)

# ✅ JETZT:
if htf_pivot.direction == "bullish":
    wick_low = htf_pivot.extreme  # tiefster Punkt
    wick_high = htf_pivot.near    # höherer Low
else:  # bearish
    wick_low = htf_pivot.near     # tieferer High
    wick_high = htf_pivot.extreme # höchster Punkt
```

#### 4. Refinement-Such-Zeitraum korrigieren
```python
# ❌ VORHER:
if k2["time"] <= htf_pivot.time:
    continue  # erst nach HTF-Pivot

# ✅ JETZT:
if k2["time"] > htf_pivot.valid_time:
    continue  # muss WÄHREND K1/K2 entstanden sein
```

#### 5. "Unberührt"-Check korrigieren
```python
# ✅ NEU: Check ob OPEN K2 der Verfeinerung berührt wurde
refinement_created = k2["time"]
touch_window = df[(df["time"] > refinement_created) & (df["time"] <= htf_pivot.valid_time)]

was_touched = False
for _, candle in touch_window.iterrows():
    if direction == "bullish":
        # Open K2 der Verfeinerung = k2["open"]
        if candle["low"] <= k2["open"]:  # Open K2 berührt
            was_touched = True
            break
    else:  # bearish
        if candle["high"] >= k2["open"]:  # Open K2 berührt
            was_touched = True
            break

if was_touched:
    continue  # Refinement ungültig
```

#### 6. Entry-Bestätigung (Close-Modi) korrigieren
```python
# Für 1h_close und 4h_close:
if direction == "bullish":
    # ❌ VORHER: if close > refinement.entry_level
    # ✅ JETZT: if close > refinement.near
    if candle["close"] > refinement.near:
        entry_confirmed = True
else:  # bearish
    if candle["close"] < refinement.near:
        entry_confirmed = True
```

---

## 📁 GEÄNDERTE DATEIEN

### Dokumentation
1. ✅ `STRATEGIE.md` - Alle Korrekturen eingepflegt
2. ✅ `MODEL3_CONFIG.md` - Standard-Einstellungen angepasst
3. ✅ `archive/MODEL 3 KOMMPLETT` - Vollständige Dokumentation korrigiert

### Code (noch anzupassen)
4. ⏳ `scripts/backtesting/backtest_model3.py` - Code-Korrekturen implementieren

---

## 🎯 NÄCHSTE SCHRITTE

1. ✅ Dokumentation korrigiert
2. ✅ TP-Check Code korrigiert (29.12.2025) - FINALE VERSION
   - ✅ Entry Time Parameter hinzugefügt
   - ✅ Check-Fenster mit Ende definiert (bis Entry)
   - ✅ Reihenfolge in validation_trades.py korrigiert
3. ✅ RR Berechnung Bug behoben (29.12.2025)
   - ✅ `rr = 1.5` nach SL-Anpassung setzen
4. ✅ Validation-Test durchgeführt (AUDNZD M Juli 2018)
   - ✅ Trade gefunden mit korrekten Werten
   - ✅ RR = 1.50 (exakt wie TradingView)
   - ✅ Entry bei W Verfeinerung (1.09737), nicht HTF Near
   - ✅ Exit: SL mit -1.00R
5. ⏳ Weitere Validation-Tests durchführen (random Pivots)
6. ⏳ Manuell validieren (TradingView)
7. ⏳ Falls korrekt → Full Backtest
8. ⏳ Weitere Code-Korrekturen (#1-6) implementieren

---

*Last Updated: 29.12.2025*
