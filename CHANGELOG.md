# Model 3 - Changelog

**Letzte Updates**: 30.12.2025

---

## Wichtigste Korrekturen

### 1. Verfeinerungen Max TF = Weekly
- Vorher: Dachte M kann Verfeinerung sein
- Jetzt: M → W,3D,D,H4,H1 / W → 3D,D,H4,H1 / 3D → D,H4,H1
- Max TF für Verfeinerungen ist W!

### 2. Unberührt-Check
- Vorher: Near darf nicht berührt werden
- Jetzt: K2 OPEN der Verfeinerung darf nicht berührt werden (bis HTF Valid Time)
- Ab Valid Time: Entry bei Near (K2 Open egal)

### 3. Versatz-Regel
- Standard: OHNE Versatz (weder Pivots noch Verfeinerungen)

### 4. TP-Check Zeitfenster
- Start: `max(Valid Time, Gap Touch)`
- Ende: BEI Entry (nicht danach)
- TP Touch NACH Entry = normaler Trade

### 5. RR-Berechnung
- Bei RR > 1.5: SL erweitern UND `rr = 1.5` setzen

### 6. Gap Touch auf H1
- H1 statt Daily (stunden-genau!)

---

## Code-Fixes (30.12.2025)

1. TP-Check nicht ausgeführt → Jetzt in Trade-Flow eingebaut
2. Unberührt-Check falsch → Jetzt k2 open statt near
3. Variable near_level → Korrigiert zu nears_result[i]
4. CAGR Bug → Check ending_capital > 0
5. Wick Diff Entry → Vollständig implementiert

---

## Status

✅ Alle Regeln korrekt implementiert
✅ Alle Bugs behoben
✅ Code 100% produktionsbereit

---

*Last Updated: 30.12.2025*
