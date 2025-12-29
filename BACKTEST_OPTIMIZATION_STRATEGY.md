# Model 3 - Backtest Optimization Strategy

## Problem Statement

**Ohne Optimierung**: Jeder Backtest-Run dauert lange weil:
1. Daten müssen geladen werden (28 Pairs × 6 TFs)
2. Pivots müssen detektiert werden (auf 3D/W/M)
3. Refinements müssen gesucht werden (auf H1-W)
4. Entry/Exit muss simuliert werden (H1 Iteration)

**Ziel**: Backtest in <30 Minuten! ⚡

---

## ✅ LÖSUNG: Parquet Pre-Processing Cache

### Konzept

**Idee**: Teure Operationen EINMAL machen, Ergebnisse cachen

**Was cachen?**
1. ✅ **HTF Pivots** (Pivot Detection ist teuer!)
2. ⚠️ **Refinements** (optional - sehr teuer, aber große Datei)
3. ❌ **Entry/Exit** (NICHT cachen - muss immer neu wegen Portfolio-Simulation)

---

## 🔧 IMPLEMENTATION PLAN

### Phase 1: Pivot Pre-Processing ⭐ MUST HAVE

**Script**: `scripts/preprocessing/cache_pivots.py`

```python
"""
Detektiert ALLE HTF Pivots für alle Pairs + Timeframes
Speichert als Parquet für schnellen Zugriff
"""

import pandas as pd
from pathlib import Path
from config import ALL_PAIRS
from data_loader import load_oanda_data
from pivot_detection import detect_pivots_in_df

def cache_htf_pivots(pairs, htf_timeframes, start_date, end_date):
    """
    Findet alle HTF Pivots und speichert sie
    """

    print("🔍 Detecting HTF Pivots for Backtest Cache...")
    print(f"   Pairs: {len(pairs)}")
    print(f"   HTF: {', '.join(htf_timeframes)}")
    print(f"   Period: {start_date} to {end_date}")
    print()

    all_pivots = []

    for pair in pairs:
        print(f"Processing {pair}...")

        for htf_tf in htf_timeframes:
            # Load HTF Data
            df_htf = load_oanda_data(pair, htf_tf, start_date, end_date)

            # Detect Pivots
            pivots = detect_pivots_in_df(df_htf)

            # Store Pivot Info
            for pivot in pivots:
                all_pivots.append({
                    'pair': pair,
                    'htf_timeframe': htf_tf,
                    'direction': pivot.direction,  # 'bullish' or 'bearish'

                    # Timestamps (ALLE Open-Zeit!)
                    'k1_time': pivot.k1_time,
                    'k2_time': pivot.k2_time,
                    'valid_time': pivot.valid_time,  # K3 Open

                    # Price Levels
                    'pivot_price': pivot.pivot,
                    'extreme_price': pivot.extreme,
                    'near_price': pivot.near,

                    # Gap Info
                    'gap_pips': pivot.gap_pips,
                    'wick_diff_pips': pivot.wick_diff_pips,
                    'wick_diff_pct': pivot.wick_diff_pct
                })

            print(f"   {htf_tf}: {len(pivots)} pivots")

    # Convert to DataFrame
    df_pivots = pd.DataFrame(all_pivots)

    # Save as Parquet (fast loading!)
    cache_dir = Path('cache')
    cache_dir.mkdir(exist_ok=True)

    output_file = cache_dir / 'htf_pivots.parquet'
    df_pivots.to_parquet(output_file, index=False)

    print(f"\n✅ Cache created!")
    print(f"   Total Pivots: {len(df_pivots)}")
    print(f"   File: {output_file}")
    print(f"   Size: {output_file.stat().st_size / 1024 / 1024:.1f} MB")

    return df_pivots

if __name__ == '__main__':
    # Config for Weekly Baseline
    cache_htf_pivots(
        pairs=ALL_PAIRS,  # 28 Pairs
        htf_timeframes=['W'],  # Weekly only für Baseline
        start_date='2010-01-01',
        end_date='2024-12-31'
    )
```

**Ausführung**:
```bash
cd "05_Model 3"
python scripts/preprocessing/cache_pivots.py
```

**Output**:
```
🔍 Detecting HTF Pivots for Backtest Cache...
   Pairs: 28
   HTF: W
   Period: 2010-01-01 to 2024-12-31

Processing EURUSD...
   W: 47 pivots
Processing GBPUSD...
   W: 42 pivots
Processing USDJPY...
   W: 39 pivots
...
Processing EURCAD...
   W: 35 pivots

✅ Cache created!
   Total Pivots: 1,247
   File: cache/htf_pivots.parquet
   Size: 0.3 MB
```

**Dauer**: ~5-10 Minuten (einmalig!)

---

### Phase 2: Backtest mit Pivot Cache

**Script**: `scripts/backtesting/backtest_weekly_baseline.py`

```python
"""
Backtest mit Pre-Computed Pivots aus Cache
"""

import pandas as pd
from pathlib import Path

def load_pivot_cache(htf_timeframe, start_date=None, end_date=None):
    """
    Lädt Pivots aus Cache
    """
    cache_file = Path('cache/htf_pivots.parquet')

    if not cache_file.exists():
        raise FileNotFoundError(
            "Pivot cache not found! Run: python scripts/preprocessing/cache_pivots.py"
        )

    # Load Parquet (super schnell!)
    df_pivots = pd.read_parquet(cache_file)

    # Filter by HTF
    df_pivots = df_pivots[df_pivots['htf_timeframe'] == htf_timeframe]

    # Filter by date range (optional)
    if start_date:
        df_pivots = df_pivots[df_pivots['valid_time'] >= pd.Timestamp(start_date)]
    if end_date:
        df_pivots = df_pivots[df_pivots['valid_time'] <= pd.Timestamp(end_date)]

    print(f"📂 Loaded {len(df_pivots)} pivots from cache")

    return df_pivots

def run_backtest_with_cache(config):
    """
    Backtest mit Pivot-Cache
    """

    print("=" * 80)
    print("MODEL 3 - WEEKLY BASELINE BACKTEST")
    print("=" * 80)
    print(f"HTF: {config['htf_timeframe']}")
    print(f"Pairs: {len(config['pairs'])}")
    print(f"Period: {config['start_date']} to {config['end_date']}")
    print(f"Entry: {config['entry_confirmation']}")
    print()

    # 1. Load Pivot Cache
    print("📂 Loading pivot cache...")
    pivots_df = load_pivot_cache(
        htf_timeframe=config['htf_timeframe'],
        start_date=config['start_date'],
        end_date=config['end_date']
    )

    # 2. Data Cache für schnelles Loading während Backtest
    data_cache = DataCache()

    # 3. Backtest Loop (Portfolio-Style)
    print("\n🔄 Running backtest...")
    trades = []
    rejected = {
        'no_gap_touch': 0,
        'tp_touched_before_entry': 0,
        'no_refinement': 0,
        'rr_too_low': 0,
        'entry_failed': 0
    }

    for idx, (_, pivot) in enumerate(pivots_df.iterrows(), 1):
        if idx % 50 == 0:
            print(f"   Processed {idx}/{len(pivots_df)} pivots... ({len(trades)} trades found)")

        # --- GAP TOUCH CHECK ---
        df_daily = data_cache.load_data(
            pair=pivot['pair'],
            timeframe='D',
            start_date=pivot['k1_time'],
            end_date=pivot['valid_time'] + pd.Timedelta(days=365)
        )

        gap_touch_time = find_gap_touch(df_daily, pivot)
        if not gap_touch_time:
            rejected['no_gap_touch'] += 1
            continue

        # --- REFINEMENT SEARCH ---
        # Hier: ON-THE-FLY (nicht aus Cache)
        # Weil Refinement-Cache optional ist
        refinements = find_refinements_for_pivot(
            pivot,
            data_cache,
            max_tf='W',
            max_size_pct=20.0
        )

        if not refinements:
            rejected['no_refinement'] += 1
            continue

        # --- ENTRY LEVEL SELECTION ---
        entry_level = select_priority_refinement(refinements, pivot)

        # RR-Check für Entry-Level
        sl, tp, rr = compute_sl_tp(
            pivot,
            entry_price=entry_level['near_price'],  # Approximation
            config=config
        )

        if rr is None or rr < config['min_rr']:
            rejected['rr_too_low'] += 1
            continue

        # --- ENTRY SEARCH ---
        df_h1 = data_cache.load_data(
            pair=pivot['pair'],
            timeframe='1H',
            start_date=gap_touch_time,
            end_date=gap_touch_time + pd.Timedelta(days=90)
        )

        entry_time, entry_price = find_entry(
            df_h1,
            entry_level,
            confirmation_type=config['entry_confirmation']
        )

        if not entry_time:
            rejected['entry_failed'] += 1
            continue

        # --- TP-CHECK (korrigierte Logik!) ---
        tp_price = calculate_tp(pivot)
        tp_touched = check_tp_touched_before_entry(
            df_h1,
            pivot,
            gap_touch_time,
            entry_time,
            tp_price
        )

        if tp_touched:
            rejected['tp_touched_before_entry'] += 1
            continue

        # --- SL/TP FINAL CALCULATION ---
        sl, tp, rr = compute_sl_tp(pivot, entry_price, config)
        if sl is None:
            rejected['rr_too_low'] += 1
            continue

        # --- EXIT SIMULATION ---
        exit_time, exit_price, exit_type = simulate_exit(
            df_h1,
            entry_time,
            entry_price,
            sl,
            tp
        )

        # --- MFE/MAE CALCULATION ---
        mfe_pips, mfe_pct = calculate_mfe(
            df_h1[df_h1['time'] >= entry_time],
            entry_price,
            tp,
            pivot['direction']
        )

        mae_pips, mae_pct = calculate_mae(
            df_h1[df_h1['time'] >= entry_time],
            entry_price,
            sl,
            pivot['direction']
        )

        # --- TRADE RECORD ---
        pnl_r = calculate_pnl_r(entry_price, exit_price, sl, exit_type, pivot['direction'])

        trade = {
            'trade_id': len(trades) + 1,
            'pair': pivot['pair'],
            'htf_timeframe': pivot['htf_timeframe'],
            'direction': pivot['direction'],
            'entry_type': config['entry_confirmation'],

            # Timestamps
            'pivot_time': pivot['k2_time'],
            'valid_time': pivot['valid_time'],
            'gap_touch_time': gap_touch_time,
            'entry_time': entry_time,
            'exit_time': exit_time,
            'duration_days': (exit_time - entry_time).days,

            # HTF Pivot Levels
            'pivot_price': pivot['pivot_price'],
            'extreme_price': pivot['extreme_price'],
            'near_price': pivot['near_price'],
            'gap_pips': pivot['gap_pips'],
            'wick_diff_pips': pivot['wick_diff_pips'],
            'wick_diff_pct': pivot['wick_diff_pct'],

            # Refinement Info
            'total_refinements': len(refinements),
            'priority_refinement_tf': entry_level['timeframe'],

            # Trade Levels
            'entry_price': entry_price,
            'sl_price': sl,
            'tp_price': tp,
            'exit_price': exit_price,

            # Trade Metrics
            'final_rr': rr,
            'sl_distance_pips': abs(entry_price - sl) * 10000,
            'tp_distance_pips': abs(entry_price - tp) * 10000,
            'exit_type': exit_type,  # 'TP' or 'SL'
            'pnl_pips': (exit_price - entry_price) * 10000 * (1 if pivot['direction'] == 'bullish' else -1),
            'pnl_r': pnl_r,
            'win_loss': 'win' if pnl_r > 0 else 'loss',

            # MFE/MAE
            'mfe_pips': mfe_pips,
            'mfe_pct': mfe_pct,
            'mae_pips': mae_pips,
            'mae_pct': mae_pct
        }

        trades.append(trade)

    print(f"\n✅ Backtest Complete!")
    print(f"   Total Trades: {len(trades)}")
    print(f"   Rejected Setups:")
    for reason, count in rejected.items():
        print(f"      {reason}: {count}")

    # Convert to DataFrame
    trades_df = pd.DataFrame(trades)

    # 4. Generate Reports
    print("\n📊 Generating reports...")

    # Calculate all stats
    stats = calculate_all_stats(trades_df, config, rejected)

    # TXT Report
    txt_report = generate_txt_report(stats, config)
    report_path = Path('Backtest/02_W_test/baseline_report.txt')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(txt_report, encoding='utf-8')
    print(f"   TXT: {report_path}")

    # HTML Report (QuantStats)
    returns = calculate_returns_series(trades_df, config)
    html_path = Path('Backtest/02_W_test/baseline_report.html')
    generate_quantstats_report(returns, html_path, config)
    print(f"   HTML: {html_path}")

    # CSV Exports
    trades_df.to_csv('Backtest/02_W_test/trades.csv', index=False)
    print(f"   CSV: Backtest/02_W_test/trades.csv")

    print("\n✅ All reports generated!")
    print(f"\n📊 View Reports:")
    print(f"   TXT:  cat Backtest/02_W_test/baseline_report.txt")
    print(f"   HTML: open Backtest/02_W_test/baseline_report.html")

    return trades_df, stats

if __name__ == '__main__':
    config = {
        'htf_timeframe': 'W',
        'pairs': ALL_PAIRS,
        'entry_confirmation': 'direct_touch',
        'start_date': '2010-01-01',
        'end_date': '2024-12-31',
        'risk_per_trade': 0.01,
        'starting_capital': 100000,
        'min_rr': 1.0,
        'max_rr': 1.5,
        'min_sl_distance': 60,
        # Transaktionskosten
        'spread_pips': SPREADS,  # Dictionary per Pair
        'slippage_pips': 0.5
    }

    trades_df, stats = run_backtest_with_cache(config)
```

**Ausführung**:
```bash
python scripts/backtesting/backtest_weekly_baseline.py
```

**Dauer**: ~10-20 Minuten (mit Cache!)

---

## ⚡ PERFORMANCE IMPACT

### Ohne Cache:
```
1. Load Data (28 Pairs × 6 TFs): ~5-10 min
2. Pivot Detection (on-the-fly): ~5 min
3. Refinement Search: ~15 min
4. Entry/Exit Simulation: ~10 min
TOTAL: ~35-40 min
```

### Mit Pivot Cache:
```
1. Load Pivot Cache: <10 seconds ⚡
2. Data Cache (während Backtest): built-in
3. Refinement Search: ~10 min (Data Cache!)
4. Entry/Exit Simulation: ~8 min
TOTAL: ~18-20 min (2x schneller!)
```

---

## 🔄 REFINEMENT CACHE (Optional - Phase 2)

**Wenn Backtest immer noch zu langsam**:

Script: `scripts/preprocessing/cache_refinements.py`

```python
def cache_refinements(pivots_df):
    """
    Findet ALLE Refinements für alle Pivots
    WARNUNG: Große Datei! (~5-10 MB)
    """

    all_refinements = []

    for _, pivot in pivots_df.iterrows():
        refinements = find_refinements_for_pivot(pivot, ...)

        for ref in refinements:
            all_refinements.append({
                'pivot_id': f"{pivot['pair']}_{pivot['htf_timeframe']}_{pivot['k2_time']}",
                # ... refinement details
            })

    df_ref = pd.DataFrame(all_refinements)
    df_ref.to_parquet('cache/refinements.parquet')

    return df_ref
```

**Trade-off**:
- ✅ Noch schneller (~5 min total!)
- ❌ Große Cache-Datei
- ❌ Cache muss neu erstellt werden bei Regel-Änderung

**Empfehlung**: Erst OHNE Refinement-Cache testen!

---

## 📁 FOLDER STRUCTURE

```
05_Model 3/
├── cache/                              ← NEU!
│   ├── .gitignore                      ← Cache nicht committen
│   ├── htf_pivots.parquet              ← HTF Pivots (0.3 MB)
│   └── refinements.parquet             ← Optional (5-10 MB)
│
├── scripts/
│   ├── preprocessing/                  ← NEU!
│   │   ├── cache_pivots.py             ← Pivot Cache erstellen
│   │   └── cache_refinements.py        ← Optional: Refinement Cache
│   │
│   └── backtesting/
│       ├── backtest_weekly_baseline.py ← Mit Cache
│       └── backtest_model3.py          ← Alte Version (ohne Cache)
│
├── Backtest/
│   └── 02_W_test/                      ← Baseline Results
│       ├── baseline_report.txt
│       ├── baseline_report.html
│       ├── trades.csv
│       └── equity_curve.csv
```

---

## 🎯 WORKFLOW

### 1. Cache Erstellen (Einmalig)

```bash
cd "05_Model 3"

# Pivot Cache für Weekly
python scripts/preprocessing/cache_pivots.py
# Dauer: ~10 min, Output: cache/htf_pivots.parquet
```

### 2. Baseline Backtest

```bash
# Run Backtest mit Cache
python scripts/backtesting/backtest_weekly_baseline.py
# Dauer: ~20 min

# Check Reports
cat Backtest/02_W_test/baseline_report.txt
open Backtest/02_W_test/baseline_report.html
```

### 3. Cache Erneuern (Bei Bedarf)

**Wann Cache erneuern?**
- Strategie-Regel geändert (Pivot-Definition)
- Neue Daten verfügbar (2025 Update)
- HTF Timeframe geändert (W → 3D, M)

```bash
# Cache löschen
rm cache/*.parquet

# Neu erstellen
python scripts/preprocessing/cache_pivots.py --htf W,3D,M
```

---

## ✅ NEXT STEPS

1. ✅ Dokumentation finalisiert
2. 🔄 Implement `cache_pivots.py`
3. 🔄 Implement `backtest_weekly_baseline.py`
4. ▶️ Run Cache Creation
5. ▶️ Run Baseline Backtest
6. 📊 Analyze Results

---

*Last Updated: 29.12.2025*
