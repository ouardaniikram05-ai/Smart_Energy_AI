# Dataset – Smart_Energy_AI

## 1. Source des données

- **Nom :** Individual Household Electric Power Consumption
- **Source :** UCI Machine Learning Repository
- **Lien :** https://archive.ics.uci.edu/dataset/235/individual+household+electric+power+consumption
- **Période :** 16/12/2006 au 26/11/2010
- **Fréquence :** une mesure par minute.

## 2. Dataset nettoyé

- **Fichier :** `household_power_consumption_final.csv.gz`
- **Format :** CSV compressé (GZIP)
- **Lignes :** 2 049 280
- **Colonnes :** 10
- **Valeurs manquantes :** 0

## 3. Description des colonnes

| Colonne | Description | Unité |
|---|---|---|
| Date | Date de mesure | - |
| Time | Heure de mesure | - |
| Global_active_power | Puissance active globale | kW |
| Global_reactive_power | Puissance réactive globale | kW |
| Voltage | Tension électrique | V |
| Global_intensity | Intensité électrique | A |
| Sub_metering_1 | Sous-compteur cuisine | Wh/min |
| Sub_metering_2 | Sous-compteur buanderie | Wh/min |
| Sub_metering_3 | Sous-compteur chauffe-eau et climatisation | Wh/min |
| Datetime | Date et heure combinées | - |

## 4. Nettoyage effectué

- Remplacement des symboles `?` par des valeurs manquantes.
- Suppression des lignes dont toutes les mesures électriques étaient manquantes.
- Conversion des variables électriques en valeurs numériques.
- Création de la colonne `Datetime`.
- Tri chronologique des données.
- Vérification des doublons et des valeurs manquantes.

Les valeurs extrêmes ont été conservées pour permettre leur étude dans la détection des anomalies.

## 5. Chargement avec Python

```python
import pandas as pd

df = pd.read_csv(
    "01_Dataset/Processed/household_power_consumption_final.csv.gz",
    compression="gzip",
    parse_dates=["Datetime"]
)

print(df.shape)
print(df.head())
```

## 6. Utilisation dans le projet

Ce dataset constitue la base commune pour :

- La prédiction de consommation électrique.
- La détection des anomalies.
- L'analyse des variables électriques.
- La visualisation des consommations.

## 7. Dataset horaire

- **Fichier :** `household_hourly.csv.gz`, 34 159 lignes (une par heure), aucune valeur manquante.
- **Attention :** la série a 7 sauts temporels (coupures de 15 h à 5 jours) ; la colonne `is_interpolated` (8 heures) sert à l'évaluation, pas comme variable d'entrée.

**Projet : Smart_Energy_AI**