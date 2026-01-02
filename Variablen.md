NUR VON BENUTZTER GEÄNDERT NICHT AI!

MODEL 3 Variablen für Backtests

HTF - Pivot cration

1. Pivot

fix: 

- Pivot auf OPEN k2
- Pivot auf CLOSE k1

variable: 
(open k2 oder close k1) 

- nach größter Pivot gap 
- nach kleinster Pivot gap

2. Entry Variablen

- `direct_touch` - Entry bei erster Berührung des Entry-Levels (Default)
- `1h_close` - Entry bei Close UNTER/ÜBER Entry-Level (1H Bar)
- `4h_close` - Entry bei Close UNTER/ÜBER Entry-Level (4H Bar)

Entry nach gutem close (bei bullish über near von verfeinerung / Wick diff (entry level), bei bearish darunter)

check immer min 1RR 

2 Anwendungen: 

