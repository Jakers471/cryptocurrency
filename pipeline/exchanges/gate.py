"""Gate.io: the widest coin coverage (~2,000 USDT pairs)."""
from pipeline.http import RateLimiter, get
from pipeline.store import DAY, TODAY, write

NAME, WORKERS = "gate", 8
lim = RateLimiter(15)


def pairs():
    ps = get("https://api.gateio.ws/api/v4/spot/currency_pairs", lim)
    return [(p["base"], p["quote"], p["id"]) for p in ps if p["quote"] in ("USDT", "USDC", "BTC")]


def fetch(base, quote, pid):
    rows, end = [], TODAY
    while True:
        start = end - 999 * DAY
        data = get("https://api.gateio.ws/api/v4/spot/candlesticks", lim,
                   {"currency_pair": pid, "interval": "1d", "from": start, "to": end})
        if not data or not isinstance(data, list):
            break
        rows += [(r[0], r[5], r[3], r[4], r[2], r[6], r[1]) for r in data]
        end = start - 1
    return write(NAME, base, quote, rows)
