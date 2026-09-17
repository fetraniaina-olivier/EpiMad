from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import import_etl
from app.routers import cas, maladies, regions, stats, predictions, historique, alertes, comparatif, import_data
from app.routers import auth
from app.routers import historique_donnees
from app.routers import arima_predictions
from app.routers import dashboard_stats

app = FastAPI(
    title="EpiMad API",
    description="API pour la surveillance épidémiologique pour Madagascar",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cas.router)
app.include_router(maladies.router)
app.include_router(regions.router)
app.include_router(stats.router)
app.include_router(predictions.router)
app.include_router(historique.router)
app.include_router(alertes.router)
app.include_router(arima_predictions.router)
app.include_router(comparatif.router)
app.include_router(import_data.router)
app.include_router(auth.router)
app.include_router(import_etl.router)
app.include_router(historique_donnees.router)
app.include_router(dashboard_stats.router)

@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Bienvenue sur l'API EpiMad !",
        "docs": "/docs",
        "status": "Opérationnel"
    }