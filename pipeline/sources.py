"""Reading raw per-exchange candles and grouping them by coin."""
import glob
import os
import re

import pandas as pd

from core import paths

# Per date, earlier exchanges win (among liquid sources; see combine.py)
PRIORITY = ["binance", "coinbase", "bitfinex", "okx", "kucoin", "gate", "mexc", "poloniex"]
STABLE_QUOTES = ["USD", "USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USDP"]

# Exchange-specific tickers -> common ticker
ALIASES = {
    "bitfinex": {"ALG": "ALGO", "DSH": "DASH", "QTM": "QTUM", "IOT": "IOTA", "UST": "USDT", "UDC": "USDC",
                 "XCH": "XCHF", "DAT": "DATA", "MNA": "MANA", "OMN": "OMNI", "YYW": "YOYOW", "AMP": "AMPL",
                 "ATO": "ATOM", "TSD": "TUSD", "DOG": "MDOGE", "LUNA2": "LUNA", "SNG": "SNGLS",
                 "B21X": "B21", "PAS": "PASS", "WBT": "WBTC"},
    "kucoin": {"XBT": "BTC"},
}
LEVERAGED = re.compile(r"\d+[LS]$")      # BTC3L, ETH5S ...
LEV_WORDS = ("UP", "DOWN", "BULL", "BEAR")  # BTCUP, ETHBULL ... (only if the stripped base exists)


def index(only=None):
    """-> {coin: [(rank, exchange, quote, path)]} from filenames alone (no file reads).
    only = set of coins to include (None = all)."""
    files = glob.glob(os.path.join(paths.RAW, "*", "*.csv"))
    bases = {os.path.basename(f).rsplit("-", 1)[0] for f in files}
    coins = {}
    for f in files:
        ex = os.path.basename(os.path.dirname(f))
        if ex not in PRIORITY:
            continue
        base, quote = os.path.basename(f)[:-4].rsplit("-", 1)
        base = ALIASES.get(ex, {}).get(base, base)
        if only and base not in only:
            continue
        if LEVERAGED.search(base):
            continue
        if any(base.endswith(w) and base[: -len(w)] in bases and len(base) > len(w) + 1 for w in LEV_WORDS):
            continue
        stable = quote in STABLE_QUOTES
        rank = (0 if stable else 100) + PRIORITY.index(ex) * 10 + (STABLE_QUOTES.index(quote) if stable else 0)
        coins.setdefault(base, []).append((rank, ex, quote, f))
    return coins


def read(entries):
    """[(rank, exchange, quote, path)] -> [(rank, exchange, quote, df)], skipping empty files."""
    out = []
    for rank, ex, quote, f in entries:
        df = pd.read_csv(f, parse_dates=["date"], index_col="date")
        if not df.empty:
            out.append((rank, ex, quote, df))
    return out
