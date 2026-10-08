"""Turn one coin's analysis into flat, display-ready records for the UI.

row(...)    -> one table row: coin info + a compact summary per pair (usd / btc)
detail(...) -> everything the viewer panel shows for that coin (all unbroken zones + mains)
"""
import math

from analysis.score import coin_score
from analysis.zones import Zone


def _num(v, nd=6):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    return round(float(v), nd) if isinstance(v, float) else v


def _date(ts):
    return None if ts is None else ts.strftime("%Y-%m-%d")


def _zone(z: Zone):
    return {"tf": z.tf, "formed": _date(z.formed), "bottom": _num(z.bottom, 10), "top": _num(z.top, 10),
            "move": _num(z.move_pct, 1), "move_atr": _num(z.move_atr, 1), "bos": z.bos, "taps": z.taps,
            "status": z.status, "dist": _num(z.dist_pct, 2), "drop": _num(z.drop_to_zone_pct, 2),
            "conf": bool(z.confluence), "main": z.main, "main_active": z.main_active, "age": z.age_days,
            "last_tap": _date(z.last_tap), "deepest": _num(z.deepest_pct, 0), "wick": z.wick_zone,
            "broken": _date(z.broken)}


def _brief(z: Zone):
    """The few zone fields the table needs (keeps ui/data/scan.js small)."""
    return {"tf": z.tf, "bottom": _num(z.bottom, 10), "top": _num(z.top, 10), "drop": _num(z.drop_to_zone_pct, 2),
            "dist": _num(z.dist_pct, 2), "taps": z.taps, "status": z.status, "conf": bool(z.confluence),
            "formed": _date(z.formed), "move": _num(z.move_pct, 0), "tap_days": z.days_since_tap}


def _absorbing(zones, last, now):
    """A zone broken recently that price sits just below ("absorbing demand"), or None."""
    from analysis.config import ABSORB_DAYS, ABSORB_RANGE
    recent = [z for z in zones if z.status == "broken" and (now - z.broken).days <= ABSORB_DAYS
              and z.bottom * (1 - ABSORB_RANGE) <= last < z.bottom]
    return max(recent, key=lambda z: z.move_pct) if recent else None


def _nearest(zones):
    """Closest unbroken zone at or below the price (smallest drop), or None."""
    alive = [z for z in zones if z.status != "broken" and z.dist_pct >= 0]
    return min(alive, key=lambda z: z.dist_pct) if alive else None


def _st(t):
    """SuperTrend direction and how many bars since it last flipped."""
    d = t.direction.values
    flips = (d[1:] != d[:-1]).nonzero()[0]
    since = len(d) - 1 - (flips[-1] + 1) if len(flips) else len(d) - 1
    return int(d[-1]), int(since)


def pair_summary(res):
    """Compact per-pair fields for the table (res = analyze(coin, quote))."""
    if not res:
        return None
    s = res["ath"]
    out = {"price": _num(s["last"], 10), "ath": _num(s["ath"], 10), "ath_date": _date(s["ath_date"]),
           "ath_days": s["days_since_ath"], "ath_launch": bool(s["ath_launch_week"]),
           "dd_now": _num(s["current_drawdown_pct"], 2), "dd_score": _num(s["drawdown_ex_launch_pct"], 2), "dd_max": _num(s["max_drawdown_pct"], 2),
           "bounce": _num(s["bounce_from_low_pct"], 1),
           "first": _date(s["first_date"]), "years": round((s["last_date"] - s["first_date"]).days / 365, 1)}
    for tf in ("W", "D"):
        t = res[tf]
        k = tf.lower()
        out[f"st_{k}"], out[f"st_{k}_bars"] = _st(t) if t.direction is not None else (None, None)
        near = _nearest(t.zones)
        out[f"near_{k}"] = _brief(near) if near else None
        out[f"alive_{k}"] = sum(z.status != "broken" for z in t.zones)
    main = next((z for z in res["W"].zones if z.main), None)
    out["main_w"] = _brief(main) if main else None
    ab = _absorbing(res["W"].zones + res["D"].zones, s["last"], s["last_date"])
    out["absorb"] = _brief(ab) if ab else None
    return out


def row(coin, info, results, chart):
    usd, btc = pair_summary(results.get("USD")), pair_summary(results.get("BTC"))
    return {"coin": coin, "name": info.get("name", ""), "rank": info.get("rank"), "mcap": info.get("mcap"),
            "stable": is_stable(results), "chart": chart, "usd": usd, "btc": btc, "score": coin_score(usd, btc)}


def detail(coin, results):
    out = {}
    for q, res in results.items():
        if not res:
            continue
        keep = [z for tf in ("W", "D") for z in res[tf].zones if z.status != "broken" or z.main or z.main_active]
        out[q.lower()] = {"zones": [_zone(z) for z in keep],
                          "ath": {k: (_date(v) if hasattr(v, "strftime") else _num(v, 10))
                                  for k, v in res["ath"].items()}}
    return out


def is_stable(results):
    """Stablecoins (USD ~1) and BTC-pegged tokens (BTC pair ~1) over the last year."""
    for q in ("USD", "BTC"):
        r = results.get(q)
        if not r:
            continue
        c = r["D"].candles["close"].iloc[-365:]
        if 0.9 < c.median() < 1.1 and (c.max() / c.min()) < 1.15:
            return True
    return False
