from pathlib import Path

# API CONFIGURATION
OANDA_API_KEY = "cc9f7bc8c8c8ba1ae722d1566ef1732f-f89066eb8786c746b38a43d5d99d3527"
OANDA_ACCOUNT_TYPE = "live"  # Changed from "practice" - Live has more accurate historical data

# PAIRS
PAIRS = [
    "AUD_CAD", "AUD_CHF", "AUD_JPY", "AUD_NZD", "AUD_USD",
    "CAD_CHF", "CAD_JPY", "CHF_JPY",
    "EUR_AUD", "EUR_CAD", "EUR_CHF", "EUR_GBP", "EUR_JPY", "EUR_NZD", "EUR_USD",
    "GBP_AUD", "GBP_CAD", "GBP_CHF", "GBP_JPY", "GBP_NZD", "GBP_USD",
    "NZD_CAD", "NZD_CHF", "NZD_JPY", "NZD_USD",
    "USD_CAD", "USD_CHF", "USD_JPY"
]

# TIMEFRAMES
TIMEFRAMES = ["H1", "H4", "D", "3D", "W", "M"]

# PATHS
PROJECT_ROOT = Path(__file__).parent
BACKTEST_ROOT = PROJECT_ROOT.parent.parent  # /Users/carvin/Documents/Trading Backtests/
DATA_PATH = BACKTEST_ROOT / "Data" / "Chartdata" / "Forex"
RESULTS_PATH = PROJECT_ROOT / "results"

# SETTINGS
INITIAL_CAPITAL = 100000
START_DATE = "2010-01-01"

# MODEL X SETTINGS
DOJI_THRESHOLD = 5.0
VERSATZ_FILTER = 2.0
FIB_SL = 1.5
FIB_TP = -3.0