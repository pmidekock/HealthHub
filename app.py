"""HealthHub — your fitness, body and sleep dashboard, live from Notion."""

import hmac
from html import escape

import pandas as pd
import streamlit as st

from src import charts, theme
from src import components as ui
from src.config import (DATA_SOURCES, FOCUS_ORDER, GOAL_EXERCISE_MIN, GOAL_MOVE_KCAL, GOAL_SESSIONS_WEEK,
                        GOAL_SLEEP_HOURS, GOAL_STAND_HRS, GOAL_STEPS, GOAL_SLEEP_MIN_NIGHT, NAME, REP_RANGE, SPORT_STYLE, START_DATE, TIMEZONE)
from src.demo_data import genereer
from src.notion_api import query_data_source
from src.transform import (overload_hint, pr_momenten, schoon_activiteit, records, schoon_fitness, schoon_lichaam,
                           schoon_slaap, sessies, slaap_vs_training, streak_days, streak_weeks)

st.set_page_config(page_title="HealthHub", page_icon=":material/favorite:", layout="wide",
                   initial_sidebar_state="collapsed")
theme.inject()
T = theme.tokens()


# ---------- Optional password gate (set APP_PASSWORD in secrets) ----------
def _gate():
    try:
        pw = st.secrets.get("APP_PASSWORD")
    except Exception:
        pw = None
    if not pw or st.session_state.get("auth_ok"):
        return
    ui.render('<p class="hh-top-date">HealthHub</p>'
              '<div class="hh-top-title" role="heading" aria-level="1">Welcome <em>back</em></div>')
    with st.form("login", border=False):
        entered = st.text_input("Password", type="password")
        if st.form_submit_button("Open dashboard"):
            if hmac.compare_digest(entered, str(pw)):
                st.session_state["auth_ok"] = True
                st.rerun()
            st.error("That password didn't match. Try again.")
    st.stop()


_gate()


# ---------- Data ----------
def _token():
    try:
        return st.secrets.get("NOTION_TOKEN")
    except Exception:
        return None


@st.cache_data(ttl=600, show_spinner="Syncing with Notion…")
def load_notion(token: str):
    return {k: query_data_source(token, v) for k, v in DATA_SOURCES.items()}


@st.cache_data
def load_demo():
    f, l, s, a = genereer()
    return {"fitness": f, "lichaam": l, "slaap": s, "activiteit": a}


token = _token()
demo = not token
try:
    raw = load_demo() if demo else load_notion(token)
except RuntimeError as e:
    st.error(f"We couldn't reach Notion. Check your token and connection. ({e})")
    st.stop()

fit_all = schoon_fitness(raw["fitness"])
body_all = schoon_lichaam(raw["lichaam"])
sleep_all = schoon_slaap(raw["slaap"])
act_all = schoon_activiteit(raw.get("activiteit", pd.DataFrame()))
if not demo:  # start fresh from START_DATE
    start = pd.Timestamp(START_DATE)
    fit_all = fit_all[fit_all["datum"] >= start].reset_index(drop=True)
    body_all = body_all[body_all["datum"] >= start].reset_index(drop=True)
    sleep_all = sleep_all[sleep_all["datum"] >= start].reset_index(drop=True)
    act_all = act_all[act_all["datum"] >= start].reset_index(drop=True)
sess_all = sessies(fit_all)
prs_all = pr_momenten(fit_all)

now = pd.Timestamp.now(tz=TIMEZONE)
today = now.normalize().tz_localize(None)
week_start = today - pd.Timedelta(days=today.dayofweek)
month_start = today.replace(day=1)


def when(d: pd.Timestamp) -> str:
    diff = (today - d).days
    return "Today" if diff == 0 else "Yesterday" if diff == 1 else f"{d:%a}, {d:%b} {d.day}" if diff < 7 else f"{d:%b} {d.day}"


def section(title: str, sub: str = ""):
    ui.render(f'<div class="hh-h2" role="heading" aria-level="2">{title}</div>' + (f'<p class="hh-h2-sub">{sub}</p>' if sub else ""))


def plot(fig):
    st.plotly_chart(fig, config=charts.config(), theme=None, width="stretch")


# ---------- Top ----------
greet = "morning" if now.hour < 12 else "afternoon" if now.hour < 18 else "evening"
top_l, top_r = st.columns([3, 2], vertical_alignment="bottom")
with top_l:
    ui.render(f'<p class="hh-top-date">{now:%A}, {now:%B} {now.day}</p>'
              f'<div class="hh-top-title" role="heading" aria-level="1">Good <em>{greet}</em>, {NAME}</div>')
with top_r:
    p_col, r_col = st.columns([5, 1], vertical_alignment="center")
    with p_col:
        period = st.segmented_control("Period", ["Week", "Month", "Quarter", "Year"], default="Month",
                                      label_visibility="collapsed", key="period") or "Month"
    if r_col.button(":material/refresh:", help="Fetch the latest data from Notion", key="refresh_top"):
        st.cache_data.clear()
        st.rerun()
if demo:
    ui.render('<p class="bl-note">You\'re looking at demo data. Add your Notion token to see your own.</p>')

days = {"Week": 7, "Month": 30, "Quarter": 91, "Year": 365}[period]
t0 = today - pd.Timedelta(days=days - 1)
fit = fit_all[fit_all["datum"] >= t0]
sess = sess_all[sess_all["datum"] >= t0]
body = body_all[body_all["datum"] >= t0 - pd.Timedelta(days=31)]  # monthly scans: keep one earlier point
sleep = sleep_all[sleep_all["datum"] >= t0]

# Week columns for the calendar and volume charts (at least 5, so cells stay compact) and the 8-week bars (from START_DATE)
_start = pd.Timestamp(START_DATE)
_first = (max(t0, _start) if not demo else t0)
_first_wk = _first - pd.Timedelta(days=_first.dayofweek)
chart_weeks = pd.date_range(end=week_start, periods=min(53, max(5, (week_start - _first_wk).days // 7 + 1)), freq="7D")
_sw_first = week_start - pd.Timedelta(weeks=7)
if not demo:
    _sw_first = max(_sw_first, _start - pd.Timedelta(days=_start.dayofweek))
sessions_weeks = pd.date_range(_sw_first, week_start, freq="7D")
days_tracked = days if demo else min(days, (today - _start).days + 1)
if not demo and days_tracked < days:
    ui.render(f'<p class="bl-note">Counting from {_start:%b} {_start.day}: {days_tracked} day{"s" if days_tracked != 1 else ""} of data so far.</p>')


# ---------- This week in one line ----------
_wk_parts = []
if not sess_all.empty or not demo:
    n_wk = int((sess_all["week"] == week_start).sum()) if not sess_all.empty else 0
    n_prev = int((sess_all["week"] == week_start - pd.Timedelta(days=7)).sum()) if not sess_all.empty else 0
    _wk_parts.append(f"{n_wk} of {GOAL_SESSIONS_WEEK} sessions" + (f" (last week {n_prev})" if n_prev else ""))
n_pr_wk = int((prs_all["datum"] >= week_start).sum() - prs_all.loc[prs_all["datum"] >= week_start, "vorig_max"].isna().sum()) \
    if ("vorig_max" in prs_all and not prs_all.empty) else 0
if n_pr_wk:
    _wk_parts.append(f"{n_pr_wk} new PR{'s' if n_pr_wk != 1 else ''}")
_sl_wk = sleep_all.loc[sleep_all["datum"] >= week_start, "uren"].dropna()
if not _sl_wk.empty:
    gap = _sl_wk.mean() - GOAL_SLEEP_HOURS
    _wk_parts.append(f"sleep averaging {_sl_wk.mean():.1f} h" + (f", {abs(gap):.1f} h under your goal" if gap < -0.05 else ", on goal"))
_act_wk = act_all[act_all["datum"] >= week_start].dropna(subset=["move"]) if not act_all.empty else act_all
if not _act_wk.empty:
    _wk_parts.append(f"move ring closed on {int((_act_wk['move'] >= GOAL_MOVE_KCAL).sum())} of {len(_act_wk)} logged days")
if _wk_parts:
    ui.render(f'<p class="bl-note"><b>This week</b> · {" · ".join(_wk_parts)}</p>')


# ---------- Rings (today) + active energy ----------
c1, c2 = st.columns(2)
with c1:
    day = act_all[act_all["datum"] == today]
    if day.empty and not act_all.empty:
        day = act_all.tail(1)
    if day.empty:
        ui.render(ui.card('<p class="bl-empty">Log your Apple Watch rings in Daily Activity to see them here.</p>',
                          title="Activity"))
    else:
        r = day.iloc[0]
        vals = [("move", r["move"], GOAL_MOVE_KCAL), ("exercise", r["exercise"], GOAL_EXERCISE_MIN),
                ("stand", r["stand"], GOAL_STAND_HRS)]
        closed = [n for n, v, g in vals if pd.notna(v) and v >= g]
        is_today = r["datum"] == today
        msg = ("You closed all three rings." if len(closed) == 3
               else f"You closed your {' and '.join(closed)} ring{'s' if len(closed) > 1 else ''}." if closed
               else "Every step counts. Your rings are filling up." if is_today
               else "Nothing logged for today yet.")
        ui.render(ui.card(
            ui.activity_rings([
                {"label": "Move", "value": round(r["move"] or 0), "goal": GOAL_MOVE_KCAL, "unit": "kcal", "tone": "move"},
                {"label": "Exercise", "value": round(r["exercise"] or 0), "goal": GOAL_EXERCISE_MIN, "unit": "min", "tone": "exercise"},
                {"label": "Stand", "value": round(r["stand"] or 0), "goal": GOAL_STAND_HRS, "unit": "hrs", "tone": "stand"},
            ]) + f'<p class="bl-note">{msg}</p>',
            title="Activity", sub="Today" if is_today else when(r["datum"])))
with c2:
    days7 = pd.date_range(today - pd.Timedelta(days=6), today)
    mv = act_all.set_index("datum")["move"].reindex(days7) if not act_all.empty else pd.Series(float("nan"), index=days7)
    bars = [{"label": f"{d:%a}", "value": float(v) if pd.notna(v) else 0.0, "missing": bool(pd.isna(v))} for d, v in mv.items()]
    ui.render(ui.card(ui.week_bars(bars, goal=GOAL_MOVE_KCAL, unit="kcal", tone="move"),
                      title="Active energy", sub="Last 7 days · dashed = not logged"))


# ---------- Metric tiles ----------
def body_tile(col: str, label: str, unit: str, tone: str, good_when_down: bool | None):
    d = body_all.dropna(subset=[col]) if col in body_all else pd.DataFrame()
    if d.empty:
        return ui.metric_card(label, "–", tone=tone)
    last = d[col].iat[-1]
    dl = ""
    if len(d) == 1:
        dl = ui.delta("First scan", f"on {d['datum'].iat[-1]:%b} {d['datum'].iat[-1].day}", trend="flat", good="neutral")
    if len(d) > 1:
        diff = last - d[col].iat[-2]
        tr = "up" if diff > 0.05 else "down" if diff < -0.05 else "flat"
        good = "neutral" if good_when_down is None else (tr == "down") == good_when_down if tr != "flat" else None
        dl = ui.delta(f"{diff:+.1f} {unit}".strip(), "vs last scan", trend=tr, good=good)
    return ui.metric_card(label, f"{last:.1f}", unit, tone, dl, d[col].tail(12).tolist())


s14 = sleep_all[sleep_all["datum"] > today - pd.Timedelta(days=14)]
this7 = s14[s14["datum"] > today - pd.Timedelta(days=7)]["uren"]
prev7 = s14[s14["datum"] <= today - pd.Timedelta(days=7)]["uren"]
if this7.notna().any():
    avg = this7.mean()
    val = f"{int(avg)}h {round((avg % 1) * 60):02d}m"
    n7 = int(this7.notna().sum())
    dl = ui.delta(f"{n7} of 7 nights", "logged", trend="flat", good="neutral") if n7 < 7 else ""
    if prev7.notna().any():
        diff = round((avg - prev7.mean()) * 60)
        dl = ui.delta(f"{diff:+d} min", "vs last week", trend="up" if diff > 0 else "down" if diff < 0 else "flat",
                      good=diff > 0 if diff else None)
    sleep_tile = ui.metric_card("Sleep · 7-day avg", val, "", "sleep", dl, s14["uren"].tolist())
else:
    last_s = sleep_all.dropna(subset=["uren"])
    note = (ui.delta("No nights logged this week", f"· last {when(last_s['datum'].iat[-1])}", trend="flat", good="neutral")
            if not last_s.empty else "")
    sleep_tile = ui.metric_card("Sleep · 7-day avg", "–", tone="sleep", dlt=note)

st7 = act_all[act_all["datum"] > today - pd.Timedelta(days=7)]["steps"].dropna() if not act_all.empty else pd.Series(dtype=float)
if st7.empty:
    last_st = act_all.dropna(subset=["steps"]) if not act_all.empty else pd.DataFrame()
    note = (ui.delta("No steps logged this week", f"· last {when(last_st['datum'].iat[-1])}", trend="flat", good="neutral")
            if not last_st.empty else "")
    steps_tile = ui.metric_card("Steps · 7-day avg", "–", tone="stand", dlt=note)
else:
    hit = int((st7 >= GOAL_STEPS).sum())
    steps_tile = ui.metric_card("Steps · 7-day avg", round(st7.mean()), "", "stand",
                                ui.delta(f"{hit} of {len(st7)} days", f"at {GOAL_STEPS:,}", trend="flat", good="neutral"),
                                act_all["steps"].tail(14).tolist())
m = st.columns(4)
for col, html in zip(m, [
    steps_tile,
    body_tile("gewicht", "Weight", "kg", "exercise", None),
    body_tile("vet_pct", "Body fat", "%", "move", True),
    sleep_tile,
]):
    with col:
        ui.render(html)

cov_days = 14 if demo else min(14, (today - _start).days + 1)
_cw = today - pd.Timedelta(days=cov_days - 1)


def _logged(df, col):
    return int(df.loc[df["datum"] >= _cw, col].notna().sum()) if (not df.empty and col in df) else 0


def _last(df, col):
    d = df.dropna(subset=[col]) if (not df.empty and col in df) else df.iloc[0:0]
    return when(d["datum"].max()) if not d.empty else "never"


_cover = [("Rings", _logged(act_all, "move"), cov_days), ("Steps", _logged(act_all, "steps"), cov_days),
          ("Sleep", _logged(sleep_all, "uren"), cov_days)]
ui.render(ui.coverage(_cover))
if any(got < tot for _, got, tot in _cover):
    ui.render(f'<p class="bl-note">Logged in the last {cov_days} days. Last entry: rings {_last(act_all, "move")} · '
              f'steps {_last(act_all, "steps")} · sleep {_last(sleep_all, "uren")}.</p>')


# ---------- Training ----------
section("Training", f"{len(sess)} session{'s' if len(sess) != 1 else ''} in the last {days} days · {sess['duur'].sum() / 60:.1f} hours of training")
c1, c2 = st.columns([2, 1])
with c1:
    rows = []
    for _, s in sess_all.sort_values("datum", ascending=False).head(6).iterrows():
        tone, ic = SPORT_STYLE.get(s["sport"], ("exercise", "run"))
        day_rows = fit_all[(fit_all["datum"] == s["datum"]) & (fit_all["sport"] == s["sport"])]
        if s["sport"] == "Gym":
            title = f"Strength · {s['focus']}"
        else:
            title = f"{s['sport']} · {day_rows['oefening'].iat[0]}" if not day_rows.empty else s["sport"]
        sub = when(s["datum"]) + (f" · {s['duur']:.0f} min" if pd.notna(s["duur"]) else "")
        n_pr = len(prs_all[(prs_all["datum"] == s["datum"]) & prs_all["vorig_max"].notna()]) if s["sport"] == "Gym" else 0
        meta = f"{n_pr} new PR{'s' if n_pr > 1 else ''}!" if n_pr else f"{int(s['n_oefeningen'])} exercise{'s' if int(s['n_oefeningen']) != 1 else ''}" if s["sport"] == "Gym" else ""
        if pd.notna(s["kcal"]):
            rows.append(ui.workout_row(title, sub, round(s["kcal"]), "kcal", meta, tone, ic))
        else:
            rows.append(ui.workout_row(title, sub, f"{s['volume']:,.0f}", "kg", meta or "volume", tone, ic))
    ui.render(ui.card(ui.row_list(rows), title="Recent workouts"))
with c2:
    dim = pd.Period(today, "M").days_in_month
    scale = dim / 7
    mo = sess_all[sess_all["datum"] >= month_start]
    act_mo = act_all[act_all["datum"] >= month_start]

    def ring_days(col, goal):
        return int((act_mo[col] >= goal).sum()) if not act_mo.empty else 0

    nights = sleep_all[(sleep_all["datum"] >= month_start) & (sleep_all["uren"] >= GOAL_SLEEP_MIN_NIGHT)]
    pace = today.day / dim  # share of the month that has passed
    ui.render(ui.card(
        '<div class="bl-stack">'
        + ui.goal_progress("Workouts", len(mo), round(GOAL_SESSIONS_WEEK * scale), "", "exercise", pace)
        + ui.goal_progress("Move ring closed", ring_days("move", GOAL_MOVE_KCAL), dim, "days", "move", pace)
        + ui.goal_progress("Exercise ring closed", ring_days("exercise", GOAL_EXERCISE_MIN), dim, "days", "exercise", pace)
        + ui.goal_progress("Stand ring closed", ring_days("stand", GOAL_STAND_HRS), dim, "days", "stand", pace)
        + ui.goal_progress(f"{GOAL_STEPS // 1000}k step days", ring_days("steps", GOAL_STEPS), dim, "days", "stand", pace)
        + ui.goal_progress(f"Nights {GOAL_SLEEP_MIN_NIGHT:g}h+", len(nights), dim, "", "sleep", pace)
        + '<p class="bl-note">The tick on each bar shows where you would be today if you were exactly on pace.</p>'
        + "</div>",
        title=f"{today:%B} goals", sub=f"Day {today.day} of {dim}"))

c1, c2 = st.columns(2)
with c1:
    per_week = (sess_all.groupby("week").size().reindex(sessions_weeks, fill_value=0) if not sess_all.empty
                else pd.Series(0, index=sessions_weeks))
    wb = [{"label": f"{w:%b} {w.day}", "value": int(v)} for w, v in per_week.items()]
    ui.render(ui.card(ui.week_bars(wb, goal=GOAL_SESSIONS_WEEK, unit="sessions", tone="exercise"),
                      title="Sessions per week", sub=f"Last {len(sessions_weeks)} week{'s' if len(sessions_weeks) != 1 else ''}"))
with c2:
    with st.container(key="card_calendar"):
        ui.render(ui.card_head("When you train", f"Last {days} days"))
        if sess.empty:
            ui.render('<p class="bl-empty">No sessions in this period yet.</p>')
        else:
            plot(charts.calendar(sess, chart_weeks, T))


# ---------- Streaks ----------
wk_cur, wk_best, wk_now = streak_weeks(sess_all, GOAL_SESSIONS_WEEK, week_start)
if not act_all.empty:
    _a = act_all.set_index("datum")
    rg_cur, rg_best = streak_days((_a["move"] >= GOAL_MOVE_KCAL) & (_a["exercise"] >= GOAL_EXERCISE_MIN) & (_a["stand"] >= GOAL_STAND_HRS), today)
    sp_cur, sp_best = streak_days(_a["steps"] >= GOAL_STEPS, today)
else:
    rg_cur = rg_best = sp_cur = sp_best = 0


def _unit(n, one):
    return one if n == 1 else one + "s"


s1, s2, s3 = st.columns(3)
with s1:
    ui.render(ui.metric_card(f"Weeks with {GOAL_SESSIONS_WEEK} sessions", wk_cur, _unit(wk_cur, "week"), "exercise",
                             ui.delta(f"{wk_now} of {GOAL_SESSIONS_WEEK} this week", f"· best {wk_best}", trend="flat", good="neutral")))
with s2:
    ui.render(ui.metric_card("All three rings closed", rg_cur, _unit(rg_cur, "day"), "move",
                             ui.delta("in a row", f"· best {rg_best}", trend="flat", good="neutral")))
with s3:
    ui.render(ui.metric_card(f"{GOAL_STEPS // 1000}k steps", sp_cur, _unit(sp_cur, "day"), "stand",
                             ui.delta("in a row", f"· best {sp_best}", trend="flat", good="neutral")))


# ---------- Strength ----------
section("Strength", "Your working weights, estimated max and personal records.")
gym = fit[(fit["sport"] == "Gym") & fit["gewicht"].notna()]
c1, c2 = st.columns([2, 1])
with c1:
    with st.container(key="card_progress"):
        if gym.empty:
            ui.render(ui.card_head("Progress per exercise") + '<p class="bl-empty">No gym sets in this period yet.</p>')
        else:
            f1, f2 = st.columns([1, 2])
            focuses = [f for f in FOCUS_ORDER if f in gym["focus"].unique()]
            focus = f1.selectbox("Focus", ["All"] + focuses)
            pool = gym if focus == "All" else gym[gym["focus"] == focus]
            exercise = f2.selectbox("Exercise", pool["oefening"].value_counts().index.tolist())
            plot(charts.exercise_progress(fit, exercise, prs_all, T))
            hint = overload_hint(fit_all, exercise, REP_RANGE)
            if hint:
                ui.render(f'<p class="bl-note"><b>Next time</b> · {escape(hint)} '
                          f'(double progression, {REP_RANGE[0]}-{REP_RANGE[1]} reps)</p>')
            if pool.loc[pool["oefening"] == exercise, "gewicht"].fillna(0).max() <= 0:
                ui.render('<p class="bl-note">Bodyweight exercise: progress is shown in reps.</p>')
            else:
                ui.render('<p class="bl-note">Est. 1RM uses the Epley formula: weight × (1 + reps / 30).</p>')
with c2:
    rec = records(fit_all)
    rows = []
    if not rec.empty:
        for _, r in rec.sort_values("PR date", ascending=False).head(6).iterrows():
            prog = r["Progress (%)"]
            rows.append(ui.workout_row(r["Exercise"], when(r['PR date']), f"{r['PR (kg)']:g}", "kg",
                                       f"+{prog:.0f}% since start" if prog and prog > 0 else "First logged" if r["Sessions"] <= 1 else "",
                                       "move", "strength"))
    ui.render(ui.card(ui.row_list(rows), title="Personal records", sub="Most recent first"))

if not sess[sess["sport"] == "Gym"].empty:
    with st.container(key="card_volume"):
        ui.render(ui.card_head("Weekly strength volume", "Sets × reps × kg"))
        plot(charts.weekly_volume(sess, chart_weeks, T))

gw = fit_all[(fit_all["sport"] == "Gym") & (fit_all["week"] >= chart_weeks[0])]
if not gw.empty:
    with st.container(key="card_focus"):
        ui.render(ui.card_head("Balance per muscle group", "Sets per week"))
        ymax = gw.groupby(["focus", "week"])["sets"].sum().max()
        ymax = float(ymax) if pd.notna(ymax) else 0.0
        for col, (foc, tone) in zip(st.columns(3), [("Glutes & Quads", "move"), ("Back & Biceps", "exercise"),
                                                    ("Shoulders Chest & Triceps", "stand")]):
            with col:
                n_sets = int(gw.loc[gw["focus"] == foc, "sets"].sum())
                ui.render(f'<div class="bl bl-tone-{tone}"><div class="bl-label"><span class="bl-dot"></span>{escape(foc)}</div>'
                          f'<p class="bl-note">{n_sets} set{"s" if n_sets != 1 else ""} in this period</p></div>')
                plot(charts.focus_sets(gw, chart_weeks, foc, tone, ymax, T))


# ---------- Body ----------
section("Body", "Every monthly scan from the body composition machine.")
if body_all.empty:
    ui.render(ui.card('<p class="bl-empty">No scans yet. Your first one is on the 1st.</p>'))
else:
    cols = st.columns(3)
    for col, (key, label, unit, tone) in zip(cols, [("gewicht", "Weight", "kg", "exercise"),
                                                    ("vet_pct", "Body fat", "%", "move"),
                                                    ("spier_pct", "Muscle mass", "%", "stand")]):
        with col:
            with st.container(key=f"card_body_{key}"):
                ui.render(ui.card_head(label))
                if key in body_all:
                    plot(charts.body_line(body_all.tail(12), key, unit, tone, T))

    last = body_all.dropna(subset=["gewicht"]).iloc[-1] if "gewicht" in body_all else None
    if last is not None:
        extra = f"BMI {last['bmi']:.1f}" + (f" · bone mass {last['bot_pct']:.1f}%" if pd.notna(last.get("bot_pct")) else "")
        ui.render(f'<p class="bl-note">{extra} · based on your height of 1.58 m.</p>')


# ---------- Sleep ----------
section("Sleep", "Recovery is part of the plan.")
if sleep.empty:
    ui.render(ui.card('<p class="bl-empty">No sleep logged in this period yet.</p>'))
else:
    c1, c2 = st.columns([2, 1])
    with c1:
        with st.container(key="card_sleep"):
            ui.render(ui.card_head("Hours slept", f"Last {days} days"))
            plot(charts.sleep_trend(sleep, GOAL_SLEEP_HOURS, T, GOAL_SLEEP_MIN_NIGHT))
    with c2:
        good_n = int((sleep["uren"] >= GOAL_SLEEP_MIN_NIGHT).sum())
        ui.render(ui.card(
            '<div class="bl-stack">'
            + f'<div class="bl-tone-sleep"><div class="bl-label"><span class="bl-dot"></span>Average</div>'
              f'<div class="bl-value bl-value-l">{sleep["uren"].mean():.1f}<span class="bl-unit">h</span></div></div>'
            + f'<div class="bl-tone-sleep"><div class="bl-label"><span class="bl-dot"></span>Quality</div>'
              f'<div class="bl-value bl-value-l">{ui.fmt(sleep["kwaliteit"].mean())}<span class="bl-unit">/ 10</span></div></div>'
            + ui.goal_progress(f"Nights {GOAL_SLEEP_MIN_NIGHT:g}h+", good_n, len(sleep), "", "sleep")
            + f'<p class="bl-note">{int(sleep["uren"].notna().sum())} of {days_tracked} nights logged.</p>'
            + "</div>", title="Your nights"))

    pair = slaap_vs_training(sess, sleep)
    if len(pair) < 5:
        ui.render(ui.card(f'<p class="bl-empty">This unlocks at 5 sessions with a sleep log from the same morning ({len(pair)} so far).</p>',
                          title="Does sleep move your training?"))
    else:
        with st.container(key="card_sleep_training"):
            ui.render(ui.card_head("Does sleep move your training?", f"{len(pair)} sessions"))
            pick = st.segmented_control("Compare with", ["Hours slept", "Sleep quality"], default="Hours slept",
                                        key="sleep_x", label_visibility="collapsed") or "Hours slept"
            xcol = "uren" if pick == "Hours slept" else "kwaliteit"
            pr = pair.dropna(subset=[xcol])
            ok = pr[[xcol, "kcal"]].dropna()
            if len(ok) >= 3 and ok[xcol].nunique() > 1 and ok["kcal"].nunique() > 1:
                r = ok.corr().iat[0, 1]
                strength = "barely" if abs(r) < 0.2 else "somewhat" if abs(r) < 0.5 else "clearly"
                direction = "more" if r > 0 else "fewer"
                nights = "longer nights" if xcol == "uren" else "better-rated nights"
                ui.render(f'<p class="bl-note">After {nights} you burn {strength} {direction} calories '
                          f'(r = {r:.2f}). Each dot is a session, placed by the sleep you logged that morning.</p>')
            else:
                ui.render('<p class="bl-note">Not enough variation yet to say anything. Each dot is a session.</p>')
            a, b = st.columns(2)
            with a:
                ui.render('<div class="bl"><div class="bl-label">Active energy</div></div>')
                plot(charts.sleep_vs(pr, "kcal", "kcal", "move", T, xcol))
            with b:
                g = pr[pr["sport"] == "Gym"]
                ui.render('<div class="bl"><div class="bl-label">Strength volume</div></div>')
                if len(g) >= 3:
                    plot(charts.sleep_vs(g, "volume", "kg", "exercise", T, xcol))
                else:
                    ui.render('<p class="bl-empty">Log a few more gym sessions to see this.</p>')


# ---------- Data ----------
section("Your data")
with st.expander("Browse and download"):
    choice = st.segmented_control("Table", ["Exercises", "Sessions", "Activity", "Body", "Sleep"], default="Sessions",
                                  key="table") or "Sessions"
    table = {"Exercises": fit, "Sessions": sess, "Activity": act_all, "Body": body, "Sleep": sleep}[choice]
    st.dataframe(table, hide_index=True, width="stretch")
    st.download_button("Download CSV", table.to_csv(index=False).encode("utf-8"),
                       file_name=f"healthhub-{choice.lower()}.csv", mime="text/csv")
st.caption("Demo data" if demo else "Synced from Notion · refreshes every 10 minutes, or use Refresh at the top")
