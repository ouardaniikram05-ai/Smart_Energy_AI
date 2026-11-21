# Smart Energy AI ⚡

Dashboard interactif de suivi, prévision et analyse de la consommation électrique d'une habitation.

##  À propos du projet

Smart Energy AI est un dashboard **Streamlit** qui transforme des données brutes de consommation électrique en informations actionnables : suivi en temps réel, prévisions, détection d'anomalies, analyse par appareil et conseils d'économie d'énergie.

**Technologies utilisées :**
- Python 3.10+
- Streamlit (interface web)
- Plotly (visualisations interactives)
- Pandas & NumPy (traitement des données)

## Source des données

Toutes les données de consommation proviennent du fichier `household_hourly` :
- **Période** : du 16/12/2006 au 26/11/2010
- **Granularité** : une ligne par heure
- **Foyer** : foyer de référence (pas les données réelles de l'utilisateur)

### Colonnes principales

| Colonne | Signification |
|---|---|
| `power_kW` | Puissance moyenne de l'heure. Sur une heure, elle vaut aussi l'énergie en kWh. |
| `reactive_kW` | Puissance réactive (énergie qui circule sans produire de travail). |
| `voltage_V`, `intensity_A` | Tension du réseau et courant. |
| `sub_metering_1/2/3` | Trois compteurs par zone : cuisine, buanderie et réfrigérateur, chauffe-eau et climatisation. |
| « Autres usages » | Calculé : puissance totale moins les 3 zones mesurées. |
| `is_interpolated` | Heure reconstituée par le Membre 1 (aucune ne l'est dans ce fichier). |

### Précisions importantes

- Les « 7 derniers jours » et « 30 derniers jours » se comptent à partir de la **dernière date des données** (26/11/2010), pas d'aujourd'hui.
- Les chiffres sont des **moyennes horaires** : un pic de 6,6 kW par heure peut cacher un pic de 11 kW à la minute.

---

## Structure du dashboard

Le dashboard est organisé en 3 sections :

### 1. Vue générale
- **Accueil** : chiffres essentiels et vue d'ensemble

### 2. Analyse
- **Historique** : explorer la consommation passée en détail
- **Prédictions** : consommation prévue pour les prochains jours
- **Anomalies** : pics et comportements inhabituels détectés

### 3. Pilotage
- **Appareils** : coût et consommation de chaque appareil
- **Conseils** : pistes concrètes pour réduire la facture

---

##  Guide page par page

### Accueil

Page de synthèse avec les indicateurs clés pour répondre rapidement à « y a-t-il un problème ? »

| Donnée | Calcul | Signification |
|---|---|---|
| **Statut** (vert, orange, rouge) | Rouge : dépassement de la puissance souscrite ou anomalie confirmée par 3 méthodes dans la semaine. Orange : anomalie à 2 méthodes, dépassement dans le mois ou tendance supérieure à +25 %. | Réponse rapide à « y a-t-il un problème ? » |
| **Énergie, coût, moyenne par jour** | Puissance moyenne × 24 h, sommée sur la période. Coût = kWh × prix du kWh. | Combien la maison consomme et ce que ça coûte |
| **Pic de puissance** | Maximum de la puissance horaire | Le moment le plus chargé |
| **% du compteur utilisé** | Pic des 30 jours ÷ puissance souscrite | Marge restante avant la limite du compteur |
| **Anomalies (7 jours)** | Épisodes d'au moins 10 minutes de `consensus_anomalies.csv` | Comportements inhabituels récents |
| **Dépassements (30 jours)** | Périodes de `overload_periods.csv` au-dessus de la puissance souscrite | Risque de disjonction |
| **Tendance** | 7 derniers jours comparés aux 4 semaines d'avant | « Je consomme plus ou moins que d'habitude » |
| **Fenêtres de la maison** | Part de chaque zone sur 12 mois | Plus la fenêtre est éclairée, plus la zone consomme |
| **Journée type, moyenne par mois, hiver et été** | Moyennes par heure et par mois ; hiver = déc. à fév., été = juin à août | Habitudes et saisonnalité |

---

### Historique

Explorer la consommation passée avec filtres temporels et échelles de temps variables.

- **Énergie, coût, moyenne par jour, pic horaire** : mêmes calculs que l'accueil, sur la période choisie.
- **Courbe** : puissance (kW) ou énergie (kWh) à l'échelle heure, jour, semaine ou mois. La ligne pointillée est la moyenne.
- **Carte des rythmes** : puissance moyenne par jour de semaine et par heure. Elle montre quand la maison consomme le plus.
- **Semaine et week-end** : deux profils de journée comparés.
- **Comparaison annuelle** : kWh par jour, mois par mois, année par année.
- **Tension** : normale entre 207 et 253 V (230 V ± 10 %). « Heures hors plage » est la part des heures en dehors.
- **Facteur de puissance** : P ÷ √(P² + Q²). Proche de 1, l'énergie est bien utilisée. C'est une approximation calculée sur des moyennes horaires.
- **Intensité** : le courant moyen et son maximum.

---

###  Prédictions

Consommation prévue pour les prochaines heures et jours.

| Donnée | Calcul | Signification |
|---|---|---|
| **Prévision** | Si `data/predictions.csv` existe, il est utilisé. Sinon : moyenne des 4 semaines précédentes à la même heure. | Consommation attendue |
| **Énergie et coût prévus** | Somme de la puissance prévue sur l'horizon choisi, puis × prix | Facture attendue |
| **Précision** | 100 % − (somme des écarts ÷ somme du réel) sur les 14 derniers jours | Fiabilité de la prévision. Avec la méthode de repli, elle est d'environ 58 %. |
| **Marge d'incertitude** | ± 1,28 × l'écart-type des erreurs passées | La consommation réelle devrait y rester 8 fois sur 10 |

**Note** : Les « prochains jours » commencent après la dernière mesure (26/11/2010).

---

### Anomalies

Détection d'épisodes anormaux et de surcharges de puissance.

#### Anomalies de consommation
- **Épisode** : minutes anormales consécutives (écart maximal de 5 minutes), de `consensus_anomalies.csv`. Les trois méthodes sont Isolation Forest, Z-score et LOF.
- **Confirmation** : « 2 sur 3 » signifie deux méthodes d'accord, « 3 sur 3 » les trois.
- **Indicateurs** : nombre d'épisodes, nombre de confirmés par 3 méthodes, durée cumulée, heure de la journée la plus touchée.

#### Surcharge de puissance
- **Surcharge** (`overload_periods.csv`) : une période où la puissance à la minute atteint **la puissance souscrite**. Les indicateurs sont le nombre de dépassements, leur durée cumulée, la puissance maximale (9,7 kW) et le plus long dépassement (63 min). Sur le graphique, la taille d'une bulle représente la durée.

#### Forte charge
- **Forte charge** (`hourly_` et `daily_overload_analysis.csv`) : part du temps passé au-dessus du seuil de forte charge du Membre 3, par heure de la journée et par jour.

#### Comparaison des méthodes
- Bloc replié : part d'anomalies de chaque méthode et combinaisons de méthodes d'accord.

**Distinction importante** :
- Une **anomalie** est un écart aux habitudes
- Une **surcharge** est le dépassement de la limite du compteur
- Une **forte charge** est un seuil statistique du Membre 3

---

### Appareils

Estimation de la consommation par appareil et comparaison avec les mesures réelles.

| Donnée | Origine | Calcul |
|---|---|---|
| **Nom, puissance (W), heures par jour, quantité** | Saisis par l'utilisateur (valeurs types indicatives du catalogue) | — |
| **kWh par mois** | Calculé | W × h × quantité ÷ 1000 × jours du mois |
| **Coût** | Calculé | kWh × prix du kWh |
| **Puissance si tout est allumé** | Calculé | Somme de W × quantité, comparée à la puissance souscrite (alerte dès 80 %) |
| **Estimé et mesuré** | Mesuré sur 12 mois | Consommation moyenne par jour × jours du mois |
| **« Liste complète ? »** | Calculé | Estimé ÷ mesuré (47 % par défaut, donc il manque des appareils) |

---

### Conseils

Recommandations personnalisées basées sur l'analyse des 12 derniers mois.

**Note** : Tout est calculé sur les **12 derniers mois**, avec des règles fixes. Ce ne sont ni des normes ni de l'apprentissage automatique.

| Conseil | Condition de déclenchement |
|---|---|
| **Consommation de nuit** | La puissance moyenne entre 2 h et 5 h dépasse 30 % de la moyenne |
| **Chauffe-eau et climatisation** | Ce poste représente plus de 25 % de la consommation |
| **Soir** | Plus de 28 % de l'énergie entre 18 h et 22 h |
| **Saison froide** | L'hiver consomme plus de 25 % de plus que l'été |
| **Surcharge** | Au moins une heure au-dessus de 90 % de la puissance souscrite |

**Veille** : puissance moyenne entre 2 h et 5 h × 8 760 h, soit une estimation de ce qui tourne toute l'année.

**Simulateur** : économie = part de chaque poste × kWh par an × réduction choisie. Les résultats donnent un ordre de grandeur, pas une garantie.

---

##  Mises en garde importantes

Ces points sont essentiels à comprendre :

1. **Données de référence** : Les données sont celles d'un foyer de référence, pas celles de la maison de l'utilisateur. Le capteur de la Partie B changera cela.

2. **Seuils des Conseils** : Les seuils (30 %, 25 %, 28 %) sont des choix de conception, pas des normes officielles.

3. **Période des anomalies** : Les anomalies ne couvrent que la période depuis février 2010.

4. **Granularité temporelle** : Les moyennes horaires cachent les pics à la minute, c'est pourquoi les surcharges viennent d'un fichier à la minute.




