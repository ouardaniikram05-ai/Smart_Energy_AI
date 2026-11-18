
# ============================================================
# SMART ENERGY AI
# PARTIE 4 : ANALYSE DE LA CONSOMMATION ENERGETIQUE
# Dataset : Individual Household Electric Power Consumption
# Frequence normale : 1 mesure par minute
# ============================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_PATH = BASE_DIR / "data" / "household_power_consumption_final.csv.gz"

RESULTS_DIR = BASE_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

print("\n========== PARTIE 4 : ANALYSE ENERGETIQUE ==========\n")


# ============================================================
# 2. CHARGEMENT DES DONNEES
# ============================================================

df = pd.read_csv(DATA_PATH, compression="gzip")

df.columns = df.columns.str.strip()

print("Dataset charge avec succes !")
print("Dimensions initiales :", df.shape)

print("\nApercu des donnees :")
print(df.head())

print("\nValeurs manquantes initiales :")
initial_missing = df.isnull().sum()
print(initial_missing)

print("\nNombre total de valeurs manquantes :",
      initial_missing.sum())


# ============================================================
# 3. IDENTIFICATION ET PREPARATION DES VARIABLES
# ============================================================

# Identification de la date

date_candidates = ["timestamp", "Datetime", "datetime"]

date_col = next(
    (col for col in date_candidates if col in df.columns),
    None
)

# Construction du timestamp si necessaire

if date_col is None and {"Date", "Time"}.issubset(df.columns):

    df["timestamp"] = pd.to_datetime(
        df["Date"].astype(str) + " " + df["Time"].astype(str),
        errors="coerce",
        dayfirst=True
    )

    date_col = "timestamp"

if date_col is None:
    raise ValueError("Aucune colonne temporelle trouvee.")

# Identification de la puissance active

power_candidates = ["power_kW", "Global_active_power"]

power_col = next(
    (col for col in power_candidates if col in df.columns),
    None
)

if power_col is None:
    raise ValueError("Colonne de puissance introuvable.")

# Harmonisation des noms

df = df.rename(columns={
    date_col: "timestamp",
    power_col: "power_kW"
})

# Conversion des types

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce",
    dayfirst=True
)

df["power_kW"] = pd.to_numeric(
    df["power_kW"],
    errors="coerce"
)

# Verification des valeurs invalides

print("\n========== QUALITE DES VARIABLES ==========")

print("Dates invalides :", df["timestamp"].isna().sum())
print("Puissances invalides :", df["power_kW"].isna().sum())

# Suppression des lignes invalides

before_cleaning = len(df)

df = df.dropna(
    subset=["timestamp", "power_kW"]
).copy()

removed_rows = before_cleaning - len(df)

print("Nombre de lignes supprimees :", removed_rows)

# Tri chronologique

df = df.sort_values("timestamp").reset_index(drop=True)

print("\nPeriode des donnees :")
print("Debut :", df["timestamp"].min())
print("Fin :", df["timestamp"].max())


# ============================================================
# 4. STATISTIQUES GENERALES
# ============================================================

print("\n========== STATISTIQUES DE LA PUISSANCE ==========\n")

print(df["power_kW"].describe())

print("\nPuissance moyenne :",
      round(df["power_kW"].mean(), 3), "kW")

print("Puissance maximale :",
      round(df["power_kW"].max(), 3), "kW")

print("Puissance minimale :",
      round(df["power_kW"].min(), 3), "kW")

print("Ecart-type :",
      round(df["power_kW"].std(), 3), "kW")


# ============================================================
# 5. VERIFICATION DES DOUBLONS TEMPORELS
# ============================================================

print("\n========== DOUBLONS TEMPORELS ==========\n")

duplicate_count = df["timestamp"].duplicated().sum()

print("Nombre de timestamps dupliques :", duplicate_count)

df = df.drop_duplicates(
    subset=["timestamp"],
    keep="first"
).copy()

df = df.sort_values("timestamp").reset_index(drop=True)

print("Dimensions apres suppression des doublons :", df.shape)


# ============================================================
# 6. ANALYSE DE LA CONTINUITE TEMPORELLE
# ============================================================

print("\n========== CONTINUITE TEMPORELLE ==========\n")

# Difference entre deux mesures successives

df["time_diff"] = df["timestamp"].diff()

# Intervalles superieurs a une minute

gaps = df[
    df["time_diff"] > pd.Timedelta(minutes=1)
].copy()

print("Nombre d'intervalles superieurs a 1 minute :",
      len(gaps))

print("\nFrequence des intervalles :")
print(df["time_diff"].value_counts().head(15))

# Estimation des minutes manquantes

df["missing_minutes"] = (
    df["time_diff"] / pd.Timedelta(minutes=1)
).round().sub(1).clip(lower=0)

total_missing_minutes = int(
    df["missing_minutes"].sum()
)

print("\nNombre estime de minutes manquantes :",
      total_missing_minutes)

# Sauvegarde des interruptions

gaps.to_csv(
    RESULTS_DIR / "temporal_gaps.csv",
    index=False
)


# ============================================================
# 7. ANALYSE DE LA QUALITE DES DONNEES JOURNALIERES
# ============================================================

print("\n========== QUALITE DES DONNEES JOURNALIERES ==========\n")

df["date"] = df["timestamp"].dt.date

daily_quality = df.groupby("date").agg(
    nombre_mesures=("timestamp", "count"),
    premiere_mesure=("timestamp", "min"),
    derniere_mesure=("timestamp", "max")
)

daily_quality["duree_couverte_minutes"] = (
    daily_quality["derniere_mesure"]
    - daily_quality["premiere_mesure"]
).dt.total_seconds() / 60

daily_quality["journee_complete"] = (
    (daily_quality["nombre_mesures"] == 1440)
    & (daily_quality["duree_couverte_minutes"] == 1439)
)

print(daily_quality.head(10))

incomplete_days = (
    ~daily_quality["journee_complete"]
).sum()

print("\nNombre de journees non completes :", incomplete_days)

print("Nombre de journees completes :",
      daily_quality["journee_complete"].sum())

daily_quality.to_csv(
    RESULTS_DIR / "daily_data_quality.csv"
)


# ============================================================
# 8. CALCUL DE L'ENERGIE CONSOMMEE
# ============================================================

print("\n========== CALCUL DE L'ENERGIE ==========\n")

# E (kWh) = P (kW) x duree (heure)
# Pour une minute : E = P / 60

previous_power = df["power_kW"].shift(1)

average_power = (
    previous_power + df["power_kW"]
) / 2

# Intervalles exactement egaux a une minute

valid_interval = (
    df["time_diff"] == pd.Timedelta(minutes=1)
)

df["Energy_kWh"] = np.where(
    valid_interval,
    average_power / 60,
    np.nan
)

total_energy = df["Energy_kWh"].sum()

print("Energie totale sur les intervalles valides :",
      round(total_energy, 3), "kWh")

print("Nombre d'intervalles valides :",
      int(valid_interval.sum()))

print("Nombre d'intervalles exclus :",
      int((~valid_interval).sum()))


# ============================================================
# 9. ANALYSE DE LA CONSOMMATION PAR HEURE
# ============================================================

print("\n========== CONSOMMATION PAR HEURE ==========\n")

df["hour"] = df["timestamp"].dt.hour

hourly_analysis = df.groupby(
    "hour"
)["power_kW"].mean()

print(hourly_analysis)

hourly_analysis.to_csv(
    RESULTS_DIR / "hourly_consumption.csv"
)

plt.figure(figsize=(12, 5))

hourly_analysis.plot(
    kind="bar",
    edgecolor="black"
)

plt.title("Puissance moyenne selon l'heure de la journee")
plt.xlabel("Heure")
plt.ylabel("Puissance moyenne (kW)")
plt.xticks(range(24), rotation=0)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "hourly_consumption.png",
    dpi=300
)

plt.show()


# ============================================================
# 10. ANALYSE JOURNALIERE
# ============================================================

print("\n========== ANALYSE JOURNALIERE ==========\n")

daily_power = df.resample(
    "D",
    on="timestamp"
)["power_kW"].mean()

daily_energy = df.resample(
    "D",
    on="timestamp"
)["Energy_kWh"].sum(min_count=1)

daily_analysis = pd.DataFrame({
    "Puissance_moyenne_kW": daily_power,
    "Energie_kWh": daily_energy
})

print(daily_analysis.head(10))

daily_analysis.to_csv(
    RESULTS_DIR / "daily_consumption.csv"
)

# Graphique de la puissance journaliere

plt.figure(figsize=(14, 5))

daily_power.plot()

plt.title("Evolution de la puissance moyenne journaliere")
plt.xlabel("Date")
plt.ylabel("Puissance moyenne (kW)")
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "daily_power.png",
    dpi=300
)

plt.show()

# Graphique de l'energie journaliere

plt.figure(figsize=(14, 5))

daily_energy.plot()

plt.title("Evolution de l'energie journaliere")
plt.xlabel("Date")
plt.ylabel("Energie (kWh)")
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "daily_energy.png",
    dpi=300
)

plt.show()


# ============================================================
# 11. ANALYSE MENSUELLE
# ============================================================

print("\n========== ANALYSE MENSUELLE ==========\n")

monthly_power = df.resample(
    "ME",
    on="timestamp"
)["power_kW"].mean()

monthly_energy = df.resample(
    "ME",
    on="timestamp"
)["Energy_kWh"].sum(min_count=1)

monthly_analysis = pd.DataFrame({
    "Puissance_moyenne_kW": monthly_power,
    "Energie_kWh": monthly_energy
})

print(monthly_analysis)

monthly_analysis.to_csv(
    RESULTS_DIR / "monthly_consumption.csv"
)

# Graphique de la puissance mensuelle

plt.figure(figsize=(12, 5))

monthly_power.plot(marker="o")

plt.title("Puissance moyenne mensuelle")
plt.xlabel("Mois")
plt.ylabel("Puissance moyenne (kW)")
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "monthly_power.png",
    dpi=300
)

plt.show()

# Graphique de l'energie mensuelle

plt.figure(figsize=(12, 5))

monthly_energy.plot(
    kind="bar",
    edgecolor="black"
)

plt.title("Energie consommee par mois")
plt.xlabel("Mois")
plt.ylabel("Energie (kWh)")
plt.xticks(rotation=45)
plt.grid(axis="y", alpha=0.3)
plt.tight_layout()

plt.savefig(
    RESULTS_DIR / "monthly_energy.png",
    dpi=300
)

plt.show()


# ============================================================
# 12. SAUVEGARDE DU DATASET FINAL
# ============================================================

df.to_csv(
    RESULTS_DIR / "consumption_analysis_complete.csv",
    index=False
)

print("\nDataset final sauvegarde avec succes !")


# ============================================================
# 13. BILAN FINAL
# ============================================================

print("\n================================================")
print("       BILAN DE LA PARTIE 4")
print("================================================")

print("\nNombre de mesures finales :", len(df))

print("Nombre de doublons temporels :", duplicate_count)

print("Nombre de lignes supprimees :", removed_rows)

print("Puissance moyenne :",
      round(df["power_kW"].mean(), 3), "kW")

print("Puissance maximale :",
      round(df["power_kW"].max(), 3), "kW")

print("Puissance minimale :",
      round(df["power_kW"].min(), 3), "kW")

print("Energie totale sur intervalles valides :",
      round(total_energy, 3), "kWh")

print("Intervalles superieurs a une minute :",
      len(gaps))

print("Minutes manquantes estimees :",
      total_missing_minutes)

print("Journees non completes :", incomplete_days)

print("\nTous les resultats sont sauvegardes dans :")
print(RESULTS_DIR)

print("\n========== FIN DE LA PARTIE 4 ==========\n")

