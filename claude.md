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

### Was ist implementiert ✅

1. **HTF-Pivot-Erkennung** (W nur, in `backtest_model3.py`)
   - 2-Kerzen-Pattern (rot→grün / grün→rot)
   - Doji-Filter: 2% Body Minimum (NICHT 5% wie in Strategie!)
   - Kein Versatz-Filter
   - Pivot-Struktur korrekt (Pivot, Extreme, Near, Gap, Wick Diff)

2. **Verfeinerungs-Suche** (W, 3D, D, H4, H1)
   - Suche innerhalb Wick Difference
   - Max. 20% der Pivot Gap
   - Priorität: höchster TF zuerst
   - Doji-Filter: 2% (NICHT 5%!)

3. **Entry-Mechanismus**
   - Direkter Touch der Verfeinerung (OHNE Close-Bestätigung)
   - Gap muss zuerst getriggert werden
   - Verfeinerungs-Invalidierung bei Durchbruch

4. **SL/TP-Berechnung**
   - SL: Min. 60 Pips + unter/über Fib 1.1
   - TP: Fib -1
   - RR-Anpassung: 1.0 - 1.5

5. **Trade-Simulation**
   - H1-basiert
   - Exit bei SL/TP oder am Ende der Daten

### Was fehlt oder ist nicht korrekt ⚠️

1. **Doji-Filter:** Aktuell 2%, sollte 5% sein (laut Strategie-Dokumentation)

2. **Entry-Bestätigung:** Aktuell direkter Touch, sollte:
   - **1H Close Bestätigung** (Originalstrategie)
   - Zu testen: 1H Close, 4H Close, direkter Touch

3. **Versatz-Regel:** Aktuell nicht implementiert
   - Versatz = Lücke zwischen Close K1 und Open K2
   - Größere Box-Variante vs. kleinere Box
   - Versatz-Filter (2x Standard)
   - Zu testende Varianten dokumentiert

4. **Mehrere HTF-Timeframes:**
   - Aktuell nur **W** (Weekly)
   - Sollte: 3D, W, M (alle drei!)
   - Pivot-Overlap-Regel bei gleichen Extremen

5. **Model X Skripte nicht umbenannt:**
   - `backtest_modelx.py` → sollte umbenennt/entfernt werden
   - `modelx_pivot.py` → Model X spezifisch

6. **README/Dokumentation:**
   - PROJECT_README.md noch auf "Model X" bezogen
   - SETUP.md noch auf Model X Pfade

---

## Nächste Schritte (Empfohlen)

### Hochpriorität

1. **Doji-Filter korrigieren:**
   - Von 2% auf 5% ändern in `backtest_model3.py`
   - Sowohl für HTF-Pivots als auch Verfeinerungen

2. **Entry-Bestätigung implementieren:**
   - 1H Close Bestätigung (Originalstrategie)
   - Als parametrisierbar gestalten für Tests

3. **Mehrere HTF-Timeframes:**
   - 3D, W, M alle drei nutzen (nicht nur W)
   - Pivot-Overlap-Regel implementieren
   - Multi-Timeframe-Strategie aus `backtest_config.py` berücksichtigen

4. **Dokumentation aktualisieren:**
   - PROJECT_README.md auf Model 3 anpassen
   - SETUP.md auf Model 3 Pfade anpassen
   - Referenzen zu "Model X" entfernen/korrigieren

### Mittlere Priorität

5. **Versatz-Regel implementieren:**
   - Versatz-Erkennung (Close K1 ≠ Open K2)
   - Größere/kleinere Box-Variante
   - Versatz-Filter (2x Standard)
   - Parametrisierbar für Tests

6. **Test-Varianten implementieren:**
   - Entry: 1H Close, 4H Close, direkter Touch
   - Versatz: größere Box, kleinere Box, immer Close K1, immer Open K2
   - Doji-Filter: verschiedene Prozentsätze
   - Verfeinerungsgröße: verschiedene Prozentsätze

7. **Model X Skripte bereinigen:**
   - `backtest_modelx.py` in archive verschieben oder löschen
   - `modelx_pivot.py` entfernen (nicht relevant für Model 3)

### Niedrige Priorität

8. **Weitere Features:**
   - Position Management aus `backtest_config.py` nutzen
   - Risk Limits implementieren
   - Reporting/Visualisierung anpassen
   - Monte Carlo Simulation für Model 3

9. **Fundamentale Integration vorbereiten:**
   - COT-Daten Integration (später)
   - Seasonality-Filter
   - Valuation & Bonds Indikatoren

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

### Projekt-Struktur
```
05_Model 3/
├── config.py                    # Basis-Config (API, Pairs, Pfade)
├── backtest_config.py           # Backtest-Regeln (variabel)
├── PROJECT_README.md            # Projekt-Dokumentation (noch Model X!)
├── SETUP.md                     # Setup-Anleitung (noch Model X!)
├── MODEL 3 KOMMPLETT            # Vollständige Strategie-Doku
├── Model 3 Regeln übersicht     # Kurzübersicht Regeln
│
├── scripts/
│   ├── backtesting/
│   │   ├── backtest_model3.py       ← Hauptskript Model 3 ✅
│   │   ├── backtest_modelx.py       ← Model X (zu entfernen!)
│   │   ├── modelx_pivot.py          ← Model X spezifisch (zu entfernen!)
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
├── pivot_analysis/
│   ├── pivot_analysis.py
│   ├── pivot_quality_test.py
│   └── results/
│
└── results/                     # Backtest Outputs
    ├── trades/
    ├── charts/
    └── reports/
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

## Usage

### 1. Backtest ausführen

**Model 3 (Standard, nur W):**
```bash
python scripts/backtesting/backtest_model3.py --pairs EURUSD --start-date 2020-01-01
```

**Alle 28 Pairs:**
```bash
python scripts/backtesting/backtest_model3.py --start-date 2015-01-01 --output results/trades/model3_all.csv
```

### 2. Ergebnisse anzeigen

```bash
python scripts/backtesting/view_results.py -i results/trades/model3_all.csv
python scripts/backtesting/visualizations.py -i results/trades/model3_all.csv
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

## Bekannte Issues

1. **Doji-Filter:** 2% statt 5% (zu korrigieren)
2. **Nur W Pivots:** 3D und M fehlen noch
3. **Entry ohne Close:** Sollte 1H Close sein
4. **Versatz-Regel:** Noch nicht implementiert
5. **Dokumentation:** Noch auf Model X bezogen
6. **Model X Skripte:** Noch vorhanden, sollten bereinigt werden

---

## Kontakt & Git

- **Repository:** Eigenes Git-Repo in `05_Model 3/.git`
- **Remote:** Zu klären (aktuell nur lokal)
- **Branch:** main

---

*Last Updated: 2025-12-28*
