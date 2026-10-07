"""
==============================================================================
Point d'entrée WSGI de Production — Galaxy Training Manager (GTM)
==============================================================================
Utilisé par Gunicorn, uWSGI ou tout serveur WSGI de production.
Exemple d'exécution :
    gunicorn wsgi:app -w 4 -b 0.0.0.0:5000
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()

