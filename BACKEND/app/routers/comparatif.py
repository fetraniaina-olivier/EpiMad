from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/api/comparatif", tags=["Comparatif Régions"])

SEUILS = {
    "Paludisme": 1500, "Peste": 100, "Rougeole": 300,
    "COVID-19": 500, "Hépatite virale": 200, "Tuberculose": 150
}

@router.get("/regions")
def get_comparatif_regions(db: Session = Depends(get_db)):
    """Retourne un comparatif des 24 régions avec TOUTES leurs maladies actives."""
    
    query = text("""
        SELECT 
            c.region_id, 
            r.nom_region, 
            m.nom_officiel, 
            c.cas_nouveaux,
            c.date_observation
        FROM cas_epidemiques c
        JOIN regions r ON c.region_id = r.id
        JOIN maladies m ON c.maladie_id = m.id
        WHERE c.date_observation = (
            SELECT MAX(date_observation) 
            FROM cas_epidemiques 
            WHERE region_id = c.region_id AND maladie_id = c.maladie_id
        )
        ORDER BY c.region_id, c.cas_nouveaux DESC;
    """)

    try:
        
        rows = db.execute(query).fetchall()
        
        regions_data = {}
        for row in rows:
            rid, rnom, mnom, cas, date = row
            if rid not in regions_data:
                regions_data[rid] = {
                    "id": rid, 
                    "nom": rnom, 
                    "maladies": [],
                    "cas_total": 0
                }
            
            seuil = SEUILS.get(mnom, 500)
            ratio = (cas / seuil) * 100
            
            if ratio >= 100:
                risque = "CRITIQUE"
            elif ratio >= 80:
                risque = "ÉLEVÉ"
            elif ratio >= 50:
                risque = "MODÉRÉ"
            else:
                risque = "STABLE"
            
            regions_data[rid]["maladies"].append({
                "nom": mnom,
                "cas": cas,
                "seuil": seuil,
                "ratio": round(ratio, 1),
                "risque": risque
            })
            
            regions_data[rid]["cas_total"] += cas

        resultats = []
        for rid, data in regions_data.items():
            maladie_plus_critique = max(data["maladies"], key=lambda m: m["ratio"])
            ordre_risque = {"CRITIQUE": 0, "ÉLEVÉ": 1, "MODÉRÉ": 2, "STABLE": 3}
            risque_global = min(
                data["maladies"], 
                key=lambda m: ordre_risque.get(m["risque"], 99)
            )["risque"]
            
            resultats.append({
                "id": data["id"],
                "nom": data["nom"],
                "cas_total": data["cas_total"],
                "risque_global": risque_global,
                "maladie_principale": maladie_plus_critique["nom"],
                "ratio_max": maladie_plus_critique["ratio"],
                "maladies": data["maladies"]
            })

        resultats.sort(key=lambda x: ordre_risque.get(x["risque_global"], 99))

        return {"status": "success", "total": len(resultats), "data": resultats}

    except Exception as e:
        print(f"Erreur comparatif régions: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")