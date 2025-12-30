# 03_fundamentals - Backtests mit fundamentalen Filtern

## Ziel
Integration fundamentaler Filter zur Verbesserung der Performance.

---

## ⚠️ Status: NOCH NICHT IMPLEMENTIERT

Dieser Ordner ist für **zukünftige Tests** vorgesehen, sobald fundamentale Filter implementiert sind.

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
