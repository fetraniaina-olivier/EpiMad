import os
import sys
import warnings
import pandas as pd
import numpy as np
import pmdarima as pm # type: ignore
import matplotlib # type: ignore
matplotlib.use('Agg')
import matplotlib.pyplot as plt # type: ignore
import joblib

from sqlalchemy import text
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine

warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)


def get_all_couples():
    """Récupère la liste de tous les couples (region_id, maladie_id) présents dans la BDD."""
    query = text("SELECT DISTINCT region_id, maladie_id FROM cas_epidemiques ORDER BY region_id, maladie_id;")
    try:
       
        with engine.connect() as conn:
            result = conn.execute(query)
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        print(f" Trouvé {len(df)} couples (Région, Maladie) avec des données dans la BDD.")
        return df
    except Exception as e:
        print(f" Erreur lors de la récupération des couples : {e}")
        return pd.DataFrame()


def charger_et_preparer_serie(region_id: int, maladie_id: int) -> pd.Series:
    """Charge les données pour un couple et prépare la série temporelle (preprocessing ARIMA)."""
    query = text("""
        SELECT date_observation, cas_nouveaux 
        FROM cas_epidemiques 
        WHERE region_id = :region_id AND maladie_id = :maladie_id
        ORDER BY date_observation ASC;
    """)
   
    with engine.connect() as conn:
        result = conn.execute(query, {"region_id": region_id, "maladie_id": maladie_id})
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    
    if df.empty:
        return None

    df['date_observation'] = pd.to_datetime(df['date_observation'])
    df.set_index('date_observation', inplace=True)

    df = df.resample('W').sum().fillna(0)
    
    return df['cas_nouveaux']


def entrainer_modele(region_id: int, maladie_id: int, horizon: int = 4):
    """Entraîne le modèle ARIMA pour un couple spécifique, sauvegarde et génère les prévisions."""
    print(f"\n--- Traitement : Région {region_id}, Maladie {maladie_id} ---")
    
    serie = charger_et_preparer_serie(region_id, maladie_id)
    
    if serie is None or len(serie) < 10:
        print(f" Pas assez de données (moins de 10 semaines). Modèle ignoré.")
        return

    print(f" {len(serie)} Semaines de données chargées. Recherche des paramètres (p,d,q)...")
    
    modele = pm.auto_arima(
        serie, 
        seasonal=False,
        trace=False,
        error_action='ignore',
        suppress_warnings=True,
        stepwise=True
    )
    
    print(f" Meilleur modèle trouvé : ARIMA{modele.order}")
    
    previsions, intervalles = modele.predict(n_periods=horizon, return_conf_int=True)
    
    derniere_date = serie.index[-1]
    dates_futures = pd.date_range(start=derniere_date + pd.Timedelta(weeks=1), periods=horizon, freq='W')
    
    df_previsions = pd.DataFrame({
        'date_previson': dates_futures,
        'cas_prevus': previsions,
        'intervalle_confiance_min': intervalles[:, 0],
        'intervalle_confiance_max': intervalles[:, 1]
    })
    
    # SAUVEGARDES
    nom_modele = f"arima_r{region_id}_m{maladie_id}.pkl"
    joblib.dump(modele, os.path.join(MODELS_DIR, nom_modele))
    
    nom_csv = f"previsions_r{region_id}_m{maladie_id}.csv"
    df_previsions.to_csv(os.path.join(RESULTS_DIR, nom_csv), index=False)
    
    # Génération du graphique
    plt.figure(figsize=(10, 5))
    plt.plot(serie.index, serie.values, label='Historique', color='blue', alpha=0.6)
    plt.plot(df_previsions['date_previson'], df_previsions['cas_prevus'], label='Prévision ARIMA', color='red', marker='o')
    plt.fill_between(df_previsions['date_previson'], df_previsions['intervalle_confiance_min'], df_previsions['intervalle_confiance_max'], color='red', alpha=0.2)
    plt.title(f'Prévision ARIMA - Région {region_id}, Maladie {maladie_id}')
    plt.legend()
    plt.grid(True)
    
    nom_graph = f"graphique_r{region_id}_m{maladie_id}.png"
    plt.savefig(os.path.join(RESULTS_DIR, nom_graph))
    plt.close()
    
    print(f" Sauvegardé : Modèle, CSV et Graphique.")


def main():
    print("="*60)
    print(" DÉMARRAGE DE L'ENTRAÎNEMENT ARIMA (Boucle sur tous les couples)")
    print("="*60)
    
    couples_df = get_all_couples()
    
    if couples_df.empty:
        print("Aucune donnée trouvée. Arrêt du script.")
        return

    for index, row in couples_df.iterrows():
        region_id = row['region_id']
        maladie_id = row['maladie_id']
        
        try:
            entrainer_modele(region_id, maladie_id, horizon=4)
        except Exception as e:
            print(f" Erreur critique pour Région {region_id}, Maladie {maladie_id} : {e}")

    print("\n" + "="*60)
    print(" ENTRAINEMENT TERMINÉ ! Tous les modèles sont dans le dossier 'models/'.")
    print("="*60)

if __name__ == "__main__":
    main()