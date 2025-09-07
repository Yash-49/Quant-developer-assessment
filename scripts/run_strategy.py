# scripts/run_strategy.py
import json
import argparse
from pathlib import Path
import pandas as pd

REQUIRED_COLS = ["date","open","high","low","close","volume"]
OUTPUT_COLS = ["entry_dt","entry_price","qty","exit_dt","exit_price","pnl","bars_held"]


def load_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_data(csv_path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    if list(df.columns) != REQUIRED_COLS:
        raise ValueError(f"Columns mismatch. Found {list(df.columns)}, required {REQUIRED_COLS}")
    df["date"] = pd.to_datetime(df["date"])  # naive date
    df = df.sort_values("date").reset_index(drop=True)
    return df


def compute_sma_signals(df: pd.DataFrame, fast: int, slow: int) -> pd.DataFrame:
    out = df.copy()
    out[f"sma_{fast}"] = out["close"].rolling(fast).mean()
    out[f"sma_{slow}"] = out["close"].rolling(slow).mean()
    # signal = 1 when fast > slow, 0 otherwise (flat)
    out["signal"] = (out[f"sma_{fast}"] > out[f"sma_{slow}"]).astype(int)
    return out


def _make_dt(date_val: pd.Timestamp, hh: int, mm: int, tzname: str) -> pd.Timestamp:
    # combine date with time and localize to timezone
    ts = pd.Timestamp(year=date_val.year, month=date_val.month, day=date_val.day, hour=hh, minute=mm)
    try:
        return ts.tz_localize(tzname)
    except Exception:
        # if already tz-aware or tz not found, return naive with time set
        return ts


def generate_orders(df: pd.DataFrame, qty: int, tzname: str) -> pd.DataFrame:
    # Trades occur when signal changes (entry on 0->1, exit on 1->0). Execute at next day's open.
    out = df.copy()
    out["signal_prev"] = out["signal"].shift(1).fillna(0)

    orders = []
    open_entry = None
    n = len(out)

    for idx in range(n - 1):
        row = out.iloc[idx]
        next_row = out.iloc[idx + 1]

        # signal availability assumed at end of trading day (e.g., 15:30 local)
        # and execution at next day's open (e.g., 09:15)
        # entry signal: prev=0, curr=1
        if row["signal_prev"] == 0 and row["signal"] == 1 and open_entry is None:
            # execute at next open
            open_entry = {
                "entry_dt": _make_dt(next_row["date"], 9, 15, tzname),
                "entry_price": next_row["open"],
                "qty": qty,
            }

        # exit signal: prev=1, curr=0
        if row["signal_prev"] == 1 and row["signal"] == 0 and open_entry is not None:
            exit_dt = _make_dt(next_row["date"], 9, 15, tzname)
            pnl = (next_row["open"] - open_entry["entry_price"]) * open_entry["qty"]
            bars_held = (pd.to_datetime(exit_dt).tz_localize(None) - pd.to_datetime(open_entry["entry_dt"]).tz_localize(None)).days
            orders.append({
                "entry_dt": open_entry["entry_dt"],
                "entry_price": float(open_entry["entry_price"]),
                "qty": int(open_entry["qty"]),
                "exit_dt": exit_dt,
                "exit_price": float(next_row["open"]),
                "pnl": float(pnl),
                "bars_held": int(bars_held),
            })
            open_entry = None

    # if still open at end, record open position with exit fields blank
    if open_entry is not None:
        orders.append({
            "entry_dt": open_entry["entry_dt"],
            "entry_price": float(open_entry["entry_price"]),
            "qty": int(open_entry["qty"]),
            "exit_dt": "",
            "exit_price": "",
            "pnl": "",
            "bars_held": "",
        })

    orders_df = pd.DataFrame(orders, columns=OUTPUT_COLS)
    # format datetimes as 'YYYY-MM-DD HH:MM:SS' (IST as per config)
    for c in ["entry_dt", "exit_dt"]:
        if c in orders_df.columns and orders_df[c].dtype == "datetime64[ns, Asia/Kolkata]":
            orders_df[c] = pd.to_datetime(orders_df[c]).dt.tz_localize(None).dt.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # if tz-naive datetime
            try:
                orders_df[c] = pd.to_datetime(orders_df[c]).dt.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                pass
    return orders_df


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run SMA crossover strategy from config")
    p.add_argument("--config", default="configs/strategy.json", help="Path to JSON config")
    p.add_argument("--out", default="outputs/orders.xlsx", help="Path to output Excel file")
    return p.parse_args()


def run(config_path: str | Path, out_path: str | Path) -> Path:
    cfg = load_config(config_path)
    df = load_data(cfg["data_file"])  # timezone not used for daily bars
    fast = int(cfg["strategy"]["fast"]) 
    slow = int(cfg["strategy"]["slow"]) 
    qty = int(cfg["execution"]["qty"]) 
    tzname = cfg.get("timezone", "Asia/Kolkata")

    df_sig = compute_sma_signals(df, fast=fast, slow=slow)
    orders = generate_orders(df_sig, qty=qty, tzname=tzname)

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as xw:
        # write only required columns to the 'orders' sheet
        orders.to_excel(xw, index=False, sheet_name="orders")
    return out_path


if __name__ == "__main__":
    args = parse_args()
    out = run(args.config, args.out)
    print("Wrote", out)
