NUR VON BENUTZTER GEÄNDERT NICHT AI!

# MODEL 3 Variablen für Backtests

## 1. HTF - Pivot cration

### 1. Pivot

**fix:**

- Pivot auf OPEN k2
- Pivot auf CLOSE k1

**variable:** 
(open k2 oder close k1) 

- nach größter Pivot gap 
- nach kleinster Pivot gap

### 2. Timeframes

- 3D / W / M einzeln 
- Kombiniert 


## 2. Trade Variablen

### 2.1 Entry

- `direct_touch` - Entry bei erster Berührung des Entry-Levels (Default)
- `1h_close` - Entry bei Close UNTER/ÜBER Entry-Level (1H Bar)
- `4h_close` - Entry bei Close UNTER/ÜBER Entry-Level (4H Bar)

Entry nach gutem close (bei bullish über near von verfeinerung / Wick diff (entry level), bei bearish darunter)

check immer min 1RR 

**2 Anwendungen:**

- wenn Close schlecht: lösche Verfeinerung

- wenn Close gut: 

    1. entry bei close der canlde (H1 / H4)
    2. entry bei near wick diff wenn wieder berührt wird

jeweils min 1 RR bei ENTRY als Grundvorraussetzung (wenn nach close kerze zu weit von near entfernt dann wahrscheinlich unter 1RR kein entry)

### 2.2 SL

- mindest SL pips von 40-100 
- fixe Sl min. pro Pair (OVERFITTING aufpassen)

- Mindest RR: 1,0 / 1,1 / 1,2 

#### Fixer SL

- Sl fix (unabhänig von RR) bei Fib 1.1 / 1.2 / 1.5


### 2.3 TP

- Tp bei FIb level: -1 / -1,5 / -2 / -2,5 (verscheiede normale FIB levels)

- Min / Max Pips für TP 50-300

### 2.4 RR

- max RR 1.5 / 2.0 / 2.5 / 3.0


## 3. Verfeinerungen

- benutzte nur h1 / h4 / D / 3D / W einzeln
- kombiniere verschiende Timeframes die am besten funktionieren

- Benutzte NUR nur Wick Diff generell / nur unter 20%
- kombinire wick diff mit besten verfeinerungen Timeframes

- Verfeinerungen Valid check (zwischen Pivot creation) k2 touch (Pivot) / Near touch

- Size: 10 - 30% 

- Doji Filter: 0% / 5% / 10%

#### Variante 1:

wie Default:

- Höchste Prio = höchstes Timeframe
- bei Mehreren Verfeinrungen pro Timframe nächste zu HTF Pivot

#### Variante 2:

- nehme IMMER Verfeinerung (Höchste Prio) nächste zu HTF Pivot



## Ziele für Optimisierung:

- höherer Profit expectancy (ca. 0,1-3)
- Winrate ab 45-50%
- max Duration geringer (95% der trades sollten unter 60T liegen)
- min Duration 2/3 Tage kein Tp / Sl innerhalb 1-2 Tage

- bessere Grundlage für Fundamentale Filter (nicht zu viele Trades filtern) aber positiver outcome nur technisch

