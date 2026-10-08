"""Plain daily candle charts: USD on top, BTC below.

Usage (from the project root):
    python3 -m charts.price              # every ranked coin
    python3 -m charts.price HBAR XRP     # specific coins
    python3 -m charts.price --linear     # linear instead of log price scale
Writes png/price/<rank band>/<rank>_<COIN>.png
"""
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor

import matplotlib.pyplot as plt
import pandas as pd

from charts.candles import date_axis, draw_candles
from charts.style import INK, INK2, SURFACE, fmt_mcap, fmt_price, style_axes
from core import paths, universe

WIDTH_IN, DPI = 16, 110


def _load(coin, quote):
    f = paths.series_path(coin, quote)
    return pd.read_csv(f, parse_dates=["date"], index_col="date") if os.path.exists(f) else None


def render(job):
    coin, info, out, log = job
    usd, btc = _load(coin, "USD"), _load(coin, "BTC")
    if usd is None or usd.empty:
        return None
    panels = [(usd, "USD")] + ([(btc, "BTC")] if btc is not None and len(btc) else [])
    height = 5 * len(panels) + 1
    fig, axes = plt.subplots(len(panels), 1, figsize=(WIDTH_IN, height), sharex=True, facecolor=SURFACE,
                             squeeze=False)
    for ax, (df, q) in zip(axes[:, 0], panels):
        draw_candles(ax, df, WIDTH_IN)
        style_axes(ax, q, log)
        ax.set_title(f"{coin} / {q}   last close {fmt_price(df['close'].iloc[-1], q)}", loc="left",
                     color=INK, fontsize=12, fontweight="bold")
    rank, name, mcap = info.get("rank"), info.get("name"), info.get("mcap")
    fig.suptitle(f"{f'#{rank} ' if rank else ''}{coin}{f' ({name})' if name else ''}"
                 f"{f' · mcap {fmt_mcap(mcap)}' if mcap else ''} · daily OHLC · "
                 f"{usd.index[0]:%Y-%m-%d} → {usd.index[-1]:%Y-%m-%d} · {len(usd):,} days{' · log scale' if log else ''}",
                 x=0.01, y=1 - 0.2 / height, va="top", ha="left", color=INK, fontsize=15, fontweight="bold")
    sub = "USD sources: " + ", ".join(usd["source"].value_counts().index[:4])
    if len(panels) == 2:
        native = (btc["source"] != "synthetic").mean()
        sub += f"   ·   BTC: {native:.0%} native {coin}/BTC pair" + (", rest USD ÷ BTC" if native < 1 else "")
    fig.text(0.01, 1 - 0.58 / height, sub, va="top", color=INK2, fontsize=9)
    date_axis(axes[-1, 0], usd.index[0], usd.index[-1])
    fig.tight_layout(rect=(0, 0, 1, 1 - 0.8 / height))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=DPI)
    plt.close(fig)
    return out


def main():
    args = [a.upper() for a in sys.argv[1:] if not a.startswith("--")]
    log = "--linear" not in sys.argv
    ranks = universe.ranking()
    coins = args or sorted(ranks, key=lambda c: ranks[c]["rank"])
    jobs = [(c, ranks.get(c, {}), universe.chart_path(paths.PNG_PRICE, c, ranks.get(c, {}).get("rank")), log)
            for c in coins]
    if not args:  # full rebuild: clear stale files (ranks shift between runs)
        shutil.rmtree(paths.PNG_PRICE, ignore_errors=True)
    done = 0
    with ProcessPoolExecutor() as ex:
        for out in ex.map(render, jobs, chunksize=4):
            done += out is not None
            if args and out:
                print(os.path.relpath(out, paths.ROOT))
    print(f"{done} charts in {os.path.relpath(paths.PNG_PRICE, paths.ROOT)}/")


if __name__ == "__main__":
    main()
