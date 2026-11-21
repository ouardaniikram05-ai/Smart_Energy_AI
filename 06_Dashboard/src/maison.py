"""Bandeau d'accueil : maison moderne interactive (survol = consommation de chaque zone)."""
import random
from html import escape

AMBRE = "#E8A317"

CSS_HERO = """
<style>
.hero { position: relative; display: grid; grid-template-columns: minmax(320px, 1.15fr) minmax(360px, 1.2fr);
        align-items: center; gap: 8px; border-radius: 18px; padding: 30px 34px 12px 38px; overflow: hidden;
        border: 1px solid var(--hero-bord); background: var(--hero-fond); margin-bottom: 1.2rem;
        box-shadow: 0 18px 50px -24px rgba(8, 20, 30, .55); }
.hero h1 { font-size: 2.5rem; line-height: 1.1; margin: .1rem 0 .35rem 0; color: var(--hero-titre) !important; }
.hero .bonjour { margin: 0; letter-spacing: .14em; text-transform: uppercase; font-size: .78rem; color: var(--hero-doux) !important; }
.hero .lieu { margin: 0 0 1rem 0; color: var(--hero-doux) !important; font-size: 1rem; }
.hero .pastille { display: inline-flex; align-items: center; gap: 8px; padding: 6px 14px; border-radius: 999px;
                  font-size: .9rem; font-weight: 500; color: #fff !important; }
.hero .pastille i { width: 9px; height: 9px; border-radius: 50%; background: #fff; display: inline-block;
                    animation: pouls 2s ease-in-out infinite; }
.hero .vert { background: #2E9E6B; } .hero .orange { background: #E08A12; } .hero .rouge { background: #D64545; }
.hero .chips { display: flex; gap: 10px; flex-wrap: wrap; margin-top: 1.2rem; }
.hero .chip { background: var(--hero-chip); border: 1px solid var(--hero-bord); border-radius: 12px; padding: 8px 12px;
              backdrop-filter: blur(6px); min-width: 96px; }
.hero .chip b { display: block; font-size: 1.1rem; color: var(--hero-titre) !important; font-weight: 600; }
.hero .chip span { font-size: .78rem; color: var(--hero-doux) !important; }
.hero .astuce { font-size: .8rem; color: var(--hero-doux) !important; margin: 0 0 6px 0; text-align: right; }
.hero svg { width: 100%; height: auto; display: block; }
.hero .zone { cursor: pointer; }
.hero .zone .lueur { animation: respire 5s ease-in-out infinite; transition: opacity .3s; }
.hero .zone:hover .lueur { opacity: 1 !important; animation: none; }
.hero .zone:hover .cadre { stroke: #E8A317; stroke-width: 2.4; }
.hero .bulle { opacity: 0; transition: opacity .25s, transform .25s; transform: translateY(6px); pointer-events: none; }
.hero .zone:hover .bulle { opacity: 1; transform: translateY(0); }
.hero .etoile { animation: scintille 4s ease-in-out infinite; }
.hero .vague { animation: ondule 6s ease-in-out infinite; }
@keyframes respire { 0%, 100% { opacity: var(--l, .8); } 50% { opacity: calc(var(--l, .8) * .78); } }
@keyframes scintille { 0%, 100% { opacity: .25; } 50% { opacity: 1; } }
@keyframes pouls { 0%, 100% { opacity: 1; } 50% { opacity: .35; } }
@keyframes ondule { 0%, 100% { transform: translateX(0); } 50% { transform: translateX(7px); } }
@media (max-width: 900px) { .hero { grid-template-columns: 1fr; } .hero h1 { font-size: 2rem; } }
</style>
"""

THEMES = {
    "clair": dict(fond="linear-gradient(135deg, #EAF3F6 0%, #F8F4EA 100%)", bord="#D5E1E7", titre="#12303F",
                  doux="#52656F", chip="rgba(255,255,255,.72)"),
    "sombre": dict(fond="linear-gradient(135deg, #07111A 0%, #12303F 100%)", bord="#25394A", titre="#F1F6F8",
                   doux="#9DB0BC", chip="rgba(255,255,255,.06)"),
}


def _svg(zones: dict, nuit: bool) -> str:
    """zones : {code: (libellé, part en %, kWh)} avec codes 'salon', 'cuisine', 'buanderie', 'eau'."""
    c = dict(
        sol="#0E1E28" if nuit else "#D3E0E6", mur="#98A8B3" if nuit else "#F7F8F8", mur_b="#2A3C48" if nuit else "#C7D2D8",
        bois="#7A5A3E", dalle="#16242E" if nuit else "#22343F", vitre_h="#33546A" if nuit else "#A9CBD9",
        vitre_b="#12222D" if nuit else "#E4F0F5", texte="#F1F6F8" if nuit else "#12303F",
        bulle="#0F1D26" if nuit else "#FFFFFF", bulle_b="#E8A317",
    )
    maxi = max(p for _, p, _ in zones.values()) or 1

    def glow(code):  # intensité de la lueur selon la part de consommation
        return round((0.30 + 0.70 * zones[code][1] / maxi) if nuit else (0.10 + 0.55 * zones[code][1] / maxi), 2)

    def zone(code, x, y, w, h):
        lib, part, kwh = zones[code]
        l1, l2 = escape(lib), f"{part:.0f} % · {kwh:,.0f} kWh".replace(",", "\u202f")
        bw = max(len(l1), len(l2)) * 7.7 + 30
        bx, by = x + w / 2 - bw / 2, y - 56
        bx = min(max(bx, 6), 620 - bw - 6)
        return (
            f'<g class="zone" tabindex="0">'
            f'<rect class="cadre" x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="url(#vitre)" stroke="{c["mur_b"]}" stroke-width="1.4"/>'
            f'<rect class="lueur" x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="url(#lueur)" style="--l:{glow(code)};opacity:{glow(code)}"/>'
            f'<line x1="{x + w / 2}" y1="{y}" x2="{x + w / 2}" y2="{y + h}" stroke="{c["mur_b"]}" stroke-width="1.2" opacity=".7"/>'
            f'<g class="bulle"><rect x="{bx:.0f}" y="{by}" width="{bw:.0f}" height="44" rx="10" fill="{c["bulle"]}" stroke="{c["bulle_b"]}" stroke-width="1.3"/>'
            f'<text x="{bx + bw / 2:.0f}" y="{by + 19}" text-anchor="middle" font-size="13.5" font-weight="600" fill="{c["texte"]}" font-family="IBM Plex Sans, Segoe UI, sans-serif">{l1}</text>'
            f'<text x="{bx + bw / 2:.0f}" y="{by + 36}" text-anchor="middle" font-size="12.5" fill="{c["texte"]}" opacity=".8" font-family="IBM Plex Sans, Segoe UI, sans-serif">{l2}</text></g></g>'
        )

    rnd = random.Random(7)
    ciel = ""
    if nuit:
        for _ in range(34):
            ciel += (f'<circle class="etoile" cx="{rnd.randint(14, 606)}" cy="{rnd.randint(8, 120)}" r="{rnd.choice([0.8, 1.1, 1.5])}" '
                     f'fill="#fff" style="animation-delay:{rnd.random() * 4:.1f}s"/>')
        ciel += ('<circle cx="540" cy="52" r="34" fill="url(#halo)"/><circle cx="540" cy="52" r="15" fill="#F3EFD8"/>'
                 '<circle cx="546" cy="48" r="13" fill="#0B1923" opacity=".92"/>')
    else:
        ciel += '<circle cx="545" cy="55" r="46" fill="url(#halo)"/><circle cx="545" cy="55" r="17" fill="#F6C453"/>'

    def palmier(x, h, inc):
        fr = "".join(
            f'<path d="M0 0 q{dx * .55} -20 {dx} {6 + abs(dx) * .35}" stroke="#2F6B4F" stroke-width="3.4" fill="none" stroke-linecap="round"/>'
            for dx in (-40, -28, -15, 15, 28, 40))
        sommet = f"{x + inc / 2:.0f} {250 - h}"
        return (f'<path d="M{x} 250 q{inc} {-h / 2} {inc / 2} {-h}" stroke="#6B5239" stroke-width="5" fill="none" stroke-linecap="round"/>'
                f'<g transform="translate({sommet})">{fr}<path d="M0 0 q0 -14 0 -22" stroke="#2F6B4F" stroke-width="3.2" fill="none" stroke-linecap="round"/></g>')

    lattes = "".join(f'<line x1="{x}" y1="94" x2="{x}" y2="150" stroke="#5E4430" stroke-width="1.2" opacity=".55"/>' for x in range(182, 420, 9))
    vagues = "".join(
        f'<line class="vague" x1="{440 + i * 11}" y1="{270 + (i % 3) * 8}" x2="{462 + i * 11}" y2="{270 + (i % 3) * 8}" stroke="#fff" stroke-width="1.3" opacity=".5" style="animation-delay:{i * .5}s"/>'
        for i in range(7))

    return f"""<svg viewBox="0 0 620 330" role="img" aria-label="Maison moderne : survolez une fenêtre pour voir la consommation de la zone">
<defs>
<linearGradient id="vitre" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c['vitre_h']}"/><stop offset="1" stop-color="{c['vitre_b']}"/></linearGradient>
<radialGradient id="lueur" cx=".5" cy=".6" r=".8"><stop offset="0" stop-color="#FFD27A"/><stop offset="1" stop-color="#E8A317"/></radialGradient>
<radialGradient id="halo"><stop offset="0" stop-color="{'#8FB4C9' if nuit else '#F6C453'}" stop-opacity=".45"/><stop offset="1" stop-color="{'#8FB4C9' if nuit else '#F6C453'}" stop-opacity="0"/></radialGradient>
<linearGradient id="piscine" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3FB6C8"/><stop offset="1" stop-color="#1B7F95"/></linearGradient>
</defs>
{ciel}
<rect x="0" y="250" width="620" height="80" fill="{c['sol']}"/>
<ellipse cx="240" cy="252" rx="250" ry="7" fill="#000" opacity="{'.35' if nuit else '.10'}"/>
{palmier(66, 120, 16)}{palmier(560, 104, -14)}
<rect x="70" y="150" width="330" height="100" fill="{c['mur']}" stroke="{c['mur_b']}" stroke-width="1.2"/>
<rect x="170" y="92" width="252" height="58" fill="{c['bois']}"/>
{lattes}
<rect x="60" y="143" width="350" height="8" rx="1.5" fill="{c['dalle']}"/>
<rect x="158" y="84" width="276" height="8" rx="1.5" fill="{c['dalle']}"/>
{zone('eau', 196, 104, 196, 34)}
{zone('buanderie', 336, 190, 50, 50)}
{zone('cuisine', 254, 168, 66, 72)}
{zone('salon', 90, 168, 150, 72)}
<rect x="418" y="262" width="176" height="38" rx="6" fill="url(#piscine)"/>
{vagues}
<rect x="414" y="258" width="184" height="4" rx="2" fill="{c['mur_b']}"/>
</svg>"""


def hero_html(nom: str, sous_titre: str, zones: dict, etat: dict, chips: list, nuit: bool) -> str:
    t = THEMES["sombre" if nuit else "clair"]
    style = (f'<div class="hero" style="--hero-fond:{t["fond"]};--hero-bord:{t["bord"]};--hero-titre:{t["titre"]};'
             f'--hero-doux:{t["doux"]};--hero-chip:{t["chip"]}">')
    puces = "".join(f'<div class="chip"><b>{escape(v)}</b><span>{escape(l)}</span></div>' for v, l in chips)
    texte = (f'<div><p class="bonjour">Bonjour</p><h1>{escape(nom)}</h1><p class="lieu">{escape(sous_titre)}</p>'
             f'<span class="pastille {etat["niveau"]}"><i></i>{escape(etat["message"])}</span><div class="chips">{puces}</div></div>')
    maison = f'<div><p class="astuce">Survolez les fenêtres de la maison</p>{_svg(zones, nuit)}</div>'
    return CSS_HERO + style + texte + maison + "</div>"


def zones_depuis(df) -> dict:
    """Part de chaque zone sur les 12 derniers mois : {code: (libellé, %, kWh)}."""
    import pandas as pd
    from src.common import ZONES
    an = df[df["timestamp"] > df["timestamp"].max() - pd.Timedelta(days=365)]
    tot = an[list(ZONES)].sum()
    code = {"autres_kwh": "salon", "cuisine_kwh": "cuisine", "buanderie_kwh": "buanderie", "eau_clim_kwh": "eau"}
    return {code[c]: (ZONES[c][0], tot[c] / tot.sum() * 100, tot[c]) for c in ZONES}
