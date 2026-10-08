"""Bad-print removal for a merged daily series."""
import numpy as np
import pandas as pd

WICK_EXCESS = 1.25     # a wick > 25% beyond every other exchange's that day is a bad print
WICK_RANGE_MULT = 6    # single-source days: wick > 6x the typical 30-day range is a bad print


def clean_wicks(merged, frames):
    """merged: the combined OHLC series; frames: every source's OHLC for cross-checking.

    1. Bad opens: markets are 24/7, so an open should sit near the previous close (or, on the
       first day, near its own close). Way off = bad print (e.g. Poloniex ETH/BTC opening at 50 BTC).
    2. Multi-source days: a high/low only one exchange printed, more than WICK_EXCESS beyond the
       next most extreme exchange, is replaced by that exchange's value (real crashes show everywhere).
    3. Single-source days: wicks beyond WICK_RANGE_MULT x the rolling median range are trimmed.
    Adds wick_fixed = 1 on any corrected day."""
    m = merged.copy()
    med = ((m["high"] - m["low"]) / m["close"]).rolling(30, min_periods=5).median().bfill()
    cap = 1 + WICK_RANGE_MULT * med

    ref = m["close"].shift().fillna(m["close"])
    ratio = np.exp(np.abs(np.log(m["open"] / ref)))
    bad_o = (ratio > cap) & (ratio > WICK_EXCESS)
    m.loc[bad_o, "open"] = ref[bad_o]

    body_hi = m[["open", "close"]].max(axis=1)
    body_lo = m[["open", "close"]].min(axis=1)
    highs = np.column_stack([f["high"].reindex(m.index).to_numpy(float) for f in frames])
    lows = np.column_stack([f["low"].reindex(m.index).to_numpy(float) for f in frames])
    multi = pd.Series((~np.isnan(highs)).sum(axis=1), m.index) >= 2

    # 2nd most extreme value across exchanges (= the most extreme one that is corroborated)
    h2 = pd.Series(np.sort(np.where(np.isnan(highs), -np.inf, highs), axis=1)[:, -2] if highs.shape[1] > 1
                   else np.nan, m.index).where(multi)
    l2 = pd.Series(np.sort(np.where(np.isnan(lows), np.inf, lows), axis=1)[:, 1] if lows.shape[1] > 1
                   else np.nan, m.index).where(multi)
    bad_h = multi & (m["high"] > h2 * WICK_EXCESS)
    bad_l = multi & (m["low"] < l2 / WICK_EXCESS)
    m.loc[bad_h, "high"] = np.maximum(h2[bad_h], body_hi[bad_h])
    m.loc[bad_l, "low"] = np.minimum(l2[bad_l], body_lo[bad_l])

    single = ~multi
    bad_h1 = single & (m["high"] > body_hi * cap) & (m["high"] > body_hi * WICK_EXCESS)
    bad_l1 = single & (m["low"] < body_lo / cap) & (m["low"] < body_lo / WICK_EXCESS)
    m.loc[bad_h1, "high"] = (body_hi * cap)[bad_h1]
    m.loc[bad_l1, "low"] = (body_lo / cap)[bad_l1]
    m["wick_fixed"] = (bad_o | bad_h | bad_l | bad_h1 | bad_l1).astype(int)
    return m
