"""Buy-setup scoring on the precomputed pair summaries (scanner.rows.pair_summary).

Higher timeframe has more say: weekly zones outweigh daily ones in the demand part, a lone
daily zone can't make a pair "at demand", and only absorbing a weekly zone counts toward S4.

Framework: alts that explode are usually 85-95% corrected on BOTH ALT/USD and ALT/BTC and sitting
at demand on both. Each pair is scored on its own, then combined, then tagged with a scenario:
  S3  both pairs corrected and at demand          (best)
  S4  both pairs below / absorbing demand
  S1  only one pair corrected and at demand
  S2  both pairs far from demand and not corrected (pumping)
Every threshold and weight lives in analysis/config.py.
"""
from analysis import config as C


def curve(points, x):
    """Piecewise-linear interpolation through [(x, y), ...]."""
    if x is None:
        return 0.0
    if x <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return points[-1][1]


def _zone_part(z, absorbing=False):
    if not z or (z.get("status") == "broken" and not absorbing):
        return 0.0
    if absorbing:  # price just below a recently broken zone
        return 1.0
    s = curve(C.CURVE_ZONE_DROP, -z["drop"])
    if z.get("tap_days") is not None and z["tap_days"] <= C.PUSH_OFF_DAYS and z["drop"] < 0:
        s = min(1.0, s + C.PUSH_OFF_BONUS)
    return s


def _weight(source, z):
    """Weekly zones outweigh daily ones (different time horizons)."""
    if not z:
        return 0.0
    if source == "near_d" and z.get("conf"):
        return C.ZONE_DAILY_CONFLUENCE
    if source == "absorb":
        return C.ABSORB_WEIGHT.get(z.get("tf"), C.ABSORB_WEIGHT["D"])
    return C.ZONE_SOURCES[source]


def pair_score(p):
    """-> {score, corr, zone, time, impulse, corrected, at_demand, absorbing, pumping} or None."""
    if not p:
        return None
    # correction is measured from the first real high when the ATH was a listing-week spike
    dd = p.get("dd_score", p.get("dd_now"))
    below_ath = -dd if dd is not None else 0
    # the zone that best supports "at demand": main weekly, nearest weekly/daily, or one being absorbed
    options = [(_zone_part(p.get(k), absorbing=(k == "absorb")) * _weight(k, p.get(k)), k) for k in C.ZONE_SOURCES]
    zone_part, zone_src = max(options)
    z = p.get(zone_src) if zone_part > 0 else None
    parts = {
        "corr": curve(C.CURVE_CORRECTION, below_ath),
        "zone": zone_part,
        "time": curve(C.CURVE_ATH_DAYS, p.get("ath_days")),
        "impulse": curve(C.CURVE_IMPULSE, (p.get("main_w") or {}).get("move")),
    }
    score = 100 * sum(C.SCORE_WEIGHTS[k] * v for k, v in parts.items())
    return {"score": round(score, 1), **{k: round(v, 2) for k, v in parts.items()},
            "zone_src": zone_src if z else None, "zone_drop": z["drop"] if z and zone_src != "absorb" else None,
            "zone_below": round((p["price"] / z["bottom"] - 1) * 100, 1) if z and zone_src == "absorb" else None,
            "corrected": below_ath >= C.CORRECTED, "at_demand": parts["zone"] >= C.AT_DEMAND,
            # higher timeframe has more say: only absorbing a WEEKLY zone defines the scenario
            "absorbing": (p.get("absorb") or {}).get("tf") == "W",
            "pumping": parts["zone"] < 0.3 and below_ath < 60}


def coin_score(usd, btc):
    """Combine the two pair scores -> {score, scenario, usd, btc}."""
    u, b = pair_score(usd), pair_score(btc)
    if not u:
        return None
    if not b:
        return {"score": round(u["score"] * C.NO_BTC_FACTOR, 1), "scenario": "USD only", "usd": u, "btc": None}
    good = lambda s: s["corrected"] and s["at_demand"]
    score = (u["score"] + b["score"]) / 2 + (C.BOTH_BONUS if good(u) and good(b) else 0)
    if good(u) and good(b):
        scenario = "S3"
    elif (u["absorbing"] or b["absorbing"]) and all(s["absorbing"] or s["at_demand"] for s in (u, b)):
        scenario = "S4"
    elif good(u) or good(b):
        scenario = "S1"
    elif u["pumping"] and b["pumping"]:
        scenario = "S2"
    else:
        scenario = "–"
    return {"score": round(min(100.0, score), 1), "scenario": scenario, "usd": u, "btc": b}
