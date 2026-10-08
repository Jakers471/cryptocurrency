"""Combining one coin's sources into its two INDEPENDENT pairs:

    COIN/USD  <- only USD-quoted markets (USD, USDT, USDC, BUSD, FDUSD, TUSD, USDP)
    COIN/BTC  <- only real COIN/BTC markets

Nothing is converted or derived between the two: a coin with no BTC market has no BTC pair.
"""
import pandas as pd

from pipeline.clean import clean_wicks
from pipeline.sources import STABLE_QUOTES

MIN_VOLUME_SHARE = 0.10    # a source needs >= 10% of the day's top volume to supply that day's candle
MIN_DAY_VOLUME_USD = 1000  # ... and at least this much traded that day (thin early markets are noise)
MAX_DISAGREEMENT = 0.25    # median price gap vs the reference series before a source is dropped


def _merge(series, value_usd):
    """series: [(name, ohlc+volume frame)] in priority order, all in the same quote currency.
    value_usd(frame) -> that frame's daily traded value in USD (used only to judge liquidity).
    -> (merged frame with summed 'volume' in quote units, [dropped names]) or (None, [])."""
    series = [(n, s[s["close"] > 0]) for n, s in series if len(s)]
    if not series:
        return None, []

    # a different token sharing the ticker shows up as a price that doesn't match the rest
    ref_name, ref = max(series, key=lambda s: len(s[1]))
    kept, dropped = [], []
    for name, s in series:
        common = s.index.intersection(ref.index)
        if name != ref_name and len(common) >= 7 and \
                (s.loc[common, "close"] / ref.loc[common, "close"] - 1).abs().median() > MAX_DISAGREEMENT:
            dropped.append(name)
            continue
        kept.append((name, s))

    # per date: the highest-priority source among the liquid ones
    idx = sorted(set().union(*(s.index for _, s in kept)))
    usd = pd.concat([value_usd(s).reindex(idx) for _, s in kept], axis=1).fillna(0)
    liquid = usd.ge(usd.max(axis=1) * MIN_VOLUME_SHARE, axis=0) & usd.ge(MIN_DAY_VOLUME_USD)
    merged = None
    for k, (name, s) in enumerate(kept):
        ok = liquid.iloc[:, k].reindex(s.index).fillna(False).to_numpy(bool)
        s = s[ok][["open", "high", "low", "close"]].assign(source=name)
        merged = s if merged is None else merged.combine_first(s)
    if merged is None or merged.empty:
        return None, dropped
    merged["volume"] = sum((s["volume"] * s["close"]).reindex(merged.index).fillna(0) for _, s in kept)
    merged = merged.sort_index()[["open", "high", "low", "close", "volume", "source"]]
    return clean_wicks(merged, [s for _, s in kept]), dropped


def merge_usd(sources):
    """COIN/USD from USD-quoted markets only -> (frame with volume_usd, [dropped])."""
    series = [(f"{ex}:{q}", df) for _, ex, q, df in sorted(sources, key=lambda s: s[0]) if q in STABLE_QUOTES]
    merged, dropped = _merge(series, lambda s: s["volume"] * s["close"])
    return (merged.rename(columns={"volume": "volume_usd"}) if merged is not None else None), dropped


def merge_btc(sources, btc_close):
    """COIN/BTC from native COIN/BTC markets only -> frame with volume_btc, or None.
    btc_close (BTC/USD) is used only to judge each market's liquidity in dollars, never for prices."""
    series = [(f"{ex}:BTC", df) for _, ex, q, df in sorted(sources, key=lambda s: s[0]) if q == "BTC"]
    merged, _ = _merge(series, lambda s: s["volume"] * s["close"] * btc_close.reindex(s.index))
    return merged.rename(columns={"volume": "volume_btc"}) if merged is not None else None
