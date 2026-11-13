# Smart_Energy_AI

## Project Overview
-------------------
Smart_Energy_AI est un système intelligent de surveillance et de prédiction de la consommation électrique d'une habitation, basé sur l'intelligence artificielle et les systèmes embarqués.

L'objectif du projet est de mesurer la consommation électrique globale de la maison, d'analyser les habitudes d'utilisation de l'électricité, de prévoir la consommation future et de détecter les comportements électriques inhabituels.

Le système vise également à aider les utilisateurs à mieux comprendre la consommation énergétique de leur habitation et à optimiser leur utilisation de l'électricité.
______________________________________________________________________________________________________________________
## Objectifs du projet
-----------------------
Les principaux objectifs de ce projet sont :
Surveiller la consommation électrique globale de l'habitation.
Analyser les habitudes de consommation des utilisateurs.
Prédire la consommation électrique future à l'aide de modèles de Machine Learning.
Détecter les consommations anormales et les risques de surcharge électrique.
Identifier les appareils les plus énergivores à partir de leurs caractéristiques techniques et de leur durée d'utilisation.
Fournir des recommandations pour réduire la consommation électrique.
Développer un prototype embarqué permettant de suivre la consommation en temps réel.
______________________________________________________________________________________________________________________
## Fonctionnalités principales
------------------------------
### Prédiction de la consommation électrique
Utiliser des modèles de Machine Learning pour prévoir la consommation électrique future de l'habitation à partir des données historiques.

### Détection des anomalies
Identifier les comportements inhabituels dans la consommation électrique et détecter les situations pouvant indiquer une anomalie ou un risque de surcharge.

### Analyse des appareils électriques
Estimer la consommation énergétique des différents appareils à partir de leur puissance nominale et de leur durée d'utilisation.

### Tableau de bord intelligent
Afficher les données de consommation, les graphiques, les prédictions et les résultats des analyses dans une interface simple et intuitive.

### Système embarqué
Développer un prototype permettant de collecter les données électriques et de transmettre les mesures pour leur analyse en temps réel.
______________________________________________________________________________________________________________________
## Technologies et outils utilisés
Intelligence artificielle et Machine Learning: Python, NumPy, Pandas, Scikit-learn, SciPy

Analyse et visualisation des données: Matplotlib, Seaborn, Jupyter Notebook, Streamlit

Systèmes embarqués: ESP32, Arduino, Raspberry Pi 5

Gestion du projet et collaboration: Git, GitHub, Visual Studio Code
______________________________________________________________________________________________________________________
## Organisation du projet

Smart_Energy_AI/
│
├── 01_Dataset/
│   ├── Raw/
│   └── Processed/
│
├── 02_Data_Preparation/
│   ├── notebooks/
│   └── src/
│
├── 03_Consumption_Prediction/
│   ├── notebooks/
│   ├── models/
│   └── src/
│
├── 04_Anomaly_Detection/
│   ├── notebooks/
│   ├── models/
│   └── src/
│
├── 05_Appliance_Analysis/
│   └── src/
│
├── 06_Dashboard/
│
├── 07_Hardware/
│   ├── ESP32/
│   ├── Raspberry_Pi/
│   └── Circuit_Diagrams/
│
├── 08_Integration/
│
├── 09_Documentation/
│
├── .gitignore
├── requirements.txt
└── README.md
______________________________________________________________________________________________________________________
##  Installation et configuration

###  Cloner le dépôt

```bash
git clone https://github.com/ouardaniikram05-ai/Smart_Energy_AI.git
cd Smart_Energy_AI
```

###  Créer l'environnement virtuel

```bash
python -m venv .venv
```

### Activer l'environnement virtuel sous Windows

```powershell
.\.venv\Scripts\Activate.ps1
```

### Installer les bibliothèques nécessaires

```bash
python -m pip install -r requirements.txt
```
## Remarque – Accès aux datasets

Pour accéder aux datasets nettoyés et préparés, les membres de l'équipe doivent récupérer la branche `develop` du dépôt GitHub.

### 1. Récupérer le projet

```bash
git clone -b develop https://github.com/ouardaniikram05-ai/Smart_Energy_AI.git
```

### 2. Localisation des datasets

Les fichiers sont disponibles dans `01_Dataset/Processed/` :

- `household_power_consumption_final.csv.gz` : dataset nettoyé (données à la minute).
- `household_hourly.csv.gz` : dataset préparé (données horaires).
- `readme.md` : documentation des datasets.

### 3. Charger un dataset avec Python

```python
import pandas as pd

df = pd.read_csv(
    "../../01_Dataset/Processed/household_power_consumption_final.csv.gz",
    compression="gzip",
    parse_dates=["Datetime"]
)
```

**Important :** Il n'est pas nécessaire de télécharger les datasets séparément. La commande `git clone` récupère automatiquement les fichiers présents dans la branche `develop`.
