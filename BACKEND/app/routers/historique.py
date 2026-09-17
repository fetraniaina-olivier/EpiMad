import sys
import os
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
epimad_dir = os.path.dirname(backend_dir)
entrainement_dir = os.path.join(epimad_dir, 'entrainement_modele')

if entrainement_dir not in sys.path:
    sys.path.insert(0, entrainement_dir)

try:
    from database import engine
except Exception as e:
    print(f" DEBUG: Échec de l'import database: {e}")


from app.database import get_db
from app.models import CasEpidemique, Maladie, Region, User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/historique-donnees", tags=["Historique"])

@router.get("/")
def get_historique_epidemique(
    maladie_id: int = Query(..., description="ID de la maladie"),
    region_id: int = Query(..., description="ID de la région"),
    date_debut: str = Query(None, description="Date de début (YYYY-MM-DD)"),
    date_fin: str = Query(None, description="Date de fin (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère l'historique des données épidémiologiques."""
    

    query = """
        SELECT 
            ce.date_observation,
            ce.cas_nouveaux,
            ce.cas_cumules,
            ce.deces,
            ce.gueris,
            ce.hospitalisations,
            ce.taux_incidence,
            ce.taux_letalite,
            ce.niveau_alerte,
            r.nom_region as region_nom,
            m.nom_officiel as maladie_nom
        FROM cas_epidemiques ce
        JOIN regions r ON ce.region_id = r.id
        JOIN maladies m ON ce.maladie_id = m.id
        WHERE ce.region_id = :region_id 
          AND ce.maladie_id = :maladie_id
    """
    
    params = {
        "region_id": region_id,
        "maladie_id": maladie_id
    }
    
    
    if date_debut:
        query += " AND ce.date_observation >= :date_debut"
        params["date_debut"] = date_debut
    
    if date_fin:
        query += " AND ce.date_observation <= :date_fin"
        params["date_fin"] = date_fin
    
    query += " ORDER BY ce.date_observation ASC"
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), params)
            rows = result.fetchall()
            
            if not rows:
                return {
                    "region_id": region_id,
                    "maladie_id": maladie_id,
                    "data": [],
                    "statistics": None
                }
            
            historique = []
            for row in rows:
                historique.append({
                    "date": row.date_observation.strftime("%Y-%m-%d") if row.date_observation else "",
                    "semaine": f"Sem. {row.date_observation.strftime('%Y-W%V')}" if row.date_observation else "",
                    "cas_nouveaux": int(row.cas_nouveaux) if row.cas_nouveaux else 0,
                    "cas_cumules": int(row.cas_cumules) if row.cas_cumules else 0,
                    "deces": int(row.deces) if row.deces else 0,
                    "gueris": int(row.gueris) if row.gueris else 0,
                    "hospitalisations": int(row.hospitalisations) if row.hospitalisations else 0,
                    "taux_incidence": float(row.taux_incidence) if row.taux_incidence else 0.0,
                    "taux_letalite": float(row.taux_letalite) if row.taux_letalite else 0.0,
                    "niveau_alerte": row.niveau_alerte if row.niveau_alerte else "Faible",
                    "region_nom": row.region_nom if row.region_nom else "",
                    "maladie_nom": row.maladie_nom if row.maladie_nom else ""
                })
            
            # Calculer les statistiques
            total_cas = sum(item["cas_nouveaux"] for item in historique)
            total_deces = sum(item["deces"] for item in historique)
            total_gueris = sum(item["gueris"] for item in historique)
            total_hospitalisations = sum(item["hospitalisations"] for item in historique)
            
            return {
                "region_id": region_id,
                "maladie_id": maladie_id,
                "region_nom": rows[0].region_nom if rows else "",
                "maladie_nom": rows[0].maladie_nom if rows else "",
                "date_debut": date_debut,
                "date_fin": date_fin,
                "nombre_enregistrements": len(historique),
                "statistics": {
                    "total_cas": total_cas,
                    "total_deces": total_deces,
                    "total_gueris": total_gueris,
                    "total_hospitalisations": total_hospitalisations
                },
                "data": historique
            }
            
    except Exception as e:
        print(f" ERREUR SQL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")