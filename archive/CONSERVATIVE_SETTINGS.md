# Conservative Strategy Settings - ARCHIVIERT

**Datum**: 31.12.2025
**Grund**: Strategie-Fokus nur noch auf Pure (R-basiert), keine Transaction Costs mehr in Backtest-Phase

---

## Was war "Conservative"?

Die Conservative Variante hat **realistische Transaction Costs** auf die Pure Strategy angewendet:

### Transaction Costs Modell

**Spreads** (variabel nach Pair):
```python
SPREAD_RANGES = {
    # Majors (0.4-1.2 pips)
    'EURUSD': (0.4, 1.2), 'GBPUSD': (0.6, 1.5), 'USDJPY': (0.4, 1.0),
    'USDCHF': (0.7, 1.8), 'AUDUSD': (0.5, 1.5), 'USDCAD': (0.7, 1.8), 'NZDUSD': (0.8, 2.0),

    # EUR Crosses (1.0-2.0 pips)
    'EURGBP': (1.0, 2.0), 'EURJPY': (1.2, 2.5), 'EURAUD': (1.5, 3.0),
    'EURCHF': (1.0, 2.2), 'EURCAD': (1.5, 3.0), 'EURNZD': (2.0, 4.0),

    # GBP Crosses (1.5-3.0 pips)
    'GBPJPY': (1.5, 3.0), 'GBPAUD': (2.0, 4.0), 'GBPCAD': (2.5, 4.5),
    'GBPNZD': (3.0, 5.0), 'GBPCHF': (1.8, 3.5),

    # Other Crosses (1.5-3.5 pips)
    'AUDJPY': (1.2, 2.5), 'NZDJPY': (1.5, 3.0), 'CHFJPY': (1.5, 3.0), 'CADJPY': (1.5, 3.0),
    'AUDNZD': (2.0, 4.0), 'AUDCAD': (1.8, 3.5), 'AUDCHF': (2.0, 4.0),
    'NZDCAD': (2.5, 4.5), 'NZDCHF': (2.5, 4.5), 'CADCHF': (2.0, 4.0),
}
```

**Commission**: $5 per Standard Lot (beide Seiten: Entry + Exit)

**Lot Size Berechnung**:
```python
risk_amount = STARTING_CAPITAL * RISK_PER_TRADE  # z.B. $100k * 1% = $1000
sl_pips = abs(entry_price - sl_price) / pip_value
dollars_per_pip = risk_amount / sl_pips
standard_lot_pip_value = 10 if 'JPY' in pair else 1  # JPY special
lots = dollars_per_pip / standard_lot_pip_value
```

---

## Code (apply_conservative_costs)

```python
def apply_conservative_costs(trades_df, starting_capital, risk_per_trade):
    """
    Apply variable spreads + commission to trades

    Returns: DataFrame mit zusätzlichen Columns:
    - entry_spread_pips, exit_spread_pips
    - commission_usd
    - pnl_r_after_costs, pnl_usd_after_costs
    """
    trades_cons = trades_df.copy()

    for idx, row in trades_cons.iterrows():
        pair = row['pair']

        # Random spread within range
        spread_min, spread_max = SPREAD_RANGES.get(pair, (1.0, 2.5))
        entry_spread = np.random.uniform(spread_min, spread_max)
        exit_spread = np.random.uniform(spread_min, spread_max)

        trades_cons.at[idx, 'entry_spread_pips'] = entry_spread
        trades_cons.at[idx, 'exit_spread_pips'] = exit_spread

        # Spread cost in pips (Entry slippage + Exit slippage)
        total_spread_pips = entry_spread + exit_spread

        # Commission (fixed $5 per lot, both sides)
        lots = row['lots']
        commission = lots * 10  # $5 entry + $5 exit = $10 per lot
        trades_cons.at[idx, 'commission_usd'] = commission

        # Calculate new PnL after costs
        risk_amount = starting_capital * risk_per_trade
        spread_cost_r = (total_spread_pips / row['sl_pips']) if row['sl_pips'] > 0 else 0
        commission_cost_r = commission / risk_amount if risk_amount > 0 else 0

        pnl_r_after = row['pnl_r'] - spread_cost_r - commission_cost_r
        pnl_usd_after = pnl_r_after * risk_amount

        trades_cons.at[idx, 'pnl_r_after_costs'] = pnl_r_after
        trades_cons.at[idx, 'pnl_usd_after_costs'] = pnl_usd_after

    return trades_cons
```

---

## Warum archiviert?

**Grund 1**: Zu früh in Entwicklung
- Fokus soll auf R-basierter Performance sein
- Transaction Costs sind erst relevant bei finaler Strategie

**Grund 2**: Unnötige Komplexität
- Verdoppelt Report-Anzahl (Pure + Conservative)
- Macht Analyse schwieriger
- Spreads sind variabel → keine fixen Werte

**Grund 3**: Kann später einfach wieder hinzugefügt werden
- Code ist dokumentiert
- Settings sind gespeichert
- `apply_conservative_costs()` Funktion existiert in `report_helpers.py`

---

## Wann wieder aktivieren?

**NACH** erfolgreicher Optimierung der Strategie:
1. Technische Regeln optimiert → Positiver Expectancy
2. Fundamentale Filter hinzugefügt → Expectancy 2-4R
3. Finale Parameter gefunden → Strategie "locked"
4. **DANN**: Conservative Variante wieder aktivieren für Live-Simulationen

---

## Typische Impact von Transaction Costs

**Beispiel W Pure vs Conservative** (alte Results):
- Pure Return: +26.7%
- Conservative Return: -60.7%
- **Impact**: -87.4% (!)

**Warum so groß?**
- Viele Trades (~4000 über 15 Jahre)
- RR meist 1.0-1.5 (niedrig)
- Bei 1.5 pips average spread + $10 commission pro Trade
- Bei 1% Risk = $1000 → Commission = 1% of Risk!
- Spread = ~0.3-0.5% of Risk zusätzlich
- → Total Cost pro Trade: ~1.3-1.5% of Risk
- Bei Expectancy nahe 0 → wird stark negativ!

---

*Archiviert am: 31.12.2025*
*Kann reaktiviert werden wenn Strategie profitabel ist*
