"""OKX: history from 2018, but only 100 candles per request (slowest source)."""
from pipeline.http import RateLimiter, get
from pipeline.store import write

NAME, WORKERS = "okx", 4
lim = RateLimiter(8)


def pairs():
    ps = get("https://www.okx.com/api/v5/public/instruments", lim, {"instType": "SPOT"})["data"]
    return [(p["baseCcy"], p["quoteCcy"], p["instId"]) for p in ps if p["quoteCcy"] in ("USDT", "USDC", "USD", "BTC")]


def fetch(base, quote, inst):
    rows, after = [], None
    while True:
        params = {"instId": inst, "bar": "1Dutc", "limit": 100}
        if after:
            params["after"] = after
        data = get("https://www.okx.com/api/v5/market/history-candles", lim, params).get("data")
        if not data:
            break
        rows += [(r[0], r[1], r[2], r[3], r[4], r[5], r[7]) for r in data]
        after = data[-1][0]
    return write(NAME, base, quote, rows)
