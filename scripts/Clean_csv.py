# scripts/clean_csv.py
import pandas as pd
import os
from datetime import datetime, timedelta

RAW_PATH = "data/ohlc_tv_raw.csv"
OUT_PATH = "data/ohlc_tv.csv"
CLEAN_OUT = "data/ohlc_clean.csv"

def load_clean_save(raw_path=RAW_PATH, out_path=OUT_PATH, clean_out=CLEAN_OUT):
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw file not found: {raw_path}. Run fetch_yf.py first.")

    df = pd.read_csv(raw_path)
    # ensure date column exists and parse it
    if 'date' not in df.columns:
        # try capital Date
        if 'Date' in df.columns:
            df = df.rename(columns={'Date':'date'})
        else:
            raise ValueError("No 'date' column found in raw CSV")

    df['date'] = pd.to_datetime(df['date'])
    # Sort, drop duplicates, drop all-NaN rows
    df = df.sort_values('date').drop_duplicates(subset=['date'])
    df = df.dropna(subset=['open','high','low','close'])  # volume can be zero or NaN for some tickers
    # Ensure numeric types
    for col in ['open','high','low','close','volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Remove rows where OHLC are all NaN after coercion
    df = df.dropna(subset=['open','high','low','close'])

    # Optional: check time range ~ last 3 months
    last = df['date'].max()
    first = df['date'].min()
    print(f"Data range: {first.date()} -> {last.date()}, rows: {len(df)}")

    # Save final CSVs in required order/format
    final = df[['date','open','high','low','close','volume']].copy()
    # legacy path
    final.to_csv(out_path, index=False, date_format='%Y-%m-%d')
    print(f"Saved cleaned CSV -> {out_path}")
    # required by assignment
    final.to_csv(clean_out, index=False, date_format='%Y-%m-%d')
    print(f"Saved cleaned CSV -> {clean_out}")

if __name__ == "__main__":
    load_clean_save()
