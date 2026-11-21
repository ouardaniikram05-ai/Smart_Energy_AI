"""État du système : alertes récentes, dépassements de puissance et tendance de consommation."""
import pandas as pd
import streamlit as st

from src.common import charger_optionnel


@st.cache_data(show_spinner=False)
def episodes_consensus(cons: pd.DataFrame, ecart_min: int = 5) -> pd.DataFrame:
    """Regroupe les minutes anormales consécutives (écart <= 5 min) en épisodes."""
    c = cons.sort_values("Datetime")
    groupe = (c["Datetime"].diff() > pd.Timedelta(minutes=ecart_min)).cumsum()
    ep = c.groupby(groupe).agg(debut=("Datetime", "min"), fin=("Datetime", "max"),
                               minutes=("Datetime", "size"), votes=("Anomaly_votes", "max"))
    ep["duree"] = (ep["fin"] - ep["debut"]).dt.total_seconds() / 60 + 1
    return ep.reset_index(drop=True)


def etat_systeme(df: pd.DataFrame, kw_max: float, duree_min: int = 10) -> dict:
    fin = df["timestamp"].max()
    sem, mois = fin - pd.Timedelta(days=7), fin - pd.Timedelta(days=30)

    over = charger_optionnel("overload_periods.csv", ("start_time", "end_time"))
    if over is not None:
        dep = int(((over["start_time"] > mois) & (over["max_power"] >= kw_max)).sum())
        dep_sem = int(((over["start_time"] > sem) & (over["max_power"] >= kw_max)).sum())
    else:
        dep = int(((df["timestamp"] > mois) & (df["power_kW"] >= kw_max)).sum())
        dep_sem = int(((df["timestamp"] > sem) & (df["power_kW"] >= kw_max)).sum())

    cons = charger_optionnel("consensus_anomalies.csv", ("Datetime",))
    n_ep = n_crit = None
    if cons is not None:
        ep = episodes_consensus(cons)
        ep = ep[(ep["debut"] > sem) & (ep["duree"] >= duree_min)]
        n_ep, n_crit = len(ep), int((ep["votes"] == 3).sum())

    j = (df.set_index("timestamp")["power_kW"].resample("D").mean() * 24).dropna()
    recent, avant = j[j.index > sem].mean(), j[(j.index <= sem) & (j.index > fin - pd.Timedelta(days=35))].mean()
    tendance = (recent / avant - 1) * 100 if avant and avant > 0 else None

    if dep_sem > 0 or (n_crit or 0) > 0:
        niveau, message = "rouge", "Alerte à vérifier"
    elif (n_ep or 0) > 0 or dep > 0 or (tendance is not None and tendance > 25):
        niveau, message = "orange", "À surveiller"
    else:
        niveau, message = "vert", "Tout est normal"
    return dict(niveau=niveau, message=message, anomalies_7j=n_ep, critiques_7j=n_crit,
                depassements_30j=dep, tendance=tendance)
