# HealthHub Dashboard

Streamlit-dashboard dat live data uit de Notion **Health Hub** haalt (Fitness Tracker, Lichaam Tracker, Sleep Tracker, Daily Activity).

Vormgegeven volgens het **HealthHub design system** (creme/zand/dusty pink/bordeaux, Fraunces + DM Sans, light & dark mode). UI-teksten in het Engels.

**Opbouw van de pagina:** begroeting + periodekeuze (Week · Month · Quarter · Year) → Apple Watch-ringen van vandaag (Move 500 kcal, Exercise 50 min, Stand 12 u) + active energy per dag → 4 metric cards (stappen, gewicht, vet%, slaap) → Training (recente workouts, maanddoelen incl. ringen en 10k-stappendagen, sessies per week, trainingskalender) → Strength (progressie per oefening met PR-sterren en e1RM, recente PR's, weekvolume) → Body (alle scans: gewicht, vet%, spier%, BMI, botmassa) → Sleep (slaapuren, nachten 7u+, slaap × training) → Your data (tabellen + CSV).

Zonder token draait de app in **demo-modus** met synthetische data.

## Structuur

```
app.py                 # Streamlit-app (layout en secties)
src/config.py          # Notion data source IDs, doelen, sport → kleur/icoon
src/theme.py           # design tokens (light/dark) + globale CSS
src/components.py      # Card, ActivityRings, MetricCard, GoalProgress, WeekBars, WorkoutRow (HTML)
src/notion_api.py      # Notion REST API (v2025-09-03) + paginering
src/transform.py       # opschonen, sessies, PR's, BMI, slaapkoppeling
src/charts.py          # Plotly-grafieken
src/demo_data.py       # demo-data als er geen token is
.streamlit/config.toml # Streamlit-thema (light + dark) en fonts
```

## 1. Notion-integratie aanmaken

1. Ga naar <https://www.notion.so/profile/integrations> → **New integration**.
2. Naam: `Health Dashboard`, type **Internal**, workspace kiezen → Save.
3. Capabilities: alleen **Read content** is nodig.
4. Kopieer de **Internal Integration Secret** (begint met `ntn_`).
5. Open in Notion de pagina **Health Hub** → `•••` → **Connections** → voeg `Health Dashboard` toe. De drie databases eronder erven de toegang.

## 2. Lokaal draaien

```bash
cd health-dashboard
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # token invullen
streamlit run app.py
```

## 3. Naar GitHub

Maak op GitHub een **private** repo aan (bv. `health-dashboard`), zonder README. Dan:

```bash
cd health-dashboard
git init
git add .
git commit -m "Health Hub dashboard"
git branch -M main
git remote add origin https://github.com/<jouw-gebruikersnaam>/health-dashboard.git
git push -u origin main
```

`secrets.toml` staat in `.gitignore`: je token komt dus nooit in GitHub.

## 4. Streamlit Community Cloud

1. Ga naar <https://share.streamlit.io> → inloggen met GitHub.
2. **Create app** → kies de repo, branch `main`, main file `app.py`.
3. **Advanced settings → Secrets**, plak:
   ```toml
   NOTION_TOKEN = "ntn_..."
   ```
4. Deploy. Zet daarna bij **Settings → Sharing** de app op *Only specific people* (alleen jouw e-mail), want het gaat om gezondheidsdata.

Elke `git push` naar `main` herstart de app automatisch.

## Aannames in de berekeningen

- **Sessie** = unieke combinatie van datum + sport. Duur en calorieën: maximum binnen de sessie (ze staan soms op één oefening, soms op alle).
- **Oefening** = veld *Exercise*, anders de *Name*.
- **PR** = hoogste gewicht per oefening; **e1RM** (Epley) = gewicht × (1 + reps/30). Oefeningen zonder gewicht (bodyweight) tellen niet mee.
- **Slaap** op datum X = de nacht vóór de training op datum X.
- **BMI** met lengte 1,58 m (aan te passen in `src/config.py`).

## Aanpassen

- Startdatum: `START_DATE` in `src/config.py` (nu 23-09-2026). Oudere rijen blijven in Notion staan maar tellen niet mee.
- Doelen: `GOAL_*` in `src/config.py` (sessies, minuten en kcal per week, slaap). Maanddoelen worden daaruit afgeleid.
- Light/dark volgt je systeeminstelling; wisselen kan via het menu rechtsboven → Settings.
- Nieuwe sport (bv. kickboksen): voeg de optie toe in Notion (*Sport Type*); kleur en icoon staan al klaar in `SPORT_STYLE`.
- Nieuwe database: voeg het data source ID toe aan `DATA_SOURCES` en een `schoon_...`-functie in `transform.py`.
