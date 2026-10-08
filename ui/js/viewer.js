// Side panel: the coin's precomputed zone chart plus its stats and zone list.
// Per-coin detail (data/coins/<COIN>.js) is loaded on demand and cached.
window.App = window.App || {};
window.DETAIL = window.DETAIL || {};

(function () {
  const V = App.viewer = { coin: null };
  const { fmt, esc } = App;
  const loading = {};

  function loadDetail(coin) {
    if (window.DETAIL[coin]) return Promise.resolve(window.DETAIL[coin]);
    if (!loading[coin]) {
      loading[coin] = new Promise(resolve => {
        const s = document.createElement("script");
        s.src = `data/coins/${encodeURIComponent(coin)}.js`;
        s.onload = () => resolve(window.DETAIL[coin]);
        s.onerror = () => resolve(null);
        document.head.appendChild(s);
      });
    }
    return loading[coin];
  }

  function scoreBars(s) {
    if (!s) return "";
    const bar = (label, v, w) => `<div class="bar"><span>${label} <i>${w}</i></span><b style="width:${Math.round(v * 100)}%"></b><em>${Math.round(v * 100)}</em></div>`;
    return `<div class="bars">
      <div class="bars-head">Pair score <b>${Math.round(s.score)}</b>
        ${s.corrected ? '<span class="chip fresh">corrected</span>' : '<span class="chip">not corrected</span>'}
        ${s.at_demand ? '<span class="chip fresh">at demand</span>' : '<span class="chip">not at demand</span>'}
        ${s.absorbing ? '<span class="chip absorb">absorbing</span>' : ""}</div>
      ${bar("Correction", s.corr, "35%")}${bar("Demand", s.zone, "35%")}${bar("Time since ATH", s.time, "15%")}${bar("Impulse", s.impulse, "15%")}
    </div>`;
  }

  function statsBlock(q, d, s) {
    if (!d) return `<div><h3>${q.toUpperCase()} pair</h3><p class="dim">No ${q.toUpperCase()} market: this coin only trades against dollars.</p></div>`;
    const a = d.ath;
    const zones = d.zones
      .filter(z => z.status !== "broken" || z.main)
      .sort((x, y) => (x.tf === y.tf ? Math.abs(x.drop) - Math.abs(y.drop) : x.tf === "W" ? -1 : 1));
    const rows = zones.map(z => `<tr>
        <td class="l">${z.main ? "★ " : z.main_active ? "☆ " : ""}${z.tf}</td>
        <td class="l">${fmt.price(z.bottom, q)} – ${fmt.price(z.top, q)}</td>
        <td>${z.formed}</td>
        <td>${fmt.pct(z.move)}</td>
        <td>${z.status === "broken" ? "broken" : z.status === "fresh" ? "fresh" : z.taps + " taps"}</td>
        <td class="${App.heatZone(z.status === "broken" ? null : z.drop)}">${z.status === "broken" ? "–" : z.drop === 0 ? "in zone" : fmt.pct(z.drop)}</td>
        <td>${z.conf ? "W+D" : ""}</td></tr>`).join("");
    return `<div>
      <h3>${q.toUpperCase()} pair · since ${a.first_date}</h3>
      <div class="kv">
        <span>ATH</span><span>${fmt.price(a.ath, q)} · ${a.ath_date} (${fmt.days(a.days_since_ath)} ago)${a.ath_launch_week ? " · listing spike" : ""}</span>
        <span>Max drawdown</span><span>${fmt.pct(a.max_drawdown_pct, 1)} → ${fmt.price(a.low_after_ath, q)} on ${a.low_after_ath_date}</span>
        <span>Now</span><span>${fmt.price(a.last, q)} · ${fmt.pct(a.current_drawdown_pct, 1)} from ATH · ${fmt.pct(a.bounce_from_low_pct)} off the low</span>
      </div>
      <table><thead><tr><th class="l">TF</th><th class="l">Zone</th><th>Formed</th><th>Move</th><th>Status</th><th>Drop</th><th></th></tr></thead>
      <tbody>${rows || '<tr><td colspan="7" class="dim l">No unbroken zones</td></tr>'}</tbody></table>
    </div>`;
  }

  // The verdict first: scenario, combined score, and why (per pair), above the chart
  function verdict(r) {
    const el = document.getElementById("vVerdict");
    const sc = r.score;
    if (!sc) { el.innerHTML = ""; return; }
    const [tag, text] = App.SCENARIOS[sc.scenario] || ["–", ""];
    const pair = (q, s) => `<div><h3>${q} pair</h3>${s ? scoreBars(s) : '<p class="dim">No BTC market: half the picture.</p>'}</div>`;
    el.innerHTML = `<div class="verdict"><span class="scen scen-${tag}">${tag}</span><b>Score ${Math.round(sc.score)}</b>
        <span class="dim">${text}</span></div>
      <div class="vgrid">${pair("USD", sc.usd)}${pair("BTC", sc.btc)}</div>`;
  }

  V.show = function (r) {
    V.coin = r.coin;
    const el = document.getElementById("viewer");
    el.hidden = false;
    document.getElementById("vTitle").innerHTML =
      `${r.rank ? "#" + r.rank + " " : ""}${esc(r.coin)}<small>${esc(r.name)} · ${fmt.mcap(r.mcap)}`
      + ` · USD since ${r.usd ? r.usd.first : "–"} · BTC ${r.btc ? "since " + r.btc.first : "no market"}</small>`;
    const img = document.getElementById("vImg");
    img.src = r.chart;
    document.getElementById("vOpen").href = r.chart;
    const stats = document.getElementById("vStats");
    stats.innerHTML = "";
    verdict(r);
    loadDetail(r.coin).then(d => {
      if (V.coin !== r.coin) return;            // user already moved on
      stats.innerHTML = d ? '<div class="vgrid">' + statsBlock("usd", d.usd) + statsBlock("btc", d.btc) + "</div>"
                          : '<p class="dim">No detail file.</p>';
    });
  };

  V.hide = function () {
    V.coin = null;
    document.getElementById("viewer").hidden = true;
  };

  // Warm the browser cache for the next few rows so arrow-key browsing is instant
  V.prefetch = function (rows) {
    rows.forEach(r => { if (r) { const i = new Image(); i.src = r.chart; loadDetail(r.coin); } });
  };
})();
