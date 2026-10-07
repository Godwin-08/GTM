# ==============================================================================
# Dockerfile Multi-Stage Optimisé — Galaxy Training Manager (GTM)
# ==============================================================================
FROM python:3.11-slim

# Variables d'environnement Python standard
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=5000

WORKDIR /app

# Dépendances système légères pour PyMySQL et les librairies scientifiques
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    default-libmysqlclient-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie et installation des dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie de l'ensemble du code source
COPY . .

# Exposition du port
EXPOSE 5000

# Démarrage avec Gunicorn (4 workers, bind sur le port d'environnement)
CMD ["sh", "-c", "gunicorn wsgi:app --bind 0.0.0.0:${PORT:-5000} --workers 4 --threads 2 --timeout 120"]

