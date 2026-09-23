"""HealthHub — your fitness, body and sleep dashboard, live from Notion."""

import pandas as pd
import streamlit as st

from src import charts, theme
from src import components as ui
from src.config import (DATA_SOURCES, FOCUS_ORDER, GOAL_EXERCISE_MIN, GOAL_MOVE_KCAL, GOAL_SESSIONS_WEEK,
                        GOAL_SLEEP_HOURS, GOAL_STAND_HRS, GOAL_STEPS, GOAL_SLEEP_MIN_NIGHT, NAME, SPORT_STYLE, START_DATE, TIMEZONE)
from src.demo_data import genereer
from src.notion_api import query_data_source
from src.transform import (pr_momenten, schoon_activiteit, records, schoon_fitness, schoon_lichaam, schoon_slaap,
                           sessies, slaap_vs_training)

st.set_page_config(page_title="HealthHub", page_icon=":material/favorite:", layout="wide",
                   initial_sidebar_state="collapsed")
theme.inject()
T = theme.tokens()


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
    period = st.segmented_control("Period", ["Week", "Month", "Quarter", "Year"], default="Month",
                                  label_visibility="collapsed", key="period") or "Month"
if demo:
    ui.render('<p class="bl-note">You\'re looking at demo data. Add your Notion token to see your own.</p>')

days = {"Week": 7, "Month": 30, "Quarter": 91, "Year": 365}[period]
t0 = today - pd.Timedelta(days=days - 1)
fit = fit_all[fit_all["datum"] >= t0]
sess = sess_all[sess_all["datum"] >= t0]
body = body_all[body_all["datum"] >= t0 - pd.Timedelta(days=31)]  # monthly scans: keep one earlier point
sleep = sleep_all[sleep_all["datum"] >= t0]


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
    mv = act_all.set_index("datum")["move"].reindex(days7).fillna(0) if not act_all.empty else pd.Series(0, index=days7)
    bars = [{"label": f"{d:%a}", "value": float(v)} for d, v in mv.items()]
    ui.render(ui.card(ui.week_bars(bars, goal=GOAL_MOVE_KCAL, unit="kcal", tone="move"),
                      title="Active energy", sub="Last 7 days"))


# ---------- Metric tiles ----------
def body_tile(col: str, label: str, unit: str, tone: str, good_when_down: bool | None):
    d = body_all.dropna(subset=[col]) if col in body_all else pd.DataFrame()
    if d.empty:
        return ui.metric_card(label, "–", tone=tone)
    last = d[col].iat[-1]
    dl = ""
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
    dl = ""
    if prev7.notna().any():
        diff = round((avg - prev7.mean()) * 60)
        dl = ui.delta(f"{diff:+d} min", "vs last week", trend="up" if diff > 0 else "down" if diff < 0 else "flat",
                      good=diff > 0 if diff else None)
    sleep_tile = ui.metric_card("Sleep · 7-day avg", val, "", "sleep", dl, s14["uren"].tolist())
else:
    sleep_tile = ui.metric_card("Sleep · 7-day avg", "–", tone="sleep")

st7 = act_all[act_all["datum"] > today - pd.Timedelta(days=7)]["steps"].dropna() if not act_all.empty else pd.Series(dtype=float)
if st7.empty:
    steps_tile = ui.metric_card("Steps · 7-day avg", "–", tone="stand")
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


# ---------- Training ----------
section("Training", f"{len(sess)} session{'s' if len(sess) != 1 else ''} in the last {days} days · {sess['duur'].sum() / 60:.1f} hours of work")
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
        meta = f"{n_pr} new PR{'s' if n_pr > 1 else ''}!" if n_pr else f"{s['n_oefeningen']} exercises" if s["sport"] == "Gym" else ""
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
    ui.render(ui.card(
        '<div class="bl-stack">'
        + ui.goal_progress("Workouts", len(mo), round(GOAL_SESSIONS_WEEK * scale), "", "exercise")
        + ui.goal_progress("Move ring closed", ring_days("move", GOAL_MOVE_KCAL), dim, "days", "move")
        + ui.goal_progress("Exercise ring closed", ring_days("exercise", GOAL_EXERCISE_MIN), dim, "days", "exercise")
        + ui.goal_progress("Stand ring closed", ring_days("stand", GOAL_STAND_HRS), dim, "days", "stand")
        + ui.goal_progress(f"{GOAL_STEPS // 1000}k step days", ring_days("steps", GOAL_STEPS), dim, "days", "stand")
        + ui.goal_progress(f"Nights {GOAL_SLEEP_MIN_NIGHT:g}h+", len(nights), dim, "", "sleep")
        + "</div>",
        title=f"{today:%B} goals", sub=f"Day {today.day} of {dim}"))

c1, c2 = st.columns(2)
with c1:
    weeks = pd.date_range(week_start - pd.Timedelta(weeks=7), week_start, freq="7D")
    per_week = sess_all.groupby("week").size().reindex(weeks, fill_value=0) if not sess_all.empty else pd.Series(0, index=weeks)
    wb = [{"label": f"{w:%b} {w.day}", "value": int(v)} for w, v in per_week.items()]
    ui.render(ui.card(ui.week_bars(wb, goal=GOAL_SESSIONS_WEEK, unit="sessions", tone="exercise"),
                      title="Sessions per week", sub="Last 8 weeks"))
with c2:
    with st.container(key="card_calendar"):
        ui.render(ui.card_head("When you train", f"Last {days} days"))
        if sess.empty:
            ui.render('<p class="bl-empty">No sessions in this period yet.</p>')
        else:
            plot(charts.calendar(sess, T))


# ---------- Strength ----------
section("Strength", "Your working weights, estimated max and personal records.")
gym = fit[(fit["sport"] == "Gym") & (fit["gewicht"] > 0)]
c1, c2 = st.columns([2, 1])
with c1:
    with st.container(key="card_progress"):
        if gym.empty:
            ui.render(ui.card_head("Progress per exercise") + '<p class="bl-empty">No weighted gym sets in this period yet.</p>')
        else:
            f1, f2 = st.columns([1, 2])
            focuses = [f for f in FOCUS_ORDER if f in gym["focus"].unique()]
            focus = f1.selectbox("Focus", ["All"] + focuses)
            pool = gym if focus == "All" else gym[gym["focus"] == focus]
            exercise = f2.selectbox("Exercise", pool["oefening"].value_counts().index.tolist())
            plot(charts.exercise_progress(fit, exercise, prs_all, T))
            ui.render('<p class="bl-note">Est. 1RM uses the Epley formula: weight × (1 + reps / 30).</p>')
with c2:
    rec = records(fit_all)
    rows = []
    if not rec.empty:
        for _, r in rec.sort_values("PR date", ascending=False).head(6).iterrows():
            prog = r["Progress (%)"]
            rows.append(ui.workout_row(r["Exercise"], when(r['PR date']), f"{r['PR (kg)']:g}", "kg",
                                       f"+{prog:.0f}% since start" if prog and prog > 0 else "", "move", "strength"))
    ui.render(ui.card(ui.row_list(rows), title="Personal records", sub="Most recent first"))

if not sess[sess["sport"] == "Gym"].empty:
    with st.container(key="card_volume"):
        ui.render(ui.card_head("Weekly strength volume", "Sets × reps × kg"))
        plot(charts.weekly_volume(sess, T))


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
            plot(charts.sleep_trend(sleep, GOAL_SLEEP_HOURS, T))
    with c2:
        good_n = int((sleep["uren"] >= GOAL_SLEEP_MIN_NIGHT).sum())
        ui.render(ui.card(
            '<div class="bl-stack">'
            + f'<div class="bl-tone-sleep"><div class="bl-label"><span class="bl-dot"></span>Average</div>'
              f'<div class="bl-value bl-value-l">{sleep["uren"].mean():.1f}<span class="bl-unit">h</span></div></div>'
            + f'<div class="bl-tone-sleep"><div class="bl-label"><span class="bl-dot"></span>Quality</div>'
              f'<div class="bl-value bl-value-l">{ui.fmt(sleep["kwaliteit"].mean())}<span class="bl-unit">/ 10</span></div></div>'
            + ui.goal_progress(f"Nights {GOAL_SLEEP_MIN_NIGHT:g}h+", good_n, len(sleep), "", "sleep")
            + "</div>", title="Your nights"))

    pair = slaap_vs_training(sess, sleep)
    if len(pair) >= 5:
        with st.container(key="card_sleep_training"):
            r = pair[["uren", "kcal"]].corr().iat[0, 1]
            strength = "barely" if abs(r) < 0.2 else "somewhat" if abs(r) < 0.5 else "clearly"
            direction = "more" if r > 0 else "fewer"
            ui.render(ui.card_head("Does sleep move your training?", f"{len(pair)} sessions")
                      + f'<p class="bl-note">After longer nights you burn {strength} {direction} calories '
                        f'(r = {r:.2f}). Each dot is a session, placed by the sleep you logged that morning.</p>')
            a, b = st.columns(2)
            with a:
                ui.render('<div class="bl"><div class="bl-label">Active energy</div></div>')
                plot(charts.sleep_vs(pair, "kcal", "kcal", "move", T))
            with b:
                g = pair[pair["sport"] == "Gym"]
                ui.render('<div class="bl"><div class="bl-label">Strength volume</div></div>')
                if len(g) >= 3:
                    plot(charts.sleep_vs(g, "volume", "kg", "exercise", T))
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
f1, f2 = st.columns([3, 1], vertical_alignment="center")
f1.caption("Demo data" if demo else "Synced from Notion · refreshes every 10 minutes")
if f2.button("Refresh now", width="stretch"):
    st.cache_data.clear()
    st.rerun()
