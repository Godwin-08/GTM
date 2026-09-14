"""
Tests unitaires pour la route racine / et la page de connexion.
"""

import unittest
from app import create_app
from app.config import Config


class HomepageTestCase(unittest.TestCase):
    """Suite de tests pour la redirection d'accueil et le rendu de la page de connexion."""

    @classmethod
    def setUpClass(cls):
        """Configure l'application de test Flask en mémoire."""
        cls.original_database_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = "sqlite://"
        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        """Restaure la configuration initiale de la base de données."""
        Config.SQLALCHEMY_DATABASE_URI = cls.original_database_uri

    def setUp(self):
        """Instancie le client de test HTTP."""
        self.client = self.app.test_client()

    def test_root_redirects_anonymous_to_login(self):
        """Vérifie que la racine / redirige un visiteur anonyme vers /login (302)."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res.location.endswith("/login") or "/login" in res.location)

    def test_root_following_redirect_shows_login(self):
        """Vérifie que la redirection depuis / aboutit sur la page de connexion avec les éléments clés."""
        res = self.client.get("/", follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        contenu = res.data.decode("utf-8")
        self.assertIn("GTM", contenu)
        self.assertIn("Galaxy Solutions", contenu)
        self.assertIn("Connexion", contenu)

    def test_login_page_renders_branding(self):
        """Vérifie que la page /login affiche correctement la charte et le titre officiel de l'application."""
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)
        contenu = res.data.decode("utf-8")
        self.assertIn("GTM", contenu)
        self.assertIn("Galaxy Solutions", contenu)
        self.assertIn("Plateforme de Pilotage & Gestion des Formations", contenu)


if __name__ == "__main__":
    unittest.main()


