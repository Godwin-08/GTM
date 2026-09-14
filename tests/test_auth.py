"""Tests unitaires et d'intégration pour l'authentification et la déconnexion."""

import unittest
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Utilisateur, Role


class AuthTestCase(unittest.TestCase):
    """Tests unitaires pour les flux d'authentification, de déconnexion et de changement de mot de passe."""

    @classmethod
    def setUpClass(cls):
        """Initialise la configuration du test avec une base SQLite en mémoire."""
        cls.original_database_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = "sqlite://"
        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        """Restaure la configuration initiale de la base de données."""
        Config.SQLALCHEMY_DATABASE_URI = cls.original_database_uri

    def setUp(self):
        """Initialise la base de données de test et crée un compte administrateur actif."""
        self.context = self.app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()

        admin_role = Role(nom="admin")
        db.session.add(admin_role)
        db.session.flush()

        self.user = Utilisateur(
            nom="Admin User",
            email="admin@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=admin_role,
            actif=True,
        )
        db.session.add(self.user)
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        """Nettoie la session et détruit le contexte de test."""
        db.session.remove()
        self.context.pop()

    def connecter(self):
        """Simule une session connectée pour l'utilisateur de test."""
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user.id)
            session["_fresh"] = True

    def test_deconnexion_post_valide(self):
        """Vérifie la déconnexion par requête POST, l'invalidation de la session et le blocage 401 ultérieur."""
        self.connecter()

        # POST /api/auth/logout -> 200 OK
        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["message"], "Déconnexion réussie")

        # Invalidation post-logout sur API -> 401 Unauthorized
        acces_api = self.client.get("/api/sessions")
        self.assertEqual(acces_api.status_code, 401)
        self.assertEqual(acces_api.get_json()["erreur"], "Connexion requise.")

        # Accès page Web protégée après logout -> Redirection /login
        acces_web = self.client.get("/dashboard")
        self.assertEqual(acces_web.status_code, 302)
        self.assertIn("/login", acces_web.headers["Location"])

    def test_deconnexion_get_refusee(self):
        """Vérifie que la déconnexion par GET est rejetée (HTTP 405 Method Not Allowed)."""
        self.connecter()
        # GET /api/auth/logout -> 405 Method Not Allowed
        response = self.client.get("/api/auth/logout")
        self.assertEqual(response.status_code, 405)

    def test_changer_mot_de_passe_succes(self):
        """Vérifie la modification de mot de passe réussie lorsque l'ancien mot de passe est correct."""
        self.connecter()
        res = self.client.post("/api/auth/changer-mot-de-passe", json={
            "ancien_mot_de_passe": "Secret123",
            "nouveau_mot_de_passe": "NouveauSecret2026!"
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn("modifié avec succès", res.get_json()["message"])

    def test_changer_mot_de_passe_erreurs(self):
        """Vérifie les erreurs lors de la saisie d'un ancien mot de passe invalide ou d'un nouveau trop court."""
        self.connecter()
        # Ancien mot de passe faux
        res = self.client.post("/api/auth/changer-mot-de-passe", json={
            "ancien_mot_de_passe": "MauvaisMdp",
            "nouveau_mot_de_passe": "NouveauSecret2026!"
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("incorrect", res.get_json()["erreur"])

        # Nouveau mot de passe trop court
        res2 = self.client.post("/api/auth/changer-mot-de-passe", json={
            "ancien_mot_de_passe": "Secret123",
            "nouveau_mot_de_passe": "court"
        })
        self.assertEqual(res2.status_code, 400)


if __name__ == "__main__":
    unittest.main()

