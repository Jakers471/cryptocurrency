"""Zone charts: USD | BTC side by side, weekly (full history) on top, daily (3 years) below.
Charts only; the numbers live in the UI (charts.zone_table still renders the text table if needed).

Usage (from the project root):
    python3 -m charts.zones              # every ranked coin, in parallel
    python3 -m charts.zones HBAR XRP     # specific coins
Writes png/zones/<rank band>/<rank>_<COIN>.png
"""
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from analysis import analyze
from charts.style import BROKEN, DOWN, INK, INK2, MAIN, ST_DOWN, ST_UP, SURFACE, UP, ZONE, fmt_mcap
from charts.zone_panel import DAILY_WINDOW_DAYS, draw_panel
from core import paths, universe

LEGEND = [Patch(color=UP, label="up candle"), Patch(color=DOWN, label="down candle"),
          Line2D([], [], color=ST_UP, lw=1.5, label="SuperTrend up (10, 3×ATR)"),
          Line2D([], [], color=ST_DOWN, lw=1.5, label="SuperTrend down"),
          Patch(color=MAIN, alpha=0.4, label="main zone"), Patch(color=ZONE, alpha=0.35, label="unbroken zone"),
          Patch(color=BROKEN, alpha=0.3, label="broken zone (close below)"),
          Line2D([], [], marker="^", color=INK2, ls="none", label="swing low / high"),
          Line2D([], [], marker="*", color=ST_DOWN, markeredgecolor=INK, ls="none", markersize=10, label="ATH"),
          Line2D([], [], marker="o", color=ST_DOWN, markeredgecolor=INK, ls="none", label="low since ATH")]


def render(coin, info, out, results=None):
    """results: optional {'USD': analyze(...), 'BTC': ...} to avoid recomputing."""
    res = results or {q: analyze(coin, q) for q in ("USD", "BTC")}
    quotes = [q for q in ("USD", "BTC") if res.get(q)]
    if not quotes:
        return None
    # charts only (the UI shows the numbers): USD | BTC across, weekly on top, daily below
    fig = plt.figure(figsize=(12 * len(quotes), 13), facecolor=SURFACE)
    gs = fig.add_gridspec(2, len(quotes), hspace=0.16, wspace=0.12, left=0.045, right=0.95, top=0.9, bottom=0.04)
    for c, q in enumerate(quotes):
        draw_panel(fig.add_subplot(gs[0, c]), res[q], "W", q, coin)
        draw_panel(fig.add_subplot(gs[1, c]), res[q], "D", q, coin)

    d = res[quotes[0]]["D"].candles
    rank, mcap = info.get("rank"), info.get("mcap")
    fig.suptitle(f"{f'#{rank} ' if rank else ''}{coin}{f' · mcap {fmt_mcap(mcap)}' if mcap else ''} · demand zones · "
                 f"data {d.index[0]:%Y-%m-%d} → {d.index[-1]:%Y-%m-%d}",
                 x=0.045, y=0.985, ha="left", fontsize=16, fontweight="bold", color=INK)
    fig.legend(handles=LEGEND, loc="upper left", bbox_to_anchor=(0.04, 0.958), ncol=10, frameon=False, fontsize=9)
    fig.text(0.95, 0.955, f"daily panels show last {DAILY_WINDOW_DAYS // 365} years · labels: % from zone · "
             "taps (wick into zone)", ha="right", fontsize=8.5, color=INK2)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=100)
    plt.close(fig)
    return out


def _job(args):
    coin, info, out = args
    try:
        return render(coin, info, out)
    except Exception as e:  # one bad series shouldn't stop a 1,000-chart batch
        print(f"FAIL {coin}: {e}", flush=True)
        return None


def main():
    args = [a.upper() for a in sys.argv[1:]]
    ranks = universe.ranking()
    coins = args or sorted(ranks, key=lambda c: ranks[c]["rank"])
    jobs = [(c, ranks.get(c, {}), universe.chart_path(paths.PNG_ZONES, c, ranks.get(c, {}).get("rank")))
            for c in coins]
    if not args:
        shutil.rmtree(paths.PNG_ZONES, ignore_errors=True)
    done = 0
    with ProcessPoolExecutor() as ex:
        for out in ex.map(_job, jobs, chunksize=2):
            done += out is not None
            if out and (args or done % 100 == 0):
                print(os.path.relpath(out, paths.ROOT) if args else f"{done}/{len(jobs)}", flush=True)
    print(f"{done} zone charts in {os.path.relpath(paths.PNG_ZONES, paths.ROOT)}/")


if __name__ == "__main__":
    main()
