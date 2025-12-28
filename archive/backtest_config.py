"""
Model X Backtest Configuration
Alle Backtest-Regeln als konfigurierbare Parameter
"""

# =============================================================================
# PIVOT RULES (FIXED - nicht variabel)
# =============================================================================

# Pivot Timeframes - NUR diese für Pivot-Generierung
PIVOT_TIMEFRAMES = ['3D', 'W', 'M']

# Pivot Validation - Pivot aus 2 Candles, valid ab Open der 3. / Close der 2. Candle
PIVOT_VALIDATION_CANDLES = 2  # Pivot braucht 2 Candles
PIVOT_VALID_AFTER_CANDLES = 2  # Valid ab 3. Candle (nach 2 Candles)


# =============================================================================
# ENTRY RULES (VARIABLE)
# =============================================================================

# Multiple Timeframe Gaps für gleiches Pair
# Wenn ein Pair gleichzeitig auf mehreren Timeframes ein Gap hat
MULTIPLE_TIMEFRAME_STRATEGY = 'highest'  # 'highest', 'lowest', 'largest_gap', 'all'
# 'highest': Nimm nur höchsten Timeframe (M > W > 3D)
# 'lowest': Nimm nur niedrigsten Timeframe (3D > W > M)
# 'largest_gap': Nimm Gap mit größtem Pip-Range
# 'all': Nimm alle Gaps (mehrere Trades pro Pair)

# Entry bei offenen Trades
ENTRY_WITH_OPEN_TRADES = 'always'  # 'always', 'only_if_profit', 'only_if_no_loss', 'wait'
# 'always': Neue Trades immer nehmen
# 'only_if_profit': Nur wenn offene Trades im Profit
# 'only_if_no_loss': Nur wenn keine offenen Losses
# 'wait': Warten bis X% geschlossen sind

# Entry Types
ENTRY_TYPE = 'direct_touch'  # 'direct_touch', 'retest', 'candle_close'

# Exit Types  
EXIT_TYPE = 'fixed'  # 'fixed', 'trailing', 'breakeven'


# =============================================================================
# POSITION MANAGEMENT (VARIABLE)
# =============================================================================

# Maximum gleichzeitige Positionen
MAX_TOTAL_POSITIONS = None  # None = unbegrenzt, oder Integer (z.B. 10)
MAX_POSITIONS_PER_PAIR = None  # None = unbegrenzt, oder Integer (z.B. 3)

# Trade Priorität bei Limits (wenn mehrere Setups gleichzeitig entstehen)
TRADE_PRIORITY = 'timeframe'  # 'timeframe', 'alphabetical', 'gap_size', 'performance'
# 'timeframe': Höherer Timeframe zuerst (M > W > 3D)
# 'alphabetical': Nach Pair alphabetisch
# 'gap_size': Größerer Gap zuerst
# 'performance': Besser performende Pairs zuerst


# =============================================================================
# RISK LIMITS (VARIABLE)
# =============================================================================

# Max Pip-Größen (None = keine Limits)
MAX_GAP_SIZE_PIPS = None  # Max Pips für Gap (z.B. 500)
MAX_TP_DISTANCE_PIPS = None  # Max Pips bis TP (z.B. 1000)
MAX_SL_DISTANCE_PIPS = None  # Max Pips Risk (z.B. 200)

# Min Pip-Größen
MIN_GAP_SIZE_PIPS = None  # Min Pips für Gap (z.B. 10)
MIN_TP_DISTANCE_PIPS = None  # Min Pips bis TP
MIN_SL_DISTANCE_PIPS = None  # Min Pips Risk

# Risk per Trade
RISK_PER_TRADE_PCT = 1.0  # Prozent Risk pro Trade (für Account % Berechnungen)


# =============================================================================
# BACKTEST SETTINGS
# =============================================================================

# Alle 28 Forex Pairs
ALL_PAIRS = [
    'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'AUDUSD',
    'CADCHF', 'CADJPY', 'CHFJPY',
    'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD', 'EURUSD',
    'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD', 'GBPUSD',
    'NZDCAD', 'NZDCHF', 'NZDJPY', 'NZDUSD',
    'USDCAD', 'USDCHF', 'USDJPY'
]

# Default Timeframes für Backtest
DEFAULT_TIMEFRAMES = ['3D', 'W', 'M']

# Verfügbare Entry Timeframes (für zukünftige Erweiterung)
ENTRY_TIMEFRAMES = ['H1', 'H4', 'D', '3D', 'W', 'M']


# =============================================================================
# OUTPUT SETTINGS
# =============================================================================

# Report alle Stats anzeigen
REPORT_SHOW_ALL_STATS = True

# Trades nach Entry Time sortieren
SORT_TRADES_BY_ENTRY_TIME = True

# Verbose Output
VERBOSE = True


# =============================================================================
# CONFIG SUMMARY FUNCTION
# =============================================================================

def get_config_summary():
    """Gibt eine Zusammenfassung der aktuellen Config zurück"""
    summary = f"""
BACKTEST CONFIGURATION
{'='*80}

PIVOT RULES (FIXED):
  Pivot Timeframes:        {', '.join(PIVOT_TIMEFRAMES)}
  Validation Candles:      {PIVOT_VALIDATION_CANDLES}
  Valid After:             {PIVOT_VALID_AFTER_CANDLES} candles

ENTRY RULES:
  Multiple Timeframes:     {MULTIPLE_TIMEFRAME_STRATEGY}
  Entry with Open Trades:  {ENTRY_WITH_OPEN_TRADES}
  Entry Type:              {ENTRY_TYPE}
  Exit Type:               {EXIT_TYPE}

POSITION MANAGEMENT:
  Max Total Positions:     {MAX_TOTAL_POSITIONS if MAX_TOTAL_POSITIONS else 'Unlimited'}
  Max Per Pair:            {MAX_POSITIONS_PER_PAIR if MAX_POSITIONS_PER_PAIR else 'Unlimited'}
  Trade Priority:          {TRADE_PRIORITY}

RISK LIMITS:
  Max Gap Size:            {MAX_GAP_SIZE_PIPS if MAX_GAP_SIZE_PIPS else 'None'} pips
  Max TP Distance:         {MAX_TP_DISTANCE_PIPS if MAX_TP_DISTANCE_PIPS else 'None'} pips
  Max SL Distance:         {MAX_SL_DISTANCE_PIPS if MAX_SL_DISTANCE_PIPS else 'None'} pips
  Risk per Trade:          {RISK_PER_TRADE_PCT}%

PAIRS & TIMEFRAMES:
  Total Pairs:             {len(ALL_PAIRS)}
  Default Timeframes:      {', '.join(DEFAULT_TIMEFRAMES)}

{'='*80}
"""
    return summary


if __name__ == '__main__':
    print(get_config_summary())
