"""Current market-cap ranking (CoinPaprika, free) and the data/by_market_cap/ folder."""
import os
import shutil

import requests

from core import paths


def tickers():
    """CoinPaprika's ranked coins (free, top ~2,000), highest market cap first."""
    t = requests.get("https://api.coinpaprika.com/v1/tickers", headers={"User-Agent": "Mozilla/5.0"},
                     timeout=60).json()
    return sorted((x for x in t if x["rank"] > 0), key=lambda x: x["rank"])


def symbols_above(min_mcap, ticks=None):
    """Tickers of coins with market cap >= min_mcap."""
    return {t["symbol"].upper() for t in (ticks or tickers()) if (t["quotes"]["USD"]["market_cap"] or 0) >= min_mcap}


def add_market_cap(summary, ticks=None):
    """Attach rank / market cap / name. A ticker only matches if CoinPaprika's price is within
    50% of our last close (so a different token sharing the ticker isn't matched)."""
    best = {}
    for t in ticks or tickers():
        best.setdefault(t["symbol"].upper(), []).append(t)
    ranks, caps, names = [], [], []
    for coin, close in zip(summary.coin, summary.last_close):
        match = next((t for t in best.get(coin, [])
                      if close and abs(t["quotes"]["USD"]["price"] / close - 1) < 0.5), None)
        ranks.append(match["rank"] if match else None)
        caps.append(match["quotes"]["USD"]["market_cap"] if match else None)
        names.append(match["name"] if match else "")
    s = summary.assign(market_cap_rank=ranks, market_cap_usd=caps, name=names)
    s = s.sort_values(["market_cap_rank", "last_30d_volume_usd"], ascending=[True, False], na_position="last")
    cols = ["market_cap_rank", "coin", "name", "market_cap_usd"]
    return s[cols + [c for c in s.columns if c not in cols]]


def write_by_market_cap(s):
    """data/by_market_cap/{usd,btc}/0001_BTC.csv ... highest to lowest market cap, + ranking.csv."""
    shutil.rmtree(paths.BY_MCAP, ignore_errors=True)
    ranked = s[s.market_cap_rank.notna()].reset_index(drop=True)
    for sub, src in (("usd", paths.COINS), ("btc", paths.COINS_BTC)):
        os.makedirs(os.path.join(paths.BY_MCAP, sub))
        for rank, coin in zip(ranked.market_cap_rank.astype(int), ranked.coin):
            f = os.path.join(src, f"{coin}.csv")
            if os.path.exists(f):
                shutil.copy(f, os.path.join(paths.BY_MCAP, sub, f"{rank:04d}_{coin}.csv"))
    ranked.to_csv(paths.RANKING, index=False, float_format="%.6g")
