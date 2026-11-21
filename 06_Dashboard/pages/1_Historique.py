"""Historique : explorer la consommation passée en détail."""
from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.common import afficher, afficher_tableau

from src.common import (AMBER, JOURS, MOIS, NAVY, RED, TEAL, TEAL_LIGHT, VMAX, VMIN, agreger,
                        charger_donnees, en_tete, fmt, par_jour, prix, style_fig)

df = charger_donnees()
en_tete("Historique", "Explorez la consommation passée : période, échelle de temps, rythmes, tension et courant.")

# ---------------- Filtres ----------------
mini, maxi = df["timestamp"].min().date(), df["timestamp"].max().date()
f1, f2, f3 = st.columns([2, 1, 1])
plage = f1.date_input("Période", value=(max(mini, maxi - timedelta(days=365)), maxi),
                      min_value=mini, max_value=maxi, format="DD/MM/YYYY")
echelle = f2.selectbox("Échelle de temps", ["Heure", "Jour", "Semaine", "Mois"], index=1)
grandeur = f3.selectbox("Grandeur", ["Énergie (kWh)", "Puissance moyenne (kW)"])

if not isinstance(plage, (tuple, list)) or len(plage) != 2:
    st.info("Choisissez une date de début et une date de fin.")
    st.stop()

d = df[(df["timestamp"].dt.date >= plage[0]) & (df["timestamp"].dt.date <= plage[1])]
if echelle == "Heure" and (plage[1] - plage[0]).days > 60:
    st.info("L'échelle « Heure » est limitée à 60 jours : affichage des 60 derniers jours de la période.")
    d = d[d["timestamp"] > d["timestamp"].max() - pd.Timedelta(days=60)]
if d.empty:
    st.warning("Aucune donnée sur cette période.")
    st.stop()

FREQ = {"Heure": "h", "Jour": "D", "Semaine": "W", "Mois": "MS"}
energie = grandeur.startswith("Énergie")
unite = "kWh" if energie else "kW"
serie = agreger(d, FREQ[echelle], "power_kW", energie)

t_evol, t_rythmes, t_compar, t_elec, t_data = st.tabs(
    ["Évolution", "Rythmes de consommation", "Comparaison annuelle", "Électricité", "Données"])

# ---------------- Évolution ----------------
with t_evol:
    jour = par_jour(d)
    pic = d.loc[d["power_kW"].idxmax()]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Énergie sur la période", f"{fmt(jour.sum())} kWh")
    k2.metric("Coût estimé", f"{fmt(jour.sum() * prix())} MAD")
    k3.metric("Moyenne par jour", f"{jour.mean():.1f} kWh")
    k4.metric("Pic horaire", f"{pic['power_kW']:.1f} kW", help=f"Le {pic['timestamp']:%d/%m/%Y à %Hh}")
    st.write("")
    fig = go.Figure()
    if echelle in ("Semaine", "Mois"):
        fig.add_trace(go.Bar(x=serie.index, y=serie.values, marker_color=TEAL, name=unite,
                             hovertemplate="%{y:.1f} " + unite + "<extra></extra>"))
    else:
        fig.add_trace(go.Scatter(x=serie.index, y=serie.values, mode="lines", name=unite,
                                 line=dict(color=TEAL, width=1.6), fill="tozeroy",
                                 fillcolor="rgba(42,127,142,0.10)",
                                 hovertemplate="%{y:.2f} " + unite + "<extra></extra>"))
    fig.add_hline(y=serie.mean(), line_dash="dot", line_color=AMBER,
                  annotation_text=f"Moyenne : {serie.mean():.1f} {unite}", annotation_position="top left")
    fig.update_xaxes(rangeslider_visible=True)
    fig.update_yaxes(title_text=unite)
    afficher(style_fig(fig, f"{grandeur} par {echelle.lower()}", hauteur=450))
    if echelle == "Mois":
        st.caption("Les mois incomplets (début et fin du jeu de données) sont estimés à partir de la puissance moyenne.")

# ---------------- Rythmes ----------------
with t_rythmes:
    d2 = d.assign(jsem=d["timestamp"].dt.dayofweek, heure=d["timestamp"].dt.hour)
    piv = d2.pivot_table(index="jsem", columns="heure", values="power_kW", aggfunc="mean").reindex(range(7))
    fig = go.Figure(go.Heatmap(
        z=piv.values, x=[f"{h}h" for h in piv.columns], y=JOURS,
        colorscale=[[0, "#F0F6F8"], [0.45, TEAL_LIGHT], [0.75, TEAL], [1, AMBER]],
        colorbar=dict(title="kW"), hovertemplate="%{y} %{x} : %{z:.2f} kW<extra></extra>"))
    fig.update_yaxes(autorange="reversed")
    afficher(style_fig(fig, "Quand consomme-t-on le plus ? (puissance moyenne)", hauteur=360, hover="closest"))

    c1, c2 = st.columns(2)
    with c1:
        sem = d2[d2["jsem"] < 5].groupby("heure")["power_kW"].mean()
        we = d2[d2["jsem"] >= 5].groupby("heure")["power_kW"].mean()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sem.index, y=sem.values, name="Semaine", line=dict(color=NAVY, width=2.5)))
        fig.add_trace(go.Scatter(x=we.index, y=we.values, name="Week-end", line=dict(color=AMBER, width=2.5)))
        fig.update_xaxes(title_text="Heure de la journée", dtick=2)
        fig.update_yaxes(title_text="kW")
        afficher(style_fig(fig, "Semaine et week-end"))
    with c2:
        j = par_jour(d)
        par_jsem = j.groupby(j.index.dayofweek).mean().reindex(range(7))
        fig = go.Figure(go.Bar(x=JOURS, y=par_jsem.values, marker_color=TEAL,
                               hovertemplate="%{x} : %{y:.1f} kWh<extra></extra>"))
        fig.update_yaxes(title_text="kWh par jour")
        afficher(style_fig(fig, "Consommation moyenne selon le jour", hover="closest"))

# ---------------- Comparaison annuelle ----------------
with t_compar:
    st.caption("Calculée sur toute la période disponible, indépendamment du filtre de dates.")
    jall = par_jour(df)
    m = jall.groupby([jall.index.year, jall.index.month]).mean().unstack(0)
    m = m.loc[:, m.notna().sum() >= 3]
    couleurs = [TEAL_LIGHT, TEAL, NAVY, AMBER, RED]
    fig = go.Figure()
    for i, annee in enumerate(m.columns):
        fig.add_trace(go.Scatter(x=[MOIS[k - 1] for k in m.index], y=m[annee].values, name=str(annee),
                                 mode="lines+markers", line=dict(color=couleurs[i % len(couleurs)], width=2.5),
                                 connectgaps=False))
    fig.update_yaxes(title_text="kWh par jour")
    afficher(style_fig(fig, "Consommation moyenne par mois, année par année", hauteur=400))
    annuel = jall.groupby(jall.index.year).agg(["mean", "count"])
    annuel = annuel[annuel["count"] >= 300]
    if len(annuel):
        cols = st.columns(len(annuel))
        for col, (annee, ligne) in zip(cols, annuel.iterrows()):
            col.metric(f"{annee}", f"{ligne['mean']:.1f} kWh/jour")

# ---------------- Électricité ----------------
with t_elec:
    pf = (d["power_kW"] / np.sqrt(d["power_kW"] ** 2 + d["reactive_kW"] ** 2)).mean()
    hors = ((d["voltage_V"] < VMIN) | (d["voltage_V"] > VMAX)).mean() * 100
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Tension moyenne", f"{d['voltage_V'].mean():.1f} V")
    k2.metric("Heures hors plage", f"{hors:.2f} %", help=f"Tension hors de {VMIN:.0f}–{VMAX:.0f} V (230 V ± 10 %)")
    k3.metric("Facteur de puissance", f"{pf:.2f}", help="Proche de 1 : l'énergie est bien utilisée.")
    k4.metric("Intensité maximale", f"{d['intensity_A'].max():.1f} A")
    st.write("")
    dj = d.set_index("timestamp").resample("D").agg(
        v_moy=("voltage_V", "mean"), v_min=("voltage_V", "min"), v_max=("voltage_V", "max"),
        i_moy=("intensity_A", "mean")).dropna()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dj.index, y=dj["v_max"], line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=dj.index, y=dj["v_min"], fill="tonexty", fillcolor="rgba(42,127,142,0.15)",
                             line=dict(width=0), name="Min – max du jour", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=dj.index, y=dj["v_moy"], name="Moyenne", line=dict(color=NAVY, width=2),
                             hovertemplate="%{y:.1f} V"))
    fig.add_hline(y=VMAX, line_dash="dot", line_color=RED)
    fig.add_hline(y=VMIN, line_dash="dot", line_color=RED)
    fig.update_yaxes(title_text="Volts")
    afficher(style_fig(fig, "Tension du réseau (lignes rouges : limites ± 10 %)"))
    fig = go.Figure(go.Scatter(x=dj.index, y=dj["i_moy"], line=dict(color=AMBER, width=2), name="Intensité",
                               hovertemplate="%{y:.1f} A"))
    fig.update_yaxes(title_text="Ampères")
    afficher(style_fig(fig, "Intensité moyenne par jour", hauteur=280))

# ---------------- Données ----------------
with t_data:
    tableau = serie.rename(f"{grandeur}").to_frame()
    tableau.index.name = "Date"
    t = tableau.reset_index()
    t["Date"] = t["Date"].dt.strftime("%d/%m/%Y %Hh" if echelle == "Heure" else "%d/%m/%Y")
    afficher_tableau(t, {grandeur: "{:.2f}"}, hauteur=420, max_lignes=1500)
    st.download_button("Télécharger en CSV", tableau.to_csv().encode("utf-8"),
                       file_name=f"historique_{echelle.lower()}.csv", mime="text/csv")
