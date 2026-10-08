# Alt Scanner

Daily candles for every coin we can find (from its first listing), demand zones on
weekly + daily for the USD and BTC pairs, and a fast filterable UI to go through them.

## Open the UI

```
python3 serve.py
```

Opens http://127.0.0.1:8765/ui/ (local only; Ctrl+C stops it). A tiny server is needed because
macOS blocks browsers from reading the page's neighbouring files over file://.
Everything is precomputed; the page only displays it.
Shortcuts: `↑ ↓` move · `Enter` open the chart · `Esc` close · `/` search · click a header to sort.
Deep link to a coin: http://127.0.0.1:8765/ui/#coin=HBAR.
Chart browser (one coin per screen, highest market cap first, ← →): http://127.0.0.1:8765/ui/browse.html

## Rebuild the data (run from this folder)

| Step | Command | Time |
|---|---|---|
| 1. Download raw candles | `python3 -m pipeline.fetch` | ~1 h first time (skips files already there) |
| 2. Merge into one USD + one BTC series per coin, rank by market cap | `python3 -m pipeline.merge` | ~5–10 min |
| 3. Analyse every pair, write UI data + zone charts | `python3 -m scanner.build` | ~30 min (`--no-charts`: ~2 min) |

Test on a few coins: `python3 -m pipeline.merge HBAR XRP` · `python3 -m scanner.build HBAR XRP`
Inspect one coin's zones in the terminal: `python3 -m analysis HBAR`
Plain candle charts (no zones): `python3 -m charts.price`

## Layout

```
core/       paths.py (every file location) · universe.py (ranking, chart paths)
pipeline/   fetch.py · exchanges/<one file per exchange> · store.py · http.py
            sources.py (read raw) · combine.py (merge sources) · clean.py (bad prints) · ranking.py
            merge.py (runner)
analysis/   config.py (every tunable setting) · series.py · indicators.py (ATR, SuperTrend, swings)
            zones.py (demand zones) · stats.py (ATH / drawdown) · __init__.py (analyze)
charts/     style.py · candles.py · zone_panel.py · zone_table.py · zones.py · price.py
scanner/    rows.py (analysis -> display records) · build.py (runner)
ui/         index.html · css/app.css · js/{format,columns,filters,table,viewer,main}.js
            data/ (generated: scan.js + coins/<COIN>.js)
data/       raw/ · coins/ · coins_btc/ · by_market_cap/ · coins_summary.csv
png/        zones/<rank band>/ · price/<rank band>/
```

Zone settings (SuperTrend length/multiplier, impulse size, base rules, the 15% tall-zone rule)
all live in `analysis/config.py`.
