"""Bitfinex: longest USD history (BTC from 2013). Strict limit: 30 requests/minute."""
from pipeline.http import RateLimiter, get
from pipeline.store import write

NAME, WORKERS = "bitfinex", 1
lim = RateLimiter(0.45)


def pairs():
    ps = get("https://api-pub.bitfinex.com/v2/conf/pub:list:pair:exchange", lim)[0]
    out = []
    for p in ps:
        b, q = p.split(":") if ":" in p else (p[:-3], p[-3:])
        if q in ("USD", "UST", "BTC") and not b.startswith("TEST"):
            out.append((b, "USDT" if q == "UST" else q, p))
    return out


def fetch(base, quote, pair):
    rows, start = [], 0
    while True:
        data = get(f"https://api-pub.bitfinex.com/v2/candles/trade:1D:t{pair}/hist", lim,
                   {"sort": 1, "start": start, "limit": 10000})
        if not data:
            break
        rows += [(m, o, h, l, c, v, "") for m, o, c, h, l, v in data]
        if len(data) < 10000:
            break
        start = data[-1][0] + 1
    return write(NAME, base, quote, rows)
