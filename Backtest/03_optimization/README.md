# 03_optimization - Technische Optimierung

## Ziel
CSV-basierte Optimierung der Strategie-Parameter durch Sequential Optimization.

## Status
**Phase 3 - AKTUELL 🎯** (seit 04.01.2026)

---

## Philosophie

**Sequential Optimization** (eine Variable nach der anderen)
**NICHT Grid Search** (alle Kombinationen → Overfit!)

**Vorteile**:
- Überschaubare Rechenzeit
- Klare Impact-Analyse pro Variable
- Verständnis wie Variablen wirken
- Overfitting-Risiko minimiert

---

## Datenquelle

**Baseline CSVs von Phase 2**:
```
/Users/carvin/Documents/Trading Backtests/05_Model 3/Backtest/02_technical/01_Single_TF/results/Trades/
├── W_trades.csv
├── 3D_trades.csv
└── M_trades.csv
```

**Wichtigste Spalten**:
- Gap/Pivot: `gap_pips`, `wick_diff_pips`, `wick_diff_pct`
- Entry/Exit: `entry_price`, `sl_price`, `tp_price`, `final_rr`
- Performance: `pnl_r`, `win_loss`, `duration_days`, `mfe_pips`, `mae_pips`
- Meta: `pair`, `htf_timeframe`, `direction`, `priority_refinement_tf`

---

## Struktur

```
03_optimization/
├── README.md (diese Datei)
│
├── 01_Single_TF/
│   ├── scripts/
│   │   ├── optimize_gap_size.py           # Gap Size Filter (Phase A + B + Walk-Forward)
│   │   ├── optimize_wick_asymmetry.py     # Wick Asymmetrie Filter
│   │   ├── optimize_duration.py           # Duration Filter
│   │   └── report_helpers.py              # Shared Stats Functions
│   │
│   ├── 01_Gap_Size/
│   │   ├── A_Coarse_Ranges/               # Phase A: 8 Grobe Ranges
│   │   │   ├── W_report.txt
│   │   │   ├── 3D_report.txt
│   │   │   ├── M_report.txt
│   │   │   └── summary.txt                # Vergleichstabelle
│   │   │
│   │   ├── B_Fine_Steps/                  # Phase B: ~20 Feine Schritte
│   │   │   ├── W_report.txt
│   │   │   ├── 3D_report.txt
│   │   │   ├── M_report.txt
│   │   │   └── summary.txt
│   │   │
│   │   └── C_Walk_Forward/                # Walk-Forward Validation
│   │       ├── results/
│   │       │   ├── window_01.txt
│   │       │   ├── window_02.txt
│   │       │   └── ...
│   │       └── summary.txt                # OOS Stabilität
│   │
│   ├── 02_Wick_Asymmetry/
│   ├── 03_Duration/
│   └── ...
│
└── 02_Strategy/                           # Kombinierte Strategie-Tests (später)
```

---

## Test-Prioritäten

### 🔴 PRIORITÄT 1 - CSV-basiert (SCHNELL!)

1. **Gap Size Filter** - START HERE!
   - Phase A: Grobe Ranges (8 Tests)
   - Phase B: Feine Schritte (~20 Tests)
   - Walk-Forward Validation (14 Windows)
   - **Zeit**: ~3h

2. **Wick Asymmetrie Filter**
   - 5 Tests (0%, 10%, 20%, 30%, 40%)
   - **Zeit**: <10 min

3. **Duration Filter**
   - Verschiedene Min/Max Ranges
   - **Zeit**: <10 min

### 🟡 PRIORITÄT 2 - Neuer Backtest nötig

4. **Gap Versatz Filter**
   - CSV erweitern mit `k1_close`, `k2_open`, `versatz_ratio`
   - 5 Tests (unlimited, 2.0, 1.5, 1.0, 0.5)
   - **Zeit**: ~2h (Re-Run + Filter)

5. **Entry Confirmation**
   - 3 Tests (direct_touch, 1h_close, 4h_close)
   - Walk-Forward: JA
   - **Zeit**: ~6h

---

## Walk-Forward Testing

### Setup (Empfohlen)
```
IS (In-Sample): 5 Jahre
OOS (Out-of-Sample): 1 Jahr
Step: 1 Jahr
Windows: ~14 (2010-2024)
```

### Prozedur
```
Window 1: 2005-2009 IS → 2010 OOS
Window 2: 2006-2010 IS → 2011 OOS
...
Window 14: 2019-2023 IS → 2024 OOS
```

### Bewertung
- ✅ **ROBUST**: OOS Median Exp > 0.08R, >90% positive Windows, Std Dev < 0.05R
- ⚠️ **UNSICHER**: OOS Median 0.05-0.10R, 70-90% positive, Std Dev 0.05-0.10R
- ❌ **OVERFIT**: OOS negativ oder Std Dev > 0.10R

---

## Wichtige Metriken

### Primäre Ziele
- ✅ **Profit Expectancy**: 0.1 - 0.3 R/Trade
- ✅ **Win Rate**: 45-50%
- ✅ **Max Duration**: 95% der Trades unter 60 Tagen
- ✅ **SQN**: > 1.6 (gut), > 2.0 (sehr gut)

### Sekundäre Ziele
- **Profit Factor**: > 1.3
- **Max Drawdown**: < 10R
- **Sharpe Ratio**: > 1.0
- **Trade Count**: > 200 pro HTF

### Funded Account Viability
- Consistent Profitability
- Controlled Drawdown (< 5-10% Max DD)
- Genug Trades (> 200)
- Stabile OOS Performance

---

## Overfitting-Checkliste

Vor jedem Test-Abschluss prüfen:

- ✅ Nur 1 Variable optimiert
- ✅ Genug Trades (>200 pro HTF)
- ✅ Parameter logisch sinnvoll
- ✅ Robustheit über Pairs (>60% profitabel)
- ✅ Smooth Performance-Kurve (keine Cliffs)
- ✅ OOS ähnlich IS (Diff <20%)
- ✅ Walk-Forward: >90% positive Windows
- ✅ Deutliche Verbesserung vs Baseline (>20%)

---

## Nächste Schritte

1. 🎯 **Gap Size Filter** (Phase A) - JETZT
2. ⏳ Gap Size Filter (Phase B + Walk-Forward)
3. ⏳ CSV erweitern (k1/k2 Details, Versatz)
4. ⏳ Weitere CSV-Tests (Wick, Duration)
5. ⏳ Kritische Backtests (Entry, Ref TFs)

**Dokumentation**:
- Siehe `BACKTEST_PROCESS.md` für detaillierte Prozedur
- Siehe `STRATEGIE_VARIABLES.md` für alle Variablen

---

*Last Updated: 04.01.2026*
