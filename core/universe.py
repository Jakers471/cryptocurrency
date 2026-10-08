"""Which coins exist, their market-cap rank, and where their charts live."""
import os

import pandas as pd

from core import paths

MIN_MCAP = 100e6   # coins below this market cap are left out of the merge, scanner and charts
WORKERS = 2        # parallel processes for heavy jobs (keeps an 8 GB / 4-core Mac usable)


def ranking():
    """-> {coin: {"rank", "name", "mcap"}} from data/by_market_cap/ranking.csv (empty if missing)."""
    if not os.path.exists(paths.RANKING):
        return {}
    r = pd.read_csv(paths.RANKING)
    return {row.coin: {"rank": int(row.market_cap_rank),
                       "name": row.name if isinstance(row.name, str) else "",
                       "mcap": float(row.market_cap_usd)}
            for row in r.itertuples()}


def ranked_coins(min_mcap=MIN_MCAP):
    """Ranked coins at or above min_mcap, highest market cap first."""
    r = ranking()
    return [c for c in sorted(r, key=lambda c: r[c]["rank"]) if r[c]["mcap"] >= min_mcap]


def all_coins():
    return sorted(f[:-4] for f in os.listdir(paths.COINS) if f.endswith(".csv"))


def band(rank):
    """Rank folders of 100: 5 -> '0001-0100'."""
    if not rank:
        return "unranked"
    lo = (rank - 1) // 100 * 100 + 1
    return f"{lo:04d}-{lo + 99:04d}"


def chart_path(root, coin, rank):
    """png/<kind>/0001-0100/0005_XRP.png, or png/<kind>/unranked/XRP.png"""
    name = f"{rank:04d}_{coin}.png" if rank else f"{coin}.png"
    return os.path.join(root, band(rank), name)
