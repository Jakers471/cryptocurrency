"""Candlestick drawing (fast: two vline collections per colour, no per-candle patches)."""
import matplotlib.dates as mdates

from charts.style import DOWN, UP


def draw_candles(ax, df, width_in, alpha=1.0):
    """Wicks + bodies scaled to the number of candles across width_in inches."""
    x = mdates.date2num(df.index.to_pydatetime())
    up = (df["close"] >= df["open"]).values
    body_lw = max(0.4, min(6.0, width_in * 72 * 0.9 / len(df) * 0.65))
    for mask, col in ((up, UP), (~up, DOWN)):
        d = df[mask]
        ax.vlines(x[mask], d["low"], d["high"], color=col, linewidth=min(0.6, body_lw), alpha=alpha)
        ax.vlines(x[mask], d[["open", "close"]].min(axis=1), d[["open", "close"]].max(axis=1),
                  color=col, linewidth=body_lw, alpha=alpha)


def date_axis(ax, start, end):
    yrs = (end - start).days / 365
    ax.xaxis.set_major_locator(mdates.YearLocator() if yrs > 3 else mdates.MonthLocator(bymonth=(1, 4, 7, 10)))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y" if yrs > 3 else "%b %Y"))
