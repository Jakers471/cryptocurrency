"""Shared chart colours, price formatting and axis styling."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.ticker as mticker

UP, DOWN = "#2a78d6", "#e34948"            # candles: blue up / red down
ST_UP, ST_DOWN = "#1baf7a", "#eb6834"      # SuperTrend up / down
ZONE, MAIN, BROKEN = "#1baf7a", "#4a3aa7", "#9a9994"
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#8a8984", "#e8e7e3", "#fcfcfb"


def fmt_price(v, quote="USD"):
    """$1,234 / $0.1221 for USD; 0.0322 BTC or 146 sat for BTC pairs."""
    if quote == "BTC":
        if v >= 0.01:
            return f"{v:.4g} BTC"
        s = v * 1e8
        return f"{s:,.0f} sat" if s >= 100 else f"{s:.3g} sat"
    return f"${v:,.0f}" if v >= 1000 else f"${v:.4g}"


def fmt_mcap(v):
    if not v:
        return ""
    return f"${v / 1e9:,.2f}B" if v >= 1e9 else f"${v / 1e6:,.0f}M"


def style_axes(ax, quote="USD", log=True):
    ax.set_facecolor(SURFACE)
    if log:
        ax.set_yscale("log")
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: fmt_price(v, quote)))
    ax.yaxis.set_minor_formatter(mticker.NullFormatter())
