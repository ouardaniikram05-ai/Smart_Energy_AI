"""Anomalies : épisodes anormaux (consensus de 3 méthodes) et surcharges de puissance."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.common import afficher, afficher_tableau

from src.common import (AMBER, DATA, NAVY, RED, TEAL, TEAL_LIGHT, VMAX, VMIN, charger_donnees,
                        en_tete, fmt, souscrite, style_fig)

df = charger_donnees()
en_tete("Anomalies et risques", "Les moments où la consommation sort de l'ordinaire ou approche la limite du compteur.")


# ----------------------------------------------------------
# Lecture des résultats de détection (dossier data/)
# ----------------------------------------------------------
@st.cache_data(show_spinner=False)
def _lire(chemin: str, mtime: float, dates: tuple) -> pd.DataFrame:
    return pd.read_csv(chemin, parse_dates=list(dates))


def lire_m3(nom, dates=()):
    for chemin in (DATA / nom, DATA / (nom + ".gz")):
        if chemin.exists():
            return _lire(str(chemin), chemin.stat().st_mtime, tuple(dates))
    return None


@st.cache_data(show_spinner=False)
def episodes_consensus(cons: pd.DataFrame, ecart_min: int = 5) -> pd.DataFrame:
    """Regroupe les minutes anormales consécutives (écart <= 5 min) en épisodes."""
    c = cons.sort_values("Datetime")
    groupe = (c["Datetime"].diff() > pd.Timedelta(minutes=ecart_min)).cumsum()
    ep = c.groupby(groupe).agg(debut=("Datetime", "min"), fin=("Datetime", "max"),
                               minutes=("Datetime", "size"), votes=("Anomaly_votes", "max"))
    ep["duree"] = (ep["fin"] - ep["debut"]).dt.total_seconds() / 60 + 1
    return ep.reset_index(drop=True)


@st.cache_data(show_spinner=False)
def accord_methodes(cons: pd.DataFrame) -> pd.DataFrame:
    """Combien de minutes retenues viennent de quelle combinaison de méthodes."""
    cols, noms = ["Prediction_IF", "Prediction_Zscore", "Prediction_LOF"], ["Isolation Forest", "Z-score", "LOF"]
    lignes = [{"Méthodes d'accord": " + ".join(n for n, f in zip(noms, flags) if f), "Minutes": int(n)}
              for flags, n in (cons[cols] == -1).value_counts().items()]
    t = pd.DataFrame(lignes).sort_values("Minutes", ascending=False).reset_index(drop=True)
    t["Part"] = t["Minutes"] / t["Minutes"].sum() * 100
    return t


@st.cache_data(show_spinner=False)
def detection_demo(donnees: pd.DataFrame, seuil: float) -> pd.DataFrame:
    """Démo (sans fichier du Membre 3) : écart robuste à l'habitude du même jour et de la même heure."""
    d = donnees.loc[~donnees["is_interpolated"], ["timestamp", "power_kW", "voltage_V"]].copy()
    d["hdw"] = d["timestamp"].dt.dayofweek * 24 + d["timestamp"].dt.hour
    ecart = d["power_kW"] - d.groupby("hdw")["power_kW"].transform("median")
    mad = ecart.abs().groupby(d["hdw"]).transform("median") * 1.4826
    d["score"] = ecart / mad.clip(lower=0.05)
    hors = (d["voltage_V"] < VMIN) | (d["voltage_V"] > VMAX)
    return d[(d["score"] >= seuil) | hors][["timestamp", "power_kW", "score"]]


cons = lire_m3("consensus_anomalies.csv", ["Datetime"])
over = lire_m3("overload_periods.csv", ["start_time", "end_time"])
meth = lire_m3("model_evaluation.csv")

if cons is None:
    st.caption("Détection basée sur l'écart avec vos habitudes (même jour de la semaine, même heure).")

# ----------------------------------------------------------
# Période
# ----------------------------------------------------------
fin_data = df["timestamp"].max()
PERIODES = {"30 derniers jours": 30, "90 derniers jours": 90, "Dernière année": 365, "Toute la période": None}
debut_modeles = None
if cons is not None:
    debut_modeles = cons["Datetime"].min().floor("D")
    PERIODES = {f"Période analysée (depuis le {debut_modeles:%d/%m/%Y})": "modeles", **PERIODES}
periode = st.selectbox("Période affichée", list(PERIODES), index=0)
choix = PERIODES[periode]
if choix == "modeles":
    debut_p = debut_modeles
elif choix is None:
    debut_p = df["timestamp"].min()
else:
    debut_p = fin_data - pd.Timedelta(days=choix)
d = df[df["timestamp"] >= debut_p]
kw_max = souscrite()

tab_a, tab_s = st.tabs(["Anomalies de consommation", "Surcharges de puissance"])

# ==========================================================
# ONGLET 1 : ANOMALIES
# ==========================================================
with tab_a:
    if cons is not None:
        c1, c2 = st.columns([1, 1])
        confirmation = c1.radio("Confirmation", ["2 méthodes sur 3 ou plus", "3 méthodes sur 3 uniquement"], horizontal=True)
        duree_min = c2.slider("Durée minimale d'un épisode (minutes)", 1, 60, 10,
                              help="Les épisodes très courts (1 à 2 minutes) sont souvent anodins.")
        ep = episodes_consensus(cons)
        ep["critique"] = ep["votes"] == 3
        ep["confirmation"] = ep["votes"].map({2: "2 méthodes sur 3", 3: "3 méthodes sur 3"})
        if confirmation.startswith("3"):
            ep = ep[ep["critique"]]
        ep = ep[ep["duree"] >= duree_min]
    else:
        seuil = st.slider("Sensibilité de la détection", 4.0, 12.0, 8.0, 0.5,
                          help="Valeur basse : beaucoup d'alertes. Valeur haute : seulement les écarts les plus nets.")
        ep = (detection_demo(df, seuil).rename(columns={"timestamp": "debut"})
              .assign(duree=60.0, confirmation="Écart statistique"))
        ep["critique"] = ep["score"].fillna(0) >= seuil * 1.5

    ep = ep[ep["debut"] >= debut_p].sort_values("debut").reset_index(drop=True)
    if "power_kW" not in ep.columns:
        ep["power_kW"] = df.set_index("timestamp")["power_kW"].reindex(ep["debut"].dt.floor("h")).values

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Épisodes anormaux", f"{len(ep)}")
    k2.metric("Confirmés par les 3 méthodes", f"{int(ep['critique'].sum())}" if cons is not None else "—")
    k3.metric("Durée cumulée", f"{ep['duree'].sum() / 60:.0f} h" if len(ep) else "0 h")
    k4.metric("Heure la plus touchée", f"{int(ep['debut'].dt.hour.mode().iloc[0])}h" if len(ep) else "—")
    st.write("")

    if ep.empty:
        st.success("Aucune anomalie sur cette période avec les réglages actuels.", icon=":material/check_circle:")
    else:
        st.subheader("Dernières alertes")
        for _, r in ep.tail(4).iloc[::-1].iterrows():
            texte = f"**{r['debut']:%d/%m/%Y à %H:%M}** · {r['confirmation']} · {r['duree']:.0f} min"
            (st.error if r["critique"] else st.warning)(texte, icon=":material/error:" if r["critique"] else ":material/warning:")

        jmax = d.set_index("timestamp")["power_kW"].resample("D").max()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=jmax.index, y=jmax.values, name="Pic horaire du jour", mode="lines",
                                 line=dict(color=TEAL_LIGHT, width=1.2), hovertemplate="%{y:.1f} kW"))
        for crit, nom, coul in ((False, "Anomalie (2 méthodes)" if cons is not None else "Anomalie", AMBER),
                                (True, "Confirmée (3 méthodes)" if cons is not None else "Écart très net", RED)):
            g = ep[(ep["critique"] == crit) & ep["power_kW"].notna()]
            if len(g):
                fig.add_trace(go.Scatter(
                    x=g["debut"], y=g["power_kW"], name=nom, mode="markers", customdata=g["duree"],
                    marker=dict(color=coul, size=7, line=dict(color="white", width=1)),
                    hovertemplate="%{x|%d/%m/%Y %H:%M} · %{customdata:.0f} min · %{y:.1f} kW<extra></extra>"))
        fig.update_yaxes(title_text="kW (moyenne sur l'heure)")
        afficher(style_fig(fig, "Anomalies dans le temps", hauteur=400, hover="closest"))

        g1, g2 = st.columns(2)
        with g1:
            par_heure = ep.groupby(ep["debut"].dt.hour).size().reindex(range(24), fill_value=0)
            fig = go.Figure(go.Bar(x=[f"{h}h" for h in par_heure.index], y=par_heure.values, marker_color=AMBER,
                                   hovertemplate="%{x} : %{y} épisodes<extra></extra>"))
            afficher(style_fig(fig, "À quelle heure ?", hover="closest"))
        with g2:
            par_mois = ep.groupby(ep["debut"].dt.to_period("M")).size()
            fig = go.Figure(go.Bar(x=[f"{p:%m/%Y}" for p in par_mois.index.to_timestamp()], y=par_mois.values,
                                   marker_color=TEAL, hovertemplate="%{x} : %{y} épisodes<extra></extra>"))
            fig.update_xaxes(type="category")
            afficher(style_fig(fig, "Quel mois ?", hover="closest"))

        with st.expander("Liste complète des épisodes"):
            t = ep.iloc[::-1][["debut", "duree", "confirmation", "power_kW"]].rename(columns={
                "debut": "Début", "duree": "Durée (min)", "confirmation": "Confirmation", "power_kW": "Puissance de l'heure (kW)"})
            afficher_tableau(t, {"Début": lambda v: f"{v:%d/%m/%Y %H:%M}", "Durée (min)": "{:.0f}",
                                 "Puissance de l'heure (kW)": "{:.2f}"}, hauteur=360)
            st.download_button("Télécharger en CSV", t.to_csv(index=False).encode("utf-8"),
                               file_name="episodes_anormaux.csv", mime="text/csv")

# ==========================================================
# ONGLET 2 : SURCHARGES
# ==========================================================
with tab_s:
    if over is not None:
        s_all = over.rename(columns={"start_time": "debut", "duration_minutes": "duree", "max_power": "pic"})[["debut", "duree", "pic"]]
    else:
        s_all = df[["timestamp", "power_kW"]].rename(columns={"timestamp": "debut", "power_kW": "pic"}).assign(duree=60)
    s = s_all[(s_all["debut"] >= debut_p) & (s_all["pic"] >= kw_max)].sort_values("debut").reset_index(drop=True)
    st.caption(f"Seuil : puissance souscrite de {kw_max:.1f} kW (modifiable dans la barre latérale). "
               + ("Mesures à la minute : elles montrent des pics que la moyenne horaire cache." if over is not None else ""))

    total_min = int(s["duree"].sum()) if len(s) else 0
    h, m = divmod(total_min, 60)
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Dépassements", f"{len(s)}")
    k2.metric("Durée cumulée", f"{h} h {m:02d} min")
    k3.metric("Puissance maximale", f"{s['pic'].max():.1f} kW" if len(s) else "—",
              help="" if s.empty else f"Atteinte le {s.loc[s['pic'].idxmax(), 'debut']:%d/%m/%Y à %H:%M}")
    k4.metric("Plus long dépassement", f"{s['duree'].max():.0f} min" if len(s) else "—")
    st.write("")

    if s.empty:
        st.success("Aucun dépassement de la puissance souscrite sur cette période.", icon=":material/check_circle:")
    else:
        fig = go.Figure(go.Scatter(
            x=s["debut"], y=s["pic"], mode="markers", customdata=s["duree"],
            marker=dict(color=AMBER, size=np.clip(np.sqrt(s["duree"]) * 3, 6, 28), opacity=0.75,
                        line=dict(color="white", width=1)),
            hovertemplate="%{x|%d/%m/%Y %H:%M} · %{y:.1f} kW · %{customdata:.0f} min<extra></extra>"))
        fig.add_hline(y=kw_max, line_dash="dash", line_color=RED, annotation_text="Puissance souscrite",
                      annotation_position="bottom left")
        fig.update_yaxes(title_text="Puissance maximale (kW)")
        afficher(style_fig(fig, "Dépassements dans le temps (taille = durée)", hauteur=380, hover="closest"))

        g1, g2 = st.columns(2)
        with g1:
            par_heure = s.groupby(s["debut"].dt.hour).size().reindex(range(24), fill_value=0)
            fig = go.Figure(go.Bar(x=[f"{h}h" for h in par_heure.index], y=par_heure.values, marker_color=RED,
                                   hovertemplate="%{x} : %{y} dépassements<extra></extra>"))
            afficher(style_fig(fig, "À quelle heure ?", hover="closest"))
        with g2:
            top = s.nlargest(10, "pic").iloc[::-1]
            fig = go.Figure(go.Bar(y=[f"{t:%d/%m/%Y %H:%M}" for t in top["debut"]], x=top["pic"], orientation="h",
                                   marker_color=NAVY, hovertemplate="%{y} : %{x:.1f} kW<extra></extra>"))
            fig.update_xaxes(title_text="kW")
            afficher(style_fig(fig, "Les 10 pics les plus élevés", hover="closest"))

        with st.expander("Liste complète des dépassements"):
            t = s.iloc[::-1].rename(columns={"debut": "Début", "duree": "Durée (min)", "pic": "Puissance max (kW)"})
            afficher_tableau(t, {"Début": lambda v: f"{v:%d/%m/%Y %H:%M}", "Durée (min)": "{:.0f}", "Puissance max (kW)": "{:.2f}"}, hauteur=360)
            st.download_button("Télécharger en CSV", t.to_csv(index=False).encode("utf-8"),
                               file_name="surcharges.csv", mime="text/csv")

    # ---------------- Forte charge (analyse par heure et par jour) ----------------
    h_an = lire_m3("hourly_overload_analysis.csv")
    d_an = lire_m3("daily_overload_analysis.csv", ("date",))
    if h_an is not None or d_an is not None:
        st.markdown("#### Forte charge")
        st.caption("Une minute est en forte charge quand la puissance dépasse le seuil défini par l'analyse "
                   "(environ 5 % des minutes les plus chargées de l'historique).")
        c1, c2 = st.columns(2)
        if h_an is not None:
            with c1:
                top3 = set(h_an.nlargest(3, "overload_percentage")["hour"])
                fig = go.Figure(go.Bar(
                    x=[f"{h}h" for h in h_an["hour"]], y=h_an["overload_percentage"],
                    marker_color=[AMBER if h in top3 else TEAL for h in h_an["hour"]],
                    hovertemplate="%{x} : %{y:.1f} % du temps<extra></extra>"))
                fig.update_yaxes(title_text="% du temps en forte charge")
                afficher(style_fig(fig, "À quelles heures la charge est-elle forte ?", hover="closest"))
        if d_an is not None:
            with c2:
                dj = d_an[(d_an["date"] >= debut_p.normalize()) & (d_an["total_measurements"] >= 1000)]
                if dj.empty:
                    st.info("Pas de données de forte charge sur cette période.")
                else:
                    top = dj.nlargest(10, "overload_percentage").iloc[::-1]
                    fig = go.Figure(go.Bar(
                        y=[f"{d:%d/%m/%Y}" for d in top["date"]], x=top["overload_percentage"], orientation="h",
                        marker_color=AMBER, text=[f"{v:.0f} %" for v in top["overload_percentage"]],
                        textposition="outside", hovertemplate="%{y} : %{x:.1f} % du temps<extra></extra>"))
                    fig.update_xaxes(title_text="% du temps en forte charge", range=[0, top["overload_percentage"].max() * 1.2])
                    afficher(style_fig(fig, "Les 10 journées les plus chargées", hover="closest"))

# ==========================================================
# MÉTHODES (bloc replié)
# ==========================================================
with st.expander("Comment fonctionne la détection ?"):
    st.markdown(
        "- **Z-score** : repère les valeurs très éloignées de la moyenne.\n"
        "- **LOF** : repère les valeurs isolées par rapport à leurs voisines dans le temps.\n"
        "- **Isolation Forest** : modèle qui isole rapidement les points rares.\n"
        "- **Consensus** : un épisode est retenu quand au moins 2 méthodes sur 3 sont d'accord ; "
        "il est « confirmé » quand les 3 le sont. Cela limite les fausses alertes.\n"
        "- **Surcharge** : la puissance mesurée à la minute atteint la puissance souscrite.\n"
        "- Une **fuite de courant vers la terre** ne peut pas être confirmée avec la seule consommation globale : "
        "elle demande des mesures électriques adaptées."
    )
    comp = lire_m3("comparaison_methodes.csv")
    if comp is None and meth is not None:   # même contenu dans model_evaluation.csv
        comp = meth.rename(columns={"Model": "Methode", "Anomalies_detected": "Anomalies",
                                    "Normal_observations": "Observations_normales",
                                    "Anomaly_percentage": "Pourcentage_anomalies"})
    if comp is not None and {"Methode", "Anomalies", "Observations_normales", "Pourcentage_anomalies"}.issubset(comp.columns):
        st.markdown("**Comparaison des méthodes**")
        t1, t2 = st.columns([1, 1])
        with t1:
            aff = comp.rename(columns={"Methode": "Méthode", "Anomalies": "Anomalies détectées",
                                       "Observations_normales": "Observations normales",
                                       "Pourcentage_anomalies": "% d'anomalies"})
            afficher_tableau(aff, {"Anomalies détectées": fmt, "Observations normales": fmt, "% d'anomalies": "{:.2f} %"},
                             hauteur=200)
        with t2:
            fig = go.Figure(go.Bar(x=comp["Methode"], y=comp["Pourcentage_anomalies"],
                                   marker_color=[TEAL, AMBER, NAVY][:len(comp)],
                                   text=[f"{v:.1f} %" for v in comp["Pourcentage_anomalies"]], textposition="outside",
                                   hovertemplate="%{x} : %{y:.1f} %<extra></extra>"))
            fig.update_yaxes(title_text="% d'observations anormales", rangemode="tozero")
            afficher(style_fig(fig, "Part d'anomalies par méthode", hauteur=280, hover="closest"))
    if cons is not None:
        st.markdown("**Accord entre les méthodes** (minutes retenues par le consensus)")
        acc = accord_methodes(cons)
        afficher_tableau(acc, {"Minutes": fmt, "Part": "{:.1f} %"}, hauteur=220)
    st.caption("Limites : la détection porte sur la période à partir du 05/02/2010, et les méthodes sont comparées "
               "entre elles, sans mesure de précision absolue.")
