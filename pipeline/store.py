"""Writing raw candles: data/raw/<exchange>/<BASE>-<QUOTE>.csv
Columns: date,open,high,low,close,volume,quote_volume  (volume = base units)."""
import csv
import os
import re
import time
from datetime import datetime, timezone

from core import paths

DAY = 86400
TODAY = int(time.time()) // DAY * DAY  # candles at/after this are partial and dropped


def ts(v):
    """Normalize s / ms / us timestamps to seconds."""
    v = int(float(v))
    while v > 10**11:
        v //= 1000
    return v


def safe(s):
    return re.sub(r"[^A-Za-z0-9._]", "_", s.upper())


def path(exchange, base, quote):
    return os.path.join(paths.RAW, exchange, f"{safe(base)}-{safe(quote)}.csv")


def exists(exchange, base, quote):
    return os.path.exists(path(exchange, base, quote))


def write(exchange, base, quote, rows):
    """rows: iterable of (timestamp, o, h, l, c, vol, quote_vol). One row per UTC day, today dropped."""
    clean = {}
    for r in rows:
        t = ts(r[0]) // DAY * DAY
        if t < TODAY:
            clean[t] = r[1:]
    if not clean:
        return 0
    out = path(exchange, base, quote)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    tmp = out + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "open", "high", "low", "close", "volume", "quote_volume"])
        for t in sorted(clean):
            w.writerow([datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d"), *clean[t]])
    os.replace(tmp, out)
    return len(clean)
