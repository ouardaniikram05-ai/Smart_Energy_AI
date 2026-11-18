
# ==========================================
# SMART ENERGY AI
# 01 - ETUDE DES ANOMALIES ELECTRIQUES
# ==========================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# ==========================================
# 1. CHARGEMENT DU DATASET
# ==========================================

# Chemin du projet
BASE_DIR = Path(__file__).resolve().parent.parent

# Chemin du fichier de donnees
DATA_PATH = BASE_DIR / "data" / "household_power_consumption_final.csv.gz"

# Dossier de sauvegarde des resultats
RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Verification de l'existence du fichier
if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset introuvable : {DATA_PATH}"
    )

# Chargement des donnees
df = pd.read_csv(
    DATA_PATH,
    compression="gzip"
)

# Conversion de la colonne Datetime
if "Datetime" not in df.columns:
    raise KeyError("La colonne Datetime est absente du dataset.")

df["Datetime"] = pd.to_datetime(
    df["Datetime"],
    errors="coerce"
)

print("\n========== DATASET CHARGE AVEC SUCCES ==========")

# ==========================================
# 2. APERCU ET QUALITE DES DONNEES
# ==========================================

print("\n========== APERCU DES DONNEES ==========")
print(df.head())

# Dimensions
print("\n========== DIMENSIONS ==========")
print("Nombre de lignes :", df.shape[0])
print("Nombre de colonnes :", df.shape[1])

# Noms des colonnes
print("\n========== COLONNES ==========")
print(df.columns.tolist())

# Informations generales
print("\n========== INFORMATIONS GENERALES ==========")
df.info()

# Valeurs manquantes
print("\n========== VALEURS MANQUANTES ==========")
print(df.isnull().sum())

# Nombre total de valeurs manquantes
print(
    "\nNombre total de valeurs manquantes :",
    df.isnull().sum().sum()
)

# Doublons complets
print("\n========== DOUBLONS ==========")
print(
    "Nombre de lignes dupliquees :",
    df.duplicated().sum()
)

# Doublons temporels
print("\n========== DOUBLONS TEMPORELS ==========")
print(
    "Nombre de dates dupliquees :",
    df["Datetime"].duplicated().sum()
)

# Dates invalides
print("\n========== DATES INVALIDES ==========")
print(
    "Nombre de dates invalides :",
    df["Datetime"].isnull().sum()
)

# ==========================================
# 3. STATISTIQUES DESCRIPTIVES
# ==========================================

# Grandeurs electriques
colonnes_electriques = [
    "Global_active_power",
    "Global_reactive_power",
    "Voltage",
    "Global_intensity",
    "Sub_metering_1",
    "Sub_metering_2",
    "Sub_metering_3"
]

# Verification des colonnes necessaires
colonnes_absentes = [
    colonne for colonne in colonnes_electriques
    if colonne not in df.columns
]

if colonnes_absentes:
    raise KeyError(
        f"Colonnes electriques absentes : {colonnes_absentes}"
    )

# Conversion en valeurs numeriques
for colonne in colonnes_electriques:
    df[colonne] = pd.to_numeric(
        df[colonne],
        errors="coerce"
    )

# Calcul des statistiques descriptives
statistiques = df[colonnes_electriques].describe()

print("\n========== STATISTIQUES DESCRIPTIVES ==========")
print(statistiques)

# Moyennes
print("\n========== MOYENNES ==========")
print(df[colonnes_electriques].mean())

# Valeurs maximales
print("\n========== VALEURS MAXIMALES ==========")
print(df[colonnes_electriques].max())

# Valeurs minimales
print("\n========== VALEURS MINIMALES ==========")
print(df[colonnes_electriques].min())

# ==========================================
# 4. VISUALISATION DES DISTRIBUTIONS
# ==========================================

print("\n========== VISUALISATION DES DISTRIBUTIONS ==========")

fig, axes = plt.subplots(
    4, 2,
    figsize=(16, 20),
    constrained_layout=True
)

axes = axes.flatten()

for i, colonne in enumerate(colonnes_electriques):

    donnees = df[colonne].dropna()

    if donnees.empty:
        axes[i].text(
            0.5, 0.5,
            "Aucune donnee disponible",
            ha="center",
            va="center"
        )
        axes[i].set_title(colonne)
        continue

    # Echantillonnage
    echantillon = donnees.sample(
        n=min(100000, len(donnees)),
        random_state=42
    )

    # Histogramme
    axes[i].hist(
        echantillon,
        bins=50,
        color="steelblue",
        edgecolor="black",
        alpha=0.85
    )

    axes[i].set_title(
        colonne,
        fontsize=12,
        fontweight="bold",
        pad=12
    )

    axes[i].set_xlabel("Valeurs")
    axes[i].set_ylabel("Frequence")

    axes[i].grid(
        True,
        linestyle="--",
        alpha=0.3
    )

# Supprimer le graphique vide
fig.delaxes(axes[7])

fig.suptitle(
    "Distribution des grandeurs electriques",
    fontsize=18,
    fontweight="bold"
)

# Sauvegarde
chemin_image = RESULTS_DIR / "distributions_electriques.png"

fig.savefig(
    chemin_image,
    dpi=300,
    bbox_inches="tight"
)

print("\nImage sauvegardee :", chemin_image)

plt.show()
plt.close(fig)

# ==========================================
# 5. MATRICE DE CORRELATION
# ==========================================

print("\n========== MATRICE DE CORRELATION ==========")

# Calcul des correlations
correlation = df[colonnes_electriques].corr()

print(correlation)

# Creation de la figure
plt.figure(figsize=(12, 9))

sns.heatmap(
    correlation,
    annot=True,
    cmap="coolwarm",
    fmt=".2f",
    linewidths=0.5,
    square=True
)

plt.title(
    "Matrice de correlation des grandeurs electriques",
    fontsize=15,
    fontweight="bold",
    pad=15
)

plt.tight_layout()

# Sauvegarde
chemin_correlation = RESULTS_DIR / "correlation_matrix.png"

plt.savefig(
    chemin_correlation,
    dpi=300,
    bbox_inches="tight"
)

print("\nMatrice sauvegardee :", chemin_correlation)

plt.show()
plt.close()

# ==========================================
# 6. DETECTION DES VALEURS EXTREMES (OUTLIERS)
# ==========================================

print("\n========== DETECTION DES OUTLIERS ==========")

resultats_outliers = []

fig, axes = plt.subplots(
    4, 2,
    figsize=(16, 18)
)

axes = axes.flatten()

for i, colonne in enumerate(colonnes_electriques):

    donnees = df[colonne].dropna()

    # Verification des donnees
    if donnees.empty:
        print(f"\n{colonne} : aucune donnee disponible.")
        axes[i].text(
            0.5, 0.5,
            "Aucune donnee disponible",
            ha="center",
            va="center"
        )
        axes[i].set_title(colonne)
        continue

    # Calcul des quartiles
    Q1 = donnees.quantile(0.25)
    Q3 = donnees.quantile(0.75)

    # Ecart interquartile
    IQR = Q3 - Q1

    # Limites
    limite_inf = Q1 - 1.5 * IQR
    limite_sup = Q3 + 1.5 * IQR

    # Detection des outliers
    masque_outliers = (
        (donnees < limite_inf) |
        (donnees > limite_sup)
    )

    outliers = donnees[masque_outliers]

    # Nombre de valeurs extremes
    nombre_outliers = len(outliers)

    # Pourcentage
    pourcentage = (
        nombre_outliers / len(donnees)
    ) * 100

    # Stockage des resultats
    resultats_outliers.append({
        "Variable": colonne,
        "Q1": Q1,
        "Q3": Q3,
        "IQR": IQR,
        "Limite_inferieure": limite_inf,
        "Limite_superieure": limite_sup,
        "Nombre_outliers": nombre_outliers,
        "Pourcentage_outliers": pourcentage
    })

    # Affichage
    print("\nVariable :", colonne)
    print("Q1 :", round(Q1, 3))
    print("Q3 :", round(Q3, 3))
    print("IQR :", round(IQR, 3))
    print("Limite inferieure :", round(limite_inf, 3))
    print("Limite superieure :", round(limite_sup, 3))
    print("Nombre de valeurs extremes :", nombre_outliers)
    print("Pourcentage :", round(pourcentage, 2), "%")

    # Echantillon pour le boxplot
    echantillon = donnees.sample(
        n=min(50000, len(donnees)),
        random_state=42
    )

    axes[i].boxplot(
        echantillon,
        vert=False,
        patch_artist=True
    )

    axes[i].set_title(
        colonne,
        fontsize=11,
        fontweight="bold"
    )

    axes[i].set_xlabel("Valeurs")
    axes[i].grid(alpha=0.3)

# Supprimer le graphique vide
fig.delaxes(axes[7])

fig.suptitle(
    "Detection des valeurs extremes - Boxplots",
    fontsize=17,
    fontweight="bold"
)

plt.tight_layout(rect=[0, 0, 1, 0.97])

# ==========================================
# 7. SAUVEGARDE DES RESULTATS
# ==========================================

# Sauvegarde du graphique
chemin_boxplot = RESULTS_DIR / "valeurs_extremes.png"

fig.savefig(
    chemin_boxplot,
    dpi=300,
    bbox_inches="tight"
)

print("\nGraphique sauvegarde :", chemin_boxplot)

# Creation du tableau recapitulatif
df_outliers = pd.DataFrame(resultats_outliers)

# Sauvegarde CSV
chemin_csv = RESULTS_DIR / "analyse_outliers.csv"

df_outliers.to_csv(
    chemin_csv,
    index=False
)

print("\nFichier CSV sauvegarde :", chemin_csv)

# Affichage du tableau
print("\n========== TABLEAU RECAPITULATIF ==========")
print(df_outliers.to_string(index=False))

print("\n========== ANALYSE DES OUTLIERS TERMINEE ==========")

# Affichage du graphique
plt.show()
plt.close(fig)

