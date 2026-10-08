"""One price panel of the zone chart: candles, SuperTrend, swings, zones, ATH markers."""
import matplotlib.dates as mdates
import numpy as np
from matplotlib.patches import Rectangle

from charts.candles import date_axis, draw_candles
from charts.style import BROKEN, INK, INK2, MAIN, MUTED, ST_DOWN, ST_UP, ZONE, fmt_price, style_axes

DAILY_WINDOW_DAYS = 3 * 365
DAILY_MAX_DIST = 200   # daily panel: older unbroken zones only drawn if within +200% of price
PANEL_WIDTH_IN = 10


def _supertrend(ax, st, sd):
    if st is None:  # too few candles on this timeframe for SuperTrend
        return
    for d, col in ((1, ST_UP), (-1, ST_DOWN)):
        s = st.where(sd == d)
        ax.plot(s.index, s.values, color=col, linewidth=1.3, drawstyle="steps-post", alpha=0.9)


def _zones(ax, zones, view_start, x_end):
    """Boxes (+ an arrow for the main move). Returns [(y, text, bold)] right-edge labels."""
    labels = []
    for z in sorted(zones, key=lambda z: (z.main or z.main_active, z.status != "broken")):
        end = z.broken if z.status == "broken" else x_end
        if end < view_start:
            continue
        xs, xe = mdates.date2num(max(z.formed, view_start)), mdates.date2num(end)
        if z.main or z.main_active:
            col, alpha, lw, ls = MAIN, 0.30, 1.6, "-" if z.status != "broken" else "--"
        elif z.status == "broken":
            col, alpha, lw, ls = BROKEN, 0.12, 0.0, "-"
        else:
            col, alpha, lw, ls = ZONE, 0.20, 1.0, "-"
        ax.add_patch(Rectangle((xs, z.bottom), xe - xs, z.top - z.bottom, facecolor=col, alpha=alpha, linewidth=0))
        if lw:
            ax.hlines([z.bottom, z.top], xs, xe, colors=col, linewidth=lw * 0.6, linestyles=ls, alpha=0.9)
        if z.status != "broken":
            tag = "MAIN · " if z.main else ("MAIN ACTIVE · " if z.main_active else "")
            conf = " · W+D" if z.confluence else ""
            labels.append((np.sqrt(z.top * z.bottom),
                           f"{tag}{z.dist_pct:+.0f}% · {z.taps} tap{'s' if z.taps != 1 else ''}{conf}", bool(tag)))
        if z.main:
            ax.annotate("", (mdates.date2num(z.leg_high_date), z.leg_high), (mdates.date2num(z.formed), z.bottom),
                        arrowprops=dict(arrowstyle="->", color=MAIN, lw=1.2, alpha=0.8))
            ax.annotate(f"+{z.move_pct:,.0f}%  ({z.move_atr:.0f}× ATR)", (mdates.date2num(z.leg_high_date), z.leg_high),
                        xytext=(6, 4), textcoords="offset points", fontsize=9, color=MAIN, fontweight="bold")
    return labels


def _place_labels(ax, labels, x):
    """Right-edge labels, nudged apart so they never overlap (log-scale aware)."""
    lo, hi = (np.log10(v) for v in ax.get_ylim())
    gap = (hi - lo) * 0.035
    ys = sorted(((np.log10(y), t, b) for y, t, b in labels), key=lambda r: r[0])
    placed = []
    for y, t, b in ys:
        placed.append((max(y, placed[-1][0] + gap) if placed else y, t, b))
    for (y, t, b), (y0, _, _) in zip(placed, ys):
        ax.annotate(t, (x, 10 ** y0), xytext=(x, 10 ** y), textcoords="data", va="center", fontsize=8,
                    color=INK, fontweight="bold" if b else "normal", annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.5) if abs(y - y0) > gap * 0.3 else None)


def _ath_markers(ax, s, quote):
    ax.plot(s["ath_date"], s["ath"], marker="*", markersize=13, color=ST_DOWN, markeredgecolor=INK,
            markeredgewidth=0.5, linestyle="none", zorder=5)
    ax.annotate(f"ATH {fmt_price(s['ath'], quote)}", (s["ath_date"], s["ath"]), xytext=(8, -3),
                textcoords="offset points", fontsize=8.5, color=INK, fontweight="bold")
    if s["low_after_ath_date"] != s["ath_date"]:
        ax.plot(s["low_after_ath_date"], s["low_after_ath"], marker="o", markersize=7, color=ST_DOWN,
                markeredgecolor=INK, markeredgewidth=0.5, linestyle="none", zorder=5)
        ax.annotate(f"{s['max_drawdown_pct']:.0f}% from ATH", (s["low_after_ath_date"], s["low_after_ath"]),
                    xytext=(8, -10), textcoords="offset points", fontsize=8.5, color=INK, fontweight="bold")


def draw_panel(ax, res, tf, quote, coin):
    """res = analyze(coin, quote); tf = 'W' (full history) or 'D' (last 3 years)."""
    t = res[tf]
    df, zones, st, sd = t.candles, t.zones, t.supertrend, t.direction
    if tf == "D" and len(df) > DAILY_WINDOW_DAYS and st is not None:
        cut = df.index[-DAILY_WINDOW_DAYS]
        view, st, sd = df[df.index >= cut], st[st.index >= cut], sd[sd.index >= cut]
    else:
        view = df
    start, x_end = view.index[0], view.index[-1]
    if tf == "D":  # keep the daily view local; far-away zones stay in the table / weekly panel
        zones = [z for z in zones
                 if (z.status == "broken" and z.broken >= start and z.bottom >= view["low"].min())
                 or (z.status != "broken" and (z.formed >= start or z.dist_pct <= DAILY_MAX_DIST))]

    draw_candles(ax, view, PANEL_WIDTH_IN, alpha=0.75)
    _supertrend(ax, st, sd)
    for i, kind, price, conf in t.swings:
        if conf and df.index[i] >= start:
            ax.plot(df.index[i], price, marker="^" if kind == "L" else "v", markersize=5, color=INK2,
                    alpha=0.6, linestyle="none", markeredgewidth=0)
    labels = _zones(ax, zones, start, x_end)
    if tf == "W":
        _ath_markers(ax, res["ath"], quote)
    last = view["close"].iloc[-1]
    ax.axhline(last, color=INK2, linewidth=0.8, linestyle=":")
    ax.annotate(fmt_price(last, quote), (mdates.date2num(x_end), last), xytext=(4, 0),
                textcoords="offset points", va="center", fontsize=8, color=INK2)

    style_axes(ax, quote)
    alive = [z for z in zones if z.status != "broken"]
    lo = min([view["low"].min()] + ([z.bottom for z in alive] if tf == "D" else []))
    ax.set_ylim(lo * 0.85, view["high"].max() * 1.25)
    span = x_end - start
    ax.set_xlim(start - span * 0.01, x_end + span * 0.24)
    _place_labels(ax, labels, mdates.date2num(x_end + span * 0.012))
    date_axis(ax, start, x_end)
    ax.set_title(f"{coin}/{quote} · {'WEEKLY' if tf == 'W' else 'DAILY'}   {start:%Y-%m-%d} → {x_end:%Y-%m-%d}   "
                 f"· {len(zones)} zones, {len(alive)} unbroken", loc="left", fontsize=11, color=INK, fontweight="bold")
