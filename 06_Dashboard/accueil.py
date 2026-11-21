"""Page d'accueil : les chiffres et graphes essentiels, compréhensibles d'un coup d'œil."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.common import afficher

from src.alertes import etat_systeme
from src.common import (AMBER, MOIS, NAVY, TEAL, TEAL_LIGHT, ZONES, charger_donnees, fmt, par_jour,
                        prix, sombre, souscrite, style_fig)
from src.maison import hero_html, zones_depuis

PAGES = [
    ("pages/1_Historique.py", "Historique", ":material/show_chart:", "Consommation heure par heure, jour par jour, mois par mois."),
    ("pages/2_predictions.py", "Prédictions", ":material/query_stats:", "Consommation prévue pour les prochains jours."),
    ("pages/3_Anomalies.py", "Anomalies", ":material/warning:", "Pics et comportements inhabituels détectés."),
    ("pages/4_appareils.py", "Appareils", ":material/electrical_services:", "Coût et consommation de chaque appareil."),
    ("pages/5_Conseils.py", "Conseils", ":material/lightbulb:", "Pistes concrètes pour réduire la facture."),
]
PERIODES = {"Toute la période": None, "Dernière année": 365, "6 derniers mois": 183, "30 derniers jours": 30}

df = charger_donnees()

# ---------------- Bandeau : la maison et son état ----------------
profil = st.session_state.get("profil") or {}
etat = etat_systeme(df, souscrite())
j_all = par_jour(df)
trente = df[df["timestamp"] > df["timestamp"].max() - pd.Timedelta(days=30)]
chips = [(f"{j_all.iloc[-1]:.1f} kWh", f"le {j_all.index[-1]:%d/%m/%Y}"),
         (f"{fmt(par_jour(trente).sum() * prix())} MAD", "30 derniers jours"),
         (f"{trente['power_kW'].max() / souscrite() * 100:.0f} %", "du compteur utilisé (pic, 30 j)")]
lieu = " · ".join(x for x in (profil.get("ville"), profil.get("logement"),
                              f"{profil['surface']} m²" if profil.get("surface") else "",
                              f"{profil['occupants']} occupants" if profil.get("occupants") else "") if x)
st.markdown(hero_html(profil.get("nom", "Smart Energy AI"), lieu or "Suivi de votre consommation électrique",
                      zones_depuis(df), etat, chips, sombre()), unsafe_allow_html=True)

e1, e2, e3, e4 = st.columns(4)
e1.metric("Anomalies (7 jours)", "—" if etat["anomalies_7j"] is None else f"{etat['anomalies_7j']}",
          help="Épisodes d'au moins 10 minutes signalés par au moins 2 méthodes sur 3."
          + ("" if etat["critiques_7j"] is None else f" Dont {etat['critiques_7j']} confirmés par les 3 méthodes."))
e2.metric("Dépassements (30 jours)", f"{etat['depassements_30j']}",
          help="Moments où la puissance atteint la puissance souscrite.")
e3.metric("Tendance (7 jours)", "—" if etat["tendance"] is None else f"{etat['tendance']:+.0f} %",
          help="Consommation des 7 derniers jours comparée aux 4 semaines précédentes.")
with e4:
    st.page_link("pages/3_Anomalies.py", label="Voir toutes les anomalies", icon=":material/warning:")
    st.page_link("pages/5_Conseils.py", label="Réduire ma consommation", icon=":material/lightbulb:")
st.subheader("Consommation")

periode = st.sidebar.radio("Période affichée", list(PERIODES))
jours = PERIODES[periode]
fin = df["timestamp"].max()
if jours:
    debut = fin - pd.Timedelta(days=jours)
    d = df[df["timestamp"] > debut]
    precedent = df[(df["timestamp"] > debut - pd.Timedelta(days=jours)) & (df["timestamp"] <= debut)]
else:
    d, precedent = df, None

jour = par_jour(d)
total_kwh = jour.sum()

# ---------------- Indicateurs clés ----------------
variation = None
if precedent is not None and len(precedent) > 0:
    pj = par_jour(precedent)
    if len(pj) > 0 and pj.mean() > 0:
        variation = (jour.mean() / pj.mean() - 1) * 100
pic = d.loc[d["power_kW"].idxmax()]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Énergie consommée", f"{fmt(total_kwh)} kWh",
          delta=None if variation is None else f"{variation:+.1f} % vs période précédente",
          delta_color="inverse")
k2.metric("Coût estimé", f"{fmt(total_kwh * prix())} MAD")
k3.metric("Consommation moyenne", f"{jour.mean():.1f} kWh/jour")
k4.metric("Pic de puissance", f"{pic['power_kW']:.1f} kW", help=f"Atteint le {pic['timestamp']:%d/%m/%Y à %Hh}")
st.write("")

# ---------------- Tendance + répartition ----------------
g1, g2 = st.columns([2, 1])
with g1:
    fen = 30 if len(jour) > 120 else 7
    tendance = jour.rolling(fen, min_periods=max(2, fen // 3)).mean()
    jmax = jour.idxmax()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=jour.index, y=jour.values, name="Par jour", mode="lines",
                             line=dict(color=TEAL_LIGHT, width=1), hovertemplate="%{y:.1f} kWh"))
    fig.add_trace(go.Scatter(x=tendance.index, y=tendance.values, name=f"Tendance ({fen} jours)",
                             mode="lines", line=dict(color=NAVY, width=2.5), hovertemplate="%{y:.1f} kWh"))
    fig.add_trace(go.Scatter(x=[jmax], y=[jour[jmax]], name="Jour le plus chargé", mode="markers",
                             marker=dict(color=AMBER, size=11, line=dict(color="white", width=2)),
                             hovertemplate=f"{jmax:%d/%m/%Y} : {jour[jmax]:.1f} kWh"))
    fig.update_yaxes(title_text="kWh par jour")
    afficher(style_fig(fig, "Consommation par jour"))

with g2:
    cols = list(ZONES)
    mesure = d[cols].sum()
    fig = go.Figure(go.Pie(
        labels=[ZONES[c][0] for c in cols], values=mesure.values, hole=0.58, sort=False,
        marker=dict(colors=[ZONES[c][1] for c in cols], line=dict(color="white", width=2)),
        textinfo="percent", hovertemplate="%{label}<br>%{value:,.0f} kWh (%{percent})<extra></extra>"))
    afficher(style_fig(fig, "D'où vient la consommation ?", hover="closest"))

# ---------------- Journée type + saisons ----------------
g3, g4 = st.columns(2)
profil = d.groupby(d["timestamp"].dt.hour)["power_kW"].mean()
top3 = set(profil.nlargest(3).index)
with g3:
    fig = go.Figure(go.Bar(x=[f"{h}h" for h in profil.index], y=profil.values,
                           marker_color=[AMBER if h in top3 else TEAL for h in profil.index],
                           hovertemplate="%{x} : %{y:.2f} kW<extra></extra>"))
    fig.update_yaxes(title_text="Puissance moyenne (kW)")
    afficher(style_fig(fig, "Une journée type"))
with g4:
    mensuel = jour.groupby([jour.index.year, jour.index.month]).mean()
    etiq = [f"{MOIS[m - 1]} {str(a)[2:]}" for a, m in mensuel.index]
    fig = go.Figure(go.Bar(x=etiq, y=mensuel.values, marker_color=TEAL,
                           hovertemplate="%{x} : %{y:.1f} kWh/jour<extra></extra>"))
    fig.update_xaxes(type="category", tickangle=-45, nticks=16)
    fig.update_yaxes(title_text="kWh par jour (moyenne du mois)")
    afficher(style_fig(fig, "Consommation moyenne par mois"))

# ---------------- À retenir ----------------
phrases = [
    f"<b>Heure de pointe :</b> la consommation culmine vers {profil.idxmax()}h "
    f"({profil.max():.1f} kW en moyenne) et tombe à {profil.min():.1f} kW vers {profil.idxmin()}h."
]
part = mesure / mesure.sum() * 100
zmax = part.idxmax()
if zmax != "autres_kwh":
    phrases.append(f"<b>Premier poste mesuré :</b> {ZONES[zmax][0].lower()} ({part[zmax]:.0f} % de la consommation).")
else:
    sous = part.drop("autres_kwh")
    phrases.append(f"<b>Postes mesurés :</b> {ZONES[sous.idxmax()][0].lower()} est le plus gros "
                   f"({sous.max():.0f} %) ; {part['autres_kwh']:.0f} % n'est pas mesuré par zone.")
m = d.groupby(d["timestamp"].dt.month)["power_kW"].mean()
hiver, ete = m.reindex([12, 1, 2]).dropna(), m.reindex([6, 7, 8]).dropna()
if len(hiver) >= 2 and len(ete) >= 2 and ete.mean() > 0:
    ecart = (hiver.mean() / ete.mean() - 1) * 100
    phrases.append(f"<b>Saisons :</b> l'hiver consomme {abs(ecart):.0f} % de {'plus' if ecart >= 0 else 'moins'} que l'été.")
st.markdown('<div class="retenir"><b>À retenir</b>' + "".join(f"<p>{p}</p>" for p in phrases) + "</div>",
            unsafe_allow_html=True)

# ---------------- Navigation ----------------
st.write("")
st.subheader("Aller plus loin")
for col, (chemin, titre, icone, desc) in zip(st.columns(len(PAGES)), PAGES):
    with col:
        st.page_link(chemin, label=titre, icon=icone)
        st.caption(desc)
st.divider()
st.caption("Smart Energy AI · 2026")
