"""Per-pair analysis: SuperTrend swings, demand zones (weekly + daily) and ATH stats.

    from analysis import analyze
    res = analyze("HBAR", "BTC")
    res["W"].zones, res["D"].supertrend, res["ath"]["max_drawdown_pct"]
"""
from dataclasses import dataclass

import pandas as pd

from analysis.series import load, weekly
from analysis.stats import ath_stats
from analysis.zones import find_zones, mark_confluence


@dataclass
class Timeframe:
    candles: pd.DataFrame
    zones: list
    supertrend: pd.Series
    direction: pd.Series
    swings: list


def analyze(coin, quote="USD"):
    """-> {'W': Timeframe, 'D': Timeframe, 'ath': {...}} or None if there's too little data."""
    daily = load(coin, quote)
    if daily is None or len(daily) < 30:
        return None
    out = {}
    for tf, df in (("W", weekly(daily)), ("D", daily)):
        zones, st, sd, sw = find_zones(df, tf)
        out[tf] = Timeframe(df, zones, st, sd, sw)
    mark_confluence(out["W"].zones, out["D"].zones)
    out["ath"] = ath_stats(daily)
    return out
