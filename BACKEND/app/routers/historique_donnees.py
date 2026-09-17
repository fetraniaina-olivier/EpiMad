import sys
import os
import logging
from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text


backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
epimad_dir = os.path.dirname(backend_dir)
entrainement_dir = os.path.join(epimad_dir, 'entrainement_modele')

print(f" DEBUG: Chemin vers entrainement_modele: {entrainement_dir}")


if entrainement_dir not in sys.path:
    sys.path.insert(0, entrainement_dir)


try:
    from database import engine
    print(" DEBUG: Import de database.py depuis entrainement_modele réussi !")
except Exception as e:
    print(f" DEBUG: Échec de l'import: {e}")
    raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/historique-donnees", tags=["Historique"])


@router.get("/maladies")
def get_liste_maladies():
    """Retourne la liste des maladies disponibles, pour peupler les filtres du frontend."""
    query = text("""
        SELECT id, nom_officiel
        FROM maladies
        ORDER BY nom_officiel ASC;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query)
            rows = result.fetchall()

            return [
                {"id": row.id, "nom": row.nom_officiel}
                for row in rows
            ]

    except Exception as e:
        logger.error(f"Erreur SQL dans get_liste_maladies: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.get("/regions")
def get_liste_regions():
    """Retourne la liste des régions disponibles, pour peupler les filtres du frontend."""
    query = text("""
        SELECT id, nom_region
        FROM regions
        ORDER BY nom_region ASC;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query)
            rows = result.fetchall()

            return [
                {"id": row.id, "nom": row.nom_region}
                for row in rows
            ]

    except Exception as e:
        logger.error(f"Erreur SQL dans get_liste_regions: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.get("")
@router.get("/")
def get_historique_par_filtres(
    maladie_id: int = Query(...),
    region_id: int = Query(...),
    date_debut: Optional[date] = Query(default=None),
    date_fin: Optional[date] = Query(default=None),
):
    """
    Retourne l'historique filtré par maladie, région, et une plage de dates optionnelle.
    Utilisé par le frontend via des query params, ex:
    /api/historique-donnees/?maladie_id=5&region_id=1&date_debut=2023-02-12&date_fin=2023-04-13
    """
    conditions = ["region_id = :region_id", "maladie_id = :maladie_id"]
    params = {"region_id": region_id, "maladie_id": maladie_id}

    if date_debut:
        conditions.append("date_observation >= :date_debut")
        params["date_debut"] = date_debut

    if date_fin:
        conditions.append("date_observation <= :date_fin")
        params["date_fin"] = date_fin

    where_clause = " AND ".join(conditions)

    query = text(f"""
        SELECT 
            date_observation,
            cas_nouveaux,
            cas_cumules,
            deces,
            gueris,
            taux_incidence
        FROM cas_epidemiques
        WHERE {where_clause}
        ORDER BY date_observation ASC;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query, params)
            rows = result.fetchall()

            if not rows:
                raise HTTPException(
                    status_code=404,
                    detail=f"Aucune donnée trouvée pour region_id={region_id}, maladie_id={maladie_id}"
                )

            historique = []
            for row in rows:
                historique.append({
                    "date": row.date_observation.strftime("%Y-%m-%d"),
                    "semaine": f"Sem. {row.date_observation.strftime('%Y-W%V')}",
                    "cas_nouveaux": int(row.cas_nouveaux) if row.cas_nouveaux else 0,
                    "cas_cumules": int(row.cas_cumules) if row.cas_cumules else 0,
                    "deces": int(row.deces) if row.deces else 0,
                    "gueris": int(row.gueris) if row.gueris else 0,
                    "taux_incidence": float(row.taux_incidence) if row.taux_incidence else 0.0
                })

            return {
                "region_id": region_id,
                "maladie_id": maladie_id,
                "semaines_disponibles": len(historique),
                "data": historique
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur SQL dans get_historique_par_filtres: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")


@router.get("/{region_id}/{maladie_id}")
def get_historique_epidemique(
    region_id: int,
    maladie_id: int,
    semaines: int = Query(default=52, ge=1, le=365)
):
    query = text("""
        SELECT 
            date_observation,
            cas_nouveaux,
            cas_cumules,
            deces,
            gueris,
            taux_incidence
        FROM cas_epidemiques
        WHERE region_id = :region_id 
          AND maladie_id = :maladie_id
        ORDER BY date_observation DESC
        LIMIT :limit_val;
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(
                query,
                {
                    "region_id": region_id,
                    "maladie_id": maladie_id,
                    "limit_val": semaines
                }
            )

            rows = result.fetchall()

            if not rows:
                raise HTTPException(
                    status_code=404,
                    detail=f"Aucune donnée trouvée pour region_id={region_id}, maladie_id={maladie_id}"
                )

            historique = []
            for row in rows:
                historique.append({
                    "date": row.date_observation.strftime("%Y-%m-%d"),
                    "semaine": f"Sem. {row.date_observation.strftime('%Y-W%V')}",
                    "cas_nouveaux": int(row.cas_nouveaux) if row.cas_nouveaux else 0,
                    "cas_cumules": int(row.cas_cumules) if row.cas_cumules else 0,
                    "deces": int(row.deces) if row.deces else 0,
                    "gueris": int(row.gueris) if row.gueris else 0,
                    "taux_incidence": float(row.taux_incidence) if row.taux_incidence else 0.0
                })
            historique.reverse()

            return {
                "region_id": region_id,
                "maladie_id": maladie_id,
                "semaines_disponibles": len(historique),
                "data": historique
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f" ERREUR SQL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur serveur: {str(e)}")