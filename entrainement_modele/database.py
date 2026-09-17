"""
Connexion à PostgreSQL et extraction des données EpiMad.
Compatible SQLAlchemy 2.0, Pandas 2.0+ et Docker.
"""

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# variables du fichier .env
load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "epimad_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "epimad_secret_password_2026")
POSTGRES_DB = os.getenv("POSTGRES_DB", "epimad_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:"
    f"{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

print(f" Connexion à : {POSTGRES_HOST}:{POSTGRES_PORT}")
engine = create_engine(DATABASE_URL)


def test_connection():
    """Teste la connexion à PostgreSQL."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("✓ Connexion PostgreSQL réussie.")
            print(f" Résultat du test : {result.scalar()}")
    except Exception as error:
        print("✗ Échec de la connexion PostgreSQL.")
        print(f"Erreur : {error}")


def get_epidemic_data():
    """Récupère les données épidémiques avec le nom de la maladie."""
    query = text("""
        SELECT
            c.id,
            c.date_observation,
            c.semaine_epidemio,
            c.region_id,
            c.maladie_id,
            m.nom_officiel AS maladie,
            c.cas_nouveaux,
            c.cas_cumules,
            c.deces,
            c.hospitalisations,
            c.taux_incidence,
            c.taux_letalite,
            c.niveau_alerte,
            c.donnees_specifiques,
            c.gueris
        FROM cas_epidemiques c
        INNER JOIN maladies m
            ON c.maladie_id = m.id
        ORDER BY c.maladie_id, c.region_id, c.date_observation;
    """)

    try:
       
        with engine.connect() as conn:
            result = conn.execute(query)
           
            columns = result.keys()
            
            rows = result.fetchall()
            
            df = pd.DataFrame(rows, columns=columns)
            print(f" Données récupérées : {len(df):,} observations")
            return df
    except Exception as error:
        print("✗ Erreur lors de l'extraction des données.")
        print(f"Erreur : {error}")
        return pd.DataFrame()


def inspect_db_truth():
    """Vérifie la vérité brute dans la base de données, semaine par semaine."""
    query = text("""
        SELECT 
            EXTRACT(YEAR FROM c.date_observation) as annee,
            EXTRACT(WEEK FROM c.date_observation) as semaine,
            COUNT(DISTINCT c.region_id) as nb_regions_actives,
            SUM(c.cas_nouveaux) as total_cas_nouveaux,
            SUM(c.cas_cumules) as total_cas_cumules
        FROM cas_epidemiques c
        INNER JOIN maladies m ON c.maladie_id = m.id
        WHERE m.nom_officiel = 'Paludisme'
        GROUP BY 
            EXTRACT(YEAR FROM c.date_observation), 
            EXTRACT(WEEK FROM c.date_observation)
        ORDER BY annee DESC, semaine DESC
        LIMIT 30;
    """)
    try:
       
        with engine.connect() as conn:
            result = conn.execute(query)
            columns = result.keys()
            rows = result.fetchall()
            df = pd.DataFrame(rows, columns=columns)
            
            print("\n" + "="*80)
            print(" VÉRITÉ BRUTE DE LA BASE DE DONNÉES (PALUDISME)")
            print("="*80)
            print(df.to_string(index=False))
            print("="*80)
            
            df_2026 = df[df['annee'] == 2026]
            if not df_2026.empty:
                print(f"\n ANALYSE 2026 : {len(df_2026)} semaines trouvées.")
                print(f"   ➔ Maximum de cas en une semaine en 2026 : {df_2026['total_cas_nouveaux'].max():,}")
                print(f"   ➔ Moyenne de cas par semaine en 2026    : {df_2026['total_cas_nouveaux'].mean():.0f}")
            else:
                print("\n AUCUNE DONNÉE TROUVÉE POUR 2026 DANS LA BASE !")
                
    except Exception as e:
        print(f"Erreur SQL : {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE CONNEXION À EpiMad")
    print("=" * 60)

    test_connection()

    print("\n Lancement de l'inspection directe de la base de données...")
    inspect_db_truth()