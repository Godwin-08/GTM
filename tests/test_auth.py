"""Tests unitaires et d'intégration pour l'authentification et la déconnexion."""

import unittest
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Utilisateur, Role


class AuthTestCase(unittest.TestCase):
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
        db.session.remove()
        self.context.pop()

    def connecter(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.user.id)
            session["_fresh"] = True

    def test_deconnexion_post_valide(self):
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
        self.connecter()
        # GET /api/auth/logout -> 405 Method Not Allowed
        response = self.client.get("/api/auth/logout")
        self.assertEqual(response.status_code, 405)


if __name__ == "__main__":
    unittest.main()

