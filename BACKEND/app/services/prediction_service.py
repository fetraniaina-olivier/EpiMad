import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

ML_DIR = Path(__file__).resolve().parent.parent.parent / "ML"
sys.path.insert(0, str(ML_DIR))

from preprocessing import prepare_for_xgboost, XGBOOST_FEATURES # type: ignore
from database import get_epidemic_data

class PredictionService:
    """Service de prédiction qui charge et utilise les modèles XGBoost."""
    
    def __init__(self):
        self.models = {}
        self.models_dir = ML_DIR / "models"
        self._load_all_models()
    
    def _load_all_models(self):
        """Charge tous les modèles .joblib disponibles au démarrage."""
        print(" Chargement des modèles XGBoost...")
        
        for model_file in self.models_dir.glob("xgboost_*.joblib"):
            disease_name = model_file.stem.replace("xgboost_", "").replace("_", " ").title()
            
            if "Covid" in disease_name:
                disease_name = "COVID-19"
            elif "Hepatite" in disease_name:
                disease_name = "Hépatite virale"
            
            try:
                model = joblib.load(model_file)
                self.models[disease_name] = {
                    "model": model,
                    "path": model_file,
                    "loaded_at": pd.Timestamp.now().isoformat()
                }
                print(f"   {disease_name} chargé depuis {model_file.name}")
            except Exception as e:
                print(f"   Erreur chargement {model_file.name}: {e}")
        
        print(f" {len(self.models)} modèles chargés avec succès.\n")
    
    def predict_disease(self, disease: str, horizon: int = 4):
        """
        Prédit l'évolution d'une maladie pour les 24 régions sur l'horizon donné.
        
        Args:
            disease: Nom de la maladie (ex: "Paludisme", "Rougeole")
            horizon: Nombre de semaines à prédire (défaut: 4)
        
        Returns:
            Liste de dict avec les prédictions par région et semaine
        """
        if disease not in self.models:
            raise ValueError(f"Modèle non trouvé pour: {disease}. Modèles disponibles: {list(self.models.keys())}")
        
        model_info = self.models[disease]
        model = model_info["model"]
        
        # Charger les données
        df = get_epidemic_data()
        df_disease = df[df["maladie"] == disease].copy()
        
        if df_disease.empty:
            raise ValueError(f"Aucune donnée trouvée pour: {disease}")
        
        df_ml = prepare_for_xgboost(df_disease, create_lags=True, remove_first_lag_rows=True)
        
        
        weekly_totals = df_ml.groupby(["annee", "semaine"])["cas_nouveaux"].sum()
        MIN_CASES_THRESHOLD = 100 if disease == "Peste" else 1000
        
        valid_weeks = weekly_totals[weekly_totals >= MIN_CASES_THRESHOLD]
        if valid_weeks.empty:
            last_valid_week = weekly_totals.index[-1]
        else:
            last_valid_week = valid_weeks.index[-1]
        
        df_ml_valid = df_ml[
            (df_ml["annee"] < last_valid_week[0]) | 
            ((df_ml["annee"] == last_valid_week[0]) & (df_ml["semaine"] <= last_valid_week[1]))
        ].copy()
        
        
        current_state = df_ml_valid.groupby("region_id").last().reset_index()
        
        all_predictions = []
        
        for step in range(1, horizon + 1):
            df_future = current_state.copy()
            
            
            df_future["cas_lag_1"] = current_state["cas_nouveaux"]
            df_future["cas_lag_2"] = current_state["cas_lag_1"]
            df_future["cas_lag_4"] = current_state["cas_lag_3"] if "cas_lag_3" in current_state.columns else current_state["cas_lag_2"]
            df_future["cas_lag_8"] = current_state["cas_lag_7"] if "cas_lag_7" in current_state.columns else current_state["cas_lag_4"]
            
            # Moyennes
            for col in ["moyenne_4sem", "moyenne_8sem", "var_moyenne_4sem", "var_moyenne_8sem"]:
                if col in current_state.columns:
                    df_future[col] = current_state[col]
            
            # Mise à jour du temps
            df_future["semaine"] = (current_state["semaine"].astype(int) % 52) + 1
            df_future["mois"] = ((df_future["semaine"] - 1) // 4) + 1
            df_future["trimestre"] = ((df_future["mois"] - 1) // 3) + 1
            df_future["annee"] = current_state["annee"].astype(int) + (current_state["semaine"].astype(int) // 52)
            
            # Features cycliques
            df_future["mois_sin"] = np.sin(2 * np.pi * df_future["mois"] / 12)
            df_future["mois_cos"] = np.cos(2 * np.pi * df_future["mois"] / 12)
            df_future["semaine_sin"] = np.sin(2 * np.pi * df_future["semaine"] / 52)
            df_future["semaine_cos"] = np.cos(2 * np.pi * df_future["semaine"] / 52)
            df_future["tendance"] = df_future["annee"] * 52 + df_future["semaine"]
            df_future["est_pic"] = (df_future["cas_lag_1"] > (df_future["moyenne_8sem"] * 1.5)).astype(int)
            
            # Inférence
            features_to_use = [f for f in XGBOOST_FEATURES if f in df_future.columns]
            X_future = df_future[features_to_use].fillna(0)
            
            y_pred_log = model.predict(X_future)
            y_pred = np.maximum(np.expm1(y_pred_log), 0).astype(int)
            
            # Mise à jour pour la prochaine itération
            current_state["cas_nouveaux"] = y_pred
            current_state["cas_lag_1"] = y_pred
            current_state["semaine"] = df_future["semaine"]
            current_state["annee"] = df_future["annee"]
            current_state["mois"] = df_future["mois"]
            
            # Sauvegarde des prédictions
            for _, row in current_state.iterrows():
                all_predictions.append({
                    "maladie": disease,
                    "region_id": int(row["region_id"]),
                    "annee": int(row["annee"]),
                    "semaine": int(row["semaine"]),
                    "horizon": f"T+{step}",
                    "cas_predits": int(y_pred[current_state["region_id"] == row["region_id"]][0])
                })
        
        return all_predictions
    
    def predict_all_diseases(self, horizon: int = 4):
        """
        Prédit toutes les maladies disponibles.
        
        Returns:
            Dict structuré avec toutes les prédictions
        """
        results = {}
        
        for disease in self.models.keys():
            try:
                predictions = self.predict_disease(disease, horizon)
                results[disease] = {
                    "predictions": predictions,
                    "model_file": self.models[disease]["path"].name,
                    "loaded_at": self.models[disease]["loaded_at"]
                }
            except Exception as e:
                results[disease] = {
                    "error": str(e),
                    "model_file": self.models[disease]["path"].name
                }
        
        return results
    
    def get_available_models(self):
        """Retourne la liste des modèles disponibles."""
        return {
            disease: {
                "model_file": info["path"].name,
                "loaded_at": info["loaded_at"]
            }
            for disease, info in self.models.items()
        }

prediction_service = PredictionService()