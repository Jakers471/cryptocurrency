"""One module per exchange. Each exposes:
    NAME     folder name under data/raw/
    WORKERS  parallel threads (the module's RateLimiter keeps it within the API limits)
    pairs()  -> [(base, quote, exchange_symbol), ...]
    fetch(base, quote, symbol) -> rows written (full daily history, oldest -> newest)
"""
from pipeline.exchanges import binance, bitfinex, coinbase, gate, kucoin, mexc, okx, poloniex

ALL = {m.NAME: m for m in (binance, coinbase, bitfinex, gate, kucoin, okx, mexc, poloniex)}
