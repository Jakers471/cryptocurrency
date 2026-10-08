"""Merge raw per-exchange candles into one USD and one BTC daily series per coin.

Usage (from the project root):
    python3 -m pipeline.merge              # coins >= core.universe.MIN_MCAP + summary + market-cap folder
    python3 -m pipeline.merge --all        # every coin we have data for
    python3 -m pipeline.merge XRP HBAR     # just these coins (fast, for testing)
    --workers N                            # parallel processes (default core.universe.WORKERS)

Writes data/coins/<COIN>.csv, data/coins_btc/<COIN>.csv, data/coins_summary.csv,
       data/by_market_cap/ (see pipeline.ranking)
"""
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import pandas as pd

from core import paths, universe
from pipeline.combine import merge_btc, merge_usd
from pipeline.ranking import add_market_cap, symbols_above, tickers, write_by_market_cap
from pipeline.sources import index, read

CSV = dict(date_format="%Y-%m-%d", float_format="%.10g")


def summary_row(coin, m, dropped, exchanges):
    return {
        "coin": coin,
        "first_date": m.index.min(),
        "last_date": m.index.max(),
        "days": len(m),
        "last_close": m["close"].iloc[-1],
        "last_30d_volume_usd": m["volume_usd"].iloc[-30:].mean(),
        "exchanges": " ".join(exchanges),
        "dropped_sources": " ".join(dropped),
    }


def write_coin(coin, sources, btc):
    """sources: [(rank, exchange, quote, path)]; reads, merges and writes one coin's two pairs.
    COIN/USD and COIN/BTC are built independently (see pipeline.combine)."""
    sources = read(sources)
    if not sources:
        return None
    usd, dropped = merge_usd(sources)
    if usd is None or usd.empty:
        return None
    usd.to_csv(os.path.join(paths.COINS, f"{coin}.csv"), **CSV)
    pair_btc = merge_btc(sources, btc["close"])
    btc_file = os.path.join(paths.COINS_BTC, f"{coin}.csv")
    if pair_btc is not None and len(pair_btc):
        pair_btc.to_csv(btc_file, **CSV)
    elif os.path.exists(btc_file):  # no real BTC market: no BTC pair (drop any old derived file)
        os.remove(btc_file)
    return summary_row(coin, usd, dropped, sorted({s[1] for s in sources}))


def _job(args):
    coin, sources, btc = args
    try:
        return write_coin(coin, sources, btc)
    except Exception as e:
        print(f"FAIL {coin}: {e}", flush=True)
        return None


def _arg(flag, default):
    return type(default)(sys.argv[sys.argv.index(flag) + 1]) if flag in sys.argv else default


def main():
    workers = _arg("--workers", universe.WORKERS)
    only = [a.upper() for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]
    ticks = None if only else tickers()
    if only:
        wanted = {"BTC", *only}
    elif "--all" in sys.argv:
        wanted = None
    else:
        wanted = {"BTC"} | symbols_above(universe.MIN_MCAP, ticks)
    coins = index(wanted)
    os.makedirs(paths.COINS, exist_ok=True)
    os.makedirs(paths.COINS_BTC, exist_ok=True)

    # BTC first: it's needed to convert BTC-quoted pairs
    btc_sources = read(coins.pop("BTC"))
    btc, btc_dropped = merge_usd(btc_sources)
    btc.to_csv(os.path.join(paths.COINS, "BTC.csv"), **CSV)
    summary = [summary_row("BTC", btc, btc_dropped, sorted({s[1] for s in btc_sources}))]

    jobs = [(coin, entries, btc) for coin, entries in sorted(coins.items())]
    print(f"merging {len(jobs) + 1} coins with {workers} workers", flush=True)
    with ProcessPoolExecutor(workers) as ex:
        for i, row in enumerate(ex.map(_job, jobs, chunksize=4), 1):
            if row:
                summary.append(row)
                if only:
                    print(f"{row['coin']}: {row['first_date']:%Y-%m-%d} -> {row['last_date']:%Y-%m-%d}, {row['days']} days")
            if not only and i % 100 == 0:
                print(f"{i}/{len(jobs)}", flush=True)
    if only:  # quick re-merge: leave summary / market-cap folder alone
        return

    s = add_market_cap(pd.DataFrame(summary), ticks)
    s.to_csv(paths.SUMMARY, index=False, float_format="%.6g")
    write_by_market_cap(s)
    print(f"{len(s)} coins written to {paths.COINS}")
    print(f"  ranked by market cap: {s.market_cap_rank.notna().sum()}")
    print(f"  with >= 1 year of history: {(s.days >= 365).sum()}")
    print(f"  still trading (data in last 7 days): {(s.last_date >= s.last_date.max() - pd.Timedelta(days=7)).sum()}")


if __name__ == "__main__":
    main()
