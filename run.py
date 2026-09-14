"""
==============================================================================
Point d'entrée principal de l'application Galaxy Training Manager (GTM)
==============================================================================
Ce script démarre le serveur de développement WSGI de Flask.
Il lit la configuration réseau depuis l'environnement ou applique les valeurs
par défaut (0.0.0.0:5000) et affiche les URLs d'accès local et réseau local.
"""

import os
import socket
from app import create_app

# Instanciation de l'application Flask via le patron Factory défini dans app/__init__.py
app = create_app()

if __name__ == "__main__":
    # Récupération de l'hôte et du port d'écoute depuis les variables d'environnement
    # 0.0.0.0 permet d'écouter sur toutes les interfaces réseau (local + Wi-Fi/LAN)
    host = os.environ.get("FLASK_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_PORT", 5000))
    # Activation du mode débogage (rechargement à chaud et traceback détaillé en développement)
    debug = os.environ.get("FLASK_DEBUG", "true").lower() in ("true", "1", "yes")

    # Détection automatique de l'adresse IP locale sur le réseau local
    try:
        local_ip = socket.gethostbyname(socket.gethostname())
    except Exception:
        local_ip = "127.0.0.1"

    # Bannière d'accueil dans la console avec les liens d'accès
    print("\n" + "=" * 60)
    print("  GALAXY TRAINING MANAGER (GTM) — Galaxy Solutions")
    print(f"  * Accès local       : http://localhost:{port}")
    print(f"  * Accès réseau/Wi-Fi: http://{local_ip}:{port}")
    print("=" * 60 + "\n")

    # Démarrage effectif du serveur web Flask
    app.run(host=host, port=port, debug=debug)


