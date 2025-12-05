# Model X Forex Backtest

## Data Setup Workflow

### 1. Download Oanda Data (H1, H4, D, W, M)
```bash
python scripts/1_download_data.py
```
Downloads all pairs for H1, H4, D, W, M and saves as CSV files.
**Note:** 3D data is NOT downloaded (must be added manually).

### 2. Add 3D Data Manually
Export 3D candles from TradingView and place in `data/3D_raw/`:
```
data/3D_raw/EURUSD.csv
data/3D_raw/GBPUSD.csv
data/3D_raw/AUDUSD.csv
...
```

### 3. Convert to Parquet
```bash
python scripts/2_convert_csv_to_parquet.py
```
Converts all CSV files (including manual 3D data) to Parquet format.

### 4. Run Backtest
```bash
python scripts/backtest_modelx.py
# or
python scripts/run_all_backtests.py
```
