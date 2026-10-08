"""Demand zones: where they are, how they formed, and what price has done since.

  - leg  = swing low -> next swing high, must be >= min_leg_atr x ATR (impulsive)
  - base = the small-bodied candles at the low, before the first strong bullish (departure) candle
  - zone = lowest wick of the base (bottom) -> highest body of the base (top)
  - outlier-tall zones (> TALL_ZONE_MULT x this series' median zone height) keep only their bottom 15%
  - tap  = any wick back into the zone; consecutive bars = one tap
  - broken = a close below the zone bottom
  - main = origin of the biggest move; main_active = biggest move whose zone is unbroken
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from analysis.config import (BASE_BODY_PCT, BASE_RANGE_ATR, DEPART_BODY_PCT, DEPART_RANGE_ATR, LEAVE_ATR, PARAMS,
                             TALL_ZONE_KEEP, TALL_ZONE_MULT)
from analysis.indicators import atr, supertrend, swings


@dataclass
class Zone:
    tf: str
    formed: pd.Timestamp        # swing-low candle
    departed: pd.Timestamp      # departure candle
    bottom: float
    top: float
    base_bars: int
    leg_high: float
    leg_high_date: pd.Timestamp
    leg_confirmed: bool         # False = leg still running (no SuperTrend flip down yet)
    move_pct: float             # swing low -> leg high
    move_atr: float
    bars_to_high: int
    bos: bool                   # leg broke the previous swing high (break of structure)
    wick_zone: bool = False     # outlier-tall zone, trimmed to its bottom 15%
    taps: int = 0
    first_tap: pd.Timestamp = None
    last_tap: pd.Timestamp = None
    deepest_pct: float = 0.0    # deepest wick into zone, 0 = touched top, 100 = touched bottom
    status: str = "fresh"       # fresh | tested | broken
    broken: pd.Timestamp = None
    dist_pct: float = 0.0       # current close vs zone: + above top, 0 inside, - below bottom
    drop_to_zone_pct: float = 0.0  # move needed from current close to reach the zone top (negative)
    dist_atr: float = 0.0
    age_days: int = 0
    days_since_tap: int = None
    main: bool = False
    main_active: bool = False
    confluence: bool = False    # overlaps an unbroken zone on the other timeframe


def _departure(i, j, o, c, rng, body, a, price, p):
    """First strong bullish candle at/after the low, else the first close clearly away from it."""
    for t in range(i, min(i + p["depart_within"] + 1, j + 1)):
        if c[t] > o[t] and rng[t] >= DEPART_RANGE_ATR * a[t] and body[t] >= DEPART_BODY_PCT * rng[t]:
            return t
    return next((t for t in range(i, j + 1) if c[t] >= price + LEAVE_ATR * a[i]), None)


def _base(i, dep, o, c, rng, body, a, p):
    """-> (base candle indexes, zone top)."""
    if dep == i:  # V-bottom: the departure candle itself; zone = its wick below the body
        return [i], min(o[i], c[i])
    base = list(range(i, dep))
    b = i - 1
    while b >= 0 and len(base) < p["max_base"] and (body[b] <= BASE_BODY_PCT * rng[b] or rng[b] <= BASE_RANGE_ATR * a[b]):
        base.insert(0, b)
        b -= 1
    return base, max(max(o[t], c[t]) for t in base)


def find_zones(df, tf):
    """-> (zones, supertrend line, supertrend direction, swings)."""
    p = PARAMS[tf]
    if len(df) < p["atr_len"] + 5:
        return [], None, None, []
    a = atr(df, p["atr_len"]).values
    st, sd = supertrend(df, p["st_len"], p["st_mult"])
    sw = swings(df, sd)
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    rng, body = h - l, np.abs(c - o)
    found, prev_high = [], None

    for k, (i, kind, price, conf) in enumerate(sw):
        if kind == "H":
            prev_high = price
            continue
        if not conf or k + 1 >= len(sw):
            continue
        j, _, hi, hconf = sw[k + 1]
        if a[i] <= 0 or (hi - price) / a[i] < p["min_leg_atr"]:
            continue
        dep = _departure(i, j, o, c, rng, body, a, price, p)
        if dep is None:
            continue
        base, top = _base(i, dep, o, c, rng, body, a, p)
        bottom = min(l[t] for t in base)
        if top <= bottom:
            top = bottom + 0.25 * a[i]
        z = Zone(tf=tf, formed=df.index[i], departed=df.index[dep], bottom=bottom, top=top, base_bars=len(base),
                 leg_high=hi, leg_high_date=df.index[j], leg_confirmed=hconf,
                 move_pct=(hi / price - 1) * 100, move_atr=(hi - price) / a[i], bars_to_high=j - i,
                 bos=prev_high is not None and hi > prev_high)
        found.append((z, dep))

    _trim_tall(z for z, _ in found)
    for z, dep in found:
        lifecycle(z, df, dep, a)
    zones = [z for z, _ in found]
    if zones:
        max(zones, key=lambda z: z.move_pct).main = True
        alive = [z for z in zones if z.status != "broken"]
        if alive:
            max(alive, key=lambda z: z.move_pct).main_active = True
    return zones, st, sd, sw


def _trim_tall(zones):
    """Outlier-tall zones (vs this series' own zones, in % terms) keep only their bottom 15%."""
    zones = list(zones)
    if not zones:
        return
    heights = np.array([np.log(z.top / z.bottom) for z in zones])
    limit = TALL_ZONE_MULT * np.median(heights)
    for z, hgt in zip(zones, heights):
        if hgt > limit:
            z.top = z.bottom * np.exp(TALL_ZONE_KEEP * hgt)
            z.wick_zone = True


def lifecycle(z, df, dep, a):
    """Taps, breaks, and the zone's position relative to the latest close."""
    l, c = df["low"].values, df["close"].values
    idx = df.index
    in_tap = True  # the base itself is "inside"; a tap needs price to leave first
    height = z.top - z.bottom
    for t in range(dep + 1, len(df)):
        if c[t] < z.bottom:
            z.status, z.broken = "broken", idx[t]
            break
        if l[t] <= z.top:
            if not in_tap:
                z.taps += 1
                z.first_tap = z.first_tap or idx[t]
                in_tap = True
            if z.taps:
                z.last_tap = idx[t]
                z.deepest_pct = max(z.deepest_pct, min(100.0, (z.top - l[t]) / height * 100))
        else:
            in_tap = False
    if z.status != "broken" and z.taps:
        z.status = "tested"
    set_position(z, c[-1], a[-1], idx[-1])


def set_position(z, last, last_atr, now):
    """Spatial / temporal context against the latest close."""
    if last > z.top:
        z.dist_pct = (last / z.top - 1) * 100
        z.drop_to_zone_pct = (z.top / last - 1) * 100
        z.dist_atr = (last - z.top) / last_atr
    elif last < z.bottom:
        z.dist_pct = (last / z.bottom - 1) * 100
        z.drop_to_zone_pct = 0.0
        z.dist_atr = (last - z.bottom) / last_atr
    else:
        z.dist_pct = z.drop_to_zone_pct = z.dist_atr = 0.0
    z.age_days = (now - z.formed).days
    z.days_since_tap = (now - z.last_tap).days if z.last_tap is not None else None


def mark_confluence(weekly_zones, daily_zones):
    """Flag unbroken weekly and daily zones whose price ranges overlap."""
    for w in weekly_zones:
        for d in daily_zones:
            if w.status != "broken" and d.status != "broken" and d.bottom <= w.top and d.top >= w.bottom:
                w.confluence = d.confluence = True
