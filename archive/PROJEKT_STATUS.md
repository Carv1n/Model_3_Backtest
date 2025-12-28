# Model 3 - Projekt Status & Nächste Schritte

## 📊 Aktueller Stand (28.12.2025)

### ✅ Was ist fertig implementiert

#### 1. Backtest-Script (`backtest_model3.py`)
- ✅ HTF-Pivot-Erkennung (3D, W, M)
- ✅ Verfeinerungs-Suche (1H, 4H, D, 3D, W)
- ✅ Entry-Bestätigung (1h_close, direct_touch, 4h_close)
- ✅ SL/TP-Berechnung (Fib 1.1, Fib -1, RR 1.0-1.5)
- ✅ Trade-Simulation auf H1-Daten
- ✅ Portfolio-Backtest-Modus (chronologisch)

#### 2. Parameter
- ✅ Doji-Filter: 5%
- ✅ HTF-Timeframes: 3D, W, M (parametrisierbar)
- ✅ Entry-Bestätigung: 1h_close (default), direct_touch, 4h_close
- ✅ Verfeinerungsgröße: max 20% der Pivot Gap
- ✅ SL: Min. 60 Pips + Fib 1.1
- ✅ TP: Fib -1
- ✅ RR: 1.0 - 1.5 (anpassbar)

#### 3. Dokumentation
- ✅ `BACKTEST_OVERVIEW.md` - Vollständige Übersicht
- ✅ `MODEL3_CONFIG.md` - Standard-Konfiguration
- ✅ `PROJECT_README.md` - Hauptdokumentation
- ✅ `SETUP.md` - Setup-Anleitung
- ✅ `claude.md` - Claude Kontext
- ✅ `Backtest/01_test/README.md` - Test-Plan Validation
- ✅ `Backtest/02_technical/README.md` - Test-Plan Technical
- ✅ `Backtest/03_fundamentals/README.md` - Test-Plan Fundamentals

---

### ⚠️ Was NOCH NICHT implementiert ist

#### 1. Versatz-Regel
- ❌ Erkennung: Close K1 ≠ Open K2
- ❌ Größere vs. kleinere Box-Variante
- ❌ Versatz-Filter (2x Standard)

#### 2. Pivot-Overlap-Regel
- ❌ Wenn 2-3 Pivots gleiches Extreme haben
- ❌ Nur größere Pivot Gap nutzen

#### 3. Fundamentale Filter
- ❌ COT-Daten Integration
- ❌ Seasonality-Analyse
- ❌ Valuation (PPP, REER, Zinsen)
- ❌ Bonds (10Y Yields, Spreads)

#### 4. Position Management
- ❌ Max gleichzeitige Positionen
- ❌ Max pro Pair
- ❌ Trade-Priorität

#### 5. Erweiterte CLI-Parameter
- ❌ `--doji-filter` (aktuell hardcoded 5%)
- ❌ `--refinement-size` (aktuell hardcoded 20%)
- ❌ `--versatz-filter` (noch nicht implementiert)

---

## 🎯 NÄCHSTER SCHRITT: 01_test Validation

### Ziel
**Logik-Validierung**: Überprüfen, dass Pivot-Erkennung, Verfeinerungen, Entry, SL/TP korrekt funktionieren.

### Was zu tun ist

#### 1. Standard-Einstellungen festlegen ✅ ERLEDIGT
- In `MODEL3_CONFIG.md` dokumentiert
- Standard: W, 1h_close, 2010-2025

#### 2. Sample-Tests durchführen (6 Tests)
**Setup**: EURUSD, 2 Zeiträume (2010-2015 & 2020-2025), 3 HTF-TFs (W, M, 3D)

```bash
# Test 1: 2010-2015, Weekly
python scripts/backtesting/backtest_model3.py \
    --pairs EURUSD \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --start-date 2010-01-01 \
    --end-date 2015-12-31 \
    --output Backtest/01_test/validation_2010-2015_W_EURUSD.csv

# Test 2: 2010-2015, Monthly
python scripts/backtesting/backtest_model3.py \
    --pairs EURUSD \
    --htf-timeframes M \
    --entry-confirmation 1h_close \
    --start-date 2010-01-01 \
    --end-date 2015-12-31 \
    --output Backtest/01_test/validation_2010-2015_M_EURUSD.csv

# Test 3-6: Analog für 3D und 2020-2025
```

#### 3. Manuell validieren (5-10 Trades pro Test)
**Checkliste pro Trade**:
- [ ] Pivot korrekt erkannt? (2-Kerzen-Pattern, Doji-Filter)
- [ ] Pivot-Struktur korrekt? (Pivot, Extreme, Near, Gap, Wick Diff)
- [ ] Verfeinerung korrekt? (innerhalb Wick Diff, max 20%, unberührt)
- [ ] Entry korrekt? (Gap zuerst, 1H Close Bestätigung, Entry bei Open)
- [ ] SL korrekt? (Min. 60 Pips, min. über/unter Fib 1.1)
- [ ] TP korrekt? (Fib -1)
- [ ] RR korrekt? (1.0-1.5)

#### 4. Vollständiger Backtest (wenn Validation OK)
```bash
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --start-date 2010-01-01 \
    --output Backtest/01_test/full_backtest_W_1h_close.csv
```

---

## 📁 Projekt-Organisation

### Aktuell
```
05_Model 3/
├── scripts/backtesting/
│   ├── backtest_model3.py ✅ VERWENDEN
│   ├── backtest_modelx.py ⚠️  NICHT VERWENDEN (alt)
│   └── modelx_pivot.py ⚠️  NICHT VERWENDEN (alt)
│
├── Backtest/
│   ├── 01_test/ ← AKTUELL HIER
│   ├── 02_technical/ ← SPÄTER
│   └── 03_fundamentals/ ← VIEL SPÄTER
│
└── [Dokumentations-Dateien]
```

### Aufräumen (optional, später)
- `backtest_modelx.py` → archivieren/löschen
- `modelx_pivot.py` → archivieren/löschen
- `config.py` → Model X Settings entfernen (FIB_SL, FIB_TP)

---

## 🚀 Roadmap

### Phase 1: ✅ Implementierung (ERLEDIGT)
- [x] Doji-Filter auf 5% korrigieren
- [x] HTF-Timeframes auf 3D, W, M erweitern
- [x] 1H Close Bestätigung implementieren
- [x] Dokumentation aktualisieren

### Phase 2: ⏳ Validation (JETZT)
- [ ] Sample-Tests durchführen (6 Tests)
- [ ] Manuell validieren (Logik korrekt?)
- [ ] Bugs fixen (falls vorhanden)
- [ ] Vollständiger Backtest (Weekly, alle Pairs)

### Phase 3: 📊 Technical Backtests
- [ ] Entry-Varianten vergleichen (1h_close vs direct_touch)
- [ ] HTF-Varianten testen (nur W vs alle)
- [ ] Parameter-Optimierung (Doji-Filter, Refinement-Size)
- [ ] Baseline dokumentieren

### Phase 4: 🔧 Features erweitern
- [ ] Versatz-Regel implementieren
- [ ] Pivot-Overlap-Regel implementieren
- [ ] CLI-Parameter erweitern (doji-filter, refinement-size)
- [ ] Position Management implementieren

### Phase 5: 🌍 Fundamentals
- [ ] COT-Daten Download & Integration
- [ ] Seasonality-Analyse & Integration
- [ ] Valuation & Bonds Integration
- [ ] Vollständiger Backtest mit Fundamentals

### Phase 6: 🎯 Forward Testing
- [ ] Live-Setup vorbereiten
- [ ] Risk Management finalisieren
- [ ] Forward-Testing starten

---

## 💡 Wichtige Erkenntnisse

### Implementierung
- **Doji-Filter**: 5% ist Standard (war vorher 2%)
- **HTF-Timeframes**: Alle drei (3D, W, M) unterstützt
- **Entry-Bestätigung**: 1H Close ist Standard (parametrisierbar)
- **RR-Anpassung**: SL wird vergrößert wenn RR > 1.5

### Strategie
- **Fundamentals sind kritisch**: Ohne COT/Seasonality wahrscheinlich breakeven/negativ
- **Technisches = Entry-Timing**: Pivots/Verfeinerungen geben WO/WANN
- **Fundamentals = Richtungs-Bias**: COT/Seasonality geben WELCHE Richtung

### Testing
- **Portfolio-Modus**: Trades chronologisch, mehrere Pairs gleichzeitig
- **Validation zuerst**: Logik manuell überprüfen bevor große Backtests
- **Baseline etablieren**: Technical-Performance dokumentieren für Vergleich

---

## 📞 Fragen & TODOs

### Offene Fragen
1. Welche Stats sind am wichtigsten für Validation?
   → **Antwort**: Win Rate, Expectancy (R), Max DD, Profit Factor

2. Wie viele Sample-Trades validieren?
   → **Antwort**: 5-10 pro Test-Setup ausreichend

3. Versatz-Regel Priorität?
   → **Antwort**: Nach 01_test, vor 02_technical

### Nächste TODOs
1. ⏳ **01_test ausführen** (Sample-Tests + Validation)
2. ⏳ **Logik validieren** (Manuell überprüfen)
3. ⏳ **Vollbacktest** (Weekly, alle Pairs)
4. ⏳ **Baseline dokumentieren** (Performance ohne Fundamentals)

---

## 🎯 Fokus: JETZT

**WAS**: 01_test Validation durchführen

**WIE**:
1. 6 Sample-Tests laufen lassen
2. 5-10 Trades pro Test manuell validieren
3. Bugs fixen (falls vorhanden)
4. Vollbacktest laufen lassen

**WARUM**:
- Sicherstellen dass Logik korrekt ist
- Baseline etablieren
- Vor größeren Tests validieren

---

*Last Updated: 28.12.2025*
