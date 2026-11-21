
import streamlit as st

from src import profil
from src.common import appliquer_css, charger_donnees, sidebar_commun, sombre
from src.maison import zones_depuis

st.set_page_config(
    page_title="Smart Energy AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

df = charger_donnees()

# Profil du foyer : lu une fois par session, saisi à la première connexion
if "profil" not in st.session_state:
    st.session_state.profil = profil.charger()
    if st.session_state.profil:
        profil.appliquer(st.session_state.profil)

appliquer_css()

if st.session_state.profil is None or st.session_state.get("profil_a_modifier"):
    profil.ecran_bienvenue(sombre(), zones_depuis(df))
    st.stop()

navigation = st.navigation(
    {
        "Vue générale": [
            st.Page("accueil.py", title="Accueil", icon=":material/home:", default=True),
        ],
        "Analyse": [
            st.Page("pages/1_Historique.py", title="Historique", icon=":material/show_chart:"),
            st.Page("pages/2_predictions.py", title="Prédictions", icon=":material/query_stats:"),
            st.Page("pages/3_Anomalies.py", title="Anomalies", icon=":material/warning:"),
        ],
        "Pilotage": [
            st.Page("pages/4_appareils.py", title="Appareils", icon=":material/electrical_services:"),
            st.Page("pages/5_Conseils.py", title="Conseils", icon=":material/lightbulb:"),
        ],
    }
)

sidebar_commun(df)
with st.sidebar:
    p = st.session_state.profil
    st.divider()
    st.markdown(f"**{p['nom']}**")
    st.caption(f"{p['ville']} · {p['logement']} · {p['surface']} m² · {p['occupants']} occupants")
    c1, c2 = st.columns(2)
    if c1.button("Modifier", width="stretch", help="Modifier les informations du foyer"):
        st.session_state.profil_a_modifier = True
        st.rerun()
    if c2.button("Quitter", width="stretch", help="Se déconnecter et revenir à l'écran d'accueil"):
        profil.effacer()
        st.session_state.profil = None
        st.rerun()

navigation.run()
