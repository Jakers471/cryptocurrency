"""All-time-high / drawdown statistics for one series."""
import pandas as pd

from analysis.config import LAUNCH_DAYS


def ath_stats(df):
    """ATH, the lowest low after it, and where the current price sits."""
    ath_date = df["high"].idxmax()
    ath = df["high"].max()
    after = df.loc[ath_date:]
    low_date = after["low"].idxmin()
    low = after["low"].min()
    last, now = df["close"].iloc[-1], df.index[-1]
    launch = (ath_date - df.index[0]).days < LAUNCH_DAYS
    settled = df[df.index >= df.index[0] + pd.Timedelta(days=LAUNCH_DAYS)]
    ath_ex = settled["high"].max() if launch and len(settled) else ath
    return {
        "ath": ath, "ath_date": ath_date, "days_since_ath": (now - ath_date).days,
        "ath_launch_week": launch,  # the ATH was a listing-week spike
        "ath_ex_launch": ath_ex,    # highest high after the listing week (= ath when no spike)
        "drawdown_ex_launch_pct": (last / ath_ex - 1) * 100,  # used for scoring the correction
        "low_after_ath": low, "low_after_ath_date": low_date,
        "max_drawdown_pct": (low / ath - 1) * 100,       # ATH -> lowest point since
        "current_drawdown_pct": (last / ath - 1) * 100,  # ATH -> current price
        "bounce_from_low_pct": (last / low - 1) * 100,   # lowest point since ATH -> current price
        "atl": df["low"].min(), "atl_date": df["low"].idxmin(),
        "last": last, "last_date": now, "first_date": df.index[0],
    }
