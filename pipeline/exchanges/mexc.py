"""MEXC: many small coins, but only the most recent ~500 days are served."""
from pipeline.http import RateLimiter, get
from pipeline.store import write

NAME, WORKERS = "mexc", 4
lim = RateLimiter(8)


def pairs():
    ps = get("https://api.mexc.com/api/v3/exchangeInfo", lim)["symbols"]
    return [(p["baseAsset"], p["quoteAsset"], p["symbol"]) for p in ps if p["quoteAsset"] in ("USDT", "USDC")]


def fetch(base, quote, sym):
    data = get("https://api.mexc.com/api/v3/klines", lim, {"symbol": sym, "interval": "1d", "limit": 1000})
    if not isinstance(data, list):
        return 0
    return write(NAME, base, quote, [(r[0], r[1], r[2], r[3], r[4], r[5], r[7]) for r in data])
