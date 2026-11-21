"""Profil du foyer : informations saisies à la première connexion (et modifiables ensuite)."""
import json

import streamlit as st

from src.common import DATA
from src.maison import hero_html

FICHIER = DATA / "profil.json"
LOGEMENTS = ["Maison", "Villa", "Appartement", "Riad"]
CHAUFFAGES = ["Électrique", "Gaz", "Bois / autre", "Pas de chauffage"]
SOURCES = ["Données de référence", "Capteur en direct (ESP32)"]
DEFAUT = dict(nom="Ma maison", ville="Marrakech", logement="Maison", surface=120, occupants=4,
              chauffage="Électrique", puissance=6.0, prix=1.2, source=SOURCES[0])


def charger():
    try:
        return {**DEFAUT, **json.loads(FICHIER.read_text(encoding="utf-8"))} if FICHIER.exists() else None
    except (OSError, ValueError):
        return None


def sauver(p: dict):
    FICHIER.parent.mkdir(exist_ok=True)
    FICHIER.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")


def effacer():
    FICHIER.unlink(missing_ok=True)


def appliquer(p: dict):
    """Reporte les réglages du foyer dans la barre latérale (prix du kWh, puissance souscrite)."""
    st.session_state["prix_kwh"] = float(p["prix"])
    st.session_state["puissance_souscrite"] = float(p["puissance"])


def ecran_bienvenue(sombre: bool, zones: dict):
    """Première connexion : présentation + formulaire du foyer."""
    st.markdown("<style>[data-testid='stSidebar'], [data-testid='stSidebarCollapsedControl'] { display: none; }</style>",
                unsafe_allow_html=True)
    st.markdown(hero_html("Smart Energy AI", "Votre maison, mesurée et comprise.", zones,
                          dict(niveau="vert", message="Configuration de votre foyer"),
                          [("Suivi", "en temps réel"), ("Prévision", "par IA"), ("Alertes", "intelligentes")], sombre),
                unsafe_allow_html=True)
    _, centre, _ = st.columns([1, 2.4, 1])
    with centre:
        st.toggle("Mode nuit", key="mode_nuit")
        st.subheader("Parlez-nous de votre maison")
        st.caption("Ces informations personnalisent le tableau de bord (coût, risque de surcharge, conseils).")
        with st.form("formulaire_foyer"):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nom du foyer", DEFAUT["nom"])
            ville = c2.text_input("Ville", DEFAUT["ville"])
            c1, c2, c3 = st.columns(3)
            logement = c1.selectbox("Type de logement", LOGEMENTS)
            surface = c2.number_input("Surface (m²)", 15, 1000, DEFAUT["surface"], 5)
            occupants = c3.number_input("Occupants", 1, 20, DEFAUT["occupants"])
            c1, c2, c3 = st.columns(3)
            chauffage = c1.selectbox("Chauffage", CHAUFFAGES)
            puissance = c2.number_input("Puissance souscrite (kW)", 1.0, 36.0, DEFAUT["puissance"], 0.5,
                                        help="Indiquée sur votre contrat ou votre compteur.")
            prix = c3.number_input("Prix du kWh (MAD)", 0.1, 5.0, DEFAUT["prix"], 0.1)
            source = st.radio("Source des mesures", SOURCES, horizontal=True,
                              help="Le capteur en direct sera disponible avec le module de mesure du prototype.")
            if source != SOURCES[0]:
                st.info("Le capteur n'est pas encore relié : les données de référence seront utilisées en attendant.")
            ok = st.form_submit_button("Accéder à mon tableau de bord", type="primary", width="stretch")
        if ok:
            p = dict(nom=nom.strip() or DEFAUT["nom"], ville=ville.strip(), logement=logement, surface=int(surface),
                     occupants=int(occupants), chauffage=chauffage, puissance=float(puissance), prix=float(prix), source=source)
            sauver(p)
            appliquer(p)
            st.session_state.profil = p
            st.session_state.profil_a_modifier = False
            st.rerun()
