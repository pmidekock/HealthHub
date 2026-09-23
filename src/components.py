"""HealthHub components as HTML strings (port of the design system's components.js)."""

import math
from html import escape

import streamlit as st

ICONS = {
    "run": "M13 4.5a1.5 1.5 0 1 0 0 .01M7 21l3-6 3 2v5M6 12l3-4 4 1 3 4 3 1M10 15l-1-4",
    "strength": "M3 10v4M6 7v10M18 7v10M21 10v4M6 12h12",
    "bike": "M5.5 17.5a3.5 3.5 0 1 0 0-.01M18.5 17.5a3.5 3.5 0 1 0 0-.01M5.5 17.5L9 10h6l3.5 7.5M9 10l3 7.5M14 6h2l-1 4",
    "swim": "M2 18c2 0 2-1.5 4-1.5s2 1.5 4 1.5 2-1.5 4-1.5 2 1.5 4 1.5 2-1.5 4-1.5M8 14l3-6 4 2 2 4M15.5 5.5a1.5 1.5 0 1 0 0 .01",
    "yoga": "M12 4.5a1.5 1.5 0 1 0 0 .01M12 8v6M6 10l6-2 6 2M8 20l4-6 4 6",
    "walk": "M13 4.5a1.5 1.5 0 1 0 0 .01M10 21l2-7 3 3v4M9 10l3-2 3 3 3 1M9 10l-1 4",
    "heart": "M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z",
    "moon": "M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5z",
    "flame": "M12 21a6 6 0 0 0 6-6c0-4-3-6-4-9-1 2-2 3-3 3 0-2 0-3-1-5-2 3-4 6-4 11a6 6 0 0 0 6 6z",
}


def fmt(n, dec: int = 1) -> str:
    """Comma for thousands, dot for decimals, trailing .0 dropped."""
    if n is None or (isinstance(n, float) and math.isnan(n)):
        return "–"
    if not isinstance(n, (int, float)):
        return escape(str(n))
    s = f"{n:,.{dec}f}"
    return s[:-2] if dec == 1 and s.endswith(".0") else s


def render(html: str):
    # st.markdown keeps inline SVG (st.html strips it)
    st.markdown(html, unsafe_allow_html=True)


def icon(name: str) -> str:
    return f'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="{ICONS.get(name, ICONS["run"])}"/></svg>'


def card(body: str, title: str | None = None, sub: str | None = None) -> str:
    head = ""
    if title:
        head = f'<div class="bl-card-head"><div class="bl-card-title" role="heading" aria-level="3">{escape(title)}</div>' + (
            f'<span class="bl-card-sub">{escape(sub)}</span>' if sub else "") + "</div>"
    return f'<section class="bl bl-card">{head}{body}</section>'


def card_head(title: str, sub: str | None = None) -> str:
    return (f'<div class="bl bl-card-head"><div class="bl-card-title" role="heading" aria-level="3">{escape(title)}</div>'
            + (f'<span class="bl-card-sub">{escape(sub)}</span>' if sub else "") + "</div>")


def activity_rings(rings: list[dict], size: int = 176) -> str:
    stroke = round(size * 0.11)
    gap = max(2, round(stroke * 0.18))
    c = size / 2
    default = ["move", "exercise", "stand", "sleep"]
    parts, legend, aria = [], [], []
    for i, r in enumerate(rings):
        tone = r.get("tone", default[i])
        rad = c - stroke / 2 - i * (stroke + gap)
        circ = 2 * math.pi * rad
        pct = max(0.0, r["value"] / r["goal"]) if r["goal"] else 0
        g = (f'<g class="bl-tone-{tone}" transform="rotate(-90 {c} {c})">'
             f'<circle class="bl-ring-track" cx="{c}" cy="{c}" r="{rad:.1f}" stroke-width="{stroke}"/>'
             f'<circle class="bl-ring-bar" cx="{c}" cy="{c}" r="{rad:.1f}" stroke-width="{stroke}" '
             f'stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ * (1 - min(pct, 1)):.1f}"/>')
        if pct > 1:
            g += (f'<circle class="bl-ring-bar" cx="{c}" cy="{c}" r="{rad:.1f}" stroke-width="{stroke}" '
                  f'stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ * (1 - min(pct - 1, 1)):.1f}" '
                  f'style="filter:drop-shadow(0 0 2px rgba(60,20,40,.3))"/>')
        parts.append(g + "</g>")
        unit = r.get("unit", "")
        aria.append(f'{r["label"]} {fmt(r["value"])} of {fmt(r["goal"])} {unit}')
        legend.append(
            f'<div class="bl-tone-{tone}"><div class="bl-label">{escape(r["label"])}</div>'
            f'<div><span class="bl-legend-value">{fmt(r["value"])}</span>'
            f'<span class="bl-legend-goal">/{fmt(r["goal"])} {escape(unit)}</span></div></div>')
    svg = (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" role="img" '
           f'aria-label="{escape(", ".join(aria))}">{"".join(parts)}</svg>')
    return f'<div class="bl bl-rings">{svg}<div class="bl-rings-legend">{"".join(legend)}</div></div>'


def spark(data: list[float], w: int = 88, h: int = 36) -> str:
    d = [x for x in data if x is not None and not (isinstance(x, float) and math.isnan(x))]
    if len(d) < 2:
        return ""
    mn, mx = min(d), max(d)
    rg = (mx - mn) or 1
    pts = [(i * (w - 4) / (len(d) - 1) + 2, h - 2 - (v - mn) / rg * (h - 4)) for i, v in enumerate(d)]
    path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    return f'<svg class="bl-spark" width="{w}" height="{h}" viewBox="0 0 {w} {h}" aria-hidden="true"><path d="{path}"/></svg>'


def delta(value, label: str = "", trend: str | None = None, good: bool | None = None) -> str:
    if value is None:
        return ""
    if trend is None:
        trend = "up" if isinstance(value, (int, float)) and value > 0 else "down" if isinstance(value, (int, float)) and value < 0 else "flat"
    tone = "up" if good is True else "down" if good is False else "flat" if good == "neutral" else trend
    arrow = {"up": "▲", "down": "▼"}.get(trend, "–")
    txt = (("+" if value > 0 else "") + fmt(value)) if isinstance(value, (int, float)) else escape(str(value))
    return (f'<div class="bl-delta"><span class="bl-arrow-{tone if trend != "flat" else "flat"}" aria-hidden="true">{arrow}</span>'
            f'<span class="sr-only" style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0,0,0,0)">{trend}</span>'
            f'<span>{txt}{(" " + escape(label)) if label else ""}</span></div>')


def metric_card(label: str, value, unit: str = "", tone: str = "move", dlt: str = "", sparkline=None) -> str:
    return (f'<section class="bl bl-card bl-tone-{tone}">'
            f'<div class="bl-label"><span class="bl-dot"></span>{escape(label)}</div>'
            f'<div class="bl-metric-row"><div>'
            f'<div class="bl-value bl-value-l">{fmt(value) if not isinstance(value, str) else escape(value)}'
            + (f'<span class="bl-unit">{escape(unit)}</span>' if unit else "") + "</div>"
            f"{dlt}</div>{spark(sparkline) if sparkline else ''}</div></section>")


def goal_progress(label: str, value: float, goal: float, unit: str = "", tone: str = "accent") -> str:
    pct = max(0.0, min(1.0, value / goal)) if goal else 0
    return (f'<div class="bl bl-progress bl-tone-{tone}"><div class="bl-progress-top">'
            f'<span class="bl-progress-name">{escape(label)}</span>'
            f'<span class="bl-progress-num"><b>{fmt(value)}</b> / {fmt(goal)}{(" " + escape(unit)) if unit else ""}</span></div>'
            f'<div class="bl-track" role="progressbar" aria-valuemin="0" aria-valuemax="{goal}" aria-valuenow="{value}" aria-label="{escape(label)}">'
            f'<div class="bl-fill" style="width:{pct * 100:.1f}%"></div></div></div>')


def week_bars(data: list[dict], goal: float | None = None, unit: str = "", tone: str = "move", today_index: int | None = None) -> str:
    if not data:
        return '<p class="bl-empty">Nothing logged yet.</p>'
    mx = max([x["value"] for x in data] + [goal or 0]) * 1.1 or 1
    ti = len(data) - 1 if today_index is None else today_index
    bars = []
    for i, x in enumerate(data):
        cls = "bl-bar" + (" is-today" if i == ti else "") + (" is-dim" if goal and x["value"] < goal else "")
        bars.append(f'<div class="{cls}" style="height:{x["value"] / mx * 100:.1f}%" '
                    f'title="{escape(x["label"])}: {fmt(x["value"])} {escape(unit)}"></div>')
    gl = (f'<div class="bl-goal-line" style="bottom:{goal / mx * 100:.1f}%"><span class="bl-goal-tag">goal {fmt(goal)}</span></div>'
          if goal else "")
    axis = "".join(f'<span class="{"is-today" if i == ti else ""}">{escape(x["label"])}</span>' for i, x in enumerate(data))
    aria = ", ".join(f'{x["label"]} {fmt(x["value"])}' for x in data)
    return (f'<div class="bl bl-bars bl-tone-{tone}"><div class="bl-bars-plot" role="img" aria-label="{escape(aria)}">'
            f'{"".join(bars)}{gl}</div><div class="bl-bars-axis">{axis}</div></div>')


def workout_row(title: str, subtitle: str, value, unit: str = "", meta: str = "", tone: str = "exercise", ic: str = "run") -> str:
    return (f'<div class="bl bl-row bl-tone-{tone}"><div class="bl-row-icon">{icon(ic)}</div>'
            f'<div class="bl-row-main"><p class="bl-row-title">{escape(title)}</p><p class="bl-row-sub">{escape(subtitle)}</p></div>'
            f'<div class="bl-row-stat"><div class="bl-value bl-value-s">{fmt(value) if not isinstance(value, str) else escape(value)}'
            + (f'<span class="bl-unit">{escape(unit)}</span>' if unit else "") + "</div>"
            + (f'<div class="bl-delta" style="justify-content:flex-end">{escape(meta)}</div>' if meta else "")
            + "</div></div>")


def row_list(rows: list[str]) -> str:
    return f'<div class="bl bl-list">{"".join(rows)}</div>' if rows else '<p class="bl-empty">Nothing logged yet.</p>'
