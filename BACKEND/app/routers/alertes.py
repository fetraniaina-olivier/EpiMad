from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db

router = APIRouter(prefix="/api/alertes", tags=["Alertes"])

# Seuils d'alerte par maladie
SEUILS_ALERTES = {
    "Paludisme": 1500,
    "Peste": 100,
    "Rougeole": 300,
    "COVID-19": 500,
    "Hépatite virale": 200,
    "Tuberculose": 150
}

@router.get("/")
def get_alertes_ia_predictives(horizon: int = 4, db: Session = Depends(get_db)):
    """
    Génère des ALERTES FUTURES en projetant la tendance.
    horizon: nombre de semaines à prédire (1, 2, 4, 8)
    """
    alertes = []
    
    # Récupérer l'historique des 4 dernières semaines
    query = text("""
        SELECT 
            c.region_id, 
            r.nom_region, 
            c.maladie_id, 
            m.nom_officiel, 
            c.date_observation, 
            c.cas_nouveaux
        FROM cas_epidemiques c
        JOIN regions r ON c.region_id = r.id
        JOIN maladies m ON c.maladie_id = m.id
        WHERE c.date_observation >= (
            SELECT MAX(date_observation) - INTERVAL '28 days' 
            FROM cas_epidemiques 
            WHERE region_id = c.region_id AND maladie_id = c.maladie_id
        )
        ORDER BY c.region_id, c.maladie_id, c.date_observation ASC;
    """)

    try:
       
        result = db.execute(query)
        rows = result.fetchall()
        
        groupes = {}
        for row in rows:
            key = (row[0], row[2])
            if key not in groupes:
                groupes[key] = {
                    "region_nom": row[1],
                    "maladie_nom": row[3],
                    "dates": [],
                    "cas": []
                }
            groupes[key]["dates"].append(row[4])
            groupes[key]["cas"].append(row[5])

        for (region_id, maladie_id), data in groupes.items():
            if len(data["cas"]) < 2:
                continue
            
            cas_actuels = data["cas"]
            maladie_nom = data["maladie_nom"]
            region_nom = data["region_nom"]
            seuil = SEUILS_ALERTES.get(maladie_nom, 500)
            
            variation_moyenne = (cas_actuels[-1] - cas_actuels[0]) / (len(cas_actuels) - 1)
            
            cas_prevus = int(cas_actuels[-1] + variation_moyenne * horizon)
            cas_prevus_j7 = int(cas_actuels[-1] + variation_moyenne)
            cas_prevus_j14 = int(cas_actuels[-1] + (variation_moyenne * horizon))
            
            date_alerte_future = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")

            if cas_prevus_j14 > seuil:
                alertes.append({
                    "id": f"alert_future_{region_id}_{maladie_id}",
                    "type": "PREDICTION_IA",
                    "priorite": "CRITIQUE",
                    "icone": "🚨",
                    "titre": f"Risque de dépassement dans {horizon} semaines",
                    "description": f"Selon la tendance actuelle, {maladie_nom} à {region_nom} devrait atteindre ~{cas_prevus} cas dans {horizon} semaines (Seuil: {seuil}).",
                    "region": region_nom,
                    "maladie": maladie_nom,
                    "valeur_actuelle": cas_actuels[-1],
                    "valeur_prevue": cas_prevus_j14,
                    "seuil": seuil,
                    "horizon": horizon,
                    "date": date_alerte_future,
                    "statut": "NOUVELLE"
                })
            elif cas_prevus_j7 > seuil * 0.85:
                alertes.append({
                    "id": f"alert_warning_{region_id}_{maladie_id}",
                    "type": "PREDICTION_IA",
                    "priorite": "ELEVEE",
                    "icone": "⚠️",
                    "titre": f"Augmentation critique détectée",
                    "description": f"La tendance de {maladie_nom} à {region_nom} est en forte hausse. Surveillance renforcée recommandée.",
                    "region": region_nom,
                    "maladie": maladie_nom,
                    "valeur_actuelle": cas_actuels[-1],
                    "valeur_prevue": cas_prevus_j7,
                    "seuil": seuil,
                    "horizon": horizon,
                    "date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                    "statut": "NOUVELLE"
                })

        ordre_priorite = {"CRITIQUE": 0, "ELEVEE": 1, "MODEREE": 2, "FAIBLE": 3}
        alertes.sort(key=lambda x: ordre_priorite.get(x["priorite"], 99))

        return {
            "status": "success",
            "total_alertes": len(alertes),
            "horizon_utilise": horizon,
            "derniere_maj": datetime.now().isoformat(),
            "data": alertes
        }

    except Exception as e:
        print(f"Erreur génération alertes: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")