# ⚡ Smart Energy AI

## Détection intelligente des anomalies et analyse des consommations électriques

---

## 1. Présentation du projet

**Smart Energy AI** est un projet d'intelligence artificielle consacré à l'analyse des consommations électriques et à la détection des anomalies énergétiques.

Ce projet utilise des méthodes statistiques et des algorithmes de Machine Learning non supervisé afin d'identifier les comportements inhabituels dans les données de consommation électrique.

L'objectif principal est de détecter les anomalies, analyser les dépassements de puissance et comparer différentes méthodes de détection pour mieux comprendre les comportements énergétiques.

## 2. Objectifs du projet

Les principaux objectifs sont :

- Étudier les données de consommation électrique.
- Comprendre les caractéristiques et les comportements de consommation.
- Nettoyer et préparer les données avant leur analyse.
- Détecter les anomalies à l'aide de méthodes statistiques et de Machine Learning.
- Analyser l'évolution de la consommation énergétique.
- Identifier et visualiser les dépassements de puissance.
- Comparer les résultats des différents modèles.
- Évaluer les accords et les différences entre les méthodes de détection.

## 3. Méthodes de détection utilisées

Le projet repose sur trois méthodes principales.

### 3.1 Z-score

Le Z-score est une méthode statistique qui mesure l'éloignement d'une observation par rapport à la moyenne.

Il utilise la moyenne et l'écart-type pour identifier les valeurs inhabituelles.

Dans notre projet, une observation est considérée comme suspecte lorsque :

\[
|Z| > 3
\]

### 3.2 Isolation Forest

Isolation Forest est un algorithme de Machine Learning non supervisé spécialisé dans la détection des anomalies.

Son principe consiste à isoler les observations à travers des divisions aléatoires.

Les observations qui sont isolées plus facilement sont considérées comme potentiellement anormales.

### 3.3 Local Outlier Factor (LOF)

LOF est un algorithme de détection des anomalies basé sur la densité locale.

Il compare la densité d'une observation avec celle de ses voisins.

Une observation présentant une densité locale nettement plus faible que celle de ses voisins peut être considérée comme une anomalie.

## 4. Architecture du projet

Le projet est organisé de la manière suivante :

```text
Smart_Energy_AI/
│
├── anomaly_detection/
│   │
│   ├── 01_etude_anomalies.py
│   ├── 02_data_preprocessing.py
│   ├── 03_detection_models.py
│   ├── 04_consumption_analysis.py
│   ├── 05_overload_analysis.py
│   ├── 06_evaluation.py
│   │
│   ├── PLAN_DETECTION_ANOMALIES.md
│   └── PROGRESSION_PROJET.md
│
├── data/
│
├── results/
│
├── README.md
│
└── .gitignore
```

## 5. Étapes de réalisation

Le projet est divisé en six grandes parties.

| Partie | Description |
|---|---|
| 01 | Étude exploratoire des anomalies |
| 02 | Prétraitement et préparation des données |
| 03 | Détection des anomalies avec trois modèles |
| 04 | Analyse énergétique et consommation |
| 05 | Analyse et visualisation des dépassements |
| 06 | Évaluation et comparaison des modèles |

### Partie 1 : Étude exploratoire

Cette étape permet de découvrir le dataset, comprendre ses variables, étudier les distributions et identifier les premières caractéristiques des consommations électriques.

### Partie 2 : Prétraitement des données

Cette étape consiste à préparer les données pour les rendre exploitables par les méthodes d'analyse et les algorithmes de Machine Learning.

### Partie 3 : Détection des anomalies

Trois méthodes sont utilisées :

- Z-score
- Isolation Forest
- Local Outlier Factor (LOF)

Chaque méthode produit ses propres prédictions concernant les observations normales et anormales.

### Partie 4 : Analyse énergétique

Cette partie permet d'étudier les consommations électriques, leur évolution et leurs caractéristiques statistiques.

### Partie 5 : Analyse et visualisation des dépassements

Cette étape permet d'identifier les dépassements de puissance, d'étudier leur fréquence et leur répartition temporelle et de représenter les résultats graphiquement.

### Partie 6 : Évaluation des modèles

Cette dernière partie permet de comparer les résultats des trois méthodes, d'étudier les anomalies détectées individuellement et d'analyser les accords entre les modèles.

## 6. Résultats de l'évaluation

Lors de l'évaluation, les trois méthodes ont analysé **409 856 observations**.

Les résultats obtenus sont les suivants :

| Modèle | Anomalies détectées | Pourcentage |
|---|---:|---:|
| Isolation Forest | 41 944 | 10,23 % |
| Z-score | 21 139 | 5,16 % |
| LOF | 12 456 | 3,04 % |

### Analyse du consensus

La comparaison des prédictions a également permis d'obtenir les résultats suivants :

- **21 991 observations** ont été détectées comme anormales par au moins deux modèles.
- **1 269 observations** ont été détectées comme anormales par les trois modèles.
- Le pourcentage de consensus majoritaire est de **5,37 %**.

Ces résultats montrent que les trois méthodes n'identifient pas exactement les mêmes observations, car elles reposent sur des principes de détection différents.

### Interprétation

Isolation Forest a identifié le plus grand nombre d'anomalies dans cette expérience.

Cependant, le nombre d'anomalies détectées ne suffit pas à déterminer quel modèle est le plus performant. Il faut également tenir compte de la pertinence des observations identifiées et, si des données de référence sont disponibles, de métriques d'évaluation adaptées.

## 7. Technologies utilisées

Les principales technologies et bibliothèques utilisées sont :

- **Python** : langage de programmation.
- **Pandas** : manipulation et analyse des données.
- **NumPy** : calculs numériques.
- **Matplotlib** : visualisation graphique.
- **Scikit-learn** : implémentation des algorithmes de Machine Learning.
- **Machine Learning non supervisé** : détection des comportements inhabituels.

## 8. Installation du projet

### Prérequis

- Python 3.x
- pip
- Visual Studio Code (recommandé)

### Installation des bibliothèques

Ouvrir un terminal dans le dossier du projet et exécuter :

```bash
pip install pandas numpy matplotlib scikit-learn
```

### Exécution

Lancer les scripts dans l'ordre :

```bash
python anomaly_detection/01_etude_anomalies.py

python anomaly_detection/02_data_preprocessing.py

python anomaly_detection/03_detection_models.py

python anomaly_detection/04_consumption_analysis.py

python anomaly_detection/05_overload_analysis.py

python anomaly_detection/06_evaluation.py
```

**Important :** les fichiers de données d'entrée doivent être disponibles dans les emplacements attendus par les scripts. Certaines parties utilisent également les résultats générés par les étapes précédentes.

## 9. Conclusion

Le projet **Smart Energy AI** propose une approche d'analyse intelligente des consommations électriques basée sur les méthodes statistiques et le Machine Learning non supervisé.

L'utilisation de Z-score, Isolation Forest et LOF permet de comparer plusieurs approches de détection et d'identifier des comportements inhabituels dans les données énergétiques.

L'analyse des consommations, la visualisation des dépassements et l'évaluation comparative des modèles permettent d'obtenir une meilleure compréhension des anomalies électriques.

Ce projet représente une application de l'intelligence artificielle dans le domaine de la gestion et de la surveillance énergétique.

---

**Projet : Smart Energy AI**

**Domaine :** Intelligence artificielle, Machine Learning et Génie électrique.
