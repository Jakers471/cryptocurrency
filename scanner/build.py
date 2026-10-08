"""Precompute everything the UI shows (it only displays; it never analyses).

Usage (from the project root):
    python3 -m scanner.build              # ranked coins >= core.universe.MIN_MCAP + their zone charts
    python3 -m scanner.build --all        # every coin with merged data
    python3 -m scanner.build --no-charts  # table data only (about a minute)
    python3 -m scanner.build HBAR XRP     # just these (for testing)
    --workers N                           # parallel processes (default core.universe.WORKERS)

Writes ui/data/scan.js            window.SCAN = {generated, rows: [...]}   (table)
       ui/data/coins/<COIN>.js    window.DETAIL["COIN"] = {...}           (viewer, loaded on click)
       png/zones/...              zone charts (charts.zones), linked from each row
Plain .js files (not .json) so ui/index.html works straight from disk with no server.
"""
import json
import os
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from analysis import analyze
from charts import zones as zone_charts
from core import paths, universe
from scanner.rows import detail, row

DETAIL_DIR = os.path.join(paths.UI_DATA, "coins")


def _plain(v):
    """numpy scalars -> plain Python for JSON."""
    if isinstance(v, np.generic):
        return v.item()
    raise TypeError(f"not JSON serializable: {type(v)}")


def _js(var, key, obj):
    body = json.dumps(obj, separators=(",", ":"), allow_nan=False, default=_plain)
    return f"{var}={body};\n" if key is None else f'{var}["{key}"]={body};\n'


def process(job):
    coin, info, charts = job
    try:
        results = {q: analyze(coin, q) for q in ("USD", "BTC")}
        if not results["USD"]:
            return None
        png = universe.chart_path(paths.PNG_ZONES, coin, info.get("rank"))
        if charts:
            zone_charts.render(coin, info, png, results)
        with open(os.path.join(DETAIL_DIR, f"{coin}.js"), "w") as f:
            f.write("window.DETAIL=window.DETAIL||{};" + _js("window.DETAIL", coin, detail(coin, results)))
        return row(coin, info, results, os.path.relpath(png, paths.UI))
    except Exception as e:
        print(f"FAIL {coin}: {e}", flush=True)
        return None


def main():
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else universe.WORKERS
    args = [a.upper() for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]
    charts = "--no-charts" not in sys.argv
    ranks = universe.ranking()
    coins = args or (universe.all_coins() if "--all" in sys.argv else universe.ranked_coins())
    os.makedirs(DETAIL_DIR, exist_ok=True)
    if not args and charts:  # full rebuild: clear charts whose rank (file name) has changed
        shutil.rmtree(paths.PNG_ZONES, ignore_errors=True)
    t0 = time.time()
    rows = []
    print(f"building {len(coins)} coins with {workers} workers", flush=True)
    existing = _read_existing() if args else []  # partial run: merge into the existing table
    with ProcessPoolExecutor(workers) as ex:
        for i, r in enumerate(ex.map(process, [(c, ranks.get(c, {}), charts) for c in coins], chunksize=1), 1):
            if r:
                rows.append(r)
            if i % 25 == 0:  # save as we go: refreshing the UI shows the coins done so far
                _write_table(rows, existing)
                print(f"{i}/{len(coins)}  ({time.time() - t0:.0f}s)", flush=True)
    n = _write_table(rows, existing)
    print(f"{n} coins → ui/data/scan.js in {time.time() - t0:.0f}s")


def _write_table(rows, existing=()):
    keep = {r["coin"] for r in rows}
    allrows = sorted([r for r in existing if r["coin"] not in keep] + rows,
                     key=lambda r: (r["rank"] is None, r["rank"] or 0, r["coin"]))
    tmp = os.path.join(paths.UI_DATA, "scan.js.tmp")
    with open(tmp, "w") as f:
        f.write(_js("window.SCAN", None, {"generated": time.strftime("%Y-%m-%d %H:%M"), "rows": allrows}))
    os.replace(tmp, os.path.join(paths.UI_DATA, "scan.js"))  # atomic: the UI never reads a half-written file
    return len(allrows)


def _read_existing():
    f = os.path.join(paths.UI_DATA, "scan.js")
    if not os.path.exists(f):
        return []
    text = open(f).read()
    return json.loads(text[text.index("=") + 1:].rstrip().rstrip(";"))["rows"]


if __name__ == "__main__":
    main()
