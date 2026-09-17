import pandas as pd
import joblib
from pathlib import Path

if Path("/app/entrainement_modele").exists(): 
    BASE_DIR = Path("/app")
else:
    
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

MODELS_DIR = BASE_DIR / "entrainement_modele" / "arima" / "models"

print(f"ARIMA - Chemin des modèles : {MODELS_DIR}")

def charger_et_predire(region_id: int, maladie_id: int, horizon: int = 4):
    """Charge le modèle ARIMA et génère les prévisions."""
    nom_fichier = f"arima_r{region_id}_m{maladie_id}.pkl"
    chemin_modele = MODELS_DIR / nom_fichier
    print(f"Recherche du modèle : {chemin_modele}")
    if not chemin_modele.exists():
        raise FileNotFoundError(
            f"Aucun modèle trouvé pour la Région {region_id} et la Maladie {maladie_id} "
            f"dans {MODELS_DIR}."
        )
    
    print(f" Modèle trouvé, chargement en cours...")
    modele = joblib.load(chemin_modele)
    
    # Générer les prévisions et créer la feature
    previsions, intervalles = modele.predict(n_periods=horizon, return_conf_int=True)
    date_debut = pd.Timestamp.now() + pd.Timedelta(weeks=1)
    dates_futures = pd.date_range(start=date_debut, periods=horizon, freq='W')
    
    resultats = []
    
    for i in range(horizon):
        resultats.append({
            "date": dates_futures[i].strftime("%Y-%m-%d"),
            "cas_prevus": int(round(float(previsions.iloc[i]))),
            "min_confiance": int(round(max(0, float(intervalles[i][0])))),
            "max_confiance": int(round(max(0, float(intervalles[i][1]))))
        })
        
    print(f" {len(resultats)} prévisions ARIMA générées avec succès !")
    return resultats