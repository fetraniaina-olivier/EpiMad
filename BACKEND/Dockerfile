FROM python:3.12-slim

WORKDIR /app

# dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# dépendances Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copier le code source
COPY BACKEND/ /app/
COPY entrainement_modele/ /app/entrainement_modele/
COPY ETL/ /app/ETL/

# Configuration des imports
ENV PYTHONPATH="/app/app:/app:${PYTHONPATH}"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]