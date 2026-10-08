"""The monospace stats + zone table printed under each column of the zone chart."""
from charts.style import fmt_price


def stats_line(coin, quote, s):
    return (f"{coin}/{quote}  ATH {fmt_price(s['ath'], quote)} on {s['ath_date']:%Y-%m-%d} "
            f"({s['days_since_ath']:,}d ago{', LISTING-WEEK SPIKE' if s['ath_launch_week'] else ''})"
            f" · max drawdown {s['max_drawdown_pct']:.1f}% (low {fmt_price(s['low_after_ath'], quote)}"
            f" {s['low_after_ath_date']:%Y-%m-%d}) · now {s['current_drawdown_pct']:+.1f}% from ATH,"
            f" {s['bounce_from_low_pct']:+.0f}% off the low")


def zone_table(res, quote, max_daily=4, max_weekly=3):
    """Main zones first, then the biggest unbroken ones per timeframe."""
    lines = [f"{'':2}{'TF':<3}{'zone (bottom–top)':<26}{'formed':<11}{'move':>8}{'×ATR':>6} {'BOS':<4}{'taps':>4}"
             f"  {'status':<7}{'dist':>8}{'drop':>7}  {'W+D':<4}{'age':>5}"]
    for tf, n in (("W", max_weekly), ("D", max_daily)):
        zs = res[tf].zones
        keep = [z for z in zs if z.main or z.main_active] + sorted(
            [z for z in zs if z.status != "broken" and not (z.main or z.main_active)], key=lambda z: -z.move_pct)[:n]
        for z in keep:
            mark = "★ " if z.main else ("☆ " if z.main_active else "  ")
            zone = f"{fmt_price(z.bottom, quote)}–{fmt_price(z.top, quote)}"
            drop = f"{z.drop_to_zone_pct:.0f}%" if z.status != "broken" else ""
            lines.append(f"{mark}{z.tf:<3}{zone:<26}{z.formed:%Y-%m-%d} {z.move_pct:>7,.0f}%{z.move_atr:>6.0f} "
                         f"{'yes' if z.bos else 'no':<4}{z.taps:>4}  {z.status:<7}{z.dist_pct:>+7.0f}%{drop:>7}  "
                         f"{'yes' if z.confluence else '':<4}{z.age_days / 365:>4.1f}y")
    lines.append("★ main = origin of biggest move   ☆ biggest move whose zone is still unbroken")
    lines.append("dist = price vs zone (+ above / − below)   drop = move needed to reach the zone   W+D = weekly & daily overlap")
    return "\n".join(lines)
