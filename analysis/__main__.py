"""Print a coin's zones:  python3 -m analysis HBAR"""
import sys
from dataclasses import asdict

import pandas as pd

from analysis import analyze

COLS = ["tf", "formed", "bottom", "top", "move_pct", "move_atr", "bos", "taps", "status", "dist_pct",
        "drop_to_zone_pct", "main", "main_active", "confluence"]

coin = (sys.argv[1] if len(sys.argv) > 1 else "HBAR").upper()
for q in ("USD", "BTC"):
    r = analyze(coin, q)
    if not r:
        continue
    f = pd.DataFrame([asdict(z) for tf in ("W", "D") for z in r[tf].zones])
    s = r["ath"]
    print(f"\n=== {coin}/{q} ===  ATH {s['ath']:.6g} ({s['days_since_ath']}d ago) · max DD {s['max_drawdown_pct']:.1f}%"
          f" · now {s['current_drawdown_pct']:+.1f}% from ATH")
    with pd.option_context("display.width", 220, "display.max_rows", 200):
        print(f[COLS].to_string(index=False, float_format=lambda v: f"{v:.4g}"))
