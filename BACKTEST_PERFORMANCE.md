# Backtest Performance & Optimierung

## 🔍 Wie funktioniert das Script?

### Aktueller Ablauf (backtest_model3.py)

```python
for pair in pairs:                           # 28 Pairs
    # 1. Lade ALLE Timeframes für dieses Pair
    cache = {
        "H1": load_tf_data("H1", pair),     # ~15 Jahre × 365 × 24 = ~130.000 Kerzen
        "H4": load_tf_data("H4", pair),     # ~32.000 Kerzen
        "D": load_tf_data("D", pair),       # ~5.500 Kerzen
        "3D": load_tf_data("3D", pair),     # ~1.800 Kerzen
        "W": load_tf_data("W", pair),       # ~780 Kerzen
        "M": load_tf_data("M", pair),       # ~180 Kerzen
    }

    for htf_tf in ["3D", "W", "M"]:         # 3 HTF-Timeframes
        # 2. Finde HTF-Pivots (auf 3D/W/M)
        pivots = detect_htf_pivots(htf_df)  # z.B. ~100-300 Pivots pro Pair

        for pivot in pivots:
            # 3. Suche Verfeinerungen (auf H1, H4, D, 3D, W)
            refinements = detect_refinements()

            # 4. Simuliere Entry/Exit auf H1
            # Iteriert durch H1-Daten ab Pivot-Time
            for h1_candle in h1_data:       # Kann 1000+ Kerzen sein
                # Prüfe Gap-Trigger, Refinement-Touch, Entry, Exit
```

---

## ⏱️ Performance-Analyse

### Geschwindigkeit pro Pair

**1 Pair (z.B. EURUSD, 2010-2025):**
- **Daten laden**: ~2-5 Sekunden (alle 6 TFs)
- **Pivot-Erkennung**: ~0.1 Sekunden pro HTF-TF
- **Verfeinerungs-Suche**: ~0.5-2 Sekunden pro Pivot
- **Entry/Exit-Simulation**: ~0.1-1 Sekunde pro Trade

**Gesamt pro Pair**: ~10-30 Sekunden (je nach Anzahl Pivots/Trades)

### Hochrechnung

**28 Pairs:**
- Optimistisch: 28 × 10 Sek = **~5 Minuten**
- Realistisch: 28 × 20 Sek = **~10 Minuten**
- Pessimistisch: 28 × 30 Sek = **~15 Minuten**

**Für Validation-Sampler (2 Pairs):**
- **~20-60 Sekunden**

---

## 🐌 Performance-Probleme

### Bottlenecks

1. **H1-Daten laden** (~130k Kerzen pro Pair)
   - Größte Datei
   - Wird für JEDEN Pivot durchsucht

2. **Verfeinerungs-Suche**
   - Iteriert durch ALLE LTF-Daten
   - Für JEDEN HTF-Pivot
   - Kann 1000+ Kerzen sein

3. **Entry/Exit-Simulation**
   - Iteriert durch H1 ab Gap-Trigger
   - Bis Trade geschlossen
   - Im Worst-Case: Monate/Jahre

### Warum H1?

**Gap-Trigger & Entry-Simulation laufen auf H1:**
- Gap-Trigger: Wann berührt Preis die HTF-Pivot-Gap? → H1 für Präzision
- Entry: Wann berührt Preis die Verfeinerung? → H1 für Präzision
- Exit: Wann SL/TP getroffen? → H1 für Präzision

**Problem:**
- H1 = 130.000 Kerzen
- Für JEDEN Pivot werden potentiell 1000+ H1-Kerzen durchsucht

---

## 🚀 Optimierungen

### 1. **Nur relevante H1-Daten laden** (WICHTIG!)

**Aktuell:**
```python
h1_df = load_tf_data("H1", pair)  # Alle 130k Kerzen
```

**Optimiert:**
```python
# Nur H1-Daten ab frühestem Pivot
earliest_pivot_time = min(p.time for p in all_pivots)
h1_df = h1_df[h1_df["time"] >= earliest_pivot_time]
```

**Vorteil:** Reduziert H1-Daten um 50-80% wenn start_date gesetzt ist

---

### 2. **Vectorized Operations** (wo möglich)

**Aktuell:**
```python
for i in range(gap_touch_idx, len(h1_after)):  # Loop durch jede Kerze
    row = h1_after.iloc[i]
    if touched:
        # Entry-Logik
```

**Optimiert:**
```python
# Pandas Vectorized Operations nutzen
touched_mask = (h1_after["low"] <= ref_level) & (h1_after["high"] >= ref_level)
first_touch_idx = touched_mask.idxmax() if touched_mask.any() else None
```

**Vorteil:** 10-50x schneller für große Datensätze

---

### 3. **Parallel Processing** (für mehrere Pairs)

**Aktuell:**
```python
for pair in pairs:  # Sequentiell
    backtest(pair)
```

**Optimiert:**
```python
from multiprocessing import Pool

def backtest_pair(pair):
    # Backtest für 1 Pair
    return results

with Pool(processes=4) as pool:  # 4 Pairs parallel
    all_results = pool.map(backtest_pair, pairs)
```

**Vorteil:** 4x Speedup auf 4-Core CPU

---

### 4. **Caching von Verfeinerungen**

**Problem:** Gleiche Verfeinerungen werden mehrfach gesucht

**Lösung:**
```python
refinement_cache = {}  # {(pair, htf_tf, pivot_time): [refinements]}

def get_refinements(pair, htf_tf, pivot):
    key = (pair, htf_tf, pivot.time)
    if key not in refinement_cache:
        refinement_cache[key] = detect_refinements(...)
    return refinement_cache[key]
```

---

### 5. **Early Exit Optimierungen**

**Gap-Trigger:**
```python
# Sobald Gap getriggert, nur ab da weitersuchen
gap_touch_idx = find_first_touch(h1_df, gap_level)
h1_after = h1_df[gap_touch_idx:]  # Rest wegwerfen
```

**Trade Exit:**
```python
# Sobald Trade geschlossen, nicht weiter iterieren
if sl_hit or tp_hit:
    break  # ✅ Schon implementiert
```

---

## 📊 Realistische Zeiten (nach Optimierung)

### Mit Optimierungen 1-3

**1 Pair:**
- Optimistisch: ~5 Sekunden
- Realistisch: ~10 Sekunden

**28 Pairs:**
- Sequentiell: ~5-10 Minuten
- Parallel (4 Cores): **~2-3 Minuten**

**Validation (2 Pairs, 6 Samples):**
- **~10-20 Sekunden**

---

## 🎯 Empfohlene Optimierungen (Priorität)

### Sofort implementieren:

1. **Start-Date filtering** (einfach, großer Effekt)
   - Wenn start_date gesetzt: Filtere H1-Daten SOFORT
   - Spart 50-80% der Daten

2. **Vectorized Gap-Trigger** (mittlerer Aufwand, großer Effekt)
   - Finde Gap-Touch mit Pandas statt Loop
   - 10-50x schneller

### Später:

3. **Parallel Processing** (mittlerer Aufwand, 4x Speedup)
   - Nur für große Backtests (28 Pairs)
   - Für Validation nicht nötig

4. **Numba JIT Compilation** (fortgeschritten)
   - Für kritische Loops
   - Kann 10-100x schneller sein

---

## 🧪 Validation-Sampler Performance

**Aktuell (ohne Optimierung):**
- 2 Pairs × 3 HTF × 2 Zeiträume = 12 Backtest-Runs
- ~20-60 Sekunden total

**Mit Optimierung 1+2:**
- **~10-20 Sekunden**

**Akzeptabel!** ✅

---

## 💡 Weitere Optimierungen (für große Backtests)

### Datenbank statt CSV/Parquet
- SQLite mit Index auf time
- Schnellere Queries

### Chunked Processing
- Verarbeite Daten in Chunks (z.B. monatlich)
- Reduziert RAM-Usage

### Profile-Guided Optimization
- Profiling mit `cProfile`
- Identifiziere echte Bottlenecks
- Optimiere gezielt

---

## 🎯 Fazit

### Aktuelle Situation:
- **Validation**: ~20-60 Sekunden (akzeptabel)
- **28 Pairs Backtest**: ~10-15 Minuten (OK für gelegentliche Tests)

### Mit einfachen Optimierungen:
- **Validation**: ~10-20 Sekunden
- **28 Pairs**: ~2-3 Minuten (mit Parallel Processing)

### Für Produktiv-Backtests:
- Erst Validation durchführen
- Dann entscheiden ob Optimierung nötig
- Falls Backtests > 30 Min: Optimierungen 1-3 implementieren

---

**Recommendation:** Validation erst mal OHNE Optimierung starten, Zeiten messen, dann entscheiden! ⏱️

*Last Updated: 28.12.2025*
