import os
import sys

# Ajoute le dossier racine au path pour que les imports de l'application fonctionnent
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

app = create_app()

# Point d'entrée pour le runtime Serverless de Vercel
if __name__ == "__main__":
    app.run()
