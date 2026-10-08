// Chart browser: one coin per screen, highest market cap first, USD and BTC side by side.
// Display only: every number comes precomputed from data/scan.js.
(function () {
  const { fmt, esc } = App;
  if (!window.SCAN) {
    document.getElementById("coinhead").innerHTML = "No data yet. Run <code>python3 -m scanner.build</code>.";
    return;
  }
  const STORE = "altscanner.browse";
  const all = SCAN.rows.filter(r => r.rank).sort((a, b) => a.rank - b.rank);
  let list = [], pos = 0;

  const saved = (() => { try { return JSON.parse(localStorage.getItem(STORE) || "{}"); } catch { return {}; } })();
  const save = () => { try { localStorage.setItem(STORE, JSON.stringify({ coin: list[pos] && list[pos].coin, hideStable: hideEl.checked })); } catch { } };

  const hideEl = document.getElementById("hideStable");
  if (saved.hideStable === false) hideEl.checked = false;

  document.getElementById("meta").textContent = `data as of ${SCAN.generated}`;
  document.getElementById("coinlist").innerHTML = all.map(r => `<option value="${esc(r.coin)}">${esc(r.name)}</option>`).join("");

  const btc = SCAN.rows.find(r => r.coin === "BTC");
  if (btc && btc.usd) {
    const u = btc.usd, a = d => d > 0 ? '<span class="u">▲</span>' : '<span class="d">▼</span>';
    document.getElementById("btcctx").innerHTML = `<b>BTC</b> ${fmt.price(u.price, "usd")} · ${fmt.pct(u.dd_now)} from ATH · W ${a(u.st_w)} D ${a(u.st_d)}`;
  }

  const trend = (d, bars) => d == null ? "–" : `<span class="${d > 0 ? "u" : "d"}">${d > 0 ? "▲ up" : "▼ down"}</span> <span class="dim">${bars} bars</span>`;
  const ZN = { main_w: "main weekly zone", near_w: "weekly zone", near_d: "daily zone", absorb: "absorbing" };

  function demand(p, s) {
    if (!s || !s.zone_src) return '<span class="dim">no zone near</span>';
    const z = p[s.zone_src];
    if (s.zone_src === "absorb") return `absorbing ${z.tf === "W" ? "weekly" : "daily"} zone (${fmt.pct(s.zone_below)})`;
    const name = s.zone_src === "near_d" && z.conf ? "daily zone inside weekly" : ZN[s.zone_src];
    return `${s.zone_drop === 0 ? "in" : fmt.pct(s.zone_drop) + " to"} ${name} · ${z.status === "fresh" ? "fresh" : z.taps + " taps"}`;
  }

  // One compact line per pair: the chart is the focus, these are the reference numbers
  function pairCard(q, p, s) {
    const Q = q.toUpperCase();
    if (!p) return `<div class="pair"><b class="pq">${Q}</b><span class="dim">no ${Q} market (trades against dollars only)</span></div>`;
    const item = (k, v, cls = "") => `<span class="it ${cls}"><i>${k}</i>${v}</span>`;
    return `<div class="pair">
      <b class="pq">${Q}</b>
      ${s ? `<span class="pscore ${App.heatScore(s.score)}">${Math.round(s.score)}</span>` : ""}
      ${item("price", fmt.price(p.price, q))}
      ${item("ATH", `${fmt.price(p.ath, q)} <span class="dim">${fmt.days(p.ath_days)} ago</span>${p.ath_launch ? ' <span class="chip spike">L</span>' : ""}`)}
      ${item("below ATH", fmt.pct(p.dd_now) + (s && s.corrected ? " ✓" : ""), "pill " + App.heatDd(p.dd_now))}
      ${item("max DD", fmt.pct(p.dd_max))}
      ${item("demand", demand(p, s) + (s && s.at_demand ? " ✓" : ""), "pill " + App.heatZone(s && s.zone_src !== "absorb" ? s.zone_drop : null))}
      ${item("trend W·D", `${arrow(p.st_w)} ${arrow(p.st_d)}`)}
      ${item("since", p.first)}
    </div>`;
  }
  const arrow = d => d == null ? "–" : `<span class="${d > 0 ? "u" : "d"}">${d > 0 ? "▲" : "▼"}</span>`;

  function show(i) {
    if (!list.length) return;
    pos = (i + list.length) % list.length;
    const r = list[pos];
    const sc = r.score;
    const [tag, text] = sc ? (App.SCENARIOS[sc.scenario] || ["–", ""]) : ["–", ""];
    document.getElementById("coinhead").innerHTML = `
      <span class="rank">#${r.rank}</span>
      <span class="sym">${esc(r.coin)}</span>
      <span class="name">${esc(r.name)}</span>
      <span class="mc">mcap <b>${fmt.mcap(r.mcap)}</b></span>
      ${sc ? `<span class="scen scen-${tag}" title="${esc(text)}">${tag}</span><span class="total">score <b>${Math.round(sc.score)}</b></span><span class="dim">${esc(text)}</span>` : ""}`;
    document.getElementById("pairs").innerHTML =
      pairCard("usd", r.usd, sc && sc.usd) + pairCard("btc", r.btc, sc && sc.btc);
    document.getElementById("chart").src = r.chart;
    document.getElementById("pos").textContent = `${pos + 1} / ${list.length}`;
    history.replaceState(null, "", `#coin=${encodeURIComponent(r.coin)}`);
    save();
    [1, 2, 3, -1].forEach(d => { const n = list[(pos + d + list.length) % list.length]; if (n) new Image().src = n.chart; });
  }

  function rebuild(keepCoin) {
    list = all.filter(r => !(hideEl.checked && r.stable));
    const i = list.findIndex(r => r.coin === keepCoin);
    show(i >= 0 ? i : 0);
  }

  hideEl.addEventListener("change", () => rebuild(list[pos] && list[pos].coin));
  document.getElementById("prev").addEventListener("click", () => show(pos - 1));
  document.getElementById("next").addEventListener("click", () => show(pos + 1));
  const jump = document.getElementById("jump");
  jump.addEventListener("change", () => {
    const c = jump.value.trim().toUpperCase();
    let i = list.findIndex(r => r.coin === c);
    if (i < 0 && hideEl.checked && all.some(r => r.coin === c)) { hideEl.checked = false; rebuild(c); i = pos; }
    if (i >= 0) show(i);
    jump.value = ""; jump.blur();
  });
  document.addEventListener("keydown", e => {
    const typing = document.activeElement === jump;
    if (e.key === "/" && !typing) { e.preventDefault(); jump.focus(); return; }
    if (e.key === "Escape") { jump.blur(); return; }
    if (typing) return;
    if (e.key === "ArrowRight" || e.key === "j") { e.preventDefault(); show(pos + 1); }
    if (e.key === "ArrowLeft" || e.key === "k") { e.preventDefault(); show(pos - 1); }
    if (e.key === "Home") show(0);
  });

  const root = document.documentElement;
  try { const t = localStorage.getItem("altscanner.theme"); if (t) root.dataset.theme = t; } catch { }
  document.getElementById("theme").addEventListener("click", () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("altscanner.theme", root.dataset.theme); } catch { }
  });

  const linked = decodeURIComponent((location.hash.match(/coin=([^&]+)/) || [])[1] || "").toUpperCase();
  rebuild(linked || saved.coin);
})();
