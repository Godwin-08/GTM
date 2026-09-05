"""
Script de migration de schéma pour la base MySQL Galaxy Solutions.
Ajoute les colonnes d'onboarding (token_activation_hash, expiration_token)
et rend mot_de_passe_hash nullable sur la table Utilisateur si elles n'existent pas encore.
"""

import sys
import os
sys.path.insert(0, os.path.abspath("."))

from sqlalchemy import text, inspect
from app import create_app
from app.extensions import db


def appliquer_migration():
    print(">>> Verification et migration du schema MySQL pour l'Onboarding...")
    app = create_app()
    with app.app_context():
        inspecteur = inspect(db.engine)
        colonnes_existantes = [col["name"] for col in inspecteur.get_columns("utilisateur")]
        print(f"Colonnes actuelles sur 'utilisateur' : {colonnes_existantes}")

        with db.engine.connect() as conn:
            # 1. Rendre mot_de_passe_hash nullable
            try:
                conn.execute(text("ALTER TABLE Utilisateur MODIFY COLUMN mot_de_passe_hash VARCHAR(255) NULL;"))
                print("  [OK] 'mot_de_passe_hash' modifie en NULLABLE.")
            except Exception as e:
                print(f"  [INFO] mot_de_passe_hash: {e}")

            # 2. Ajouter token_activation_hash si absent
            if "token_activation_hash" not in colonnes_existantes:
                try:
                    conn.execute(text("ALTER TABLE Utilisateur ADD COLUMN token_activation_hash VARCHAR(64) NULL;"))
                    conn.execute(text("CREATE INDEX idx_utilisateur_token_activation ON Utilisateur(token_activation_hash);"))
                    print("  [OK] Colonne 'token_activation_hash' ajoutee avec succes.")
                except Exception as e:
                    print(f"  [ERREUR] Ajout token_activation_hash: {e}")
            else:
                print("  [INFO] Colonne 'token_activation_hash' deja presente.")

            # 3. Ajouter expiration_token si absent
            if "expiration_token" not in colonnes_existantes:
                try:
                    conn.execute(text("ALTER TABLE Utilisateur ADD COLUMN expiration_token DATETIME NULL;"))
                    print("  [OK] Colonne 'expiration_token' ajoutee avec succes.")
                except Exception as e:
                    print(f"  [ERREUR] Ajout expiration_token: {e}")
            else:
                print("  [INFO] Colonne 'expiration_token' deja presente.")

            conn.commit()

        print("\n>>> Migration terminee avec succes. La base MySQL est a jour !")


if __name__ == "__main__":
    appliquer_migration()

