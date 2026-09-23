"""Opschonen en afleiden van analyse-tabellen uit de ruwe Notion-data."""

import numpy as np
import pandas as pd

from src.config import DAYS_EN, HEIGHT_M as LENGTE_M, INTENSITEIT_VOLGORDE

DAGEN_NL = {0: "Ma", 1: "Di", 2: "Wo", 3: "Do", 4: "Vr", 5: "Za", 6: "Zo"}


def _kolom(df: pd.DataFrame, naam: str):
    return df[naam] if naam in df.columns else pd.Series([None] * len(df), index=df.index)


def schoon_fitness(ruw: pd.DataFrame) -> pd.DataFrame:
    """Eén rij per oefening (gym) of per les (pilates)."""
    if ruw.empty:
        return pd.DataFrame(columns=["datum", "oefening", "sport", "focus"])
    df = pd.DataFrame({
        "datum": pd.to_datetime(_kolom(ruw, "Date"), errors="coerce").dt.tz_localize(None).dt.normalize(),
        "naam": _kolom(ruw, "Name"),
        "exercise": _kolom(ruw, "Exercise"),
        "sport": _kolom(ruw, "Sport Type"),
        "focus": _kolom(ruw, "Training Focus"),
        "sets": pd.to_numeric(_kolom(ruw, "Sets"), errors="coerce"),
        "reps": pd.to_numeric(_kolom(ruw, "Reps"), errors="coerce"),
        "gewicht": pd.to_numeric(_kolom(ruw, "Weight (kg)"), errors="coerce"),
        "duur": pd.to_numeric(_kolom(ruw, "Duration (min)"), errors="coerce"),
        "kcal": pd.to_numeric(_kolom(ruw, "Calorieën"), errors="coerce"),
        "intensiteit": _kolom(ruw, "Intensity"),
        "pilates_les": _kolom(ruw, "Pilates Les"),
        "notities": _kolom(ruw, "Notes"),
    })
    df = df.dropna(subset=["datum"])
    df["oefening"] = df["exercise"].fillna(df["naam"]).fillna("Onbekend").str.strip()
    df["sport"] = df["sport"].fillna("Overig")
    df["focus"] = np.where(df["sport"].eq("Reformer Pilates"), "Pilates", df["focus"].fillna("Overig"))
    df["volume"] = (df["sets"].fillna(0) * df["reps"].fillna(0) * df["gewicht"].fillna(0))
    df["e1rm"] = np.where(df["gewicht"] > 0, df["gewicht"] * (1 + df["reps"].fillna(1) / 30), np.nan)
    df["week"] = df["datum"].dt.to_period("W-SUN").dt.start_time
    df["dag"] = df["datum"].dt.dayofweek.map(DAGEN_NL)
    return df.drop(columns=["exercise", "naam"]).sort_values("datum").reset_index(drop=True)


def sessies(fit: pd.DataFrame) -> pd.DataFrame:
    """Eén rij per trainingssessie (datum + sport).

    Duur en calorieën staan soms op één oefening, soms op alle oefeningen
    van een sessie; daarom nemen we het maximum per sessie.
    """
    if fit.empty:
        return pd.DataFrame(columns=["datum", "sport", "focus", "duur", "kcal", "volume", "n_oefeningen", "intensiteit", "week", "dag", "dag_en"])
    rang = {v: i for i, v in enumerate(INTENSITEIT_VOLGORDE)}
    tmp = fit.assign(int_rang=fit["intensiteit"].map(rang))
    s = tmp.groupby(["datum", "sport"], as_index=False).agg(
        focus=("focus", lambda x: x.mode().iat[0] if not x.mode().empty else "Overig"),
        duur=("duur", "max"),
        kcal=("kcal", "max"),
        volume=("volume", "sum"),
        n_oefeningen=("oefening", "nunique"),
        int_rang=("int_rang", "max"),
    )
    s["intensiteit"] = s["int_rang"].map(dict(enumerate(INTENSITEIT_VOLGORDE)))
    s["week"] = s["datum"].dt.to_period("W-SUN").dt.start_time
    s["dag"] = s["datum"].dt.dayofweek.map(DAGEN_NL)
    s["dag_en"] = s["datum"].dt.dayofweek.map(dict(enumerate(DAYS_EN)))
    return s.drop(columns="int_rang").sort_values("datum").reset_index(drop=True)


def records(fit: pd.DataFrame) -> pd.DataFrame:
    """PR-overzicht per oefening (alleen oefeningen met gewicht)."""
    g = fit[(fit["sport"] == "Gym") & (fit["gewicht"] > 0)]
    if g.empty:
        return pd.DataFrame()
    idx = g.groupby("oefening")["gewicht"].idxmax()
    pr = g.loc[idx, ["oefening", "focus", "gewicht", "reps", "datum"]].rename(
        columns={"gewicht": "PR (kg)", "reps": "Reps at PR", "datum": "PR date"}
    )
    eerste = g.sort_values("datum").groupby("oefening")["gewicht"].first().rename("First (kg)")
    laatste = g.sort_values("datum").groupby("oefening")["gewicht"].last().rename("Latest (kg)")
    e1rm = g.groupby("oefening")["e1rm"].max().round(1).rename("Best e1RM (kg)")
    keer = g.groupby("oefening")["datum"].nunique().rename("Sessions")
    out = pr.set_index("oefening").join([eerste, laatste, e1rm, keer]).reset_index()
    out["Progress (%)"] = ((out["Latest (kg)"] / out["First (kg)"] - 1) * 100).round(1)
    return out.rename(columns={"oefening": "Exercise", "focus": "Focus"}).sort_values(["Focus", "Exercise"])


def pr_momenten(fit: pd.DataFrame) -> pd.DataFrame:
    """Alle momenten waarop een nieuw gewichtsrecord werd gezet."""
    g = fit[(fit["sport"] == "Gym") & (fit["gewicht"] > 0)].sort_values("datum")
    if g.empty:
        return g
    g = g.assign(vorig_max=g.groupby("oefening")["gewicht"].transform(lambda x: x.cummax().shift()))
    return g[g["vorig_max"].isna() | (g["gewicht"] > g["vorig_max"])]


def schoon_lichaam(ruw: pd.DataFrame) -> pd.DataFrame:
    if ruw.empty:
        return pd.DataFrame(columns=["datum", "gewicht"])
    kol = {
        "Weight (kg)": "gewicht", "Vestmassa (%)": "vet_pct", "Vetmassa (%)": "vet_pct",
        "Spiermassa (%)": "spier_pct", "Botmassa (%)": "bot_pct",
        "Waist (cm)": "taille", "Hips (cm)": "heup", "Thigh (cm)": "dij", "Chest (cm)": "borst",
    }
    df = pd.DataFrame({"datum": pd.to_datetime(_kolom(ruw, "Date"), errors="coerce").dt.tz_localize(None).dt.normalize()})
    for bron, doel in kol.items():
        if bron in ruw.columns:
            df[doel] = pd.to_numeric(ruw[bron], errors="coerce")
    df = df.dropna(subset=["datum"]).sort_values("datum").reset_index(drop=True)
    if "gewicht" in df:
        df["bmi"] = (df["gewicht"] / LENGTE_M ** 2).round(1)
        if "vet_pct" in df:
            df["vetmassa_kg"] = (df["gewicht"] * df["vet_pct"] / 100).round(1)
            df["vetvrije_massa_kg"] = (df["gewicht"] - df["vetmassa_kg"]).round(1)
        if "taille" in df and "heup" in df:
            df["taille_heup"] = (df["taille"] / df["heup"]).round(2)
    return df


def schoon_slaap(ruw: pd.DataFrame) -> pd.DataFrame:
    if ruw.empty:
        return pd.DataFrame(columns=["datum", "uren", "kwaliteit"])
    df = pd.DataFrame({
        "datum": pd.to_datetime(_kolom(ruw, "Date"), errors="coerce").dt.tz_localize(None).dt.normalize(),
        "uren": pd.to_numeric(_kolom(ruw, "Hours Slept"), errors="coerce"),
        "kwaliteit": pd.to_numeric(_kolom(ruw, "Quality (1-10)"), errors="coerce"),
    })
    return df.dropna(subset=["datum"]).sort_values("datum").reset_index(drop=True)


def slaap_vs_training(sess: pd.DataFrame, slaap: pd.DataFrame) -> pd.DataFrame:
    """Koppel elke sessie aan de slaap van de nacht ervoor (slaaplog op dezelfde datum)."""
    if sess.empty or slaap.empty:
        return pd.DataFrame()
    return sess.merge(slaap, on="datum", how="inner")


def schoon_activiteit(ruw: pd.DataFrame) -> pd.DataFrame:
    """Eén rij per dag met de Apple Watch-ringen."""
    kol = {"Move (kcal)": "move", "Exercise (min)": "exercise", "Stand (hrs)": "stand", "Steps": "steps"}
    if ruw.empty:
        return pd.DataFrame(columns=["datum"] + list(kol.values()))
    df = pd.DataFrame({"datum": pd.to_datetime(_kolom(ruw, "Date"), errors="coerce").dt.tz_localize(None).dt.normalize()})
    for bron, doel in kol.items():
        df[doel] = pd.to_numeric(_kolom(ruw, bron), errors="coerce")
    df = df.dropna(subset=["datum"])
    return df.groupby("datum", as_index=False).max().sort_values("datum").reset_index(drop=True)
