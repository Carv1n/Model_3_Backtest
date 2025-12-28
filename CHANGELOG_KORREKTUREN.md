# Model 3 - Korrekturen & Anpassungen (28.12.2025)

## 📝 Übersicht

Dieses Dokument listet alle Korrekturen auf, die basierend auf der finalen Klärung der Strategie-Regeln vorgenommen wurden.

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

## 🔧 CODE-KORREKTUREN NÖTIG

### `scripts/backtesting/backtest_model3.py`

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
2. ⏳ Code korrigieren (`backtest_model3.py`)
3. ⏳ Validation-Test durchführen
4. ⏳ Manuell validieren (TradingView)
5. ⏳ Falls korrekt → Full Backtest

---

*Last Updated: 28.12.2025*
