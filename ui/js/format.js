// Formatting + heat-colour classes. Display only: every number arrives precomputed.
window.App = window.App || {};

App.fmt = {
  price(v, quote) {
    if (v == null) return "–";
    if (quote === "btc") {
      if (v >= 0.01) return v.toPrecision(4) + " ₿";
      const s = v * 1e8;
      return (s >= 100 ? Math.round(s).toLocaleString() : s.toPrecision(3)) + " sat";
    }
    if (v >= 1000) return "$" + Math.round(v).toLocaleString();
    return "$" + Number(v.toPrecision(4));
  },
  pct(v, digits = 0) {
    if (v == null) return "–";
    const d = Math.abs(v) > 99 && Math.abs(v) < 100 ? Math.max(digits, 1) : digits;  // -99.8%, not -100%
    return (v > 0 ? "+" : "") + v.toFixed(d) + "%";
  },
  mcap(v) {
    if (!v) return "–";
    if (v >= 1e12) return "$" + (v / 1e12).toFixed(2) + "T";
    if (v >= 1e9) return "$" + (v / 1e9).toFixed(v >= 1e11 ? 0 : 1) + "B";
    return "$" + Math.round(v / 1e6) + "M";
  },
  days(d) {
    if (d == null) return "–";
    if (d < 60) return d + "d";
    if (d < 730) return Math.round(d / 30.4) + "mo";
    return (d / 365).toFixed(1) + "y";
  },
};

// Nearness to a zone: 0% (in zone) = strongest aqua
App.heatZone = drop => {
  if (drop == null) return "";
  const d = Math.abs(drop);
  return d === 0 ? "z0" : d <= 5 ? "z1" : d <= 15 ? "z2" : d <= 30 ? "z3" : d <= 50 ? "z4" : "";
};

// Distance below ATH: deeper = stronger red
App.heatDd = dd => {
  if (dd == null) return "";
  const d = -dd;
  return d >= 95 ? "d5" : d >= 85 ? "d4" : d >= 70 ? "d3" : d >= 50 ? "d2" : d >= 25 ? "d1" : "";
};

// Setup score 0-100: higher = stronger violet
App.heatScore = s => s == null ? "" : s >= 85 ? "s4" : s >= 70 ? "s3" : s >= 55 ? "s2" : s >= 40 ? "s1" : "";

App.esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
