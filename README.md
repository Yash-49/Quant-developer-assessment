# Quant Developer Assessment - Submission

This repository contains the required deliverables for the SMA crossover backtesting assignment.

## Deliverables
- `data/ohlc_clean.csv` (cleaned OHLCV, daily, ~3 months)
- `configs/strategy.json` (data path, timezone, starting equity, SMA params, execution rules)
- `scripts/Clean_csv.py` (clean raw export and write `data/ohlc_clean.csv`)
- `scripts/run_strategy.py` (no-lookahead SMA crossover, next-day open, fixed qty)
- `outputs/orders.xlsx` (columns: entry_dt, entry_price, qty, exit_dt, exit_price, pnl, bars_held)
- `docs/tv_export.png` (screenshot)

## How data was obtained
Via Yahoo Finance using the `yfinance` Python library (e.g., NIFTY = `^NSEI`).

Quick fetch snippet (run once in Python to create `data/ohlc_tv_raw.csv`):
```python
import yfinance as yf, pandas as pd
sym = "^NSEI"  # change if needed
raw = yf.download(sym, period="3mo", interval="1d", progress=False).reset_index()
raw = raw.rename(columns={"Date":"date","Open":"open","High":"high","Low":"low","Close":"close","Volume":"volume"})
raw = raw[["date","open","high","low","close","volume"]]
raw.to_csv("data/ohlc_tv_raw.csv", index=False)
```

## How to run
1) Clean the raw file and create `data/ohlc_clean.csv`:
```bash
python scripts/Clean_csv.py
```
2) Run the SMA crossover strategy with next-day open execution:
```bash
python scripts/run_strategy.py --config configs/strategy.json --out outputs/orders.xlsx
```
3) Results are saved to `outputs/orders.xlsx`.

## Assumptions
- Daily bars; execution at next trading day open (no lookahead).
- Fixed quantity from config; no transaction costs.
- Timezone is IST (`Asia/Kolkata`) for timestamp formatting only.
- If a position is open at the end, exit fields are left blank.

## (Optional) Time & AI prompts
- Time spent: <fill in>
- Prompts used: <add 1–2 representative prompts>

## Extras
Additional intraday utilities are provided under `extras/intraday/` for 5‑minute data (not required for the assessment).
