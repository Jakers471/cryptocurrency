// Table rendering. Each row's HTML is built once at load; filtering and sorting only
// reorder those cached strings, so updates stay in the low milliseconds.
window.App = window.App || {};

(function () {
  const T = App.table = { rows: [], view: [], sortKey: "score", sortDir: 1, selected: -1 };
  const GROUPS = { coin: "", usd: "USD pair", btc: "BTC pair" };

  function header() {
    const cols = App.columns;
    const spans = [];
    cols.forEach(c => {
      const last = spans[spans.length - 1];
      if (last && last.group === c.group) last.n++;
      else spans.push({ group: c.group, n: 1 });
    });
    const top = spans.map(s => `<th colspan="${s.n}" class="grp-${s.group}">${GROUPS[s.group]}</th>`).join("");
    const second = cols.map(c => {
      const cls = [c.left ? "l" : "", c.first ? `grp-${c.group}` : "", c.key === T.sortKey ? "sorted" : ""].join(" ");
      const arrow = c.key === T.sortKey ? (T.sortDir > 0 ? " ↓" : " ↑") : "";  // ↓ = best / first at the top
      return `<th data-key="${c.key}" class="${cls}" title="${App.esc(c.title || "")}">${c.label}${arrow}</th>`;
    }).join("");
    document.getElementById("thead").innerHTML = `<tr>${top}</tr><tr>${second}</tr>`;
  }

  function rowHtml(r, i) {
    const tds = App.columns.map(c => {
      const cls = [(c.cls && c.cls(r)) || "", c.first ? `first-${c.group}` : ""].join(" ").trim();
      return `<td${cls ? ` class="${cls}"` : ""}>${c.cell(r)}</td>`;
    }).join("");
    return `<tr data-i="${i}">${tds}</tr>`;
  }

  T.init = function (rows) {
    T.rows = rows;
    T.html = rows.map(rowHtml);                             // built once
    T.sortVals = {};                                        // per-column sort values, built lazily
    header();
    document.getElementById("thead").addEventListener("click", e => {
      const th = e.target.closest("th[data-key]");
      if (!th) return;
      const k = th.dataset.key;
      T.sortDir = k === T.sortKey ? -T.sortDir : 1;
      T.sortKey = k;
      header();
      T.render();
    });
  };

  function sortValues(key) {
    if (!T.sortVals[key]) {
      const col = App.columns.find(c => c.key === key);
      T.sortVals[key] = T.rows.map(col.sort);
    }
    return T.sortVals[key];
  }

  T.render = function () {
    const idx = [];
    for (let i = 0; i < T.rows.length; i++) if (App.filters.test(T.rows[i])) idx.push(i);
    const v = sortValues(T.sortKey), dir = T.sortDir;
    idx.sort((a, b) => (v[a] < v[b] ? -dir : v[a] > v[b] ? dir : a - b));
    T.view = idx;
    document.getElementById("tbody").innerHTML = idx.map(i => T.html[i]).join("");
    document.getElementById("empty").hidden = idx.length > 0;
    document.getElementById("count").textContent = `${idx.length.toLocaleString()} of ${T.rows.length.toLocaleString()} coins`;
    if (T.selected >= 0) T.highlight(T.selected, false);
  };

  // Select a row by its index into T.rows; scrolls it into view
  T.highlight = function (i, scroll = true) {
    T.selected = i;
    const body = document.getElementById("tbody");
    body.querySelectorAll("tr.sel").forEach(tr => tr.classList.remove("sel"));
    const tr = body.querySelector(`tr[data-i="${i}"]`);
    if (tr) {
      tr.classList.add("sel");
      if (scroll) tr.scrollIntoView({ block: "nearest" });
    }
  };

  // Move the selection up/down within the current (filtered, sorted) view
  T.step = function (delta) {
    if (!T.view.length) return null;
    const pos = T.view.indexOf(T.selected);
    const next = T.view[Math.max(0, Math.min(T.view.length - 1, pos < 0 ? 0 : pos + delta))];
    T.highlight(next);
    return next;
  };
})();
