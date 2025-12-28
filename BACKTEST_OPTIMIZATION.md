# Backtest Optimization Plan - Model 3

## Problem

Full Backtest über alle 28 Pairs + Weekly Pivots (2010-2025) = **Sehr langsam**

Warum?
- Für jeden Pivot: Lade und durchsuche 4 LTF-Datenframes (3D, D, H4, H1)
- Für jeden Trade: Simuliere Candle-by-Candle Entry/Exit auf H1
- Millionen von Rows zu durchsuchen

---

## Optimierungs-Strategien

### 1. ✅ Parquet statt CSV (BEREITS IMPLEMENTIERT)

**Was**: Parquet-Dateien statt CSV
**Speedup**: 5-10x schneller beim Laden
**Status**: ✅ Implementiert (`Data/Parquet/`)

---

### 2. Caching von LTF-Daten

**Problem**: LTF-Daten werden für jeden Pivot neu geladen

**Lösung**: Cache LTF-Daten pro Pair in Memory

```python
class Model3Backtester:
    def __init__(self):
        self.ltf_cache = {}  # {pair: {tf: df}}

    def load_ltf_for_pair(self, pair):
        if pair not in self.ltf_cache:
            self.ltf_cache[pair] = {
                "3D": load_tf_data("3D", pair),
                "D": load_tf_data("D", pair),
                "H4": load_tf_data("H4", pair),
                "H1": load_tf_data("H1", pair),
            }
        return self.ltf_cache[pair]
```

**Speedup**: 3-5x (LTF-Daten nur 1x laden statt N×)

---

### 3. Vectorized Operations statt Loops

**Problem**: Refinement-Suche = Python-Loop über alle Candles

**Lösung**: Pandas Vectorized Operations

```python
# AKTUELL (langsam):
for i in range(1, len(df)):
    k1 = df.iloc[i-1]
    k2 = df.iloc[i]
    # ... checks

# OPTIMIERT (schnell):
df['k1_red'] = df['close'] < df['open']
df['k2_green'] = df['close'].shift(-1) > df['open'].shift(-1)
df['is_bullish_pivot'] = df['k1_red'] & df['k2_green']
candidates = df[df['is_bullish_pivot']]
```

**Speedup**: 10-100x für große DataFrames

---

### 4. Parallel Processing

**Problem**: 28 Pairs werden sequentiell abgearbeitet

**Lösung**: Multiprocessing für Pairs

```python
from multiprocessing import Pool

def backtest_pair(pair):
    bt = Model3Backtester(pairs=[pair], ...)
    return bt.run()

with Pool(processes=4) as pool:
    results = pool.map(backtest_pair, PAIRS)
```

**Speedup**: 3-4x (bei 4 Cores)

**Caveat**: Jeder Process lädt eigene Daten → mehr RAM

---

### 5. Pre-Filter Pivots

**Problem**: Viele Pivots haben keine Verfeinerungen → Zeit verschwendet

**Lösung**:
1. Finde alle HTF-Pivots
2. Pre-Filter: Wick Diff >= 20% → Skip (nutze Wick Diff direkt)
3. Nur für Pivots mit Wick Diff < 20% oder validen Verfeinerungen → Full Trade Simulation

**Speedup**: 2-3x (weniger volle Simulationen)

---

### 6. Numba JIT Compilation

**Problem**: Python Loops sind langsam

**Lösung**: Numba für Performance-kritische Loops

```python
from numba import jit

@jit(nopython=True)
def find_pivots_numba(open_arr, high_arr, low_arr, close_arr):
    # ... vectorized pivot detection
    pass
```

**Speedup**: 10-50x für numerische Operationen

**Caveat**: Nicht für Pandas, nur für numpy arrays

---

### 7. Database statt Parquet (für sehr große Daten)

**Problem**: Alle Daten in Memory

**Lösung**: SQLite/PostgreSQL mit Indexing

```python
import sqlite3

# Index auf (pair, time) → sehr schnelle Queries
SELECT * FROM h1_data
WHERE pair = 'EURUSD'
  AND time >= '2020-01-01'
  AND time < '2020-02-01'
```

**Speedup**: 2-5x für große Datenmengen
**Caveat**: Setup-Overhead, komplexer

---

## Empfohlene Implementierungs-Reihenfolge

### Phase 1: Quick Wins (1-2 Stunden)
1. ✅ Parquet (bereits fertig)
2. **LTF-Caching** → 3-5x speedup
3. **Pre-Filter Pivots** → 2-3x speedup

**Gesamt**: ~10x schneller als aktuell

### Phase 2: Medium (4-6 Stunden)
4. **Vectorized Refinement Detection** → 10x speedup
5. **Parallel Processing** → 3-4x speedup

**Gesamt**: ~30-40x schneller als aktuell

### Phase 3: Advanced (1-2 Tage)
6. **Numba JIT** → 10-50x für kritische Loops
7. **Database** (nur wenn nötig)

**Gesamt**: ~100x+ schneller als aktuell

---

## Geschätzte Laufzeiten

**Aktuell (ohne Optimization)**:
- 28 Pairs × 300 Pivots × 4 LTF × Trade Simulation
- Geschätzt: **4-8 Stunden**

**Nach Phase 1** (LTF Cache + Pre-Filter):
- **30-60 Minuten**

**Nach Phase 2** (+ Vectorized + Parallel):
- **3-10 Minuten**

**Nach Phase 3** (+ Numba):
- **< 1 Minute**

---

## Nächste Schritte

1. **JETZT**: Phase 1 implementieren (LTF-Caching + Pre-Filter)
2. **Nach Validation**: Phase 2 (Vectorized + Parallel)
3. **Bei Bedarf**: Phase 3 (Numba)

---

## Memory Considerations

**Current**:
- 28 Pairs × 5 TFs × ~10 MB = ~1.4 GB RAM

**Mit Caching**:
- Peak: ~2-3 GB RAM (alle LTF gleichzeitig)
- Lösung: Clear cache nach jedem Pair

**Mit Parallel**:
- 4 Processes × 2 GB = ~8 GB RAM
- Lösung: Batch processing (7 Pairs × 4 = 28)

---

*Last Updated: 28.12.2025*
