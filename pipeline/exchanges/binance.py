"""Binance via its public bulk archive (data.binance.vision): every spot pair since 2017,
including delisted ones. The API itself is geo-blocked from the US; the archive is not."""
import csv
import io
import re
import zipfile
from datetime import datetime, timezone

from pipeline.http import RateLimiter, get
from pipeline.store import write

NAME, WORKERS = "binance", 24
S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
DL = "https://data.binance.vision/"
QUOTES = ["FDUSD", "USDT", "USDC", "BUSD", "TUSD", "USDP", "BTC"]  # longest-match order
lim = RateLimiter(40)


def s3_keys(prefix, delimiter=None):
    out, marker = [], ""
    while True:
        params = {"prefix": prefix, "marker": marker}
        if delimiter:
            params["delimiter"] = delimiter
        x = get(S3, lim, params, raw=True).decode()
        tag = "Prefix" if delimiter else "Key"
        found = re.findall(rf"<{tag}>([^<]+)</{tag}>", x)
        out += [k for k in found if k != prefix]
        if "<IsTruncated>true" not in x:
            return out
        marker = re.search(r"<NextMarker>([^<]+)", x).group(1) if delimiter else found[-1]


def pairs():
    out = []
    for p in s3_keys("data/spot/monthly/klines/", "/"):
        sym = p.rstrip("/").split("/")[-1]
        for q in QUOTES:
            if sym.endswith(q) and len(sym) > len(q):
                out.append((sym[: -len(q)], q, sym))
                break
    return out


def zip_rows(key):
    blob = get(DL + key, lim, raw=True)
    if not blob:
        return []
    rows = []
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for name in z.namelist():
            for r in csv.reader(io.TextIOWrapper(z.open(name))):
                if r and r[0].isdigit():
                    rows.append((r[0], r[1], r[2], r[3], r[4], r[5], r[7]))
    return rows


def fetch(base, quote, sym):
    keys = [k for k in s3_keys(f"data/spot/monthly/klines/{sym}/1d/") if k.endswith(".zip")]
    if not keys:
        return 0
    last = keys[-1][-11:-4]  # YYYY-MM
    cur = datetime.now(timezone.utc)
    prev = f"{cur.year}-{cur.month - 1:02d}" if cur.month > 1 else f"{cur.year - 1}-12"
    if last == prev:  # still trading: add this month's daily files
        keys += [k for k in s3_keys(f"data/spot/daily/klines/{sym}/1d/{sym}-1d-{cur:%Y-%m}-") if k.endswith(".zip")]
    rows = []
    for k in keys:
        rows += zip_rows(k)
    return write(NAME, base, quote, rows)
