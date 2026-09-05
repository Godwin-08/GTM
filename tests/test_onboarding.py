"""Tests unitaires et d'intégration pour le parcours complet d'onboarding et d'activation de compte."""

import unittest
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Utilisateur, Role
from app.services.activation_service import (
    generer_token_activation,
    hasher_token,
    calculer_expiration_activation,
)


class OnboardingTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_database_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = "sqlite://"
        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        Config.SQLALCHEMY_DATABASE_URI = cls.original_database_uri

    def setUp(self):
        self.context = self.app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()

        self.admin_role = Role(nom="admin")
        self.gestionnaire_role = Role(nom="gestionnaire")
        self.formateur_role = Role(nom="formateur")
        db.session.add_all([self.admin_role, self.gestionnaire_role, self.formateur_role])
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin Principal",
            email="admin@test.ma",
            mot_de_passe_hash=generate_password_hash("AdminSecret123"),
            role=self.admin_role,
            actif=True,
        )
        db.session.add(self.admin)
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter_admin(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin.id)
            session["_fresh"] = True

    def test_creation_compte_onboarding_sans_mot_de_passe(self):
        """L'Admin crée un compte : il doit être 'en_attente' avec un token d'activation généré."""
        self.connecter_admin()

        res = self.client.post(
            "/api/utilisateurs",
            json={
                "nom": "Nouveau Gestionnaire",
                "email": "nouveau.gest@test.ma",
                "role_id": self.gestionnaire_role.id,
            },
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["statut"], "en_attente")
        self.assertFalse(data["actif"])
        self.assertTrue(data["est_en_attente"])
        self.assertIn("token_activation", data)
        self.assertIn("url_activation", data)
        token = data["token_activation"]
        self.assertTrue(len(token) > 20)

        # Vérification en base : le token brut n'est JAMAIS stocké en clair
        user_db = Utilisateur.query.filter_by(email="nouveau.gest@test.ma").first()
        self.assertIsNotNone(user_db)
        self.assertFalse(user_db.actif)
        self.assertIsNone(user_db.mot_de_passe_hash)
        self.assertEqual(user_db.token_activation_hash, hasher_token(token))
        self.assertIsNotNone(user_db.expiration_token)

    def test_connexion_refusee_pour_compte_en_attente(self):
        """Un compte non activé ne doit jamais pouvoir se connecter."""
        token_brut, token_hash = generer_token_activation()
        user_pending = Utilisateur(
            nom="En Attente",
            email="pending@test.ma",
            role=self.gestionnaire_role,
            actif=False,
            token_activation_hash=token_hash,
            expiration_token=calculer_expiration_activation(48),
            mot_de_passe_hash=None,
        )
        db.session.add(user_pending)
        db.session.commit()

        res = self.client.post(
            "/api/auth/login",
            json={"email": "pending@test.ma", "mot_de_passe": "Tentative123"},
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.get_json()["erreur"], "Identifiants invalides")

    def test_cycle_complet_activation_reussie(self):
        """Scénario nominal : réception token -> validation -> mot de passe -> compte activé -> login réussi."""
        token_brut, token_hash = generer_token_activation()
        user = Utilisateur(
            nom="Karim Onboard",
            email="karim.onboard@test.ma",
            role=self.formateur_role,
            actif=False,
            token_activation_hash=token_hash,
            expiration_token=calculer_expiration_activation(48),
        )
        db.session.add(user)
        db.session.commit()

        # 1. Vérification du token
        res_verif = self.client.get(f"/api/auth/verifier-token/{token_brut}")
        self.assertEqual(res_verif.status_code, 200)
        self.assertTrue(res_verif.get_json()["valide"])
        self.assertEqual(res_verif.get_json()["email"], "karim.onboard@test.ma")

        # 2. Soumission de l'activation
        res_act = self.client.post(
            "/api/auth/activer-compte",
            json={"token": token_brut, "mot_de_passe": "MonNouveauPass123"},
        )
        self.assertEqual(res_act.status_code, 200)
        self.assertIn("activé avec succès", res_act.get_json()["message"])

        # 3. Vérification en base : token invalidé et compte actif
        db.session.refresh(user)
        self.assertTrue(user.actif)
        self.assertEqual(user.statut, "actif")
        self.assertIsNone(user.token_activation_hash)
        self.assertIsNone(user.expiration_token)
        self.assertIsNotNone(user.mot_de_passe_hash)

        # 4. Connexion normale avec le nouveau mot de passe
        res_login = self.client.post(
            "/api/auth/login",
            json={"email": "karim.onboard@test.ma", "mot_de_passe": "MonNouveauPass123"},
        )
        self.assertEqual(res_login.status_code, 200)
        self.assertEqual(res_login.get_json()["message"], "Connexion réussie")

    def test_activation_refusee_token_invalide(self):
        """Un token inconnu ou altéré doit être rejeté."""
        res = self.client.post(
            "/api/auth/activer-compte",
            json={"token": "faux-token-inconnu", "mot_de_passe": "Password123"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("invalide", res.get_json()["erreur"])

    def test_activation_refusee_token_expire(self):
        """Un token dont la date d'expiration est passée doit être rejeté."""
        token_brut, token_hash = generer_token_activation()
        user_expire = Utilisateur(
            nom="Compte Expire",
            email="expire@test.ma",
            role=self.gestionnaire_role,
            actif=False,
            token_activation_hash=token_hash,
            expiration_token=datetime.utcnow() - timedelta(hours=1),  # Expiré il y a 1h
        )
        db.session.add(user_expire)
        db.session.commit()

        # Tentative de vérification
        res_verif = self.client.get(f"/api/auth/verifier-token/{token_brut}")
        self.assertEqual(res_verif.status_code, 400)
        self.assertIn("expiré", res_verif.get_json()["erreur"])

        # Tentative d'activation
        res_act = self.client.post(
            "/api/auth/activer-compte",
            json={"token": token_brut, "mot_de_passe": "Password123"},
        )
        self.assertEqual(res_act.status_code, 400)
        self.assertIn("expiré", res_act.get_json()["erreur"])

    def test_usage_unique_du_token(self):
        """Un token déjà utilisé ne peut pas être réutilisé une seconde fois."""
        token_brut, token_hash = generer_token_activation()
        user = Utilisateur(
            nom="Unique Test",
            email="unique@test.ma",
            role=self.gestionnaire_role,
            actif=False,
            token_activation_hash=token_hash,
            expiration_token=calculer_expiration_activation(48),
        )
        db.session.add(user)
        db.session.commit()

        # 1ère utilisation -> 200 OK
        res1 = self.client.post(
            "/api/auth/activer-compte",
            json={"token": token_brut, "mot_de_passe": "SuperPass123"},
        )
        self.assertEqual(res1.status_code, 200)

        # 2ème utilisation avec le même token -> 400 Rejeté
        res2 = self.client.post(
            "/api/auth/activer-compte",
            json={"token": token_brut, "mot_de_passe": "AutrePass123"},
        )
        self.assertEqual(res2.status_code, 400)

    def test_mot_de_passe_trop_court_refuse(self):
        """Un mot de passe de moins de 8 caractères est refusé."""
        token_brut, token_hash = generer_token_activation()
        user = Utilisateur(
            nom="Court Test",
            email="court@test.ma",
            role=self.gestionnaire_role,
            actif=False,
            token_activation_hash=token_hash,
            expiration_token=calculer_expiration_activation(48),
        )
        db.session.add(user)
        db.session.commit()

        res = self.client.post(
            "/api/auth/activer-compte",
            json={"token": token_brut, "mot_de_passe": "court"},
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("8 caractères", res.get_json()["erreur"])

    def test_renvoyer_invitation_par_admin(self):
        """L'administrateur peut régénérer un token d'invitation pour un compte en attente."""
        self.connecter_admin()

        token_old, hash_old = generer_token_activation()
        user_pending = Utilisateur(
            nom="Attente Renvoi",
            email="renvoi@test.ma",
            role=self.formateur_role,
            actif=False,
            token_activation_hash=hash_old,
            expiration_token=calculer_expiration_activation(48),
        )
        db.session.add(user_pending)
        db.session.commit()

        res = self.client.post(f"/api/utilisateurs/{user_pending.id}/renvoyer-invitation")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("token_activation", data)
        self.assertNotEqual(data["token_activation"], token_old)

        # Vérification que le nouveau token fonctionne
        db.session.refresh(user_pending)
        self.assertEqual(user_pending.token_activation_hash, hasher_token(data["token_activation"]))


if __name__ == "__main__":
    unittest.main()
