"""ATR, SuperTrend and the swing points its flips define."""
import numpy as np
import pandas as pd


def atr(df, n):
    """Wilder's Average True Range."""
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift()
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def supertrend(df, n, mult):
    """-> (line, direction); direction +1 = up (line below price), -1 = down.
    Computed on log prices so the bands are percentage-based: stays meaningful across
    100x price ranges and can never go negative."""
    lg = np.log(df[["open", "high", "low", "close"]])
    a = atr(lg, n).values
    h, l, c = lg["high"].values, lg["low"].values, lg["close"].values
    mid = (h + l) / 2
    ub, lb = mid + mult * a, mid - mult * a
    fu, fl = ub.copy(), lb.copy()
    d = np.ones(len(df), dtype=int)
    line = np.full(len(df), np.nan)
    for i in range(1, len(df)):
        fu[i] = ub[i] if ub[i] < fu[i - 1] or c[i - 1] > fu[i - 1] else fu[i - 1]
        fl[i] = lb[i] if lb[i] > fl[i - 1] or c[i - 1] < fl[i - 1] else fl[i - 1]
        if d[i - 1] == 1:
            d[i] = -1 if c[i] < fl[i] else 1
        else:
            d[i] = 1 if c[i] > fu[i] else -1
        line[i] = fl[i] if d[i] == 1 else fu[i]
    return pd.Series(np.exp(line), df.index), pd.Series(d, df.index)


def swings(df, direction):
    """-> [(index, 'L'|'H', price, confirmed)], strictly increasing index, alternating L/H.
    Each SuperTrend flip up confirms a swing low (lowest low since the previous swing), each flip
    down a swing high. The last entry is provisional (the leg still running)."""
    h, l = df["high"].values, df["low"].values
    d = direction.values
    out, start = [], 0
    flips = [i for i in range(1, len(d)) if d[i] != d[i - 1]]
    for f in flips:
        s = start + 1 if out else start  # each swing strictly after the previous one
        if s > f:
            continue
        if d[f] == 1:
            i, kind = s + int(np.argmin(l[s:f + 1])), "L"
        else:
            i, kind = s + int(np.argmax(h[s:f + 1])), "H"
        price = (l if kind == "L" else h)[i]
        if out and out[-1][1] == kind:  # skipped a flip: keep the more extreme of the two
            if (price < out[-1][2]) if kind == "L" else (price > out[-1][2]):
                out[-1] = (i, kind, price, True)
        else:
            out.append((i, kind, price, True))
        start = out[-1][0]
    # inception: if the first swing is a high, the lowest low before it is a swing low too
    if out and out[0][1] == "H" and out[0][0] > 0:
        i = int(np.argmin(l[:out[0][0]]))
        out.insert(0, (i, "L", l[i], True))
    start = min(start + 1, len(d) - 1) if out else start
    if d[-1] == 1:
        i = start + int(np.argmax(h[start:]))
        out.append((i, "H", h[i], False))
    else:
        i = start + int(np.argmin(l[start:]))
        out.append((i, "L", l[i], False))
    return out
