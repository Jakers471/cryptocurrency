"""Every file location in one place."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
RAW = os.path.join(DATA, "raw")                  # per-exchange candles (pipeline.fetch)
COINS = os.path.join(DATA, "coins")              # merged USD series (pipeline.merge)
COINS_BTC = os.path.join(DATA, "coins_btc")      # merged BTC series
BY_MCAP = os.path.join(DATA, "by_market_cap")    # copies numbered by market cap + ranking.csv
RANKING = os.path.join(BY_MCAP, "ranking.csv")
SUMMARY = os.path.join(DATA, "coins_summary.csv")
PNG = os.path.join(ROOT, "png")
PNG_PRICE = os.path.join(PNG, "price")           # plain candle charts (charts.price)
PNG_ZONES = os.path.join(PNG, "zones")           # zone charts (charts.zones)
UI = os.path.join(ROOT, "ui")
UI_DATA = os.path.join(UI, "data")               # scanner output the UI loads (scanner.build)


def series_path(coin, quote):
    return os.path.join(COINS if quote == "USD" else COINS_BTC, f"{coin}.csv")
