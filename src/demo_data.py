"""Synthetische demo-data in hetzelfde formaat als de Notion API-output.

Wordt gebruikt als er geen NOTION_TOKEN is ingesteld, zodat het dashboard
ook zonder koppeling te bekijken en te testen is.
"""

import numpy as np
import pandas as pd

OEFENINGEN = {
    "Glutes & Quads": [("Hip thrust", 40, 2.0), ("Bulgarian split squat", 8, 0.5), ("Leg press", 60, 2.5), ("Cable kickback", 7, 0.3)],
    "Back & Biceps": [("Wide grip lat pulldown", 25, 0.6), ("Close grip lat pulldown", 25, 0.5), ("Face pulls", 13.6, 0.3), ("Diverging seated row", 18, 0.6)],
    "Shoulders Chest & Triceps": [("Shoulder press", 8, 0.3), ("Chest press", 15, 0.5), ("Tricep pushdown", 9, 0.3), ("Lateral raise", 4, 0.1)],
}
PILATES_LESSEN = ["PA Form", "PA Force", "PA Flow"]


def genereer(dagen: int = 180, seed: int = 7):
    rng = np.random.default_rng(seed)
    eind = pd.Timestamp.today().normalize()
    datums = pd.date_range(eind - pd.Timedelta(days=dagen), eind)
    fit, slaap, act = [], [], []
    rotatie = list(OEFENINGEN)
    r_i = 0
    for i, d in enumerate(datums):
        slaap.append({"Date": d.date().isoformat(), "Hours Slept": round(float(rng.normal(7.3, 0.8)), 1), "Quality (1-10)": int(np.clip(rng.normal(7, 1.4), 2, 10))})
        act.append({"Date": d.date().isoformat(), "Move (kcal)": int(rng.normal(520, 110)), "Exercise (min)": int(max(5, rng.normal(48, 18))),
                    "Stand (hrs)": int(np.clip(rng.normal(11, 1.5), 4, 16)), "Steps": int(max(2000, rng.normal(9000, 2500)))})
        wd = d.dayofweek
        if wd in (2, 4) and rng.random() < 0.85:
            fit.append({"Name": rng.choice(PILATES_LESSEN), "Date": d.date().isoformat(), "Sport Type": "Reformer Pilates",
                        "Duration (min)": round(float(rng.normal(51, 1.5)), 1), "Calorieën": int(rng.normal(285, 20)), "Intensity": "Medium"})
        elif wd in (0, 1, 3, 5) and rng.random() < 0.75:
            focus = rotatie[r_i % 3]
            r_i += 1
            duur, kcal = round(float(rng.normal(62, 6)), 1), int(rng.normal(430, 40))
            for j, (naam, basis, stap) in enumerate(OEFENINGEN[focus]):
                gewicht = round(basis + stap * (i / 7) * rng.uniform(0.7, 1.1), 1)
                fit.append({"Name": naam, "Date": d.date().isoformat(), "Sport Type": "Gym", "Training Focus": focus,
                            "Sets": int(rng.choice([3, 4])), "Reps": int(rng.choice([8, 10, 12])), "Weight (kg)": gewicht,
                            "Duration (min)": duur if j == 0 else None, "Calorieën": kcal if j == 0 else None,
                            "Intensity": rng.choice(["Medium", "High"], p=[0.6, 0.4])})
    lichaam = []
    for k, d in enumerate(pd.date_range(eind - pd.Timedelta(days=dagen), eind, freq="MS")):
        lichaam.append({"Date": d.date().isoformat(), "Weight (kg)": round(62 - 0.25 * k + rng.normal(0, 0.3), 1),
                        "Vestmassa (%)": round(30 - 0.5 * k + rng.normal(0, 0.3), 1), "Spiermassa (%)": round(31 + 0.35 * k + rng.normal(0, 0.2), 1),
                        "Botmassa (%)": round(4.1 + rng.normal(0, 0.05), 2), "Waist (cm)": round(74 - 0.5 * k, 1), "Hips (cm)": round(99 + 0.2 * k, 1),
                        "Thigh (cm)": round(57 + 0.1 * k, 1), "Chest (cm)": round(88 - 0.1 * k, 1)})
    return pd.DataFrame(fit), pd.DataFrame(lichaam), pd.DataFrame(slaap), pd.DataFrame(act)
