# 03_fundamentals - Backtests mit fundamentalen Filtern

## Ziel
Integration fundamentaler Filter zur Verbesserung der Performance.

---

## ⚠️ Status: PHASE 3 IMPLEMENTIERT (MIT BUGS)

**COT Double Divergence Filter** ist implementiert, aber **3 kritische Bugs gefunden**.

**Stand**: 31.12.2025

**BUGS**:
1. ❌ CSV-Speicherung falsch (nur Bias_8W gespeichert, Reports nutzen falsche Daten)
2. ❌ Report-Stats unvollständig (viele Stats aus Phase 2 fehlen)
3. ❌ Performance schlecht trotz 88% Filtering (nur +0.9% Win Rate Verbesserung)

**STATUS**: Wartet auf Bug-Fixes vor weiterer Nutzung
**Details**: Siehe `COT/Double_Divergence/README.md` → Abschnitt "BEKANNTE BUGS"

---

## Implementierte Filter

### COT Double Divergence (IMPLEMENTIERT ✓)

**Ordner**: `COT/Double_Divergence/`

**Implementierung**:
- ✅ COT-Indikator (`cot_double_divergence.py`)
- ✅ Trade-Filter (`apply_cot_filter.py`)
- ✅ Report-Generator (`generate_reports.py`)
- ✅ 3 Bias-Modi: Bias_8W, Bias_to_Bias, Bias_fix_0

**Beschreibung**:
- **26-Wochen WillCo Index**: Normalisierung der COT-Nettopositionen (0-100)
- **Double Divergence**: (CommIdx_base - RetailIdx_base) - (CommIdx_quote - RetailIdx_quote)
- **Pair-spezifische Schwellenwerte**: EURUSD=160, GBPUSD=180, etc. (aus Bias_Zone_Pine)
- **Filter-Logik**: Trade nur wenn Richtung mit COT-Bias aligned (check nur beim Entry)
- **Timing**: Dienstag-Daten → Freitag-Veröffentlichung → Montag verfügbar (Look-Ahead Prevention)

**3 Bias-Modi**:
1. **Bias_8W**: 8-Wochen-Countdown (Signal → 8 Wochen aktiv → Neutral)
2. **Bias_to_Bias**: Signal-zu-Signal (Long bis Short-Signal, vice versa)
3. **Bias_fix_0**: Null-Exit (Bias endet wenn Divergenz 0 kreuzt)

**Output**:
- 18 TXT-Reports: 3 Modi × 3 Timeframes × 2 Typen
- 6 Trade-CSVs: W/3D/M × pure/conservative

**Nutzung**:
```bash
cd "05_Model 3/Backtest/03_fundamentals/COT/Double_Divergence/scripts/"
python apply_cot_filter.py
```

**Ordnerstruktur**:
```
COT/Double_Divergence/
├── scripts/
│   ├── cot_double_divergence.py   # COT Indikator
│   ├── apply_cot_filter.py        # Trade Filter (Main)
│   ├── generate_reports.py        # Report Generator
│   ├── Indikator_Pine             # TradingView Referenz
│   └── Bias_Zone_Pine             # TradingView Referenz
│
└── 01_default/
    └── Single_TF/
        ├── Trades/                # Gefilterte Trade-CSVs
        │   ├── W_pure.csv
        │   ├── W_conservative.csv
        │   ├── 3D_pure.csv
        │   ├── 3D_conservative.csv
        │   ├── M_pure.csv
        │   └── M_conservative.csv
        │
        └── results/
            ├── Bias_8W/           # 6 Reports (8W Countdown)
            ├── Bias_to_Bias/      # 6 Reports (Signal-zu-Signal)
            └── Bias_fix_0/        # 6 Reports (Null-Exit)
```

---

## Geplante Fundamentale Filter

### 1. COT-Daten (Commitment of Traders)
**Quelle**: CFTC (wöchentlich, Dienstag)

**Filter**:
- **Net Positions**: Commercial Hedgers, Large Speculators, Small Speculators
- **Extreme Levels**: Überverkauft/Überkauft-Signale
- **Divergenzen**: COT vs. Preis

**Integration**:
- Nur Trades in Richtung der COT-Signale
- Gewichtung: Stärke des COT-Signals

---

### 2. Seasonality (Saisonale Muster)
**Quelle**: Historische Daten-Analyse

**Filter**:
- **Monatliche Patterns**: Welche Monate bullish/bearish für Pair?
- **Wöchentliche Patterns**: Wochentage-Tendenz
- **Quartals-Patterns**: Q1, Q2, Q3, Q4

**Integration**:
- Nur Trades in saisonal günstigen Perioden
- Oder: Gewichtung basierend auf saisonaler Stärke

---

### 3. Valuation (Bewertungsmetriken)
**Quellen**: PPP, REER, Zinsdifferenzen

**Filter**:
- **PPP (Purchasing Power Parity)**: Über-/Unterbewertet?
- **REER (Real Effective Exchange Rate)**: Relativ zu Handelspartnern
- **Zinsdifferenzen**: Carry Trade Potential

**Integration**:
- Nur Trades in Richtung der Mean-Reversion
- Oder: Gewichtung basierend auf Über-/Unterbewertung

---

### 4. Bonds (Anleihenmarkt)
**Quellen**: 10Y Yields, Spreads

**Filter**:
- **Yield-Differenzen**: US vs. EUR, UK, JPY, etc.
- **Spread-Änderungen**: Widening/Narrowing
- **Safe-Haven Flows**: USD/JPY/CHF Stärkung bei Risk-Off

**Integration**:
- Nur Trades aligned mit Bond-Flow
- Oder: Gewichtung basierend auf Yield-Differenz-Änderung

---

## Geplante Test-Struktur

### Test 1: Nur COT
```bash
# Backtest mit COT-Filter
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --fundamental-filter cot \
    --start-date 2010-01-01 \
    --output Backtest/03_fundamentals/cot_only.csv
```

### Test 2: Nur Seasonality
```bash
# Backtest mit Seasonality-Filter
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --fundamental-filter seasonality \
    --start-date 2010-01-01 \
    --output Backtest/03_fundamentals/seasonality_only.csv
```

### Test 3: Kombination (COT + Seasonality)
```bash
# Backtest mit COT + Seasonality
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --fundamental-filter cot seasonality \
    --start-date 2010-01-01 \
    --output Backtest/03_fundamentals/cot_seasonality.csv
```

### Test 4: Alle Filter
```bash
# Backtest mit allen fundamentalen Filtern
python scripts/backtesting/backtest_model3.py \
    --htf-timeframes W \
    --entry-confirmation 1h_close \
    --fundamental-filter all \
    --start-date 2010-01-01 \
    --output Backtest/03_fundamentals/all_fundamentals.csv
```

---

## Erwartete Verbesserungen

**Ohne Fundamentals (Baseline aus 02_technical)**:
- Win Rate: 40-50%
- Expectancy: 0-2 R
- Profit Factor: 0.9-1.2

**Mit Fundamentals (Ziel)**:
- Win Rate: 50-60% (+10-15%)
- Expectancy: 2-4 R (+2-3 R)
- Profit Factor: 1.5-2.0 (+50-100%)

**Trade-Anzahl**:
- Wahrscheinlich **weniger Trades** (Filter reduzieren Setups)
- Aber **höhere Qualität** (bessere Win Rate & Expectancy)

---

## Implementierungs-TODOs

### Phase 1: COT-Daten
1. [ ] COT-Daten downloaden (CFTC API/CSV)
2. [ ] COT-Parser implementieren
3. [ ] COT-Indikatoren berechnen (Net Positions, Extremes)
4. [ ] COT-Filter in Backtest integrieren

### Phase 2: Seasonality
5. [ ] Historische Daten analysieren
6. [ ] Saisonale Patterns extrahieren (monatlich, wöchentlich)
7. [ ] Seasonality-Score berechnen
8. [ ] Seasonality-Filter in Backtest integrieren

### Phase 3: Valuation
9. [ ] PPP/REER Daten beschaffen
10. [ ] Zinsdifferenzen-Daten (FRED, ECB, etc.)
11. [ ] Valuation-Score berechnen
12. [ ] Valuation-Filter in Backtest integrieren

### Phase 4: Bonds
13. [ ] 10Y Yield Daten (US, EUR, UK, JPY, etc.)
14. [ ] Spread-Berechnung
15. [ ] Bond-Flow-Indikator
16. [ ] Bond-Filter in Backtest integrieren

---

## Output-Dateien (geplant)

```
03_fundamentals/
├── cot_only.csv
├── seasonality_only.csv
├── valuation_only.csv
├── bonds_only.csv
├── cot_seasonality.csv
├── cot_valuation.csv
├── all_fundamentals.csv
└── README.md (diese Datei)
```

---

## Philosophie

**WICHTIG**: Die fundamentalen Filter sind die **eigentliche Edge** der Strategie.

- **Technisches** (Pivots, Verfeinerungen) = **Entry-Timing**
- **Fundamentals** (COT, Seasonality, etc.) = **Richtungs-Bias**

**Ohne Fundamentals**: Strategie ist wahrscheinlich breakeven/leicht negativ.

**Mit Fundamentals**: Strategie sollte profitabel sein (erwartete Expectancy: 2-4 R).

---

## Nächste Schritte

**Aktuell**: Erst 01_test und 02_technical abschließen.

**Dann**:
1. COT-Daten Download & Integration
2. Seasonality-Analyse & Integration
3. Vollständiger Backtest mit Fundamentals
4. Performance-Vergleich: Technical vs. Fundamental

---

## Voraussetzung

**Erst nach Abschluss von Phase 2** (02_technical):
- W, 3D, M Backtests abgeschlossen
- Beste technische Baseline identifiziert
- Dann COT Integration starten

---

*Last Updated: 30.12.2025*
