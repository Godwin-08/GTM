"""
Tests unitaires et d'intégration pour le système de Toasts et Feedback utilisateur (Phase Finale 3).
"""

import unittest
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Role, Utilisateur, Client, Participant


class FeedbackTestCase(unittest.TestCase):
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

        self.admin = Utilisateur(
            nom="Admin Test",
            email="admin@feedback.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=admin_role,
        )
        db.session.add(self.admin)
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter(self, utilisateur):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(utilisateur.id)
            session["_fresh"] = True

    def test_toast_succes(self):
        # Vérifie que la page de base contient les éléments d'affichage des Toasts de succès
        self.connecter(self.admin)
        res = self.client.get("/dashboard")
        self.assertEqual(res.status_code, 200)
        contenu = res.data.decode("utf-8")
        self.assertIn("toastContainerData()", contenu)
        self.assertIn("afficherToast", contenu)

    def test_toast_erreur(self):
        self.connecter(self.admin)
        res = self.client.get("/dashboard")
        contenu = res.data.decode("utf-8")
        self.assertIn("border-red-200", contenu)

    def test_toast_warning(self):
        self.connecter(self.admin)
        res = self.client.get("/dashboard")
        contenu = res.data.decode("utf-8")
        self.assertIn("border-amber-200", contenu)

    def test_toast_info(self):
        self.connecter(self.admin)
        res = self.client.get("/dashboard")
        contenu = res.data.decode("utf-8")
        self.assertIn("border-blue-200", contenu)

    def test_api_erreur_structure(self):
        self.connecter(self.admin)
        # 1. Requête 400 invalide
        res_400 = self.client.get("/api/clients?statut_activite=inconnu")
        self.assertEqual(res_400.status_code, 400)
        self.assertIn("erreur", res_400.get_json())

        # 2. Requête 409 conflit (client existant)
        client = Client(nom_entreprise="Entreprise Dup")
        db.session.add(client)
        db.session.commit()

        res_409 = self.client.post("/api/clients", json={"nom_entreprise": "Entreprise Dup"})
        self.assertEqual(res_409.status_code, 409)
        self.assertIn("erreur", res_409.get_json())

    def test_non_regression_actions(self):
        self.connecter(self.admin)
        # Création client réussie -> 201 + dict avec id
        res = self.client.post(
            "/api/clients",
            json={"nom_entreprise": "Nouveau Client Test", "secteur": "IT", "contact_email": "it@test.ma"}
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["nom_entreprise"], "Nouveau Client Test")

        # Modification -> 200 + dict
        res_mod = self.client.put(
            f"/api/clients/{data['id']}",
            json={"nom_entreprise": "Client Modifie"}
        )
        self.assertEqual(res_mod.status_code, 200)
        self.assertEqual(res_mod.get_json()["nom_entreprise"], "Client Modifie")

        # Suppression -> 204
        res_del = self.client.delete(f"/api/clients/{data['id']}")
        self.assertEqual(res_del.status_code, 204)


if __name__ == "__main__":
    unittest.main()


class FormateursFeedbackTestCase(unittest.TestCase):
    """Tests comportementaux sur le contrat API Formateurs (valide les messages JSON
    que le frontend doit afficher via afficherToast)."""

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
        from app.models import Domaine
        self.Domaine = Domaine
        self.context = self.app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()

        admin_role = Role(nom="admin")
        db.session.add(admin_role)
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin",
            email="admin@formateurs.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=admin_role,
        )
        db.session.add(self.admin)

        self.domaine = Domaine(nom="Cybersécurité")
        db.session.add(self.domaine)
        db.session.commit()

        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin.id)
            session["_fresh"] = True

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def test_formateur_creation_valide_retourne_201(self):
        res = self.client.post("/api/formateurs", json={
            "nom": "Jean Dupont",
            "domaine_id": self.domaine.id,
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["nom"], "Jean Dupont")
        self.assertIn("id", data)

    def test_formateur_creation_sans_champs_requis_retourne_400_avec_erreur(self):
        res = self.client.post("/api/formateurs", json={"nom": "Incomplet"})
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("erreur", data)
        self.assertTrue(len(data["erreur"]) > 0)

    def test_formateur_creation_domaine_invalide_retourne_400_avec_erreur(self):
        res = self.client.post("/api/formateurs", json={
            "nom": "Jean Dupont",
            "domaine_id": 99999,
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn("erreur", data)

    def test_formateur_modification_valide_retourne_200(self):
        # Créer un formateur d'abord
        res_create = self.client.post("/api/formateurs", json={
            "nom": "Avant Modif",
            "domaine_id": self.domaine.id,
        })
        self.assertEqual(res_create.status_code, 201)
        formateur_id = res_create.get_json()["id"]

        res = self.client.put(f"/api/formateurs/{formateur_id}", json={
            "nom": "Après Modif",
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["nom"], "Après Modif")

    def test_formateur_modification_domaine_invalide_retourne_400_avec_erreur(self):
        res_create = self.client.post("/api/formateurs", json={
            "nom": "Formateur Test",
            "domaine_id": self.domaine.id,
        })
        formateur_id = res_create.get_json()["id"]

        res = self.client.put(f"/api/formateurs/{formateur_id}", json={
            "domaine_id": 99999,
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("erreur", res.get_json())

    def test_formateur_creation_409_compte_deja_lie(self):
        from app.models import Formateur
        # Lier l'admin à un formateur existant
        formateur_lie = Formateur(
            nom="Déjà Lié",
            domaine_id=self.domaine.id,
            utilisateur_id=self.admin.id,
        )
        db.session.add(formateur_lie)
        db.session.commit()

        # Tenter d'en créer un second lié au même utilisateur
        res = self.client.post("/api/formateurs", json={
            "nom": "Second Formateur",
            "domaine_id": self.domaine.id,
            "utilisateur_id": self.admin.id,
        })
        self.assertEqual(res.status_code, 409)
        data = res.get_json()
        self.assertIn("erreur", data)
        self.assertTrue(len(data["erreur"]) > 0)


class UtilisateursFeedbackTestCase(unittest.TestCase):
    """Tests comportementaux sur le contrat API Utilisateurs."""

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
        db.session.add_all([self.admin_role, self.gestionnaire_role])
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin",
            email="admin@utilisateurs.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=self.admin_role,
        )
        db.session.add(self.admin)
        db.session.commit()

        self.client = self.app.test_client()
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin.id)
            session["_fresh"] = True

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def test_utilisateur_creation_valide_retourne_201(self):
        res = self.client.post("/api/utilisateurs", json={
            "nom": "Nouveau User",
            "email": "nouveau@test.ma",
            "mot_de_passe": "Pass1234",
            "role_id": self.gestionnaire_role.id,
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["nom"], "Nouveau User")
        self.assertNotIn("mot_de_passe_hash", data)

    def test_utilisateur_creation_sans_champs_retourne_400_avec_erreur(self):
        res = self.client.post("/api/utilisateurs", json={"nom": "Incomplet"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("erreur", res.get_json())

    def test_utilisateur_creation_doublon_email_retourne_409_avec_erreur(self):
        # L'admin existe déjà avec admin@utilisateurs.ma
        res = self.client.post("/api/utilisateurs", json={
            "nom": "Doublon",
            "email": "admin@utilisateurs.ma",
            "mot_de_passe": "Pass1234",
            "role_id": self.admin_role.id,
        })
        self.assertEqual(res.status_code, 409)
        data = res.get_json()
        self.assertIn("erreur", data)
        self.assertTrue(len(data["erreur"]) > 0)

    def test_utilisateur_modification_valide_retourne_200(self):
        res = self.client.put(f"/api/utilisateurs/{self.admin.id}", json={
            "nom": "Admin Modifié",
        })
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["nom"], "Admin Modifié")

    def test_utilisateur_modification_email_doublon_retourne_409_avec_erreur(self):
        # Créer un second utilisateur
        autre = Utilisateur(
            nom="Autre",
            email="autre@test.ma",
            mot_de_passe_hash=generate_password_hash("Pass1234"),
            role=self.gestionnaire_role,
        )
        db.session.add(autre)
        db.session.commit()

        # Essayer de prendre l'email de l'admin
        res = self.client.put(f"/api/utilisateurs/{autre.id}", json={
            "email": "admin@utilisateurs.ma",
        })
        self.assertEqual(res.status_code, 409)
        self.assertIn("erreur", res.get_json())

    def test_utilisateur_modification_role_invalide_retourne_400_avec_erreur(self):
        res = self.client.put(f"/api/utilisateurs/{self.admin.id}", json={
            "role_id": 99999,
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("erreur", res.get_json())
