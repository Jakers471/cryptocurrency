// Column definitions, laid out around the buy framework:
//   coin  -> score + scenario (the verdict)
//   pair  -> the same questions for USD and BTC: pair score · % below ATH · demand · ATH age · trend · history
// A column is { key, label, title, group, cls?(row), cell(row) -> html, sort(row) -> number|string }
window.App = window.App || {};

(function () {
  const { fmt, heatZone, heatDd, heatScore, esc } = App;

  const ZONE_NAMES = { main_w: "main", near_w: "W", near_d: "D", absorb: "absorbing" };
  const zoneName = (src, z) => src === "near_d" && z.conf ? "D in W" : ZONE_NAMES[src];

  const trend = (dir, bars) =>
    dir == null ? '<span class="dim">–</span>' :
    `<span class="${dir > 0 ? "u" : "d"}">${dir > 0 ? "▲" : "▼"}</span><span class="dim">${bars}</span>`;

  // "Demand" cell: which zone supports the setup and how far away it is
  function demand(p, s) {
    if (!p || !s || !s.zone_src) return { html: '<span class="dim">none near</span>', cls: "" };
    const z = p[s.zone_src];
    if (s.zone_src === "absorb")
      return { html: `${fmt.pct(s.zone_below)} <span class="chip absorb">absorbing ${z.tf}</span>`, cls: z.tf === "W" ? "z1" : "z3" };
    const tag = z.status === "fresh" ? '<span class="chip fresh">fresh</span>' : `<span class="chip">${z.taps}t</span>`;
    const where = s.zone_drop === 0 ? "in zone" : fmt.pct(s.zone_drop);
    return { html: `${where} <span class="chip zone-${s.zone_src}">${zoneName(s.zone_src, z)}</span>${tag}`, cls: heatZone(s.zone_drop) };
  }

  function pairColumns(q) {
    const p = r => r[q];
    const s = r => r.score && r.score[q];
    const Q = q.toUpperCase();
    return [
      { key: `${q}.score`, label: "Score", group: q, first: true,
        title: `${Q}-pair setup score (correction 35% · demand 35% · time since ATH 15% · impulse 15%)`,
        cell: r => s(r) ? `<b>${Math.round(s(r).score)}</b>` : '<span class="dim">–</span>',
        cls: r => s(r) ? heatScore(s(r).score) : "", sort: r => -(s(r) ? s(r).score : -1) },
      { key: `${q}.dd_now`, label: "Below ATH", group: q,
        title: "How far the price is below the all-time high (85–95% = the sweet spot)",
        cell: r => p(r) ? fmt.pct(p(r).dd_now) + (s(r) && s(r).corrected ? ' <span class="ok">✓</span>' : "") : "–",
        cls: r => p(r) ? heatDd(p(r).dd_now) : "", sort: r => p(r) ? p(r).dd_now : 1e9 },
      { key: `${q}.demand`, label: "Demand", group: q,
        title: "The zone supporting the setup and the drop needed to reach it. Weekly zones (main, W) weigh most; a daily zone counts fully only inside a weekly one (D in W)",
        cell: r => demand(p(r), s(r)).html, cls: r => demand(p(r), s(r)).cls,
        sort: r => -(s(r) ? s(r).zone : -1) },
      { key: `${q}.ath_days`, label: "ATH age", group: q,
        title: "Time since the all-time high (long = hasn't seen that high in a long time)",
        cell: r => {
          if (!p(r)) return "–";
          const d = p(r).ath_days;
          return (d <= 30 ? '<span class="chip new">NEW HIGH</span> ' : "") + fmt.days(d)
            + (p(r).ath_launch ? ' <span class="chip spike" title="ATH was a listing-week spike">L</span>' : "");
        },
        sort: r => -(p(r) ? p(r).ath_days : -1) },
      { key: `${q}.st`, label: "Trend W·D", group: q,
        title: "SuperTrend direction and bars since it flipped (weekly · daily)",
        cell: r => p(r) ? `<span class="st">${trend(p(r).st_w, p(r).st_w_bars)} · ${trend(p(r).st_d, p(r).st_d_bars)}</span>` : "–",
        sort: r => p(r) ? -((p(r).st_w ?? 0) * 2 + (p(r).st_d ?? 0)) : 9 },
      { key: `${q}.years`, label: "History", group: q,
        title: `Years of ${Q}-pair data, since its first listing`,
        cell: r => p(r) ? `<span title="since ${p(r).first}">${p(r).years}y</span>` : '<span class="dim">no market</span>',
        sort: r => -(p(r) ? p(r).years : -1) },
    ];
  }

  const SCEN = {
    S3: ["S3", "Both pairs corrected and at demand: accumulate"],
    S4: ["S4", "Both pairs below / absorbing demand: accumulate"],
    S1: ["S1", "Only one pair is corrected and at demand"],
    S2: ["S2", "Both pairs pumping, nowhere near demand"],
    "USD only": ["USD", "No BTC market: half the picture"],
    "–": ["–", "Mixed / neutral"],
  };

  App.columns = [
    { key: "rank", label: "#", group: "coin", cls: () => "rank",
      cell: r => r.rank ?? "–", sort: r => r.rank ?? 1e9 },
    { key: "coin", label: "Coin", group: "coin", left: true, cls: () => "coin l",
      cell: r => `<b>${esc(r.coin)}</b><small title="${esc(r.name)}">${esc(r.name)}</small>`, sort: r => r.coin },
    { key: "mcap", label: "Mcap", group: "coin",
      cell: r => fmt.mcap(r.mcap), sort: r => -(r.mcap ?? 0) },
    { key: "score", label: "Score", group: "coin",
      title: "Both pairs combined, +10 when both are corrected and at demand",
      cell: r => r.score ? `<b>${Math.round(r.score.score)}</b>` : "–",
      cls: r => r.score ? "score " + heatScore(r.score.score) : "", sort: r => -(r.score ? r.score.score : -1) },
    { key: "scenario", label: "Scenario", group: "coin",
      cell: r => {
        const sc = r.score ? SCEN[r.score.scenario] : null;
        return sc ? `<span class="scen scen-${sc[0]}" title="${sc[1]}">${sc[0]}</span>` : "–";
      },
      sort: r => ({ S3: 0, S4: 1, S1: 2, "–": 3, "USD only": 4, S2: 5 })[r.score ? r.score.scenario : "–"] ?? 9 },
    ...pairColumns("usd"),
    ...pairColumns("btc"),
  ];
  App.SCENARIOS = SCEN;
})();
