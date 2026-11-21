"""Utilitaires partagés par toutes les pages du dashboard (données, thème, graphes, tableaux)."""
from pathlib import Path
from string import Template

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ----------------------------------------------------------
# Chemins
# ----------------------------------------------------------
DASH = Path(__file__).resolve().parent.parent      # 06_Dashboard
RACINE = DASH.parent                               # racine du dépôt
ASSETS = DASH / "assets"
DATA = DASH / "data"

# ----------------------------------------------------------
# Identité visuelle : bleu nuit (texte), turquoise (données), ambre (ce qui compte), rouge (alerte)
# ----------------------------------------------------------
NAVY, TEAL, TEAL_LIGHT, AMBER, RED, GREY = (
    "#12303F", "#2A7F8E", "#9CC3CB", "#E8A317", "#D64545", "#8A99A3",
)

ZONES = {  # colonne -> (libellé, couleur)
    "cuisine_kwh": ("Cuisine", TEAL),
    "buanderie_kwh": ("Buanderie et réfrigérateur", TEAL_LIGHT),
    "eau_clim_kwh": ("Chauffe-eau et climatisation", AMBER),
    "autres_kwh": ("Autres usages", NAVY),
}
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
        "juil.", "août", "sept.", "oct.", "nov.", "déc."]
JOURS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
VMIN, VMAX = 207.0, 253.0   # réseau 230 V ± 10 %

# ----------------------------------------------------------
# Thème clair / sombre (au choix de l'utilisateur)
# ----------------------------------------------------------
PALETTES = {
    "clair": dict(fond="#F5F8FA", surface="#FFFFFF", lateral="#E8EFF3", bordure="#DCE5EA",
                  texte="#12303F", doux="#5B6B75", note="#FBF6EA", survol="#EEF4F7"),
    "sombre": dict(fond="#0C161D", surface="#14232D", lateral="#0F1D26", bordure="#25394A",
                   texte="#E6EEF2", doux="#9DB0BC", note="#2B2512", survol="#1B2F3B"),
}


def sombre() -> bool:
    return bool(st.session_state.get("mode_nuit", False))


def palette() -> dict:
    return PALETTES["sombre" if sombre() else "clair"]


CSS_BASE = Template("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap');
.stApp { font-family: 'IBM Plex Sans', 'Segoe UI', sans-serif; }
.block-container { padding-top: 1.6rem; max-width: 1280px; }
#MainMenu, footer { visibility: hidden; }
[data-testid="stHeader"] { background: transparent; }
h1 { font-weight: 600; letter-spacing: -0.02em; margin-bottom: 0.1rem; }
h2, h3 { font-weight: 600; }
.sous-titre { color: $doux; font-size: 1.05rem; margin: 0.1rem 0 1.4rem 0; }
.modebar-container { display: none !important; }

/* Indicateurs : la valeur ne doit jamais être coupée */
[data-testid="stMetric"] {
    background: $surface; border: 1px solid $bordure; border-left: 4px solid #2A7F8E;
    border-radius: 8px; padding: 14px 16px;
}
[data-testid="stMetricValue"], [data-testid="stMetricValue"] > div {
    font-size: 1.55rem !important; font-weight: 600; line-height: 1.25;
    white-space: normal !important; overflow: visible !important; text-overflow: clip !important;
}
[data-testid="stMetricLabel"] p { font-size: 0.86rem; }

[data-testid="stSidebar"] { border-right: 1px solid $bordure; }
.retenir { border-left: 4px solid #E8A317; background: $note; padding: 12px 18px;
           border-radius: 0 8px 8px 0; }
.retenir p { margin: 0.25rem 0; }

/* Tableaux (HTML, pour suivre le thème) */
.tbl { overflow: auto; border: 1px solid $bordure; border-radius: 8px; background: $surface; margin: 0.4rem 0 0.8rem 0; }
.tbl table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
.tbl th { position: sticky; top: 0; background: $lateral; text-align: left; padding: 8px 12px; font-weight: 600; }
.tbl td { padding: 7px 12px; border-top: 1px solid $bordure; }
.tbl tr:hover td { background: $survol; }
</style>
""")

CSS_SOMBRE = Template("""
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: $fond !important; color: $texte; }
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { background: $lateral !important; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp li, .stApp label,
[data-testid="stWidgetLabel"] *, [data-testid="stCaptionContainer"] *, [data-testid="stMetricLabel"] *,
[data-testid="stMetricValue"], [data-testid="stSidebar"] span, [data-testid="stSidebar"] p,
[data-testid="stSidebarNav"] *, .tbl, .tbl * , [data-testid="stRadio"] *, [data-testid="stSlider"] *,
[data-testid="stToggle"] *, [data-testid="stExpander"] summary * { color: $texte !important; }
.sous-titre { color: $doux !important; }
.stApp [data-testid="stAlert"] *, .stApp [data-testid="stAlertContainer"] * { color: #12303F !important; }
[data-testid="stDateInput"] div, [data-testid="stDateInput"] input { background-color: $surface !important; color: $texte !important; }
[data-testid="stDataFrame"] { filter: invert(.9) hue-rotate(180deg); }
.retenir, .retenir * { color: $texte !important; }
input, textarea, [data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="select"] > div,
[data-baseweb="textarea"] { background: $surface !important; color: $texte !important; border-color: $bordure !important; }
[data-baseweb="popover"], [data-baseweb="popover"] *, [data-baseweb="menu"], [data-baseweb="calendar"],
[data-baseweb="calendar"] * { background: $surface; color: $texte; }
[data-testid="stTabs"] [role="tab"] p { color: $doux !important; }
[data-testid="stTabs"] [aria-selected="true"] p { color: $texte !important; }
[data-testid="stExpander"], [data-testid="stExpander"] details { background: $surface; border-color: $bordure; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color: $bordure !important; }
[data-testid="stNumberInput"] button { background: $surface !important; color: $texte !important; border-color: $bordure !important; }
.stButton button, .stDownloadButton button { background: $surface; color: $texte; border: 1px solid $bordure; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: $survol !important; }
</style>
""")


def appliquer_css():
    p = palette()
    st.markdown(CSS_BASE.safe_substitute(p), unsafe_allow_html=True)
    if sombre():
        st.markdown(CSS_SOMBRE.safe_substitute(p), unsafe_allow_html=True)


# ----------------------------------------------------------
# Données
# ----------------------------------------------------------
CANDIDATS = [
    RACINE / "01_Dataset" / "Processed" / "household_hourly.csv.gz",
    RACINE / "01_Dataset" / "Processed" / "household_hourly.csv",
    DATA / "household_hourly.csv.gz",
    DATA / "household_hourly.csv",
]


# Si le fichier n'est pas trouvé sur le disque, il est téléchargé depuis le dépôt GitHub de l'équipe
URL_GITHUB = ("https://raw.githubusercontent.com/ouardaniikram05-ai/Smart_Energy_AI/develop/"
              "01_Dataset/Processed/household_hourly.csv.gz")


@st.cache_data(show_spinner="Chargement des données…")
def _lire_principal(chemin: str, mtime: float) -> pd.DataFrame:
    df = pd.read_csv(chemin, parse_dates=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
    # Pas d'1 heure : une puissance moyenne en kW équivaut à des kWh sur l'heure.
    df["cuisine_kwh"] = df["sub_metering_1_Wh"] / 1000
    df["buanderie_kwh"] = df["sub_metering_2_Wh"] / 1000
    df["eau_clim_kwh"] = df["sub_metering_3_Wh"] / 1000
    df["autres_kwh"] = (
        df["power_kW"] - df[["cuisine_kwh", "buanderie_kwh", "eau_clim_kwh"]].sum(axis=1)
    ).clip(lower=0)
    return df


def charger_donnees() -> pd.DataFrame:
    for c in CANDIDATS:
        if c.exists():
            return _lire_principal(str(c), c.stat().st_mtime)
    try:
        return _lire_principal(URL_GITHUB, 0.0)
    except Exception:
        st.error(
            "Fichier de données introuvable. Placez `household_hourly.csv.gz` dans "
            "`01_Dataset/Processed/` (ou dans `06_Dashboard/data/`), ou vérifiez votre connexion Internet."
        )
        st.stop()


@st.cache_data(show_spinner=False)
def _lire_optionnel(chemin: str, mtime: float, dates: tuple) -> pd.DataFrame:
    return pd.read_csv(chemin, parse_dates=list(dates))


def charger_optionnel(nom: str, dates=("timestamp",)):
    """Résultats de détection ou de prévision déposés dans data/. None si absent."""
    for chemin in (DATA / nom, DATA / (nom + ".gz")):
        if chemin.exists():
            return _lire_optionnel(str(chemin), chemin.stat().st_mtime, tuple(dates))
    return None


def note_methode(reel: bool, texte: str):
    """Petite note discrète, affichée seulement quand les résultats du modèle ne sont pas disponibles."""
    if not reel:
        st.caption(texte)


# ----------------------------------------------------------
# Réglages partagés (barre latérale)
# ----------------------------------------------------------
def prix() -> float:
    return float(st.session_state.get("prix_kwh", 1.2))


def souscrite() -> float:
    return float(st.session_state.get("puissance_souscrite", 6.0))


def sidebar_commun(df: pd.DataFrame):
    logo, icone = ASSETS / ("logo_nuit.svg" if sombre() else "logo.svg"), ASSETS / "icon.svg"
    if logo.exists():
        st.logo(str(logo), icon_image=str(icone) if icone.exists() else None, size="large")
    st.session_state.setdefault("prix_kwh", 1.2)
    st.session_state.setdefault("puissance_souscrite", 6.0)
    with st.sidebar:
        st.toggle("Mode nuit", key="mode_nuit", help="Passe l'application en thème sombre.")
        st.markdown("**Réglages**")
        st.number_input("Prix du kWh (MAD)", min_value=0.0, step=0.1, key="prix_kwh")
        st.number_input("Puissance souscrite (kW)", min_value=1.0, step=0.5, key="puissance_souscrite")
        st.caption(
            f"Données du {df['timestamp'].min():%d/%m/%Y} au {df['timestamp'].max():%d/%m/%Y}. "
            f"{df['is_interpolated'].mean():.1%} des heures reconstituées par interpolation."
        )


# ----------------------------------------------------------
# Calculs
# ----------------------------------------------------------
def fmt(x, dec=0) -> str:
    return f"{x:,.{dec}f}".replace(",", "\u202f")


def par_jour(d: pd.DataFrame) -> pd.Series:
    """kWh par jour = puissance moyenne x 24 h (reste juste si quelques heures manquent)."""
    return (d.set_index("timestamp")["power_kW"].resample("D").mean() * 24).dropna()


def agreger(d: pd.DataFrame, freq: str, col: str = "power_kW", energie: bool = False) -> pd.Series:
    """Agrège à l'heure ('h'), au jour ('D'), à la semaine ('W') ou au mois ('MS')."""
    s = d.set_index("timestamp")[col].resample(freq).mean().dropna()
    if energie:
        if freq == "D":
            s = s * 24
        elif freq == "W":
            s = s * 168
        elif freq == "MS":
            s = s * (s.index.days_in_month * 24)
    return s


# ----------------------------------------------------------
# Graphes et tableaux (suivent le thème)
# ----------------------------------------------------------
def style_fig(fig, titre: str, hauteur: int = 340, hover: str = "x unified"):
    p = palette()
    fig.update_layout(
        title=dict(text=titre, x=0, font=dict(size=16, color=p["texte"])),
        height=hauteur,
        margin=dict(l=0, r=0, t=50, b=0),
        template="plotly_dark" if sombre() else "plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Sans, Segoe UI, sans-serif", color=p["texte"]),
        legend=dict(orientation="h", y=-0.2, x=0),
        hovermode=hover,
    )
    if sombre():
        # Le bleu nuit des courbes devient clair, les liserés blancs prennent la couleur du fond.
        s = pio.to_json(fig)
        for ancien, nouveau in (('"#12303F"', '"#E6EEF2"'), ('"#F0F6F8"', '"#16303D"'), ('"white"', f'"{p["fond"]}"')):
            s = s.replace(ancien, nouveau)
        fig = pio.from_json(s)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        fig.update_xaxes(gridcolor="#1E3340", zerolinecolor="#1E3340")
        fig.update_yaxes(gridcolor="#1E3340", zerolinecolor="#1E3340")
    return fig


def afficher(fig):
    """Affiche un graphique en gardant exactement nos couleurs (clair ou nuit)."""
    st.plotly_chart(fig, theme=None)


def afficher_tableau(df: pd.DataFrame, formats: dict | None = None, hauteur: int = 360, max_lignes: int = 500):
    """Tableau HTML qui suit le thème clair/sombre (plus lisible qu'une grille en mode nuit)."""
    formats = formats or {}
    t = df.head(max_lignes).copy()
    for col, f in formats.items():
        if col in t.columns:
            t[col] = t[col].map(lambda v, f=f: "—" if pd.isna(v) else (f(v) if callable(f) else f.format(v)))
    html = t.to_html(index=False, border=0, escape=True, na_rep="—").replace("\n\n", "\n")
    st.markdown(f'<div class="tbl" style="max-height:{hauteur}px">{html}</div>', unsafe_allow_html=True)
    if len(df) > max_lignes:
        st.caption(f"Les {max_lignes} premières lignes sur {len(df)} sont affichées. Le CSV contient tout.")


def en_tete(titre: str, sous_titre: str):
    st.title(titre)
    st.markdown(f'<p class="sous-titre">{sous_titre}</p>', unsafe_allow_html=True)