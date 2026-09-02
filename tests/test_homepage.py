"""
Tests unitaires pour la page d'accueil (Landing Page /).
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

    def test_homepage_status(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)

    def test_homepage_contains_branding(self):
        res = self.client.get("/")
        contenu = res.data.decode("utf-8")
        self.assertIn("GTM", contenu)
        self.assertIn("Galaxy Solutions", contenu)

    def test_homepage_login_link(self):
        res = self.client.get("/")
        contenu = res.data.decode("utf-8")
        self.assertIn("/login", contenu)

    def test_homepage_accessible_without_authentication(self):
        # Vérifie que l'accès anonyme retourne HTTP 200 sans redirection brute vers /login
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("Galaxy Training Manager", res.data.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()

