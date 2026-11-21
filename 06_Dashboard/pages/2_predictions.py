"""Prédictions : consommation prévue pour les prochains jours."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.common import afficher, afficher_tableau

from src.common import (AMBER, NAVY, TEAL, TEAL_LIGHT, note_methode, charger_donnees,
                        charger_optionnel, en_tete, fmt, prix, style_fig)

df = charger_donnees()
en_tete("Prédictions", "Ce que le système prévoit pour les prochaines heures et les prochains jours.")

reel = charger_optionnel("predictions.csv")
note_methode(reel is not None, "Prévision estimée à partir de la consommation des 4 dernières semaines, à la même heure.")


@st.cache_data(show_spinner=False)
def modele_demo(donnees: pd.DataFrame, horizon_h: int = 168) -> pd.DataFrame:
    """Démo : moyenne des 4 semaines précédentes à la même heure (pas de fuite de données)."""
    s = donnees.set_index("timestamp")["power_kW"]
    idx = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(hours=horizon_h), freq="h")
    s = s.reindex(idx)
    pred = pd.concat([s.shift(168 * k) for k in range(1, 5)], axis=1).mean(axis=1)
    return pd.DataFrame({"timestamp": idx, "prediction_kW": pred.values}).dropna()


horizon_txt = st.radio("Horizon de prévision", ["24 heures", "3 jours", "7 jours"], index=1, horizontal=True)
horizon_h = {"24 heures": 24, "3 jours": 72, "7 jours": 168}[horizon_txt]

pred = (reel[["timestamp"] + [c for c in ("prediction_kW", "lower_kW", "upper_kW") if c in reel.columns]]
        if reel is not None else modele_demo(df)).sort_values("timestamp")
if "prediction_kW" not in pred.columns:
    st.error("Le fichier predictions.csv doit contenir les colonnes `timestamp` et `prediction_kW`.")
    st.stop()

actuel = df.set_index("timestamp")["power_kW"]
fin = actuel.index.max()
futur = pred[pred["timestamp"] > fin].head(horizon_h).reset_index(drop=True)
if futur.empty:
    st.error("Aucune prévision postérieure à la dernière mesure dans ce fichier.")
    st.stop()

# ---------------- Précision sur les 14 derniers jours ----------------
passe = pred[(pred["timestamp"] <= fin) & (pred["timestamp"] > fin - pd.Timedelta(days=14))].copy()
passe["reel"] = actuel.reindex(passe["timestamp"]).values
passe = passe.dropna(subset=["reel", "prediction_kW"])
mae = wape = sigma = None
if len(passe) >= 24:
    err = passe["prediction_kW"] - passe["reel"]
    mae = err.abs().mean()
    wape = err.abs().sum() / passe["reel"].abs().sum() * 100
    sigma = err.std()

# ---------------- Indicateurs ----------------
energie = futur["prediction_kW"].sum()
pic = futur.loc[futur["prediction_kW"].idxmax()]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Énergie prévue", f"{fmt(energie, 1)} kWh", help=f"Sur les {horizon_txt} à venir")
k2.metric("Coût prévu", f"{fmt(energie * prix(), 1)} MAD")
k3.metric("Pic prévu", f"{pic['prediction_kW']:.1f} kW", help=f"Le {pic['timestamp']:%d/%m à %Hh}")
k4.metric("Précision (14 derniers jours)", "—" if wape is None else f"{100 - wape:.0f} %",
          help="" if mae is None else f"Écart moyen : {mae:.2f} kW par heure")
st.write("")

# ---------------- Graphe principal ----------------
debut_aff = fin - pd.Timedelta(days=7)
hist = actuel[actuel.index > debut_aff]
courbe = pd.concat([passe[passe["timestamp"] > debut_aff][["timestamp", "prediction_kW"]],
                    futur[["timestamp", "prediction_kW"]]])
fig = go.Figure()
if "lower_kW" in futur.columns and "upper_kW" in futur.columns:
    bas, haut = futur["lower_kW"], futur["upper_kW"]
elif sigma is not None:
    bas, haut = (futur["prediction_kW"] - 1.28 * sigma).clip(lower=0), futur["prediction_kW"] + 1.28 * sigma
else:
    bas = haut = None
if bas is not None:
    fig.add_trace(go.Scatter(x=futur["timestamp"], y=haut, line=dict(width=0), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=futur["timestamp"], y=bas, fill="tonexty", fillcolor="rgba(232,163,23,0.18)",
                             line=dict(width=0), name="Marge d'incertitude (80 %)", hoverinfo="skip"))
fig.add_trace(go.Scatter(x=hist.index, y=hist.values, name="Mesuré", line=dict(color=NAVY, width=2),
                         hovertemplate="%{y:.2f} kW"))
fig.add_trace(go.Scatter(x=courbe["timestamp"], y=courbe["prediction_kW"], name="Prévu",
                         line=dict(color=AMBER, width=2.5, dash="dot"), hovertemplate="%{y:.2f} kW"))
fig.add_shape(type="rect", xref="x", yref="paper", x0=fin, x1=futur["timestamp"].max(), y0=0, y1=1,
              fillcolor="rgba(42,127,142,0.06)", line=dict(width=0), layer="below")
fig.add_annotation(x=fin, y=1, yref="paper", text="Maintenant", showarrow=False, xanchor="right", yanchor="bottom",
                   font=dict(color=TEAL, size=12))
fig.update_yaxes(title_text="kW")
afficher(style_fig(fig, "Mesuré et prévu", hauteur=420))

# ---------------- Détails ----------------
c1, c2 = st.columns(2)
with c1:
    prochaines = futur.head(24)
    top = set(prochaines["prediction_kW"].nlargest(3).index)
    fig = go.Figure(go.Bar(x=[f"{t:%Hh}" for t in prochaines["timestamp"]], y=prochaines["prediction_kW"],
                           marker_color=[AMBER if i in top else TEAL for i in prochaines.index],
                           hovertemplate="%{x} : %{y:.2f} kW<extra></extra>"))
    fig.update_yaxes(title_text="kW")
    afficher(style_fig(fig, "Les 24 prochaines heures", hover="closest"))
with c2:
    futur["bloc"] = np.arange(len(futur)) // 24 + 1
    ref = actuel.reindex(futur["timestamp"] - pd.Timedelta(hours=168)).values
    comp = futur.assign(ref=ref).groupby("bloc").agg(prevu=("prediction_kW", "sum"), ref=("ref", "sum"))
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[f"J+{b}" for b in comp.index], y=comp["ref"], name="Même jour, semaine passée",
                         marker_color=TEAL_LIGHT))
    fig.add_trace(go.Bar(x=[f"J+{b}" for b in comp.index], y=comp["prevu"], name="Prévu", marker_color=TEAL))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="kWh par jour")
    afficher(style_fig(fig, "Énergie prévue par jour"))

with st.expander("Voir le détail heure par heure"):
    t = futur[["timestamp", "prediction_kW"]].rename(columns={"timestamp": "Date et heure", "prediction_kW": "Prévu (kW)"})
    afficher_tableau(t.assign(**{"Date et heure": t["Date et heure"].dt.strftime("%d/%m %Hh")}),
                     {"Prévu (kW)": "{:.2f}"}, hauteur=320)
    st.download_button("Télécharger en CSV", t.to_csv(index=False).encode("utf-8"),
                       file_name="previsions.csv", mime="text/csv")
with st.expander("Comment lire cette page ?"):
    st.markdown(
        "- La courbe **bleue** est la consommation mesurée, la courbe **ambre** pointillée est la prévision.\n"
        "- La zone ambre claire est la **marge d'incertitude** : la consommation réelle devrait y rester 8 fois sur 10.\n"
        "- La **précision** compare, sur les 14 derniers jours, la prévision à ce qui s'est réellement passé.\n"
        + ("- Prévisions calculées par le modèle d'intelligence artificielle du système." if reel is not None else
           "- La prévision est la moyenne des 4 semaines précédentes à la même heure.")
    )
