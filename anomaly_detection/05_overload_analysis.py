
# ==========================================
# SMART ENERGY AI
# PARTIE 5 : ANALYSE DES DEPASSEMENTS
# ==========================================

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# 1. CONFIGURATION
# ==========================================

DATA_PATH = "results/consumption_analysis_complete.csv"

RESULTS_DIR = "results/overload_analysis"
os.makedirs(RESULTS_DIR, exist_ok=True)

# ==========================================
# 2. CHARGEMENT DES DONNEES
# ==========================================

print("\n========== PARTIE 5 : ANALYSE DES DEPASSEMENTS ==========\n")

df = pd.read_csv(DATA_PATH)

df["timestamp"] = pd.to_datetime(
    df["timestamp"],
    errors="coerce"
)

df["power_kW"] = pd.to_numeric(
    df["power_kW"],
    errors="coerce"
)

df = df.dropna(subset=["timestamp", "power_kW"])

df = df.sort_values("timestamp").reset_index(drop=True)

print("Dataset charge avec succes !")
print("Dimensions :", df.shape)

if df.empty:
    raise ValueError("Le dataset ne contient aucune donnee valide.")

# ==========================================
# 3. CALCUL DES SEUILS STATISTIQUES
# ==========================================

print("\n========== CALCUL DES SEUILS ==========\n")

percentiles = df["power_kW"].quantile([0.90, 0.95, 0.99])

p90 = percentiles.loc[0.90]
p95 = percentiles.loc[0.95]
p99 = percentiles.loc[0.99]

Q1 = df["power_kW"].quantile(0.25)
Q3 = df["power_kW"].quantile(0.75)

IQR = Q3 - Q1

upper_limit = Q3 + 1.5 * IQR

print(f"Percentile 90% : {p90:.3f} kW")
print(f"Percentile 95% : {p95:.3f} kW")
print(f"Percentile 99% : {p99:.3f} kW")

print(f"Q1 : {Q1:.3f} kW")
print(f"Q3 : {Q3:.3f} kW")
print(f"IQR : {IQR:.3f} kW")

print(f"Seuil superieur IQR : {upper_limit:.3f} kW")

# ==========================================
# 4. DETECTION DES DEPASSEMENTS
# ==========================================

df["overload"] = df["power_kW"] > upper_limit

overload_data = df[df["overload"]].copy()

print("\n========== RESULTATS DE DETECTION ==========\n")

print("Nombre total de mesures :", len(df))
print("Nombre de depassements :", len(overload_data))

overload_percentage = (
    len(overload_data) / len(df) * 100
)

print(f"Pourcentage de depassements : {overload_percentage:.2f}%")

overload_data.to_csv(
    os.path.join(RESULTS_DIR, "overload_events.csv"),
    index=False
)

# ==========================================
# 5. VISUALISATION DES DEPASSEMENTS
# ==========================================

plt.figure(figsize=(12, 6))

plt.hist(
    df["power_kW"],
    bins=50,
    alpha=0.7,
    label="Consommation"
)

plt.axvline(
    p90,
    color="orange",
    linestyle="--",
    label="P90"
)

plt.axvline(
    p95,
    color="red",
    linestyle="--",
    label="P95"
)

plt.axvline(
    p99,
    color="purple",
    linestyle="--",
    label="P99"
)

plt.axvline(
    upper_limit,
    color="black",
    linestyle="-",
    label="Seuil IQR"
)

plt.xlabel("Puissance (kW)")
plt.ylabel("Frequence")

plt.title(
    "Distribution de la puissance et seuils de depassement"
)

plt.legend()
plt.tight_layout()

plt.savefig(
    os.path.join(
        RESULTS_DIR,
        "power_distribution_thresholds.png"
    )
)

plt.close()

# ==========================================
# 6. EVOLUTION TEMPORELLE DES DEPASSEMENTS
# ==========================================

if not overload_data.empty:

    first_overload_date = overload_data["timestamp"].iloc[0]

    start_date = first_overload_date.normalize()

    end_date = start_date + pd.Timedelta(days=7)

    week_data = df[
        (df["timestamp"] >= start_date) &
        (df["timestamp"] < end_date)
    ].copy()

    plt.figure(figsize=(15, 6))

    plt.plot(
        week_data["timestamp"],
        week_data["power_kW"],
        label="Puissance",
        linewidth=0.8
    )

    plt.axhline(
        upper_limit,
        color="red",
        linestyle="--",
        label="Seuil de depassement"
    )

    plt.scatter(
        week_data.loc[
            week_data["overload"], "timestamp"
        ],
        week_data.loc[
            week_data["overload"], "power_kW"
        ],
        color="red",
        s=15,
        label="Depassements"
    )

    plt.xlabel("Date")
    plt.ylabel("Puissance (kW)")

    plt.title(
        "Evolution de la puissance pendant une semaine avec depassements"
    )

    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.savefig(
        os.path.join(
            RESULTS_DIR,
            "weekly_overload_evolution.png"
        )
    )

    plt.close()

else:

    print(
        "\nAucun depassement detecte : "
        "graphique hebdomadaire ignore."
    )

# ==========================================
# 7. IDENTIFICATION DES PERIODES
# ==========================================

print("\n========== IDENTIFICATION DES PERIODES ==========\n")

time_difference = df["timestamp"].diff()

new_period = (
    df["overload"].ne(df["overload"].shift()) |
    time_difference.ne(pd.Timedelta(minutes=1))
)

df["period_id"] = new_period.cumsum()

overload_periods = (
    df[df["overload"]]
    .groupby("period_id")
    .agg(
        start_time=("timestamp", "min"),
        end_time=("timestamp", "max"),
        number_of_measurements=("timestamp", "count"),
        max_power=("power_kW", "max"),
        mean_power=("power_kW", "mean")
    )
    .reset_index(drop=True)
)

overload_periods["duration_minutes"] = (
    overload_periods["end_time"] -
    overload_periods["start_time"]
).dt.total_seconds() / 60

overload_periods["duration_covered_minutes"] = (
    overload_periods["duration_minutes"] + 1
)

print(
    "Nombre de periodes de depassement :",
    len(overload_periods)
)

if not overload_periods.empty:

    print("\nApercu des periodes :")
    print(overload_periods.head())

    overload_periods.to_csv(
        os.path.join(
            RESULTS_DIR,
            "overload_periods.csv"
        ),
        index=False
    )

else:

    print("Aucune periode de depassement a enregistrer.")

# ==========================================
# 8. ANALYSE JOURNALIERE
# ==========================================

print("\n========== ANALYSE JOURNALIERE ==========\n")

df["date"] = df["timestamp"].dt.date

daily_overload = df.groupby("date").agg(
    total_measurements=("overload", "count"),
    overload_count=("overload", "sum"),
    max_power=("power_kW", "max")
).reset_index()

daily_overload["overload_percentage"] = (
    daily_overload["overload_count"] /
    daily_overload["total_measurements"] * 100
)

daily_overload.to_csv(
    os.path.join(
        RESULTS_DIR,
        "daily_overload_analysis.csv"
    ),
    index=False
)

plt.figure(figsize=(14, 6))

plt.plot(
    daily_overload["date"],
    daily_overload["overload_count"],
    marker="o",
    markersize=2
)

plt.xlabel("Date")
plt.ylabel("Nombre de depassements")

plt.title(
    "Nombre journalier de depassements electriques"
)

plt.xticks(rotation=45)
plt.tight_layout()

plt.savefig(
    os.path.join(
        RESULTS_DIR,
        "daily_overload_analysis.png"
    )
)

plt.close()

# ==========================================
# 9. ANALYSE HORAIRE
# ==========================================

df["hour"] = df["timestamp"].dt.hour

hourly_overload = df.groupby("hour").agg(
    total_measurements=("overload", "count"),
    overload_count=("overload", "sum"),
    max_power=("power_kW", "max")
).reset_index()

hourly_overload["overload_percentage"] = (
    hourly_overload["overload_count"] /
    hourly_overload["total_measurements"] * 100
)

hourly_overload.to_csv(
    os.path.join(
        RESULTS_DIR,
        "hourly_overload_analysis.csv"
    ),
    index=False
)

plt.figure(figsize=(12, 6))

plt.bar(
    hourly_overload["hour"],
    hourly_overload["overload_count"]
)

plt.xlabel("Heure de la journee")
plt.ylabel("Nombre de depassements")

plt.title(
    "Repartition horaire des depassements"
)

plt.xticks(range(24))
plt.tight_layout()

plt.savefig(
    os.path.join(
        RESULTS_DIR,
        "hourly_overload_analysis.png"
    )
)

plt.close()

# ==========================================
# 10. DISTRIBUTION DES DUREES
# ==========================================

if not overload_periods.empty:

    plt.figure(figsize=(10, 6))

    plt.hist(
        overload_periods["duration_covered_minutes"],
        bins=30
    )

    plt.xlabel("Duree estimee (minutes)")
    plt.ylabel("Nombre de periodes")

    plt.title(
        "Distribution des durees des periodes de depassement"
    )

    plt.tight_layout()

    plt.savefig(
        os.path.join(
            RESULTS_DIR,
            "overload_duration_distribution.png"
        )
    )

    plt.close()

# ==========================================
# 11. TOP 10 DES PERIODES
# ==========================================

if not overload_periods.empty:

    top_periods = overload_periods.sort_values(
        by="max_power",
        ascending=False
    ).head(10)

    top_periods.to_csv(
        os.path.join(
            RESULTS_DIR,
            "top_10_overload_periods.csv"
        ),
        index=False
    )

    print(
        "\nTop 10 des periodes avec les puissances maximales :"
    )

    print(top_periods)

# ==========================================
# 12. BILAN FINAL
# ==========================================

print("\n========== BILAN FINAL ==========\n")

print("Nombre de mesures analysees :", len(df))

print("Nombre de depassements :", len(overload_data))

print(
    f"Pourcentage de depassements : "
    f"{overload_percentage:.2f}%"
)

print("Nombre de periodes :", len(overload_periods))

print("\nFichiers enregistres dans :", RESULTS_DIR)

print("\n========== FIN DE LA PARTIE 5 ==========")






