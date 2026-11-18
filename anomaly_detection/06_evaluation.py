

# ==========================================
# SMART ENERGY AI
# PARTIE 6 : EVALUATION DES MODELES
# ==========================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

RESULTS_DIR = BASE_DIR / "results"

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================
# 2. CHARGEMENT DES PREDICTIONS
# ==========================================

print("\n========== PARTIE 6 : EVALUATION DES MODELES ==========")

print("\n========== CHARGEMENT DES PREDICTIONS ==========")

def load_predictions(filename, prediction_column):

    file_path = RESULTS_DIR / filename

    # Vérifier l'existence du fichier

    if not file_path.exists():

        raise FileNotFoundError(
            f"Fichier introuvable : {file_path}"
        )

    # Vérifier si le fichier est vide

    if file_path.stat().st_size == 0:

        raise ValueError(
            f"Le fichier est vide : {filename}"
        )

    try:

        data = pd.read_csv(file_path)

    except pd.errors.EmptyDataError:

        raise ValueError(
            f"Aucune donnée dans le fichier : {filename}"
        )

    # Vérifier les colonnes nécessaires

    required_columns = ["Datetime", prediction_column]

    missing_columns = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Colonnes manquantes dans {filename} : {missing_columns}"
        )

    # Garder uniquement les colonnes nécessaires

    data = data[required_columns].copy()

    # Convertir les dates

    data["Datetime"] = pd.to_datetime(
        data["Datetime"],
        errors="coerce"
    )

    # Supprimer les dates invalides

    invalid_dates = data["Datetime"].isna().sum()

    if invalid_dates > 0:

        print(
            f"Attention : {invalid_dates} dates invalides "
            f"supprimees dans {filename}"
        )

        data = data.dropna(subset=["Datetime"])

    # Vérifier les doublons

    if data["Datetime"].duplicated().any():

        raise ValueError(
            f"Dates dupliquees dans {filename}. "
            "Verifier le fichier de predictions."
        )

    # Vérifier les valeurs des prédictions

    data[prediction_column] = pd.to_numeric(
        data[prediction_column],
        errors="coerce"
    )

    if data[prediction_column].isna().any():

        raise ValueError(
            f"Predictions invalides dans {filename}"
        )

    invalid_predictions = ~data[prediction_column].isin([-1, 1])

    if invalid_predictions.any():

        raise ValueError(
            f"Valeurs de predictions differentes de -1 et 1 "
            f"dans {filename}"
        )

    return data.sort_values("Datetime").reset_index(drop=True)


# Chargement des trois modèles

df_if = load_predictions(
    "predictions_isolation_forest.csv",
    "Prediction_IF"
)

df_zscore = load_predictions(
    "predictions_zscore.csv",
    "Prediction_Zscore"
)

df_lof = load_predictions(
    "predictions_lof.csv",
    "Prediction_LOF"
)

print("\nPredictions chargees avec succes !")

print("Isolation Forest :", df_if.shape)

print("Z-score :", df_zscore.shape)

print("LOF :", df_lof.shape)


# ==========================================
# 3. FUSION DES RESULTATS
# ==========================================

print("\n========== FUSION DES RESULTATS ==========")

# Fusionner selon les dates communes

df = df_if.merge(
    df_zscore,
    on="Datetime",
    how="inner",
    validate="one_to_one"
)

df = df.merge(
    df_lof,
    on="Datetime",
    how="inner",
    validate="one_to_one"
)

df = df.sort_values("Datetime").reset_index(drop=True)

# Vérifier le résultat de la fusion

total = len(df)

print("\nNombre de dates communes :", total)

if total == 0:

    raise ValueError(
        "Aucune date commune entre les trois fichiers. "
        "Verifier les colonnes Datetime."
    )

print("\nDimensions du dataset fusionne :", df.shape)

print("\nApercu des resultats :")

print(df.head())

# Informer si certaines dates ont été perdues

if (
    total < len(df_if)
    or total < len(df_zscore)
    or total < len(df_lof)
):

    print(
        "\nAttention : certaines observations ne sont pas "
        "communes aux trois modeles."
    )

    print(
        "L'evaluation utilise uniquement les dates communes."
    )


# ==========================================
# 4. EVALUATION INDIVIDUELLE DES MODELES
# ==========================================

print("\n========== EVALUATION INDIVIDUELLE ==========")

models = {

    "Isolation Forest": "Prediction_IF",

    "Z-score": "Prediction_Zscore",

    "LOF": "Prediction_LOF"

}

evaluation_results = []

for model_name, column in models.items():

    # Nombre d'anomalies

    anomalies = (df[column] == -1).sum()

    # Nombre d'observations normales

    normales = (df[column] == 1).sum()

    # Pourcentage d'anomalies

    percentage = anomalies / total * 100

    evaluation_results.append({

        "Model": model_name,

        "Normal_observations": normales,

        "Anomalies_detected": anomalies,

        "Anomaly_percentage": percentage

    })

    print("\nModele :", model_name)

    print("Observations normales :", normales)

    print("Anomalies detectees :", anomalies)

    print(
        "Pourcentage d'anomalies :",
        round(percentage, 2),
        "%"
    )


# Tableau comparatif

evaluation_df = pd.DataFrame(evaluation_results)

print("\n========== TABLEAU COMPARATIF ==========")

print(evaluation_df)

evaluation_df.to_csv(
    RESULTS_DIR / "model_evaluation.csv",
    index=False
)


# ==========================================
# 5. COMPARAISON ET CONSENSUS
# ==========================================

print("\n========== ACCORD ENTRE LES MODELES ==========")

# Compter les votes des trois modèles

df["Anomaly_votes"] = (

    (df["Prediction_IF"] == -1).astype(int)

    + (df["Prediction_Zscore"] == -1).astype(int)

    + (df["Prediction_LOF"] == -1).astype(int)

)

# Détection majoritaire : au moins deux modèles

df["Majority_anomaly"] = (

    df["Anomaly_votes"] >= 2

)

# Détection unanime : les trois modèles

df["Unanimous_anomaly"] = (

    df["Anomaly_votes"] == 3

)

majority_count = df["Majority_anomaly"].sum()

unanimous_count = df["Unanimous_anomaly"].sum()

print(
    "\nAnomalies detectees par au moins 2 modeles :",
    majority_count
)

print(
    "\nAnomalies detectees par les 3 modeles :",
    unanimous_count
)

print(
    "\nPourcentage de consensus majoritaire :",
    round(majority_count / total * 100, 2),
    "%"
)

# Répartition des votes

vote_distribution = (

    df["Anomaly_votes"]
    .value_counts()
    .reindex(range(4), fill_value=0)
    .sort_index()

)

print("\nRepartition selon le nombre de modeles detecteurs :")

for votes, count in vote_distribution.items():

    print(
        f"{votes} modele(s) : {count} observations"
    )


# Sauvegarder les résultats fusionnés

df.to_csv(
    RESULTS_DIR / "combined_model_predictions.csv",
    index=False
)

# Sauvegarder les anomalies majoritaires

consensus_data = df[
    df["Majority_anomaly"]
].copy()

consensus_data.to_csv(
    RESULTS_DIR / "consensus_anomalies.csv",
    index=False
)


# ==========================================
# 6. TAUX D'ACCORD ENTRE LES MODELES
# ==========================================

print("\n========== TAUX D'ACCORD ==========")

agreement_if_zscore = (

    df["Prediction_IF"] ==
    df["Prediction_Zscore"]

).mean() * 100


agreement_if_lof = (

    df["Prediction_IF"] ==
    df["Prediction_LOF"]

).mean() * 100


agreement_zscore_lof = (

    df["Prediction_Zscore"] ==
    df["Prediction_LOF"]

).mean() * 100


print(
    "\nAccord Isolation Forest / Z-score :",
    round(agreement_if_zscore, 2),
    "%"
)

print(
    "Accord Isolation Forest / LOF :",
    round(agreement_if_lof, 2),
    "%"
)

print(
    "Accord Z-score / LOF :",
    round(agreement_zscore_lof, 2),
    "%"
)


# Accord simultané des trois modèles

unanimous_agreement = (

    (
        (df["Prediction_IF"] == df["Prediction_Zscore"])
        &
        (df["Prediction_Zscore"] == df["Prediction_LOF"])
    ).mean() * 100

)

print(
    "\nAccord simultane des trois modeles :",
    round(unanimous_agreement, 2),
    "%"
)


# ==========================================
# 7. VISUALISATION COMPARATIVE
# ==========================================

print("\n========== VISUALISATION COMPARATIVE ==========")

# Graphique 1 : Nombre d'anomalies détectées

plt.figure(figsize=(10, 5))

plt.bar(
    evaluation_df["Model"],
    evaluation_df["Anomalies_detected"]
)

plt.title(
    "Comparaison du nombre d'anomalies detectees"
)

plt.xlabel("Modeles")

plt.ylabel("Nombre d'anomalies")

plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "model_anomalies_comparison.png",
    dpi=300
)

plt.show()

plt.close()


# ==========================================
# 8. COMPARAISON DES POURCENTAGES
# ==========================================

plt.figure(figsize=(10, 5))

plt.bar(
    evaluation_df["Model"],
    evaluation_df["Anomaly_percentage"]
)

plt.title(
    "Pourcentage d'anomalies par modele"
)

plt.xlabel("Modeles")

plt.ylabel("Pourcentage (%)")

plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "model_anomaly_percentages.png",
    dpi=300
)

plt.show()

plt.close()


# ==========================================
# 9. VISUALISATION DU CONSENSUS
# ==========================================

plt.figure(figsize=(9, 5))

vote_distribution.plot(
    kind="bar"
)

plt.title(
    "Repartition des observations selon les votes"
)

plt.xlabel(
    "Nombre de modeles ayant detecte une anomalie"
)

plt.ylabel("Nombre d'observations")

plt.xticks(rotation=0)

plt.grid(axis="y", alpha=0.3)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "model_consensus.png",
    dpi=300
)

plt.show()

plt.close()


# ==========================================
# 10. VISUALISATION TEMPORELLE
# ==========================================

plt.figure(figsize=(15, 6))

plt.plot(
    df["Datetime"],
    df["Anomaly_votes"],
    linewidth=0.5,
    label="Nombre de modeles detectant une anomalie"
)

plt.axhline(
    y=2,
    color="red",
    linestyle="--",
    label="Seuil de consensus"
)

plt.title(
    "Evolution temporelle des anomalies detectees"
)

plt.xlabel("Date")

plt.ylabel("Nombre de modeles")

plt.yticks([0, 1, 2, 3])

plt.legend()

plt.grid(alpha=0.3)

plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "temporal_model_comparison.png",
    dpi=300
)

plt.show()

plt.close()


# ==========================================
# 11. CONCLUSION
# ==========================================

print("\n========== CONCLUSION DE L'EVALUATION ==========")

# Modèle ayant détecté le plus d'anomalies

most_anomalies = evaluation_df.loc[
    evaluation_df["Anomalies_detected"].idxmax()
]

print(
    "\nModele ayant detecte le plus d'anomalies :",
    most_anomalies["Model"]
)

print(
    "Nombre d'anomalies :",
    most_anomalies["Anomalies_detected"]
)

print(
    "\nNombre d'observations detectees par consensus :",
    majority_count
)

print(
    "\nNombre d'observations detectees unanimement :",
    unanimous_count
)

print("\n========== LIMITES DE L'EVALUATION ==========")

print(
    "Cette evaluation est non supervisee et comparative."
)

print(
    "Elle mesure les anomalies detectees et l'accord entre les modeles."
)

print(
    "Sans etiquettes reelles, il est impossible de calculer "
    "une precision, un rappel ou un F1-score fiables."
)

print(
    "Le modele detectant le plus d'anomalies n'est pas "
    "necessairement le meilleur."
)

print("\nFichiers enregistres dans :", RESULTS_DIR)

print("\n========== FIN DE LA PARTIE 6 ==========")
