// Wiring: data -> table, filters -> re-render, clicks/keys -> viewer.
(function () {
  const { table: T, viewer: V, filters: F } = App;

  if (!window.SCAN) {
    document.getElementById("tbody").innerHTML =
      '<tr><td class="l">No data yet. Run <code>python3 -m scanner.build</code> from the project folder.</td></tr>';
    return;
  }
  document.getElementById("meta").textContent = `data as of ${SCAN.generated}`;

  // "It all depends on bitcoin": BTC/USD context in the header
  const btc = SCAN.rows.find(r => r.coin === "BTC");
  if (btc && btc.usd) {
    const u = btc.usd, arrow = d => d > 0 ? '<span class="u">▲</span>' : '<span class="d">▼</span>';
    document.getElementById("btcctx").innerHTML =
      `<b>BTC</b> ${App.fmt.price(u.price, "usd")} · ${App.fmt.pct(u.dd_now)} from ATH · W ${arrow(u.st_w)} D ${arrow(u.st_d)}`;
  }

  T.init(SCAN.rows);
  let pending = false;
  const rerender = () => {                     // coalesce rapid typing into one frame
    if (pending) return;
    pending = true;
    requestAnimationFrame(() => { pending = false; T.render(); });
  };
  F.bind(rerender);
  T.render();

  const open = i => {
    T.highlight(i);
    V.show(T.rows[i]);
    const pos = T.view.indexOf(i);
    V.prefetch([T.rows[T.view[pos + 1]], T.rows[T.view[pos + 2]], T.rows[T.view[pos - 1]]]);
  };

  document.getElementById("tbody").addEventListener("click", e => {
    const tr = e.target.closest("tr[data-i]");
    if (tr) open(+tr.dataset.i);
  });
  document.getElementById("vClose").addEventListener("click", V.hide);

  // Deep link: index.html#coin=HBAR opens that coin's chart
  const linked = decodeURIComponent((location.hash.match(/coin=([^&]+)/) || [])[1] || "").toUpperCase();
  const li = T.rows.findIndex(r => r.coin === linked);
  if (li >= 0) open(li);

  document.addEventListener("keydown", e => {
    const typing = /INPUT|SELECT|TEXTAREA/.test(document.activeElement.tagName);
    if (e.key === "/" && !typing) { e.preventDefault(); document.getElementById("search").focus(); return; }
    if (e.key === "Escape") { if (typing) document.activeElement.blur(); else V.hide(); return; }
    if (typing) return;
    if (e.key === "ArrowDown" || e.key === "ArrowUp" || e.key === "j" || e.key === "k") {
      e.preventDefault();
      const i = T.step(e.key === "ArrowDown" || e.key === "j" ? 1 : -1);
      if (i != null && V.coin) open(i);      // viewer open: follow the selection
    } else if (e.key === "Enter" && T.selected >= 0) {
      open(T.selected);
    }
  });

  // Theme toggle: system by default, remembered per browser
  const root = document.documentElement;
  try { const t = localStorage.getItem("altscanner.theme"); if (t) root.dataset.theme = t; } catch { }
  document.getElementById("theme").addEventListener("click", () => {
    const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    root.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("altscanner.theme", root.dataset.theme); } catch { }
  });
})();
