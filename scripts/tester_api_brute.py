"""
Vérification de la réponse brute de l'API Flask avec session authentifiée.
Teste l'encodage exact (Content-Type, octets reçus, caractères accentués en texte brut).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Utilisateur

def tester_api_authentifiee():
    app = create_app()
    with app.app_context():
        admin = Utilisateur.query.filter_by(email="admin@galaxysolutions.ma").first()
        if not admin:
            print("[ERR] Compte admin introuvable en base.")
            return

        client = app.test_client()
        with client.session_transaction() as session:
            session["_user_id"] = str(admin.id)
            session["_fresh"] = True

        endpoints = [
            "/api/domaines",
            "/api/formations",
        ]

        print("\n" + "="*60)
        print("  TEST API FLASK AUTHENTIFIÉE (RÉPONSE BRUTE)")
        print("="*60)

        for ep in endpoints:
            res = client.get(ep)
            raw_data = res.data.decode("utf-8")
            print(f"\nEndpoint : {ep}")
            print(f"Status       : {res.status_code}")
            print(f"Content-Type : {res.headers.get('Content-Type')}")
            print(f"Extrait brut : {raw_data[:200]}")
            
            # Détection de double encodage
            if "Ã©" in raw_data or "Ã" in raw_data:
                print("  -> [ERR] Présence de double encodage (Ã©...) !")
            else:
                print("  -> [OK] Aucun caractère de corruption type Ã© détecté.")

if __name__ == "__main__":
    tester_api_authentifiee()

