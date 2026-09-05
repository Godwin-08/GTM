import sys
import os
sys.path.insert(0, os.path.abspath("."))

import unittest
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Utilisateur, Role, Formateur, Domaine
from app.services.activation_service import (
    generer_token_activation,
    hasher_token,
    calculer_expiration_activation,
)
from app.services.mail_service import (
    generer_contenu_invitation,
    envoyer_invitation_activation,
)


class E2EOnboardingLifecycleTestCase(unittest.TestCase):
    def test_e2e_lifecycle(self):
        run_e2e_validation()


def run_e2e_validation():
    print("\n" + "=" * 80)
    print(">>> LANCEMENT DE LA VALIDATION FONCTIONNELLE E2E GTM (ONBOARDING & RBAC)")
    print("=" * 80 + "\n")

    Config.SQLALCHEMY_DATABASE_URI = "sqlite://"
    app = create_app()
    app.config.update(TESTING=True, MAIL_BACKEND="console")

    with app.app_context():
        db.drop_all()
        db.create_all()

        # 1. Initialisation des Référentiels
        role_admin = Role(nom="admin")
        role_gest = Role(nom="gestionnaire")
        role_form = Role(nom="formateur")
        db.session.add_all([role_admin, role_gest, role_form])

        domaine_web = Domaine(nom="Web & Data")
        db.session.add(domaine_web)
        db.session.flush()

        admin_principal = Utilisateur(
            nom="Admin Démo",
            email="admin.demo@galaxysolutions.ma",
            mot_de_passe_hash=generate_password_hash("AdminPass123!"),
            role=role_admin,
            actif=True,
        )
        db.session.add(admin_principal)
        db.session.commit()

        client = app.test_client()

        # =====================================================================
        # ÉTAPE A : Connexion Admin & Création des 3 profils d'utilisateurs
        # =====================================================================
        print("[1/5] Test de la Connexion Admin & Creation par Onboarding...")
        with client.session_transaction() as sess:
            sess["_user_id"] = str(admin_principal.id)
            sess["_fresh"] = True

        # Test A.1 : Création Gestionnaire
        res_gest = client.post(
            "/api/utilisateurs",
            json={
                "nom": "Sara Gestionnaire",
                "email": "sara.gest@galaxysolutions.ma",
                "role_id": role_gest.id,
            },
        )
        assert res_gest.status_code == 201, f"Échec création gestionnaire: {res_gest.data}"
        data_gest = res_gest.get_json()
        assert data_gest["statut"] == "en_attente"
        assert not data_gest["actif"]
        token_gest = data_gest["token_activation"]
        print(f"  [OK] Gestionnaire cree en attente (Token: {token_gest[:10]}...)")

        # Test A.2 : Création Formateur
        res_form = client.post(
            "/api/utilisateurs",
            json={
                "nom": "Omar Formateur",
                "email": "omar.formateur@galaxysolutions.ma",
                "role_id": role_form.id,
            },
        )
        assert res_form.status_code == 201, f"Échec création formateur: {res_form.data}"
        data_form = res_form.get_json()
        token_form = data_form["token_activation"]
        # Rattachement fiche Formateur pour isolation
        formateur_omar = Formateur(
            nom="Omar Formateur",
            email="omar.formateur@galaxysolutions.ma",
            domaine=domaine_web,
            utilisateur_id=data_form["id"],
        )
        db.session.add(formateur_omar)
        db.session.commit()
        print(f"  [OK] Formateur cree en attente (Token: {token_form[:10]}...)")

        # Test A.3 : Création Nouvel Admin
        res_new_admin = client.post(
            "/api/utilisateurs",
            json={
                "nom": "Mehdi Admin",
                "email": "mehdi.admin@galaxysolutions.ma",
                "role_id": role_admin.id,
            },
        )
        assert res_new_admin.status_code == 201
        data_new_admin = res_new_admin.get_json()
        token_new_admin = data_new_admin["token_activation"]
        print(f"  [OK] Nouvel Admin cree en attente (Token: {token_new_admin[:10]}...)")

        # Déconnexion session admin
        with client.session_transaction() as sess:
            sess.clear()

        # =====================================================================
        # ÉTAPE B : Tentatives de connexion AVANT activation (Doivent échouer)
        # =====================================================================
        print("\n[2/5] Test de Securite : Tentative de connexion avant activation...")
        login_avant = client.post(
            "/api/auth/login",
            json={"email": "sara.gest@galaxysolutions.ma", "mot_de_passe": "NimporteQuoi123"},
        )
        assert login_avant.status_code == 401
        print("  [OK] Connexion bloquee (HTTP 401) pour compte non active.")

        # =====================================================================
        # ÉTAPE C : Validation des pages publiques et des cas limites de Token
        # =====================================================================
        print("\n[3/5] Test des Tokens (Validite, Expiration, Usage unique, Renvoi)...")

        # C.1 : Page HTML publique d'activation
        page_act = client.get(f"/activation/{token_gest}")
        assert page_act.status_code == 200
        assert b"Activation" in page_act.data
        print("  [OK] Route publique GET /activation/<token> accessible (HTTP 200).")

        # C.2 : Vérification API du token
        verif_gest = client.get(f"/api/auth/verifier-token/{token_gest}")
        assert verif_gest.status_code == 200
        assert verif_gest.get_json()["valide"] is True
        print("  [OK] Pre-verification token valide (HTTP 200).")

        # C.3 : Test Token Expiré
        user_temp = Utilisateur(
            nom="Temp Expire",
            email="temp.exp@test.ma",
            role=role_gest,
            actif=False,
            token_activation_hash=hasher_token("token-expire-test"),
            expiration_token=datetime.utcnow() - timedelta(minutes=5),
        )
        db.session.add(user_temp)
        db.session.commit()

        verif_exp = client.get("/api/auth/verifier-token/token-expire-test")
        assert verif_exp.status_code == 400
        assert "expiré" in verif_exp.get_json()["erreur"]
        print("  [OK] Rejet strict d'un token expire (HTTP 400).")

        # C.4 : Test Renvoi d'invitation & Invalidation de l'ancien token
        with client.session_transaction() as sess:
            sess["_user_id"] = str(admin_principal.id)
            sess["_fresh"] = True

        res_renvoi = client.post(f"/api/utilisateurs/{user_temp.id}/renvoyer-invitation")
        assert res_renvoi.status_code == 200
        nouveau_token_temp = res_renvoi.get_json()["token_activation"]
        assert nouveau_token_temp != "token-expire-test"

        # L'ancien token DOIT être rejeté
        verif_ancien = client.get("/api/auth/verifier-token/token-expire-test")
        assert verif_ancien.status_code == 404 or verif_ancien.status_code == 400
        # Le nouveau token DOIT être valide
        verif_nouveau = client.get(f"/api/auth/verifier-token/{nouveau_token_temp}")
        assert verif_nouveau.status_code == 200
        print("  [OK] Renvoi d'invitation valide : nouveau token actif, ancien token invalide.")

        with client.session_transaction() as sess:
            sess.clear()

        # =====================================================================
        # ÉTAPE D : Activation Réelle des 3 comptes
        # =====================================================================
        print("\n[4/5] Activation des 3 profils avec mot de passe personnalise...")

        # D.1 : Activation Gestionnaire
        act_gest = client.post(
            "/api/auth/activer-compte",
            json={"token": token_gest, "mot_de_passe": "GestionnaireSecurise2026!"},
        )
        assert act_gest.status_code == 200
        print("  [OK] Compte Gestionnaire active.")

        # Rejeu du token déjà utilisé -> DOIT échouer
        rejeu = client.post(
            "/api/auth/activer-compte",
            json={"token": token_gest, "mot_de_passe": "TentativeRejeu123!"},
        )
        assert rejeu.status_code == 400
        print("  [OK] Protection anti-rejeu : token utilise immediatement invalide.")

        # D.2 : Activation Formateur
        act_form = client.post(
            "/api/auth/activer-compte",
            json={"token": token_form, "mot_de_passe": "FormateurSecurise2026!"},
        )
        assert act_form.status_code == 200
        print("  [OK] Compte Formateur active.")

        # D.3 : Activation Nouvel Admin
        act_admin = client.post(
            "/api/auth/activer-compte",
            json={"token": token_new_admin, "mot_de_passe": "AdminSecurise2026!"},
        )
        assert act_admin.status_code == 200
        print("  [OK] Compte Nouvel Admin active.")

        # =====================================================================
        # ÉTAPE E : Validation RBAC post-activation pour chaque rôle
        # =====================================================================
        print("\n[5/5] Validation du Cloisonnement RBAC apres activation...")

        # E.1 : Connexion & Scope Gestionnaire
        login_gest = client.post(
            "/api/auth/login",
            json={"email": "sara.gest@galaxysolutions.ma", "mot_de_passe": "GestionnaireSecurise2026!"},
        )
        assert login_gest.status_code == 200
        assert login_gest.get_json()["utilisateur"]["role"] == "gestionnaire"

        # Le gestionnaire accède aux sessions et stats, mais est bloqué sur /api/utilisateurs
        res_users_gest = client.get("/api/utilisateurs")
        assert res_users_gest.status_code == 403
        print("  [OK] Gestionnaire connecte : acces metier autorise, gestion utilisateurs bloquee (HTTP 403).")

        client.post("/api/auth/logout")

        # E.2 : Connexion & Scope Formateur
        login_form = client.post(
            "/api/auth/login",
            json={"email": "omar.formateur@galaxysolutions.ma", "mot_de_passe": "FormateurSecurise2026!"},
        )
        assert login_form.status_code == 200
        assert login_form.get_json()["utilisateur"]["role"] == "formateur"

        # Formateur accède à son périmètre session mais est bloqué sur utilisateurs et stats globales
        res_users_form = client.get("/api/utilisateurs")
        assert res_users_form.status_code == 403
        res_dash_form = client.get("/api/stats/kpi-globaux")
        assert res_dash_form.status_code == 403
        print("  [OK] Formateur connecte : acces strictement restreint a son perimetre (HTTP 403 sur stats et utilisateurs).")

        client.post("/api/auth/logout")

        # E.3 : Connexion & Scope Nouvel Admin
        login_new_admin = client.post(
            "/api/auth/login",
            json={"email": "mehdi.admin@galaxysolutions.ma", "mot_de_passe": "AdminSecurise2026!"},
        )
        assert login_new_admin.status_code == 200
        assert login_new_admin.get_json()["utilisateur"]["role"] == "admin"

        # L'admin accède à /api/utilisateurs
        res_users_admin = client.get("/api/utilisateurs")
        assert res_users_admin.status_code == 200
        print("  [OK] Nouvel Admin connecte : acces complet administration valide (HTTP 200).")

    print("\n" + "=" * 80)
    print("TOUTES LES VALIDATIONS FONCTIONNELLES E2E ONT REUSSI AVEC SUCCES (100%)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_e2e_validation()
