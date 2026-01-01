# Model 3 - Multi-Timeframe Pivot Trading System

## Projekt-Übersicht

**Model 3** ist ein komplexes Multi-Timeframe Pivot-Trading-System mit Verfeinerungs-Mechanismus für 28 Forex-Paare. Im Gegensatz zu Model X (vereinfacht) nutzt Model 3 ein mehrstufiges Entry-System mit Verfeinerungen auf niedrigeren Timeframes.

### Hauptunterschiede zu Model X

| Feature | Model 3 | Model X |
|---------|---------|---------|
| Komplexität | Komplex, Multi-Timeframe Verfeinerungen | Einfach, direkte Pivots |
| Pivot TFs | 3D, W, M | 3D, W, M |
| Verfeinerungs TFs | 1H, 4H, D, 3D, W | Keine |
| Entry | Touch + 1H Close Bestätigung | Direkter Touch |
| SL | Min. 60 Pips + Fib 1.1 | Fib 1.5 (fix) |
| TP | Fib -1 | Fib -3 (fix) |
| RR | 1.0 - 1.5 (variabel, angepasst) | 2:1 (fix) |
| Doji Filter | 5% (Standard) | 5% |

---

## Strategie-Logik

### 1. Pivot-Identifikation (HTF: 3D, W, M)

**Bullish Pivot:**
- Kerze 1: Rot (Close < Open)
- Kerze 2: Grün (Close > Open)
- Pivot existiert erst NACH Close von Kerze 2

**Bearish Pivot:**
- Kerze 1: Grün (Close > Open)
- Kerze 2: Rot (Close < Open)
- Pivot existiert erst NACH Close von Kerze 2

**Pivot-Struktur:**
- **Pivot:** Open der zweiten Kerze
- **Pivot Extreme:** Ende der längeren Wick (bullish: tiefster Low, bearish: höchster High)
- **Pivot Near:** Ende der kürzeren Wick (bullish: höherer Low, bearish: niedrigerer High)
- **Pivot Gap:** Box von Pivot bis Pivot Extreme
- **Wick Difference:** Box von Pivot Near bis Pivot Extreme

### 2. Verfeinerungen (LTF: 1H, 4H, D, 3D, W)

**Such-Prozess:**
1. Suche erst NACH HTF-Pivot-Entstehung (Kerze 2 geschlossen)
2. Systematisch von höherem TF nach unten: M→W→3D→D→4H→1H
3. Innerhalb der **Wick Difference** des HTF-Pivots suchen

**Gültigkeitsbedingungen (ALLE müssen erfüllt sein):**
- Größe max. **20% der Pivot Gap**
- Position innerhalb Wick Difference (Ausnahme: exakt auf Pivot Near erlaubt)
- **Unberührt-Regel:** Vor HTF-Pivot-Entstehung nicht berührt
- Doji-Filter (Standard: 5% Body Minimum)
- Kein Versatz-Filter (aktuell deaktiviert)

**Priorität:**
- Höchster Timeframe = höchste Priorität
- Alle validen Verfeinerungen werden gespeichert
- Entry erfolgt an höchster TF Verfeinerung zuerst

### 3. Entry-Prozess

**Voraussetzungen:**
1. HTF Pivot muss valide sein (Kerze 2 geschlossen)
2. **Pivot Gap muss zuerst getriggert werden** (Preis berührt Pivot Gap)
3. Dann wird Verfeinerung relevant

**Standard-Entry (aktuell implementiert: OHNE Close-Bestätigung):**
- Bullish: Preis berührt Entry Level der Verfeinerung → Entry
- Bearish: Preis berührt Entry Level der Verfeinerung → Entry

**Zu testende Varianten:**
- Mit 1H Close Bestätigung (Originalstrategie)
- Mit 4H Close Bestätigung
- Direkter Entry bei Touch (aktuell implementiert)

**Invalidierung:**
- Wenn Verfeinerung während Prozess komplett durchbrochen wird → gelöscht
- Gehe zur nächsten Verfeinerung (nächst-niedrigerer TF)

### 4. Fibonacci & Exits

**Fibonacci-Levels:**
- **Fib 0:** Pivot
- **Fib 1:** Pivot Extreme
- **Fib 1.1:** 0.1× Gap jenseits Extreme

**Stop Loss:**
- **Min. 60 Pips** von Entry entfernt
- **Min. über/unter Fib 1.1:**
  - Bullish: SL muss UNTER 1.1 Fib sein
  - Bearish: SL muss ÜBER 1.1 Fib sein

**Take Profit:**
- Fix auf **Fib -1** (1× Gap jenseits Pivot)
- Bullish: TP über dem Pivot
- Bearish: TP unter dem Pivot

### 5. Risk/Reward Management

**RR-Grenzen:**
- **Minimum RR: 1.0** → Setup ignorieren wenn < 1.0
- **Maximum RR: 1.5** → SL vergrößern bis exakt 1.5 RR
  - Entry und TP bleiben unverändert
  - Nur SL wird nach außen verschoben

---

## Aktueller Implementierungsstatus

### Phase 1: Validation ✅ ABGESCHLOSSEN (30.12.2025)

**Ordner**: `Backtest/01_test/`

1. **01_Validation/** - 6 Sample Trades validiert
   - Alle Regeln korrekt implementiert
   - Trade-Flow geprüft und funktioniert

2. **02_W_test/** - Weekly Test (alte Struktur)
   - Archiviert, alte Struktur
   - Ersetzt durch Phase 2

### Phase 2: Technical Backtests 🎯 AKTUELL (01.01.2026)

**Ordner**: `Backtest/02_technical/01_DEFAULT/01_Single_TF/`

**Scripts (alle funktional):**
- `scripts/backtest_all.py` - Main Backtest Script (W, 3D, M) ✅ **Updated 01.01.2026**
- `scripts/backtest_W.py` - Weekly Backtest
- `scripts/backtest_3D.py` - 3-Day Backtest
- `scripts/backtest_M.py` - Monthly Backtest
- `scripts/report_helpers.py` - Shared reporting functions

**Test Scripts (Updated 01.01.2026):**
- `Backtest/01_test/02_W_test/01_test/scripts/backtest_weekly_mini.py` ✅
- `Backtest/01_test/02_W_test/02_ALL_PAIRS/scripts/backtest_weekly_full.py` ✅

**Output-Struktur:**
```
results/
├── Trades/
│   ├── W_pure.csv, W_conservative.csv
│   ├── 3D_pure.csv, 3D_conservative.csv
│   └── M_pure.csv, M_conservative.csv
├── Pure_Strategy/
│   ├── W_pure.txt
│   ├── 3D_pure.txt
│   └── M_pure.txt
└── Conservative/
    ├── W_conservative.txt
    ├── 3D_conservative.txt
    └── M_conservative.txt
```

**Implementierte Features:**

1. **HTF-Pivot-Erkennung** (W, 3D, M - alle drei!)
   - 2-Kerzen-Pattern (rot→grün / grün→rot)
   - Doji-Filter: 5% Body Minimum ✅
   - Kein Versatz-Filter
   - Pivot-Struktur korrekt (Pivot, Extreme, Near, Gap, Wick Diff)

2. **Verfeinerungs-Suche** ✅ **Fixed 01.01.2026**
   - **Dynamic LTF List**: Excludes HTF itself ✅
     - W HTF → [3D, D, H4, H1] ✓
     - 3D HTF → [D, H4, H1] ✓ (no more 3D in its own search!)
     - M HTF → [W, 3D, D, H4, H1] ✓ (now includes W!)
   - Suche innerhalb Wick Difference
   - Max. 20% der Pivot Gap
   - Priorität: höchster TF zuerst
   - Doji-Filter: 5% ✅
   - Unberührt-Check: K2 Open (nicht Near!)

3. **Entry-Mechanismus** ✅ **Updated 01.01.2026**
   - Direkter Touch (direct_touch)
   - Gap Touch auf H1 erforderlich
   - **CHRONOLOGISCHE Entry-Logik**: Touch-basierte Reihenfolge ✅
   - **Nur EINE Entry pro Pivot** ✅
   - **Höchste Prio bekommt RR-Check** ✅
   - **Niedrigere Prio → Sofort Delete** (kein RR-Check) ✅
   - **RR Fallback**: Höchste Prio < 1 RR → Delete, nächste wird aktiv ✅
   - TP-Check zwischen Gap Touch und Entry
   - Verfeinerungs-Invalidierung korrekt implementiert

4. **SL/TP-Berechnung**
   - SL: Min. 60 Pips + unter/über Fib 1.1
   - TP: Fib -1
   - RR-Anpassung: 1.0 - 1.5
   - Bei RR > 1.5: SL erweitern UND rr = 1.5 setzen

5. **Trade-Simulation**
   - H1-basiert für Präzision
   - Exit bei SL/TP oder am Ende der Daten
   - Pure + Conservative Versionen (Spreads + $5/lot Commission)

6. **Reporting**
   - TXT Reports mit vollständigen Statistiken
   - CSV Exports für weitere Analyse
   - Keine QuantStats HTML (zu kompliziert, entfernt)

### Phase 3: COT Integration ⏳ VORBEREITET

**Ordner**: `Backtest/03_fundamentals/COT/`

**Geplant:**
- COT Index Filtering auf W, 3D, M Tests anwenden
- Commercial vs Retail positioning
- Trade nur wenn COT Bias stimmt

### Was noch zu testen ist ⚠️

1. **Entry-Bestätigung Varianten:**
   - Aktuell: direkter Touch (direct_touch)
   - Zu testen: 1H Close Bestätigung (Originalstrategie)
   - Zu testen: 4H Close Bestätigung

2. **Versatz-Regel:** Aktuell nicht implementiert
   - Versatz = Lücke zwischen Close K1 und Open K2
   - Größere Box-Variante vs. kleinere Box
   - Versatz-Filter (2x Standard)
   - Zu testende Varianten dokumentiert

3. **Combined Portfolio:**
   - W + 3D + M zusammen testen
   - Überlappende Pivots bei gleichen Extremen
   - Portfolio-Performance

---

## Nächste Schritte

### Sofort (Phase 2 aktiv)

1. ✅ **W, 3D, M Backtests ausführen**
   - Run `backtest_W.py`, `backtest_3D.py`, `backtest_M.py`
   - Ergebnisse analysieren und vergleichen

2. ⏳ **Timeframe Performance Vergleich**
   - Welcher TF perforiert am besten?
   - Win Rate, Total Return, Max DD, Sharpe Ratio
   - Trade Count pro TF

3. ⏳ **COT Integration planen** (Phase 3)
   - COT Index Daten vorbereiten
   - Filter-Logik entwickeln
   - W, 3D, M Tests mit COT wiederholen

### Mittelfristig

4. **Entry-Varianten testen:**
   - 1H Close Bestätigung implementieren
   - 4H Close Bestätigung implementieren
   - Vergleich: direct_touch vs 1H close vs 4H close

5. **Combined Portfolio Test:**
   - W + 3D + M zusammen
   - Pivot-Overlap-Regel bei gleichen Extremen
   - Portfolio-Performance vs Einzelstrategien

6. **Versatz-Regel implementieren:**
   - Versatz-Erkennung (Close K1 ≠ Open K2)
   - Größere/kleinere Box-Variante
   - Versatz-Filter (2x Standard)
   - Parametrisierbar für Tests

### Niedrige Priorität

7. **Model X Skripte bereinigen:**
   - `backtest_modelx.py` in archive verschieben
   - `modelx_pivot.py` entfernen (nicht relevant für Model 3)
   - Old `scripts/backtesting/backtest_model3.py` archivieren

8. **Weitere Features:**
   - Monte Carlo Simulation für Model 3
   - Erweiterte Visualisierung
   - Portfolio Equity Curve (W+3D+M combined)

---

## Datenstruktur

### Zentrale Datenquelle
```
/Documents/Trading Backtests/Data/Chartdata/Forex/Parquet/
├── All_Pairs_H1_UTC.parquet
├── All_Pairs_H4_UTC.parquet
├── All_Pairs_D_UTC.parquet
├── All_Pairs_3D_UTC.parquet
├── All_Pairs_W_UTC.parquet
└── All_Pairs_M_UTC.parquet
```

### Projekt-Struktur (AKTUALISIERT 30.12.2025)
```
05_Model 3/
├── README.md                    # Projekt-Übersicht ✅
├── STRATEGIE_REGELN.md          # Komplette technische Regeln ✅
├── claude.md                    # Claude Kontext ✅
├── CHANGELOG.md                 # Änderungshistorie ✅
│
├── config.py                    # Basis-Config (API, Pairs, Pfade)
├── backtest_config.py           # Backtest-Regeln (deprecated für Model 3)
│
├── scripts/
│   ├── backtesting/
│   │   ├── backtest_model3.py       ← OLD Core Engine (zu archivieren)
│   │   ├── backtest_modelx.py       ← Model X (zu archivieren)
│   │   ├── modelx_pivot.py          ← Model X spezifisch (zu archivieren)
│   │   ├── run_all_backtests.py     ← Batch Runner
│   │   ├── backtest_ui.py           ← Interactive UI
│   │   ├── view_results.py          ← Results Viewer
│   │   ├── visualizations.py        ← Charts
│   │   ├── monte_carlo.py           ← MC Simulation
│   │   └── create_summary.py        ← Summary Reports
│   │
│   └── data_processing/
│       └── 0_complete_fresh_download.py
│
├── Backtest/
│   ├── 01_test/                 ← ABGESCHLOSSEN ✅
│   │   ├── 01_Validation/       ← 6 Sample Trades (validiert)
│   │   └── 02_W_test/           ← Weekly Tests (alte Struktur)
│   │
│   ├── 02_technical/            ← AKTUELL 🎯
│   │   └── 01_DEFAULT/
│   │       └── 01_Single_TF/    ← Einzelne Timeframes
│   │           ├── scripts/
│   │           │   ├── backtest_W.py
│   │           │   ├── backtest_3D.py
│   │           │   ├── backtest_M.py
│   │           │   └── report_helpers.py
│   │           └── results/
│   │               ├── Trades/
│   │               ├── Pure_Strategy/
│   │               └── Conservative/
│   │
│   └── 03_fundamentals/         ← SPÄTER (COT, Seasonality)
│       └── COT/
│
├── pivot_analysis/
│   ├── pivot_analysis.py
│   ├── pivot_quality_test.py
│   └── results/
│
└── archive/                     ← Archivierte Dateien
```

---

## Konfiguration

### `config.py` (Basis-Einstellungen)
- API Credentials (Oanda)
- 28 Forex Pairs
- Timeframes (H1, H4, D, 3D, W, M)
- Pfade (automatisch)
- **Model X Settings noch drin** (FIB_SL, FIB_TP) → könnte entfernt werden

### `backtest_config.py` (Backtest-Regeln)
- Pivot Timeframes: 3D, W, M
- Multiple Timeframe Strategy: 'highest'
- Entry Type: 'direct_touch'
- Exit Type: 'fixed'
- Position Limits: None (unbegrenzt)
- Risk per Trade: 1.0%

**Hinweis:** Diese Config ist für Model X gedacht, Model 3 nutzt aktuell noch nicht alle Parameter.

---

## Usage (AKTUALISIERT 30.12.2025)

### Phase 2: Single Timeframe Tests

**Weekly:**
```bash
cd "05_Model 3/Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_W.py
```

**3-Day:**
```bash
cd "05_Model 3/Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_3D.py
```

**Monthly:**
```bash
cd "05_Model 3/Backtest/02_technical/01_DEFAULT/01_Single_TF"
python scripts/backtest_M.py
```

**Output:**
- `results/Trades/{TF}_pure.csv` - Trade-Liste (ohne Kosten)
- `results/Trades/{TF}_conservative.csv` - Trade-Liste (mit Spreads + Commission)
- `results/Pure_Strategy/{TF}_pure.txt` - Vollständiger Report
- `results/Conservative/{TF}_conservative.txt` - Report mit Transaktionskosten

### OLD Scripts (zu archivieren)

**Model 3 Core Engine (veraltet):**
```bash
# NICHT MEHR BENUTZEN - ersetzt durch backtest_W.py, backtest_3D.py, backtest_M.py
python scripts/backtesting/backtest_model3.py --pairs EURUSD --start-date 2020-01-01
```

---

## Wichtige Hinweise

### Fundamentale Komponente

**KRITISCH:** Die technische Strategie ist NUR das Entry-Timing, NICHT die eigentliche Edge!

**Die Trading-Edge kommt von Fundamentals:**
- COT-Daten (Commitment of Traders) - Hauptindikator
- Seasonality (saisonale Muster)
- Valuation (Bewertungsmetriken)
- Bonds (Anleihenmarkt)

**Fundamentals geben:**
- WELCHES Pair
- WELCHE Richtung (Long/Short)
- Die Bias/Filter

**Technisches gibt:**
- WANN Entry
- WO Entry/SL/TP

**Ohne Fundamentals:** Strategie wird wahrscheinlich negative/neutrale Performance haben.

### Performance-Erwartung

- **Mit Fundamentals:** Win Rate 45-55% angestrebt
- **Ohne Fundamentals:** Wahrscheinlich negativ/neutral
- **Ziel:** Technische Baseline validieren → dann Fundamentals hinzufügen

---

## Bekannte Issues / To-Do

1. ✅ **Doji-Filter:** Fixed auf 5%
2. ✅ **Mehrere HTF-Timeframes:** W, 3D, M alle drei verfügbar
3. ✅ **Dokumentation:** README, CHANGELOG, claude.md aktualisiert
4. ⏳ **Entry-Bestätigung:** Aktuell direkter Touch, 1H/4H Close noch zu testen
5. ⏳ **Versatz-Regel:** Noch nicht implementiert
6. ⏳ **Model X Skripte:** Noch vorhanden, sollten ins archive verschoben werden
7. ⏳ **QuantStats HTML:** Entfernt (zu kompliziert), nur TXT + CSV Reports

---

## ⚠️ CRITICAL UPDATES (01.01.2026)

### Bug Fix 1: 3D Backtest Zero Trades
**Problem:** 9 von 28 Pairs mit 0 Trades trotz 600+ Pivots
**Root Cause:** Hardcoded `ltf_list = ["3D", "D", "H4", "H1"]`
**Fix:** Dynamic LTF list basierend auf HTF
**Impact:** 3D und M Backtests sollten jetzt signifikant mehr Trades haben

### Bug Fix 2: Chronological Entry Logic
**Problem:** Entry-Logik nur nach Priorität, nicht chronologisch
**Fix:** Neue `find_near_touch_time()` Funktion + chronologische Touch-Verarbeitung
**Impact:** Korrekte Trade-Simulation nach tatsächlicher Marktbewegung

**EMPFEHLUNG**: Alle Backtests (W, 3D, M) neu ausführen!

Details siehe [CHANGELOG.md](CHANGELOG.md)

---

## Kontakt & Git

- **Repository:** Eigenes Git-Repo in `05_Model 3/.git`
- **Remote:** Zu klären (aktuell nur lokal)
- **Branch:** main

---

*Last Updated: 2026-01-01*
