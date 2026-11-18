
# ==========================================
# SMART ENERGY AI
# 02 - ANALYSE TEMPORELLE DE LA CONSOMMATION
# ==========================================

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent

# Chemin du dataset original
DATA_PATH = (
    BASE_DIR / "data" /
    "household_power_consumption_final.csv.gz"
)

# Dossier de sauvegarde
RESULTS_DIR = BASE_DIR / "results" / "temporal_analysis"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Verification du dataset
if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Dataset introuvable : {DATA_PATH}"
    )

# ==========================================
# 2. CHARGEMENT DES DONNEES
# ==========================================

df = pd.read_csv(
    DATA_PATH,
    compression="gzip",
    sep=None,
    engine="python",
    na_values=["?"]
)

# Nettoyage des noms de colonnes
df.columns = df.columns.str.strip()

print("\n========== DATASET CHARGE AVEC SUCCES ==========")
print("Dimensions initiales :", df.shape)

print("\nColonnes disponibles :")
print(df.columns.tolist())

print("\nApercu des donnees :")
print(df.head())

# Verification des colonnes necessaires
colonnes_requises = [
    "Date",
    "Time",
    "Global_active_power"
]

for colonne in colonnes_requises:
    if colonne not in df.columns:
        raise KeyError(
            f"Colonne absente du dataset : {colonne}"
        )

# ==========================================
# 3. PREPARATION TEMPORELLE
# ==========================================

# Construction de la date et de l'heure
df["Datetime"] = pd.to_datetime(
    df["Date"].astype(str) + " " +
    df["Time"].astype(str),
    format="%d/%m/%Y %H:%M:%S",
    errors="coerce"
)

# Conversion de la consommation en numerique
df["Global_active_power"] = pd.to_numeric(
    df["Global_active_power"],
    errors="coerce"
)

# Verification des valeurs manquantes
print("\n========== QUALITE DES DONNEES ==========")

print("\nValeurs manquantes avant nettoyage :")

print(
    df[["Datetime", "Global_active_power"]]
    .isnull()
    .sum()
)

# Suppression des lignes incompletes
df = df.dropna(
    subset=["Datetime", "Global_active_power"]
).copy()

# Tri chronologique
df = df.sort_values("Datetime")

# Utilisation de Datetime comme index
df = df.set_index("Datetime")

if df.empty:
    raise ValueError(
        "Aucune donnee valide apres le nettoyage."
    )

print("\nDimensions apres nettoyage :", df.shape)

print("\nPeriode analysee :")
print("Debut :", df.index.min())
print("Fin :", df.index.max())

# ==========================================
# 4. ANALYSE HORAIRE
# ==========================================

print("\n========== ANALYSE HORAIRE ==========")

df["Hour"] = df.index.hour

hourly = df.groupby("Hour")[
    "Global_active_power"
].mean()

print(hourly)

plt.figure(figsize=(12, 5))

hourly.plot(
    kind="line",
    marker="o"
)

plt.title("Consommation moyenne selon l'heure")
plt.xlabel("Heure")
plt.ylabel("Global Active Power (kW)")
plt.xticks(range(24))
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "01_hourly_consumption.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 5. ANALYSE JOURNALIERE
# ==========================================

print("\n========== ANALYSE JOURNALIERE ==========")

daily = df["Global_active_power"].resample("D").mean()

print(daily.head())

plt.figure(figsize=(14, 5))

daily.plot()

plt.title("Evolution journaliere de la consommation")
plt.xlabel("Date")
plt.ylabel("Consommation moyenne (kW)")
plt.grid(True, alpha=0.3)
plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "02_daily_consumption.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 6. ANALYSE MENSUELLE
# ==========================================

print("\n========== ANALYSE MENSUELLE ==========")

monthly = df["Global_active_power"].resample("ME").mean()

print(monthly)

plt.figure(figsize=(12, 5))

monthly.plot(kind="bar")

plt.title("Consommation moyenne mensuelle")
plt.xlabel("Mois")
plt.ylabel("Consommation moyenne (kW)")
plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "03_monthly_consumption.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 7. ANALYSE PAR JOUR DE LA SEMAINE
# ==========================================

print("\n========== ANALYSE PAR JOUR DE LA SEMAINE ==========")

df["Day_of_week"] = df.index.dayofweek

weekly = df.groupby("Day_of_week")[
    "Global_active_power"
].mean()

noms_jours = [
    "Lundi",
    "Mardi",
    "Mercredi",
    "Jeudi",
    "Vendredi",
    "Samedi",
    "Dimanche"
]

weekly.index = noms_jours

print(weekly)

plt.figure(figsize=(10, 5))

weekly.plot(kind="bar")

plt.title("Consommation moyenne par jour de la semaine")
plt.xlabel("Jour")
plt.ylabel("Consommation moyenne (kW)")
plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "04_weekly_consumption.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================================
# 8. SAUVEGARDE DES RESULTATS
# ==========================================

print("\n========== SAUVEGARDE DES RESULTATS ==========")

hourly.to_csv(RESULTS_DIR / "hourly.csv")

daily.to_csv(RESULTS_DIR / "daily.csv")

monthly.to_csv(RESULTS_DIR / "monthly.csv")

weekly.to_csv(RESULTS_DIR / "weekly.csv")

print("\n========== ANALYSE TEMPORELLE TERMINEE ==========")

print("\nGraphiques et fichiers CSV sauvegardes dans :")
print(RESULTS_DIR)

print("\n========== TOUS LES TRAITEMENTS SONT TERMINES ==========")




