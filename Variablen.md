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





## 2. Entry Variablen

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


## 3. Verfeinerungen

- benutzte nur h1 / h4 / D / 3D / W einzeln
- kombiniere verschiende Timeframes die am besten funktionieren

- Benutzte NUR nur Wick Diff generell / nur unter 20%
- kombinire wick diff mit besten verfeinerungen Timeframes

- Verfeinerungen Valid check (zwischen Pivot creation) k2 touch (Pivot) / Near touch
