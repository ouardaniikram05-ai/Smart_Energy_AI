

# ==========================================
# SMART ENERGY AI
# PARTIE 3 : DETECTION DES ANOMALIES
# ==========================================

import pandas as pd
import numpy as np
import joblib

from pathlib import Path
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor

# ==========================================
# 1. CONFIGURATION ET CHARGEMENT
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "results" / "preprocessed"
RESULTS_DIR = BASE_DIR / "results"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_PATH = DATA_DIR / "X_train_normalise.csv"
TEST_PATH = DATA_DIR / "X_test_normalise.csv"
DATETIME_PATH = DATA_DIR / "Datetime_test.csv"

# Vérification des fichiers
for path in [TRAIN_PATH, TEST_PATH, DATETIME_PATH]:
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {path}"
        )

# Chargement des données
X_train = pd.read_csv(TRAIN_PATH)
X_test = pd.read_csv(TEST_PATH)

datetime_test = pd.read_csv(DATETIME_PATH)

datetime_test["Datetime"] = pd.to_datetime(
    datetime_test["Datetime"],
    errors="coerce"
)

if datetime_test["Datetime"].isnull().any():
    raise ValueError("Certaines dates de test sont invalides.")

if len(X_test) != len(datetime_test):
    raise ValueError(
        "Les dimensions des données et des dates ne correspondent pas."
    )

if X_train.empty or X_test.empty:
    raise ValueError("Le jeu d'entrainement ou de test est vide.")

if list(X_train.columns) != list(X_test.columns):
    raise ValueError("Les colonnes train et test ne correspondent pas.")

if not np.isfinite(X_train.to_numpy()).all():
    raise ValueError("Valeurs non finies détectées dans X_train.")

if not np.isfinite(X_test.to_numpy()).all():
    raise ValueError("Valeurs non finies détectées dans X_test.")

print("\n========== PARTIE 3 : DETECTION DES ANOMALIES ==========")

print("\nDonnees d'entrainement :", X_train.shape)
print("Donnees de test :", X_test.shape)

# Conversion en tableaux NumPy
X_train_np = X_train.to_numpy()
X_test_np = X_test.to_numpy()

# ==========================================
# 2. ISOLATION FOREST
# ==========================================

print("\n========== ISOLATION FOREST ==========")

model_if = IsolationForest(
    n_estimators=100,
    contamination="auto",
    random_state=42,
    n_jobs=-1
)

# Entrainement
model_if.fit(X_train_np)

print("Modele Isolation Forest entraine avec succes !")

# Prediction
predictions_if = model_if.predict(X_test_np)

# Calcul des scores
scores_if = model_if.decision_function(X_test_np)

# Comptage
nb_anomalies_if = np.sum(predictions_if == -1)
nb_normales_if = np.sum(predictions_if == 1)

print("Nombre total :", len(predictions_if))
print("Nombre d'anomalies :", nb_anomalies_if)
print("Nombre d'observations normales :", nb_normales_if)

print(
    "Pourcentage d'anomalies :",
    round(nb_anomalies_if / len(predictions_if) * 100, 2),
    "%"
)

# Sauvegarde du modele
joblib.dump(
    model_if,
    RESULTS_DIR / "isolation_forest.pkl"
)

# Sauvegarde des resultats
df_if = pd.DataFrame({
    "Datetime": datetime_test["Datetime"],
    "Prediction_IF": predictions_if,
    "Score_IF": scores_if
})

df_if.to_csv(
    RESULTS_DIR / "predictions_isolation_forest.csv",
    index=False
)

print("\nResultats Isolation Forest sauvegardes !")
print(df_if.head(10))

# ==========================================
# 3. Z-SCORE
# ==========================================

print("\n========== Z-SCORE ==========")

# Les donnees sont deja normalisees
# Application du seuil de 3

seuil = 3

Z_scores = X_test.copy()

# Detection des valeurs depassant le seuil
anomalies_zscore = Z_scores.abs() > seuil

# Une observation est anormale si au moins
# une variable depasse le seuil
predictions_zscore = np.where(
    anomalies_zscore.any(axis=1),
    -1,
    1
)

# Score : valeur absolue maximale parmi les variables
scores_zscore = Z_scores.abs().max(axis=1)

# Comptage
nb_anomalies_zscore = np.sum(predictions_zscore == -1)
nb_normales_zscore = np.sum(predictions_zscore == 1)

print("Seuil Z-score :", seuil)
print("Nombre total :", len(predictions_zscore))
print("Nombre d'anomalies :", nb_anomalies_zscore)
print("Nombre d'observations normales :", nb_normales_zscore)

print(
    "Pourcentage d'anomalies :",
    round(nb_anomalies_zscore / len(predictions_zscore) * 100, 2),
    "%"
)

# Sauvegarde des resultats
df_zscore = pd.DataFrame({
    "Datetime": datetime_test["Datetime"],
    "Prediction_Zscore": predictions_zscore,
    "Score_Zscore": scores_zscore
})

df_zscore.to_csv(
    RESULTS_DIR / "predictions_zscore.csv",
    index=False
)

print("\nResultats Z-score sauvegardes !")
print(df_zscore.head(10))

# ==========================================
# 4. LOCAL OUTLIER FACTOR (LOF)
# ==========================================

print("\n========== LOCAL OUTLIER FACTOR ==========")

model_lof = LocalOutlierFactor(
    n_neighbors=20,
    contamination="auto",
    novelty=True,
    n_jobs=-1
)

# Entrainement sur les donnees train
model_lof.fit(X_train_np)

print("Modele LOF entraine avec succes !")

# Prediction sur les donnees test
predictions_lof = model_lof.predict(X_test_np)

# Calcul des scores
scores_lof = model_lof.decision_function(X_test_np)

# Comptage
nb_anomalies_lof = np.sum(predictions_lof == -1)
nb_normales_lof = np.sum(predictions_lof == 1)

print("Nombre total :", len(predictions_lof))
print("Nombre d'anomalies :", nb_anomalies_lof)
print("Nombre d'observations normales :", nb_normales_lof)

print(
    "Pourcentage d'anomalies :",
    round(nb_anomalies_lof / len(predictions_lof) * 100, 2),
    "%"
)

# Sauvegarde du modele
joblib.dump(
    model_lof,
    RESULTS_DIR / "lof.pkl"
)

# Sauvegarde des resultats
df_lof = pd.DataFrame({
    "Datetime": datetime_test["Datetime"],
    "Prediction_LOF": predictions_lof,
    "Score_LOF": scores_lof
})

df_lof.to_csv(
    RESULTS_DIR / "predictions_lof.csv",
    index=False
)

print("\nResultats LOF sauvegardes !")
print(df_lof.head(10))

# ==========================================
# 5. COMPARAISON DES TROIS METHODES
# ==========================================

print("\n========== COMPARAISON DES TROIS METHODES ==========")

comparaison = pd.DataFrame({
    "Methode": [
        "Isolation Forest",
        "Z-score",
        "LOF"
    ],
    "Anomalies": [
        nb_anomalies_if,
        nb_anomalies_zscore,
        nb_anomalies_lof
    ],
    "Observations_normales": [
        nb_normales_if,
        nb_normales_zscore,
        nb_normales_lof
    ]
})

comparaison["Pourcentage_anomalies"] = (
    comparaison["Anomalies"] / len(X_test) * 100
).round(2)

print(comparaison)

comparaison.to_csv(
    RESULTS_DIR / "comparaison_methodes.csv",
    index=False
)

print("\nComparaison sauvegardee avec succes !")

# ==========================================
# 6. RESUME FINAL
# ==========================================

print("\n========== RESUME DE LA PARTIE 3 ==========")

print("Isolation Forest :", nb_anomalies_if, "anomalies")
print("Z-score :", nb_anomalies_zscore, "anomalies")
print("LOF :", nb_anomalies_lof, "anomalies")

print("\nFichiers generes :")
print("- isolation_forest.pkl")
print("- lof.pkl")
print("- predictions_isolation_forest.csv")
print("- predictions_zscore.csv")
print("- predictions_lof.csv")
print("- comparaison_methodes.csv")

print("\n========== DETECTION TERMINEE AVEC SUCCES ==========")


