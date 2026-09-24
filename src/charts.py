"""Plotly charts in the HealthHub style. One tone per chart, one y-axis, tokens from theme.py."""

import pandas as pd
import plotly.graph_objects as go

from src.config import DAYS_EN


def _rgba(hex_: str, a: float) -> str:
    h = hex_.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def _style(fig: go.Figure, t: dict, height: int = 300, legend: bool = False) -> go.Figure:
    fig.update_layout(
        height=height, margin=dict(l=8, r=8, t=8 if not legend else 36, b=8),
        font=dict(family="DM Sans, system-ui, sans-serif", size=12, color=t["ink-2"]),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        showlegend=legend, hovermode="x unified" if legend else "closest",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title=None, font=dict(color=t["ink-2"])),
        hoverlabel=dict(bgcolor=t["surface"], bordercolor=t["separator"], font=dict(family="DM Sans", color=t["ink"], size=12)),
        bargap=0.35,
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=t["separator"], tickfont=dict(color=t["ink-2"]),
                     ticks="", title=None, automargin=True)
    fig.update_yaxes(gridcolor=t["separator"], zeroline=False, tickfont=dict(color=t["ink-3"]), title=None, ticks="", automargin=True)
    return fig


def config() -> dict:
    return {"displayModeBar": False, "responsive": True}


def exercise_progress(fit: pd.DataFrame, exercise: str, prs: pd.DataFrame, t: dict) -> go.Figure:
    df = fit[fit["oefening"] == exercise].sort_values("datum")
    fig = go.Figure()
    if df["gewicht"].fillna(0).max() <= 0:
        # Bodyweight / no load: follow reps instead of kg
        fig.add_scatter(x=df["datum"], y=df["reps"], name="Reps", mode="lines+markers",
                        line=dict(color=t["move"], width=2), marker=dict(size=8, color=t["move"], line=dict(color=t["surface"], width=2)),
                        customdata=df[["sets"]], hovertemplate="%{customdata[0]:.0f}×%{y:.0f} reps · bodyweight")
        fig.update_yaxes(ticksuffix=" reps", rangemode="tozero")
    else:
        fig.add_scatter(x=df["datum"], y=df["e1rm"], name="Est. 1RM", mode="lines",
                        line=dict(color=t["ink-3"], width=1.5, dash="dot"), hovertemplate="%{y:.1f} kg")
        fig.add_scatter(x=df["datum"], y=df["gewicht"], name="Working weight", mode="lines+markers",
                        line=dict(color=t["move"], width=2), marker=dict(size=8, color=t["move"], line=dict(color=t["surface"], width=2)),
                        customdata=df[["sets", "reps"]], hovertemplate="%{y} kg · %{customdata[0]:.0f}×%{customdata[1]:.0f}")
        p = prs[(prs["oefening"] == exercise) & (prs["datum"] >= df["datum"].min())]
        fig.add_scatter(x=p["datum"], y=p["gewicht"], name="Personal record", mode="markers",
                        marker=dict(size=13, symbol="star", color=t["accent"], line=dict(color=t["surface"], width=1.5)),
                        hovertemplate="PR %{y} kg")
        fig.update_yaxes(ticksuffix=" kg")
    _date_axis(fig, df["datum"])
    return _style(fig, t, 320, legend=True)


def _date_axis(fig: go.Figure, dates: pd.Series) -> None:
    """Always show whole dates; pad the range so one or two points don't zoom to milliseconds."""
    d = pd.to_datetime(dates).dropna()
    fig.update_xaxes(type="date", tickformat="%b %-d", hoverformat="%a %b %-d")
    if d.empty:
        return
    lo, hi = d.min(), d.max()
    if (hi - lo) < pd.Timedelta(days=7):
        mid = lo + (hi - lo) / 2
        lo, hi = mid - pd.Timedelta(days=4), mid + pd.Timedelta(days=4)
        fig.update_xaxes(range=[lo, hi], dtick=86400000)


def weekly_volume(sess: pd.DataFrame, t: dict) -> go.Figure:
    g = sess[sess["sport"] == "Gym"].groupby("week")["volume"].sum().reset_index()
    fig = go.Figure(go.Bar(x=g["week"], y=g["volume"], marker=dict(color=t["move"], cornerradius=6),
                           hovertemplate="Week of %{x|%b %d}<br>%{y:,.0f} kg<extra></extra>"))
    fig.update_xaxes(tickformat="%b %-d")
    return _style(fig, t, 260)


def calendar(sess: pd.DataFrame, t: dict) -> go.Figure:
    df = sess.groupby(["week", "dag_en"]).size().reset_index(name="n")
    piv = df.pivot(index="dag_en", columns="week", values="n").reindex(DAYS_EN).fillna(0)
    fig = go.Figure(go.Heatmap(
        z=piv.values.clip(0, 1), x=piv.columns, y=piv.index, zmin=0, zmax=1,
        colorscale=[[0, t["fill"]], [1, t["exercise"]]], showscale=False, xgap=4, ygap=4,
        customdata=piv.values, hovertemplate="Week of %{x|%b %d} · %{y}<br>%{customdata:.0f} session(s)<extra></extra>",
    ))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    fig.update_xaxes(tickformat="%b %-d")
    return _style(fig, t, 230)


def body_line(lich: pd.DataFrame, col: str, unit: str, tone: str, t: dict) -> go.Figure:
    df = lich.dropna(subset=[col])
    fig = go.Figure(go.Scatter(
        x=df["datum"], y=df[col], mode="lines+markers", line=dict(color=t[tone], width=2),
        marker=dict(size=8, color=t[tone], line=dict(color=t["surface"], width=2)),
        hovertemplate=f"%{{x|%b %d, %Y}}<br>%{{y:.1f}} {unit}<extra></extra>"))
    fig.update_xaxes(tickformat="%b", dtick="M1")
    fig.update_yaxes(ticksuffix=f" {unit}")
    return _style(fig, t, 220)


def sleep_trend(slaap: pd.DataFrame, goal: float, t: dict) -> go.Figure:
    df = slaap.copy()
    df["avg7"] = df["uren"].rolling(7, min_periods=3).mean()
    fig = go.Figure()
    fig.add_bar(x=df["datum"], y=df["uren"], name="Hours slept",
                marker=dict(color=_rgba(t["sleep"], 0.38) if t["sleep"].startswith("#") else t["sleep"], cornerradius=4),
                hovertemplate="%{y:.1f} h")
    fig.add_scatter(x=df["datum"], y=df["avg7"], name="7-day average", mode="lines",
                    line=dict(color=t["sleep"], width=2.5), hovertemplate="%{y:.1f} h")
    fig.add_hline(y=goal, line_dash="dot", line_color=t["ink-3"], line_width=1.5,
                  annotation_text=f"goal {goal:g} h", annotation_position="top right",
                  annotation_font=dict(color=t["ink-2"], size=11))
    fig.update_xaxes(tickformat="%b %-d")
    fig.update_yaxes(ticksuffix=" h")
    fig.update_layout(bargap=0.2)
    return _style(fig, t, 300, legend=True)


def sleep_vs(koppel: pd.DataFrame, y: str, unit: str, tone: str, t: dict) -> go.Figure:
    fig = go.Figure(go.Scatter(
        x=koppel["uren"], y=koppel[y], mode="markers",
        marker=dict(size=10, color=t[tone], opacity=0.8, line=dict(color=t["surface"], width=1.5)),
        hovertemplate=f"%{{x:.1f}} h sleep<br>%{{y:,.0f}} {unit}<extra></extra>"))
    fig.update_xaxes(ticksuffix=" h", title=dict(text="Sleep the night before", font=dict(color=t["ink-2"], size=12)))
    return _style(fig, t, 260)
