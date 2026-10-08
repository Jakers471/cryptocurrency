"""Every tunable setting for the zone analysis, in one place."""

# Per timeframe: ATR length, SuperTrend (length, multiplier), minimum impulse leg (x ATR),
# max base candles, how many bars after the low to look for the departure candle
PARAMS = {
    "D": dict(atr_len=14, st_len=10, st_mult=3.0, min_leg_atr=4.0, max_base=8, depart_within=8),
    "W": dict(atr_len=14, st_len=10, st_mult=3.0, min_leg_atr=3.0, max_base=6, depart_within=6),
}
DEPART_RANGE_ATR = 1.0   # departure candle: range >= 1 ATR ...
DEPART_BODY_PCT = 0.5    # ... and body >= 50% of its range, bullish
LEAVE_ATR = 1.5          # fallback departure: first close this far above the low
BASE_BODY_PCT = 0.5      # base candle: body <= 50% of range, or range <= BASE_RANGE_ATR
BASE_RANGE_ATR = 0.8
TALL_ZONE_MULT = 2.5     # zone > 2.5x the median zone height (same coin + timeframe) is an outlier ...
TALL_ZONE_KEEP = 0.15    # ... keep only its bottom 15% (top 15% for supply)
LAUNCH_DAYS = 7          # an ATH within this many days of listing is flagged as a listing spike

# ---------------------------------------------------------------- scoring (analysis/score.py)
# Piecewise-linear curves: [(input, score 0..1), ...]
SCORE_WEIGHTS = {"corr": 0.35, "zone": 0.35, "time": 0.15, "impulse": 0.15}
CURVE_CORRECTION = [(0, 0), (40, 0), (70, 0.4), (80, 0.75), (85, 1), (95, 1), (98, 0.7), (100, 0.4)]  # % below ATH
CURVE_ZONE_DROP = [(0, 1), (5, 0.95), (15, 0.75), (30, 0.4), (50, 0.1), (70, 0)]  # % drop still needed to reach zone
CURVE_ATH_DAYS = [(0, 0), (90, 0), (365, 0.7), (730, 1)]                          # days since the ATH
CURVE_IMPULSE = [(0, 0), (100, 0.2), (300, 0.5), (1000, 0.8), (3000, 1)]           # main zone's move, %
# How much each zone counts toward "at demand": weekly (higher time horizon) outweighs daily.
# A lone daily zone (0.6) can't reach AT_DEMAND by itself; overlapping a weekly zone lifts it.
ZONE_SOURCES = {"main_w": 1.0, "near_w": 1.0, "near_d": 0.6, "absorb": 1.0}
ZONE_DAILY_CONFLUENCE = 0.9               # daily zone that overlaps an unbroken weekly zone (W+D)
ABSORB_WEIGHT = {"W": 0.95, "D": 0.55}    # absorbing a weekly vs a daily zone
PUSH_OFF_DAYS, PUSH_OFF_BONUS = 90, 0.15  # tapped a zone within 90 days and is above it: "pushing up off it"
ABSORB_DAYS, ABSORB_RANGE = 120, 0.20     # zone broken within 120 days, price within 20% below its bottom
BOTH_BONUS = 10                           # both pairs corrected + at demand (scenario 3)
NO_BTC_FACTOR = 0.8                       # coin with no BTC market: half the equation missing
AT_DEMAND = 0.7                           # zone part >= this = "at demand"
CORRECTED = 80                            # % below ATH = "corrected"
