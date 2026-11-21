"""Appareils : estimer et comparer la consommation et le coût de chaque appareil."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.common import afficher, afficher_tableau

from src.common import (AMBER, NAVY, RED, TEAL, TEAL_LIGHT, charger_donnees, en_tete, fmt, par_jour,
                        prix, souscrite, style_fig)

df = charger_donnees()
en_tete("Appareils", "Estimez ce que consomme chaque appareil et ce qu'il coûte, puis comparez-les.")

COLONNES = ["Appareil", "Puissance (W)", "Heures/jour", "Quantité"]
CATALOGUE = {  # nom : (puissance W, heures par jour équivalentes)
    "Réfrigérateur": (150, 8), "Congélateur": (180, 8), "Climatiseur": (1200, 6), "Chauffe-eau": (1500, 2),
    "Lave-linge": (500, 1), "Lave-vaisselle": (1200, 1), "Four électrique": (2000, 0.8), "Micro-ondes": (1000, 0.3),
    "Bouilloire": (2000, 0.3), "Télévision": (100, 4), "Ordinateur": (80, 6), "Éclairage LED": (10, 24),
    "Fer à repasser": (1800, 0.5), "Sèche-cheveux": (1800, 0.2),
}
if "appareils" not in st.session_state:
    st.session_state.appareils = pd.DataFrame(
        [[n, *CATALOGUE[n], 1] for n in ("Réfrigérateur", "Climatiseur", "Chauffe-eau", "Lave-linge", "Télévision")],
        columns=COLONNES)

# ---------------- Saisie ----------------
jours_mois = st.sidebar.slider("Jours d'utilisation par mois", 1, 31, 30)
st.subheader("Vos appareils")
st.caption("Modifiez directement le tableau. Pour supprimer une ligne : cochez-la à gauche puis appuyez sur Suppr.")
edite = st.data_editor(
    st.session_state.appareils, key="editeur_appareils", num_rows="dynamic", hide_index=True,
    column_config={
        "Appareil": st.column_config.TextColumn(required=True),
        "Puissance (W)": st.column_config.NumberColumn(min_value=1, max_value=20000, step=10, format="%d W"),
        "Heures/jour": st.column_config.NumberColumn(min_value=0.0, max_value=24.0, step=0.1, format="%.1f h"),
        "Quantité": st.column_config.NumberColumn(min_value=1, max_value=50, step=1, format="%d"),
    })
a1, a2 = st.columns([3, 1])
choix = a1.selectbox("Ajouter un appareil courant", list(CATALOGUE), label_visibility="collapsed",
                     placeholder="Ajouter un appareil courant")
if a2.button("Ajouter", width="stretch"):
    ligne = pd.DataFrame([[choix, *CATALOGUE[choix], 1]], columns=COLONNES)
    st.session_state.appareils = pd.concat([edite, ligne], ignore_index=True)
    st.session_state.pop("editeur_appareils", None)
    st.rerun()

# ---------------- Calculs ----------------
t = edite.dropna(subset=["Appareil", "Puissance (W)", "Heures/jour"]).copy()
t["Quantité"] = t["Quantité"].fillna(1)
if t.empty:
    st.info("Ajoutez au moins un appareil pour voir l'analyse.")
    st.stop()
t["kWh/jour"] = t["Puissance (W)"] * t["Heures/jour"] * t["Quantité"] / 1000
t["kWh/mois"] = t["kWh/jour"] * jours_mois
t["Coût/mois"] = t["kWh/mois"] * prix()
t = t.sort_values("kWh/mois", ascending=False).reset_index(drop=True)

total_mois, total_cout = t["kWh/mois"].sum(), t["Coût/mois"].sum()
simultane = (t["Puissance (W)"] * t["Quantité"]).sum() / 1000
st.write("")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Énergie estimée", f"{fmt(total_mois, 1)} kWh/mois")
k2.metric("Coût estimé", f"{fmt(total_cout)} MAD/mois")
k3.metric("Appareil le plus gourmand", t.loc[0, "Appareil"], help=f"{t.loc[0, 'kWh/mois'] / total_mois * 100:.0f} % du total")
k4.metric("Puissance si tout est allumé", f"{simultane:.1f} kW", help="Somme des puissances de tous les appareils.")

# ---------------- Risque de surcharge ----------------
taux = simultane / souscrite()
if taux >= 1:
    st.error(f"Si tous les appareils fonctionnent en même temps ({simultane:.1f} kW), vous dépassez votre puissance "
             f"souscrite ({souscrite():.1f} kW). Évitez de les utiliser simultanément.", icon=":material/error:")
elif taux >= 0.8:
    st.warning(f"Tous les appareils allumés représenteraient {taux * 100:.0f} % de votre puissance souscrite : "
               "la marge est faible.", icon=":material/warning:")
else:
    st.success(f"Tous les appareils allumés représenteraient {taux * 100:.0f} % de votre puissance souscrite : "
               "pas de risque de surcharge.", icon=":material/check_circle:")
st.write("")

# ---------------- Graphes ----------------
g1, g2 = st.columns([3, 2])
with g1:
    p = t.iloc[::-1]
    fig = go.Figure(go.Bar(
        y=p["Appareil"], x=p["kWh/mois"], orientation="h",
        marker_color=[AMBER if i == len(p) - 1 else TEAL for i in range(len(p))],
        text=[f"{c:.0f} MAD" for c in p["Coût/mois"]], textposition="outside",
        hovertemplate="%{y} : %{x:.1f} kWh/mois<extra></extra>"))
    fig.update_xaxes(title_text="kWh par mois", range=[0, p["kWh/mois"].max() * 1.3])
    afficher(style_fig(fig, "Classement par consommation", hauteur=max(300, 60 + 42 * len(p)), hover="closest"))
with g2:
    palette = [AMBER, TEAL, NAVY, TEAL_LIGHT, "#6FA4AF", "#B8C4CB", "#5C7A89", "#C9A24A"]
    fig = go.Figure(go.Pie(labels=t["Appareil"], values=t["kWh/mois"], hole=0.55, sort=False,
                           marker=dict(colors=[palette[i % len(palette)] for i in range(len(t))],
                                       line=dict(color="white", width=2)),
                           textinfo="percent", hovertemplate="%{label}<br>%{value:.1f} kWh (%{percent})<extra></extra>"))
    afficher(style_fig(fig, "Part de chaque appareil", hauteur=max(300, 60 + 42 * len(t)), hover="closest"))

# ---------------- Estimé vs mesuré ----------------
recent = par_jour(df[df["timestamp"] > df["timestamp"].max() - pd.Timedelta(days=365)])
mesure_mois = recent.mean() * jours_mois
couverture = total_mois / mesure_mois * 100
fig = go.Figure(go.Bar(x=["Estimé", "Mesuré"],
                       y=[total_mois, mesure_mois], marker_color=[TEAL, NAVY],
                       text=[f"{total_mois:.0f} kWh", f"{mesure_mois:.0f} kWh"], textposition="outside"))
fig.update_yaxes(title_text="kWh par mois")
c1, c2 = st.columns([2, 3])
with c1:
    afficher(style_fig(fig, "Estimation et réalité", hauteur=320, hover="closest"))
with c2:
    st.markdown("**Votre liste est-elle complète ?**")
    if couverture < 70:
        st.write(f"Vos appareils expliquent environ **{couverture:.0f} %** de la consommation mesurée. "
                 "Il manque probablement des appareils, ou les durées d'utilisation sont sous-estimées.")
    elif couverture <= 130:
        st.write(f"Vos appareils expliquent environ **{couverture:.0f} %** de la consommation mesurée : "
                 "l'estimation est cohérente avec la réalité.")
    else:
        st.write(f"Votre estimation représente **{couverture:.0f} %** de la consommation mesurée : "
                 "les durées d'utilisation sont probablement trop élevées.")
    st.caption("La consommation mesurée est celle du foyer suivi ; "
               "vos appareils sont une estimation à partir de leur puissance nominale.")

with st.expander("Détail du calcul"):
    st.markdown("Énergie (kWh) = puissance (W) × heures par jour × quantité ÷ 1000. "
                "Coût = énergie × prix du kWh (réglable dans la barre latérale).")
    aff = t.rename(columns={"kWh/jour": "kWh/jour", "kWh/mois": "kWh/mois", "Coût/mois": "Coût/mois (MAD)"})
    afficher_tableau(aff, {"kWh/jour": "{:.2f}", "kWh/mois": "{:.1f}", "Coût/mois (MAD)": "{:.2f}",
                           "Heures/jour": "{:.1f}"}, hauteur=320)
    st.download_button("Télécharger en CSV", aff.to_csv(index=False).encode("utf-8"),
                       file_name="appareils.csv", mime="text/csv")
