"""Loading merged price series and resampling."""
import os

import pandas as pd

from core import paths


def load(coin, quote="USD"):
    """Daily OHLC for COIN/USD or COIN/BTC, or None."""
    f = paths.series_path(coin, quote)
    if not os.path.exists(f):
        return None
    df = pd.read_csv(f, parse_dates=["date"], index_col="date")
    return df[["open", "high", "low", "close"]].dropna()


def weekly(df):
    """Weeks starting Monday, labelled by their Monday."""
    w = df.resample("W-MON", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"})
    return w.dropna()
