"""
Tests unitaires pour la route racine / et la page de connexion.
"""

import unittest
from app import create_app
from app.config import Config


class HomepageTestCase(unittest.TestCase):
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
        self.client = self.app.test_client()

    def test_root_redirects_anonymous_to_login(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.location.endswith("/login") or "/login" in res.location)

    def test_root_following_redirect_shows_login(self):
        res = self.client.get("/", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        contenu = res.data.decode("utf-8")
        self.assertIn("GTM", contenu)
        self.assertIn("Galaxy Solutions", contenu)
        self.assertIn("Connexion", contenu)

    def test_login_page_renders_branding(self):
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)
        contenu = res.data.decode("utf-8")
        self.assertIn("GTM", contenu)
        self.assertIn("Galaxy Solutions", contenu)
        self.assertIn("Plateforme de Pilotage & Gestion des Formations", contenu)


if __name__ == "__main__":
    unittest.main()


