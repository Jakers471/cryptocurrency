"""KuCoin: history from 2017, 1,500 candles per request."""
from pipeline.http import RateLimiter, get
from pipeline.store import DAY, TODAY, write

NAME, WORKERS = "kucoin", 4
lim = RateLimiter(8)


def pairs():
    ps = get("https://api.kucoin.com/api/v2/symbols", lim)["data"]
    return [(p["baseCurrency"], p["quoteCurrency"], p["symbol"]) for p in ps
            if p["quoteCurrency"] in ("USDT", "USDC", "BTC")]


def fetch(base, quote, sym):
    rows, end = [], TODAY
    while True:
        start = end - 1500 * DAY
        data = get("https://api.kucoin.com/api/v1/market/candles", lim,
                   {"type": "1day", "symbol": sym, "startAt": start, "endAt": end}).get("data")
        if not data:
            break
        rows += [(t, o, h, l, c, v, qv) for t, o, c, h, l, v, qv in data]
        end = start
    return write(NAME, base, quote, rows)
