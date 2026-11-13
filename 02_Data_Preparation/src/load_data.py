"""Chargement du dataset Individual Household Electric Power Consumption.

Format commun du projet : une colonne `timestamp` et une colonne `power_kW`.

Utilisation (depuis n'importe quel notebook ou script du projet) :

    import sys
    sys.path.append("../../02_Data_Preparation/src")   # adapter selon l'emplacement
    from load_data import load_household

    df = load_household("hourly")   # pas d'une heure (prédiction, dashboard)
    df = load_household("minute")   # pas d'une minute (détection d'anomalies)

Colonnes retournées (les unités sont des énergies sur le pas de temps) :
    timestamp, power_kW, reactive_kW, voltage_V, intensity_A,
    sub_metering_1_Wh, sub_metering_2_Wh, sub_metering_3_Wh
    (+ is_interpolated en mode "hourly")

Les trous restent des NaN : utiliser dropna=True pour les retirer.
"""
from pathlib import Path

import pandas as pd

# Racine du projet : .../Smart_Energy_AI/02_Data_Preparation/src/load_data.py -> parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "01_Dataset" / "Processed"

FILES = {
    "hourly": PROCESSED_DIR / "household_hourly.csv.gz",
    "minute": PROCESSED_DIR / "household_power_consumption_final.csv.gz",
}

# Noms de colonnes du fichier à la minute -> noms du format commun
MINUTE_RENAME = {
    "Datetime": "timestamp",
    "Global_active_power": "power_kW",
    "Global_reactive_power": "reactive_kW",
    "Voltage": "voltage_V",
    "Global_intensity": "intensity_A",
    "Sub_metering_1": "sub_metering_1_Wh",
    "Sub_metering_2": "sub_metering_2_Wh",
    "Sub_metering_3": "sub_metering_3_Wh",
}


def load_household(freq: str = "hourly", dropna: bool = False) -> pd.DataFrame:
    """Retourne le dataset au format commun.

    freq   : "hourly" (1 heure) ou "minute" (1 minute)
    dropna : True pour retirer les lignes où power_kW est manquant
    """
    if freq not in FILES:
        raise ValueError(f"freq doit être 'hourly' ou 'minute', pas {freq!r}")

    path = FILES[freq]
    if not path.exists():
        raise FileNotFoundError(
            f"Fichier introuvable : {path}\n"
            "Récupère la branche à jour (git pull) ou génère-le avec le notebook "
            "02_Data_Preparation/notebooks/02_preparation_horaire.ipynb."
        )

    df = pd.read_csv(path, compression="gzip")

    if freq == "minute":
        df = df.drop(columns=["Date", "Time"], errors="ignore").rename(columns=MINUTE_RENAME)

    # Conversion explicite en date (ne pas se fier à parse_dates)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    if dropna:
        df = df.dropna(subset=["power_kW"]).reset_index(drop=True)

    return df


if __name__ == "__main__":
    for f in ("hourly", "minute"):
        d = load_household(f)
        print(f, d.shape, d["timestamp"].min(), "->", d["timestamp"].max(),
              "| NaN power_kW:", int(d["power_kW"].isna().sum()))
