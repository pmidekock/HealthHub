# HealthHub Dashboard

A Streamlit dashboard that pulls live data from the Notion **Health Hub** (Fitness Tracker, Body Tracker, Sleep Tracker, Daily Activity).

Styled according to the **HealthHub design system** (cream/sand/dusty pink/burgundy, Fraunces + DM Sans, light & dark mode). UI text is in English.

**Page layout:** greeting + period selector (Week · Month · Quarter · Year) → today's Apple Watch rings (Move 500 kcal, Exercise 50 min, Stand 12 h) + active energy per day → 4 metric cards (steps, weight, body fat %, sleep) → Training (recent workouts, monthly goals incl. rings and 10k-step days, sessions per week, training calendar) → Strength (progression per exercise with PR stars and e1RM, recent PRs, weekly volume) → Body (all scans: weight, body fat %, muscle %, BMI, bone mass) → Sleep (hours slept, nights 7h+, sleep × training) → Your data (tables + CSV).

Without a token, the app runs in **demo mode** with synthetic data.

## Structure

```
app.py                 # Streamlit app (layout and sections)
src/config.py          # Notion data source IDs, goals, sport → colour/icon
src/theme.py           # design tokens (light/dark) + global CSS
src/components.py      # Card, ActivityRings, MetricCard, GoalProgress, WeekBars, WorkoutRow (HTML)
src/notion_api.py      # Notion REST API (v2025-09-03) + pagination
src/transform.py       # cleaning, sessions, PRs, BMI, sleep linking
src/charts.py          # Plotly charts
src/demo_data.py       # demo data when no token is set
.streamlit/config.toml # Streamlit theme (light + dark) and fonts
```

## 1. Create a Notion integration

1. Go to <https://www.notion.so/profile/integrations> → **New integration**.
2. Name: `Health Dashboard`, type **Internal**, choose your workspace → Save.
3. Capabilities: only **Read content** is needed.
4. Copy the **Internal Integration Secret** (starts with `ntn_`).
5. In Notion, open the **Health Hub** page → `•••` → **Connections** → add `Health Dashboard`. The databases underneath inherit the access.

## 2. Run locally

```bash
cd health-dashboard
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # fill in your token
streamlit run app.py
```

## 3. Push to GitHub

Create a **private** repo on GitHub (e.g. `health-dashboard`), without a README. Then:

```bash
cd health-dashboard
git init
git add .
git commit -m "Health Hub dashboard"
git branch -M main
git remote add origin https://github.com/<your-username>/health-dashboard.git
git push -u origin main
```

`secrets.toml` is listed in `.gitignore`, so your token never ends up on GitHub.

## 4. Streamlit Community Cloud

1. Go to <https://share.streamlit.io> → sign in with GitHub.
2. **Create app** → choose the repo, branch `main`, main file `app.py`.
3. **Advanced settings → Secrets**, paste:
   ```toml
   NOTION_TOKEN = "ntn_..."
   ```
4. Deploy. Then, under **Settings → Sharing**, set the app to *Only specific people* (just your email), since this is health data.

Every `git push` to `main` restarts the app automatically.

## Calculation assumptions

- **Session** = unique combination of date + sport. Duration and calories: the maximum within the session (they are sometimes entered on one exercise, sometimes on all).
- **Exercise** = the *Exercise* field, otherwise the *Name*.
- **PR** = heaviest weight per exercise; **e1RM** (Epley) = weight × (1 + reps/30). Exercises without weight (bodyweight) are not counted.
- **Sleep** on date X = the night before the training on date X.
- **BMI** uses a height of x m (adjustable in `src/config.py`).

## Customising

- Start date: `START_DATE` in `src/config.py` (currently 23-09-2026). Older rows stay in Notion but are not counted.
- Goals: `GOAL_*` in `src/config.py` (sessions, minutes and kcal per week, sleep). Monthly goals are derived from these.
- Light/dark follows your system setting; you can switch via the menu in the top right → Settings.
- New sport (e.g. kickboxing): add the option in Notion (*Sport Type*); the colour and icon are already set up in `SPORT_STYLE`.
- New database: add its data source ID to `DATA_SOURCES` and a `schoon_...` function in `transform.py`.

## Public repo + password

Streamlit Community Cloud only allows one *private* app per workspace. If you are already using that, set the repo to **public** and set `APP_PASSWORD` in Secrets: the app will then show a password screen first. The code contains no health data; that only comes in through your Notion token (which is stored in Secrets, not in the repo).
