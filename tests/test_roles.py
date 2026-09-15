"""Tests unitaires pour l'API du référentiel des rôles (/api/roles)."""

import unittest
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Utilisateur, Role


class RolesApiTestCase(unittest.TestCase):
    """Tests unitaires pour la consultation des rôles système."""

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
        """Initialise la base de données de test et crée les 3 rôles de base et 1 admin."""
        self.context = self.app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()

        role_admin = Role(nom="admin")
        role_gestionnaire = Role(nom="gestionnaire")
        role_formateur = Role(nom="formateur")
        db.session.add_all([role_admin, role_gestionnaire, role_formateur])
        db.session.flush()

        self.user = Utilisateur(
            nom="Admin Unique",
            email="admin@galaxysolutions.ma",
            mot_de_passe_hash=generate_password_hash("Admin123"),
            role=role_admin,
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

    def test_liste_roles_sans_connexion(self):
        """Vérifie que l'accès non authentifié est rejeté (401)."""
        res = self.client.get("/api/roles")
        self.assertEqual(res.status_code, 401)

    def test_liste_roles_avec_connexion(self):
        """
        Scénario exact de l'encadrant : base avec 1 seul admin.
        L'API doit retourner les 3 rôles du référentiel indépendamment
        du nombre d'utilisateurs existants.
        """
        self.connecter()
        res = self.client.get("/api/roles")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()

        # On vérifie les noms fonctionnels, pas un nombre arbitraire
        noms_roles = {r["nom"] for r in data}
        self.assertIn("admin", noms_roles)
        self.assertIn("gestionnaire", noms_roles)
        self.assertIn("formateur", noms_roles)

        # Chaque rôle doit avoir un id valide
        for role in data:
            self.assertIn("id", role)
            self.assertIsInstance(role["id"], int)
            self.assertGreater(role["id"], 0)

    def test_creation_gestionnaire_depuis_base_admin_seul(self):
        """
        Parcours complet : Admin seul en base → créer un utilisateur Gestionnaire.
        C'est exactement le scénario bloquant décrit par l'encadrant.
        """
        self.connecter()

        # Récupère l'id du rôle gestionnaire depuis l'API
        res_roles = self.client.get("/api/roles")
        self.assertEqual(res_roles.status_code, 200)
        roles = res_roles.get_json()
        role_gestionnaire = next((r for r in roles if r["nom"] == "gestionnaire"), None)
        self.assertIsNotNone(role_gestionnaire, "Le rôle 'gestionnaire' doit être disponible dans /api/roles")

        # Crée un utilisateur gestionnaire
        res = self.client.post("/api/utilisateurs", json={
            "nom": "Sofia Amrani",
            "email": "sofia.amrani@galaxysolutions.ma",
            "role_id": role_gestionnaire["id"],
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["role"]["nom"], "gestionnaire")
        self.assertFalse(data["actif"])  # compte en attente d'activation

    def test_creation_formateur_depuis_base_admin_seul(self):
        """
        Parcours complet : Admin seul en base → créer un utilisateur Formateur.
        """
        self.connecter()

        res_roles = self.client.get("/api/roles")
        roles = res_roles.get_json()
        role_formateur = next((r for r in roles if r["nom"] == "formateur"), None)
        self.assertIsNotNone(role_formateur, "Le rôle 'formateur' doit être disponible dans /api/roles")

        res = self.client.post("/api/utilisateurs", json={
            "nom": "Karim Bensouda",
            "email": "karim.bensouda@galaxysolutions.ma",
            "role_id": role_formateur["id"],
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["role"]["nom"], "formateur")


if __name__ == "__main__":
    unittest.main()

