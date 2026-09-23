"""HealthHub design system: tokens, global CSS and the active light/dark palette."""

import streamlit as st

LIGHT = {
    "bg": "#EEE4DA", "surface": "#FBF7F2", "surface-2": "#F3EBE3", "surface-3": "#EADFD3",
    "fill": "rgba(77,14,19,0.07)", "ink": "#2E1416", "ink-2": "#735754", "ink-3": "#A38C86",
    "separator": "#EADFD5", "creme": "#EEE4DA", "sand": "#D8C4AC", "dusty-pink": "#C8A49F",
    "burgundy": "#4D0E13", "move": "#4D0E13", "exercise": "#B5776F", "stand": "#A9804F",
    "sleep": "#8A7483", "accent": "#8B2E3A", "positive": "#6B7A4F", "warning": "#9A6A28",
    "negative": "#A8323E", "on-tone": "#FBF7F2",
    "shadow-card": "0 1px 2px rgba(77,14,19,0.05), 0 8px 24px rgba(77,14,19,0.06)",
    "shadow-float": "0 4px 16px rgba(77,14,19,0.12)", "seg-on": "#FBF7F2",
}
DARK = {
    "bg": "#1C0D0F", "surface": "#2A1417", "surface-2": "#361D21", "surface-3": "#4D2C31",
    "fill": "rgba(238,228,218,0.10)", "ink": "#EEE4DA", "ink-2": "#C9B3A8", "ink-3": "#9C8580",
    "separator": "#3D2226", "creme": "#EEE4DA", "sand": "#D8C4AC", "dusty-pink": "#C8A49F",
    "burgundy": "#4D0E13", "move": "#D9707C", "exercise": "#E2B5AE", "stand": "#D8C4AC",
    "sleep": "#B7A3B3", "accent": "#E6A1A8", "positive": "#A9B98A", "warning": "#D9A65E",
    "negative": "#EF8A8A", "on-tone": "#2A1417",
    "shadow-card": "none", "shadow-float": "0 4px 16px rgba(0,0,0,0.5)", "seg-on": "#4D2C31",
}
SCALE = {
    "space-1": "4px", "space-2": "8px", "space-3": "12px", "space-4": "16px", "space-5": "20px",
    "space-6": "24px", "space-8": "32px", "space-12": "48px",
    "radius-sm": "10px", "radius-md": "16px", "radius-xl": "24px", "radius-full": "999px",
    "font-sans": '"DM Sans", -apple-system, BlinkMacSystemFont, system-ui, sans-serif',
    "font-display": '"Fraunces", "Iowan Old Style", Georgia, serif',
}

FONTS = ("https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600"
         "&family=Fraunces:ital,opsz,wght@0,9..144,300..600;1,9..144,300..600&display=swap")


def mode() -> str:
    try:
        return "dark" if st.context.theme.type == "dark" else "light"
    except Exception:
        return "light"


def tokens() -> dict:
    return DARK if mode() == "dark" else LIGHT


def _vars(d: dict) -> str:
    return ";".join(f"--{k}:{v}" for k, v in d.items())


COMPONENT_CSS = """
.bl{font-family:var(--font-sans);color:var(--ink);-webkit-font-smoothing:antialiased}
.bl *{box-sizing:border-box}
.bl-tone-move{--tone:var(--move)}.bl-tone-exercise{--tone:var(--exercise)}.bl-tone-stand{--tone:var(--stand)}.bl-tone-sleep{--tone:var(--sleep)}.bl-tone-accent{--tone:var(--accent)}.bl-tone-warning{--tone:var(--warning)}
.bl-card{background:var(--surface);border-radius:var(--radius-xl);box-shadow:var(--shadow-card);padding:var(--space-5);display:flex;flex-direction:column;gap:var(--space-3);min-width:0;height:100%}
.bl-card-head{display:flex;align-items:baseline;justify-content:space-between;gap:var(--space-2)}
.bl-card-title{font:500 20px/26px var(--font-display);letter-spacing:-.2px;margin:0;color:var(--ink)}
.bl-card-sub{font:400 13px/18px var(--font-sans);color:var(--ink-2)}
.bl-label{font:600 11px/16px var(--font-sans);letter-spacing:1.2px;text-transform:uppercase;color:var(--ink-2);display:flex;align-items:center;gap:var(--space-2)}
.bl-dot{width:8px;height:8px;border-radius:var(--radius-full);background:var(--tone)}
.bl-value{font-family:var(--font-display);font-weight:500;color:var(--ink);font-variant-numeric:tabular-nums;display:flex;align-items:baseline;gap:var(--space-1)}
.bl-value-l{font-size:34px;line-height:40px;letter-spacing:-.3px;white-space:nowrap}
.bl-value-s{font-size:22px;line-height:28px;font-weight:500}
.bl-unit{font:500 15px/20px var(--font-sans);color:var(--ink-2)}
.bl-delta{font:400 13px/18px var(--font-sans);color:var(--ink-2);display:flex;align-items:center;gap:var(--space-1);white-space:nowrap}
.bl-arrow-up{color:var(--positive)}.bl-arrow-down{color:var(--negative)}.bl-arrow-flat{color:var(--ink-3)}
.bl-metric-row{display:flex;align-items:flex-end;justify-content:space-between;gap:var(--space-3)}
.bl-spark{flex:0 1 auto;min-width:40px;max-width:88px}.bl-spark path{fill:none;stroke:var(--tone);stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.bl-rings{display:flex;align-items:center;gap:var(--space-6);flex-wrap:wrap}
.bl-rings svg{flex:none;display:block}
.bl-ring-track{fill:none;stroke:var(--tone);opacity:.2}
.bl-ring-bar{fill:none;stroke:var(--tone);stroke-linecap:round}
.bl-rings-legend{display:flex;flex-direction:column;gap:var(--space-3)}
.bl-legend-value{font-family:var(--font-display);font-weight:500;font-size:22px;line-height:28px;color:var(--tone);font-variant-numeric:tabular-nums}
.bl-legend-goal{font:400 15px/20px var(--font-sans);color:var(--ink-2)}
.bl-progress{display:flex;flex-direction:column;gap:var(--space-2)}
.bl-progress-top{display:flex;justify-content:space-between;align-items:baseline;gap:var(--space-2)}
.bl-progress-name{font:600 15px/20px var(--font-sans);color:var(--ink)}
.bl-progress-num{font:400 15px/20px var(--font-sans);color:var(--ink-2);font-variant-numeric:tabular-nums}
.bl-progress-num b{color:var(--ink);font-weight:600}
.bl-track{height:8px;border-radius:var(--radius-full);background:var(--fill);overflow:hidden}
.bl-fill{height:100%;border-radius:var(--radius-full);background:var(--tone)}
.bl-stack{display:flex;flex-direction:column;gap:var(--space-4)}
.bl-bars{display:flex;flex-direction:column;gap:var(--space-2)}
.bl-bars-plot{position:relative;display:grid;grid-auto-flow:column;grid-auto-columns:1fr;align-items:end;gap:var(--space-2);height:150px;border-bottom:1px solid var(--separator)}
.bl-bar{background:var(--tone);border-radius:var(--radius-full) var(--radius-full) 4px 4px;min-height:4px;opacity:.9}
.bl-bar.is-dim{opacity:.38}.bl-bar.is-today{opacity:1}
.bl-goal-line{position:absolute;left:0;right:0;border-top:1.5px dotted var(--ink-3);pointer-events:none}
.bl-goal-tag{position:absolute;right:0;transform:translateY(-100%);font:600 11px/14px var(--font-sans);color:var(--ink-2);background:var(--surface);padding:0 0 2px 4px}
.bl-bars-axis{display:grid;grid-auto-flow:column;grid-auto-columns:1fr;gap:var(--space-2);font:400 12px/16px var(--font-sans);color:var(--ink-2);text-align:center}
.bl-bars-axis .is-today{color:var(--ink);font-weight:600}
.bl-list{display:flex;flex-direction:column}
.bl-row{display:flex;align-items:center;gap:var(--space-3);padding:var(--space-3) 0;border-top:1px solid var(--separator)}
.bl-row:first-child{border-top:0;padding-top:0}
.bl-row-icon{flex:none;width:36px;height:36px;border-radius:var(--radius-full);background:var(--tone);color:var(--on-tone);display:grid;place-items:center}
.bl-row-icon svg{width:18px;height:18px;fill:none;stroke:currentColor;stroke-width:1.9;stroke-linecap:round;stroke-linejoin:round}
.bl-row-main{flex:1;min-width:0}
.bl-row-title{font:600 16px/22px var(--font-sans);margin:0;color:var(--ink)}
.bl-row-sub{font:400 15px/20px var(--font-sans);color:var(--ink-2);margin:0}
.bl-row-stat{text-align:right}
.bl-row-stat .bl-value{justify-content:flex-end;color:var(--tone)}
.bl-empty{font:400 15px/20px var(--font-sans);color:var(--ink-2);padding:var(--space-4) 0}
.bl-note{font:400 13px/18px var(--font-sans);color:var(--ink-2);margin:0}
"""

PAGE_CSS = """
html,body,.stApp,[data-testid="stAppViewContainer"]{background:var(--bg)!important}
.stApp{font-family:var(--font-sans);color:var(--ink)}
[data-testid="stHeader"]{background:transparent}
[data-testid="stMainBlockContainer"],.block-container{max-width:1120px;padding:32px 24px 48px!important}
[data-testid="stVerticalBlock"],[data-testid="stHorizontalBlock"]{gap:12px}
.hh-top-date{font:600 11px/16px var(--font-sans);letter-spacing:1.2px;text-transform:uppercase;color:var(--ink-2);margin:0 0 6px}
.hh-top-title{font:400 40px/46px var(--font-display);letter-spacing:-.5px;margin:0;color:var(--ink)}
.hh-top-title em{font-style:italic;color:var(--accent)}
.hh-h2{font:400 24px/30px var(--font-display);margin:20px 0 0;color:var(--ink)}
.hh-h2-sub{font:400 15px/20px var(--font-sans);color:var(--ink-2);margin:4px 0 0}
[data-testid="stMarkdownContainer"] .bl p,[data-testid="stMarkdownContainer"] p.bl-note,[data-testid="stMarkdownContainer"] p.hh-top-date,[data-testid="stMarkdownContainer"] p.hh-h2-sub,[data-testid="stMarkdownContainer"] p.bl-empty{margin:0}
[data-testid="stMarkdownContainer"] p.bl-note,[data-testid="stMarkdownContainer"] .bl-note{font:400 13px/18px var(--font-sans)!important;color:var(--ink-2)}
[data-testid="stMarkdownContainer"] .bl-row-title{font:600 16px/22px var(--font-sans)!important}
[data-testid="stMarkdownContainer"] .bl-row-sub{font:400 15px/20px var(--font-sans)!important}
[data-testid="stMarkdownContainer"] .hh-top-date{font:600 11px/16px var(--font-sans)!important}
[data-testid="stMarkdownContainer"] .hh-h2-sub{font:400 15px/20px var(--font-sans)!important}
[data-testid="stMarkdownContainer"] .bl-empty{font:400 15px/20px var(--font-sans)!important}
[data-testid="stMarkdownContainer"]:has(.bl-card){height:100%}
[data-testid="stColumn"] [data-testid="stVerticalBlock"]:has(>[data-testid="stElementContainer"] .bl-card){height:100%}
[data-testid="stElementContainer"]:has(>[data-testid="stMarkdown"] .bl-card),[data-testid="stMarkdown"]:has(.bl-card){height:100%}
[data-testid="stMarkdownContainer"] div:has(>.bl-card){height:100%}
[data-testid="stMarkdownContainer"]{margin-bottom:0!important}
.hh-h2{margin-top:20px!important}
[data-testid="stElementContainer"]:has(.hh-h2){margin-top:8px}
/* Keyed containers become cards */
[class*="st-key-card"]{background:var(--surface);border-radius:var(--radius-xl);box-shadow:var(--shadow-card);padding:var(--space-5);gap:var(--space-3)}
[class*="st-key-card"] .bl-card{padding:0;box-shadow:none;background:transparent}
/* Segmented control -> pill */
[data-testid="stButtonGroup"] [role="radiogroup"],[data-testid="stButtonGroup"]>div{background:var(--fill);border-radius:var(--radius-full);padding:3px;gap:2px;display:inline-flex}
[data-testid="stButtonGroup"] button{font:500 13px/18px var(--font-sans)!important;color:var(--ink)!important;background:none!important;border:0!important;border-radius:var(--radius-full)!important;padding:6px 18px!important;min-height:0!important;box-shadow:none!important}
[data-testid="stButtonGroup"] button[kind$="Active"],[data-testid="stButtonGroup"] button[aria-checked="true"]{background:var(--seg-on)!important;box-shadow:var(--shadow-float)!important;font-weight:600!important}
[data-testid="stButtonGroup"] button p{font:inherit!important}
/* Inputs */
[data-baseweb="select"]>div{background:var(--surface-2)!important;border-color:transparent!important;border-radius:var(--radius-sm)!important}
[data-testid="stWidgetLabel"] p{font:600 11px/16px var(--font-sans)!important;letter-spacing:1.2px;text-transform:uppercase;color:var(--ink-2)!important}
.stButton button{border-radius:var(--radius-full);border:0;background:var(--fill);color:var(--ink);font:500 13px/18px var(--font-sans)}
.stButton button:hover{color:var(--accent);background:var(--fill)}
[data-testid="stExpander"] details{background:var(--surface);border:0;border-radius:var(--radius-xl);box-shadow:var(--shadow-card)}
[data-testid="stExpander"] summary p{font:500 20px/26px var(--font-display)}
[data-testid="stAlert"]{border-radius:var(--radius-md)}
@media (max-width:640px){[data-testid="stMainBlockContainer"],.block-container{padding:24px 16px 40px!important}.hh-top-title{font-size:32px;line-height:38px}}
"""


def inject():
    t = tokens()
    st.html(
        f"<style>@import url('{FONTS}');"
        f":root{{{_vars(t)};{_vars(SCALE)}}}"
        f"{COMPONENT_CSS}{PAGE_CSS}</style>"
    )
