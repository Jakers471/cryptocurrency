"""Poloniex: the 2014-2017 era (ETH from its first week, XRP/LTC/DOGE from 2014)."""
from pipeline.http import RateLimiter, get
from pipeline.store import DAY, TODAY, write

NAME, WORKERS = "poloniex", 4
START = 1388534400  # 2014-01-01
lim = RateLimiter(8)


def pairs():
    ps = get("https://api.poloniex.com/markets", lim)
    return [(p["baseCurrencyName"], p["quoteCurrencyName"], p["symbol"]) for p in ps
            if p["quoteCurrencyName"] in ("USDT", "USDC", "USD", "BTC")]


def fetch(base, quote, sym):
    rows, start = [], START
    while start < TODAY:
        end = start + 500 * DAY
        data = get(f"https://api.poloniex.com/markets/{sym}/candles", lim,
                   {"interval": "DAY_1", "startTime": start * 1000, "endTime": end * 1000, "limit": 500})
        if isinstance(data, list):
            # [low, high, open, close, amount(quote), quantity(base), ..., ts, ...]
            rows += [(r[9], r[2], r[1], r[0], r[3], r[5], r[4]) for r in data if float(r[5]) > 0]
        start = end
    return write(NAME, base, quote, rows)
