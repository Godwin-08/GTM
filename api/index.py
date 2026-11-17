import os
import sys

# Ajoute le dossier racine au path pour les imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

flask_app = create_app()


class VercelMiddleware:
    """
    Middleware WSGI pour Vercel Serverless :
    Rétablit le vrai PATH_INFO à partir de RAW_URI ou REQUEST_URI
    pour que Flask route correctement vers les pages HTML et les endpoints API.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        raw_uri = (
            environ.get("RAW_URI")
            or environ.get("REQUEST_URI")
            or environ.get("HTTP_X_FORWARDED_URI")
            or environ.get("HTTP_X_MATCHED_PATH")
        )

        if raw_uri:
            # Extrait le chemin sans la query string
            path = raw_uri.split("?")[0]
            if path:
                environ["PATH_INFO"] = path
        else:
            path = environ.get("PATH_INFO", "")
            if path.startswith("/api/index"):
                path = path[len("/api/index") :] or "/"
                environ["PATH_INFO"] = path

        return self.wsgi_app(environ, start_response)


# Wrap l'application Flask
app = VercelMiddleware(flask_app)
