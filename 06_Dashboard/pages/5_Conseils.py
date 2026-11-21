"""Conseils : recommandations personnalisées calculées à partir de vos données."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.common import afficher

from src.common import (AMBER, NAVY, TEAL, TEAL_LIGHT, ZONES, charger_donnees, en_tete, fmt, par_jour,
                        prix, souscrite, style_fig)

df = charger_donnees()
en_tete("Conseils", "Des pistes concrètes pour réduire votre consommation, calculées sur vos 12 derniers mois.")

an = df[df["timestamp"] > df["timestamp"].max() - pd.Timedelta(days=365)]
jour = par_jour(an)
kwh_an = jour.mean() * 365
facture = kwh_an * prix()
moy = an["power_kW"].mean()

# ---------------- Calculs de base ----------------
nuit = an[an["timestamp"].dt.hour.between(2, 5)]["power_kW"].mean()
veille_kwh, veille_cout = nuit * 8760, nuit * 8760 * prix()
zones = an[list(ZONES)].sum()
part = zones / zones.sum()
soir = an[an["timestamp"].dt.hour.between(18, 21)]["power_kW"].sum() / an["power_kW"].sum()
m = an.groupby(an["timestamp"].dt.month)["power_kW"].mean()
hiver, ete = m.reindex([12, 1, 2]).dropna(), m.reindex([6, 7, 8]).dropna()
ecart_saison = (hiver.mean() / ete.mean() - 1) * 100 if len(hiver) and len(ete) and ete.mean() > 0 else None
h_risque = int((an["power_kW"] >= 0.9 * souscrite()).sum())

k1, k2, k3 = st.columns(3)
k1.metric("Consommation sur 12 mois", f"{fmt(kwh_an)} kWh")
k2.metric("Facture estimée", f"{fmt(facture)} MAD")
k3.metric("Consommation de veille", f"{veille_kwh:,.0f} kWh/an".replace(",", "\u202f"),
          help="Puissance moyenne entre 2 h et 5 h du matin, maintenue toute l'année.")
st.write("")

# ---------------- Conseils personnalisés ----------------
conseils = []
ratio_veille = nuit / moy
if ratio_veille > 0.3:
    conseils.append(("haute", "Réduire la consommation de nuit",
                     f"Entre 2 h et 5 h, la maison consomme encore {nuit:.2f} kW, soit {ratio_veille * 100:.0f} % de sa "
                     f"consommation moyenne. Cela représente environ {fmt(veille_cout)} MAD par an. "
                     "Débranchez les appareils en veille (multiprises à interrupteur) et vérifiez ce qui tourne la nuit."))
else:
    conseils.append(("bon", "Consommation de nuit maîtrisée",
                     f"La consommation entre 2 h et 5 h ({nuit:.2f} kW) reste faible par rapport à la moyenne."))
if part["eau_clim_kwh"] > 0.25:
    conseils.append(("haute", "Chauffe-eau et climatisation : le poste le plus lourd",
                     f"Ils représentent {part['eau_clim_kwh'] * 100:.0f} % de la consommation mesurée. "
                     "Réglez le chauffe-eau autour de 55 °C, programmez-le hors des pics et réglez la climatisation "
                     "à 25–26 °C."))
if soir > 0.28:
    conseils.append(("moyenne", "Étaler la consommation du soir",
                     f"{soir * 100:.0f} % de l'énergie est consommée entre 18 h et 22 h. "
                     "Lancez lave-linge et lave-vaisselle en journée ou en différé pour lisser le pic et éviter la surcharge."))
if ecart_saison is not None and ecart_saison > 25:
    conseils.append(("moyenne", "Préparer la saison froide",
                     f"L'hiver consomme {ecart_saison:.0f} % de plus que l'été. Isolation des ouvertures, entretien du "
                     "chauffage et régulation de la température sont les leviers les plus rentables."))
if h_risque > 0:
    conseils.append(("haute", "Éviter d'utiliser plusieurs gros appareils en même temps",
                     f"La puissance a dépassé 90 % de votre puissance souscrite ({souscrite():.1f} kW) pendant "
                     f"{h_risque} heure{'s' if h_risque > 1 else ''} sur les 12 derniers mois. Décalez les usages simultanés (four, lave-linge, "
                     "chauffe-eau) pour éviter le déclenchement du compteur."))
else:
    conseils.append(("bon", "Puissance souscrite adaptée",
                     "Aucun dépassement de 90 % de la puissance souscrite sur les 12 derniers mois."))

BADGE = {"haute": ":red-badge[Priorité haute]", "moyenne": ":orange-badge[À surveiller]", "bon": ":green-badge[Bon point]"}
st.subheader("Ce que nous recommandons")
for niveau in ("haute", "moyenne", "bon"):
    for n, titre, texte in [c for c in conseils if c[0] == niveau]:
        with st.container(border=True):
            st.markdown(f"{BADGE[n]}  **{titre}**")
            st.write(texte)

# ---------------- Simulateur d'économies ----------------
st.write("")
st.subheader("Combien pourriez-vous économiser ?")
st.caption("Choisissez de combien vous pensez réduire chaque poste. L'estimation s'applique à la consommation des 12 derniers mois.")
cols = st.columns(len(ZONES))
reductions = {}
for col, (c, (nom, _)) in zip(cols, ZONES.items()):
    reductions[c] = col.slider(nom, 0, 50, 10 if c in ("eau_clim_kwh", "autres_kwh") else 0, 5, format="%d %%")

eco_kwh = sum(part[c] * kwh_an * reductions[c] / 100 for c in ZONES)
eco_mad = eco_kwh * prix()
s1, s2 = st.columns([1, 1])
with s1:
    a, b = st.columns(2)
    a.metric("Économie par an", f"{fmt(eco_kwh)} kWh")
    b.metric("Gain sur la facture", f"{fmt(eco_mad)} MAD", help=f"Soit {eco_mad / facture * 100:.1f} % de la facture annuelle.")
    st.caption("Estimation indicative : elle suppose que les réductions s'appliquent à toute l'année.")
with s2:
    fig = go.Figure(go.Bar(x=["Facture actuelle", "Facture avec économies"], y=[facture, facture - eco_mad],
                           marker_color=[NAVY, TEAL], text=[f"{facture:,.0f} MAD".replace(",", "\u202f"),
                                                             f"{facture - eco_mad:,.0f} MAD".replace(",", "\u202f")],
                           textposition="outside"))
    fig.update_yaxes(rangemode="tozero", title_text="MAD par an")
    afficher(style_fig(fig, "Votre facture annuelle", hauteur=300, hover="closest"))

with st.expander("Comment ces conseils sont-ils calculés ?"):
    st.markdown(
        "- Les seuils sont appliqués aux **12 derniers mois** de données du foyer.\n"
        "- La **veille** est la puissance moyenne entre 2 h et 5 h du matin.\n"
        "- Les **postes** (cuisine, buanderie, chauffe-eau et clim., autres) viennent des 3 compteurs divisionnaires ; "
        "« autres » est le reste de la consommation.\n"
        "- Les économies sont des ordres de grandeur, pas des garanties."
    )
