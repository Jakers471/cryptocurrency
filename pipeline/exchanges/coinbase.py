"""Coinbase Exchange: USD pairs back to 2015, 300 candles per request."""
from datetime import datetime, timezone

from pipeline.http import RateLimiter, get
from pipeline.store import DAY, TODAY, write

NAME, WORKERS = "coinbase", 4
QUOTES = {"USD", "USDT", "USDC", "BTC"}
lim = RateLimiter(8)


def pairs():
    ps = get("https://api.exchange.coinbase.com/products", lim)
    return [(p["base_currency"], p["quote_currency"], p["id"]) for p in ps if p["quote_currency"] in QUOTES]


def _iso(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


def fetch(base, quote, pid):
    rows, end = [], TODAY
    while True:
        start = end - 300 * DAY
        data = get(f"https://api.exchange.coinbase.com/products/{pid}/candles", lim,
                   {"granularity": DAY, "start": _iso(start), "end": _iso(end)})
        if not data or not isinstance(data, list):
            break
        rows += [(t, o, h, l, c, v, "") for t, l, h, o, c, v in data]
        end = start
    return write(NAME, base, quote, rows)
