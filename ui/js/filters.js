// Filter state, the predicate built from it, and the filter-bar bindings.
window.App = window.App || {};

(function () {
  const DEFAULTS = {
    search: "", scenario: "any", minScore: null, rankMax: null, minYears: null, hideStable: true,
    pair: "either", zoneTf: "any", maxDrop: null, inZone: false, fresh: false, conf: false,
    stW: "any", stD: "any", minDd: null, minAthDays: null, newHighs: false,
  };
  const STORE = "altscanner.filters";

  function load() {
    try { return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(STORE) || "{}") }; }
    catch { return { ...DEFAULTS }; }
  }
  function save(s) { try { localStorage.setItem(STORE, JSON.stringify(s)); } catch { /* private mode */ } }

  App.filters = { state: load(), DEFAULTS };

  // Does one pair's summary pass the pair-level filters?
  function pairPasses(p, s) {
    if (!p) return false;
    if (s.minYears != null && !(p.years >= s.minYears)) return false;
    if (s.stW !== "any" && p.st_w !== +s.stW) return false;
    if (s.stD !== "any" && p.st_d !== +s.stD) return false;
    if (s.minDd != null && !(p.dd_now <= -s.minDd)) return false;
    if (s.minAthDays != null && !(p.ath_days >= s.minAthDays)) return false;
    if (s.newHighs && !(p.ath_days <= 30)) return false;

    const zoneFilter = s.maxDrop != null || s.inZone || s.fresh || s.conf;
    if (!zoneFilter) return true;
    const zones = s.zoneTf === "w" ? [p.near_w] : s.zoneTf === "d" ? [p.near_d] : [p.near_w, p.near_d];
    return zones.some(z => z
      && (s.maxDrop == null || Math.abs(z.drop) <= s.maxDrop)
      && (!s.inZone || z.drop === 0)
      && (!s.fresh || z.status === "fresh")
      && (!s.conf || z.conf));
  }

  App.filters.test = function (r) {
    const s = App.filters.state;
    if (s.hideStable && r.stable) return false;
    const sc = r.score ? r.score.scenario : null;
    if (s.scenario === "S3S4" ? !(sc === "S3" || sc === "S4") : s.scenario !== "any" && sc !== s.scenario) return false;
    if (s.minScore != null && !(r.score && r.score.score >= s.minScore)) return false;
    if (s.rankMax != null && !(r.rank && r.rank <= s.rankMax)) return false;
    if (s.search) {
      const q = s.search.toLowerCase();
      if (!r.coin.toLowerCase().includes(q) && !(r.name || "").toLowerCase().includes(q)) return false;
    }
    const u = pairPasses(r.usd, s), b = pairPasses(r.btc, s);
    return s.pair === "usd" ? u : s.pair === "btc" ? b : s.pair === "both" ? u && b : u || b;
  };

  // Wire the filter bar; onChange() re-renders the table
  App.filters.bind = function (onChange) {
    const s = App.filters.state;
    const root = document.getElementById("filters");
    const sync = () => {
      root.querySelectorAll("[data-f]").forEach(el => {
        const k = el.dataset.f;
        if (el.classList.contains("seg")) el.querySelectorAll("button").forEach(b => b.classList.toggle("on", b.dataset.v === s[k]));
        else if (el.type === "checkbox") el.checked = !!s[k];
        else el.value = s[k] ?? "";
      });
      document.getElementById("search").value = s.search;
    };
    const set = (k, v) => { s[k] = v; save(s); onChange(); };

    root.addEventListener("input", e => {
      const el = e.target, k = el.dataset.f;
      if (!k) return;
      if (el.type === "checkbox") set(k, el.checked);
      else if (el.type === "number") set(k, el.value === "" ? null : +el.value);
      else set(k, el.value);
    });
    root.addEventListener("click", e => {
      const b = e.target.closest(".seg button");
      if (!b) return;
      const k = b.parentElement.dataset.f;
      b.parentElement.querySelectorAll("button").forEach(x => x.classList.toggle("on", x === b));
      set(k, b.dataset.v);
    });
    document.getElementById("search").addEventListener("input", e => set("search", e.target.value.trim()));
    document.getElementById("reset").addEventListener("click", () => {
      Object.assign(s, DEFAULTS); save(s); sync(); onChange();
    });
    sync();
  };
})();
