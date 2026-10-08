"""Download full-history daily candles from every exchange module.

Usage (from the project root):
    python3 -m pipeline.fetch                 # all exchanges, in parallel
    python3 -m pipeline.fetch binance gate    # specific exchanges
    python3 -m pipeline.fetch okx --limit 5   # test on a few pairs

Re-running skips pairs that already have a file (delete a file to refetch it).
"""
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from pipeline.exchanges import ALL
from pipeline.store import exists


def run(name, limit=None):
    ex = ALL[name]
    pairs = ex.pairs()
    todo = [p for p in pairs if not exists(name, p[0], p[1])][:limit]
    print(f"[{name}] {len(pairs)} pairs, {len(todo)} to fetch", flush=True)
    done = fails = 0
    with ThreadPoolExecutor(ex.WORKERS) as pool:
        futs = {pool.submit(ex.fetch, *p): p for p in todo}
        for f in as_completed(futs):
            done += 1
            try:
                f.result()
            except Exception as e:
                fails += 1
                print(f"[{name}] FAIL {futs[f][2]}: {e}", flush=True)
            if done % 50 == 0 or done == len(todo):
                print(f"[{name}] {done}/{len(todo)} ({fails} failed)", flush=True)


def main():
    args = sys.argv[1:]
    limit = None
    if "--limit" in args:
        i = args.index("--limit")
        limit = int(args[i + 1])
        del args[i: i + 2]
    names = args or list(ALL)
    with ThreadPoolExecutor(len(names)) as pool:
        for f in [pool.submit(run, n, limit) for n in names]:
            f.result()


if __name__ == "__main__":
    main()
