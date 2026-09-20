"""Tests unitaires et d'intégration spécifiques à la Vague 2 : Sécurité et Accès.
- Point 2 : Politique de mot de passe fort (règles et validation)
- Point 5 : Isolation des formateurs (blocage RBAC /api/clients, /api/formateurs, redirections web)
- Point 1 : Activation de compte par token (validation du workflow d'onboarding)
"""

import unittest
from werkzeug.security import generate_password_hash
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Utilisateur, Role, Client, Formateur, Domaine
from app.services.activation_service import valider_force_mot_de_passe


class Vague2SecuriteTestCase(unittest.TestCase):
    """Vérification rigoureuse des règles de sécurité de la Vague 2."""

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

        self.domaine = Domaine(nom="Informatique & Data")
        db.session.add(self.domaine)
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin User",
            email="admin.vague2@test.ma",
            mot_de_passe_hash=generate_password_hash("AdminPass123!"),
            role=self.admin_role,
            actif=True,
        )
        self.formateur_user = Utilisateur(
            nom="Formateur User",
            email="formateur.vague2@test.ma",
            mot_de_passe_hash=generate_password_hash("FormateurPass123!"),
            role=self.formateur_role,
            actif=True,
        )
        self.client_corp = Client(
            nom_entreprise="Entreprise Test",
            contact_email="contact@entreprise-test.ma",
            secteur="IT",
        )
        self.formateur_profile = Formateur(
            nom="Jean Dupont",
            email="jean.dupont@test.ma",
            domaine=self.domaine,
            utilisateur=self.formateur_user,
        )

        db.session.add_all([self.admin, self.formateur_user, self.client_corp, self.formateur_profile])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter(self, user):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(user.id)
            session["_fresh"] = True

    # -------------------------------------------------------------
    # Point 2 : Tests unitaires de la politique de mot de passe fort
    # -------------------------------------------------------------
    def test_mot_de_passe_valide(self):
        """Un mot de passe complet doit être accepté."""
        valide, _ = valider_force_mot_de_passe("Abcdef1!")
        self.assertTrue(valide)
        valide, _ = valider_force_mot_de_passe("SuperSecure#2026")
        self.assertTrue(valide)
        valide, _ = valider_force_mot_de_passe("P@ssw0rd_Complex")
        self.assertTrue(valide)

    def test_mot_de_passe_trop_court(self):
        """Un mot de passe < 8 caractères doit être refusé."""
        valide, msg = valider_force_mot_de_passe("Ab1!")
        self.assertFalse(valide)
        self.assertIn("8 caractères", msg)

    def test_mot_de_passe_sans_majuscule(self):
        """Un mot de passe sans majuscule doit être refusé."""
        valide, msg = valider_force_mot_de_passe("abcdef1!")
        self.assertFalse(valide)
        self.assertIn("majuscule", msg)

    def test_mot_de_passe_sans_minuscule(self):
        """Un mot de passe sans minuscule doit être refusé."""
        valide, msg = valider_force_mot_de_passe("ABCDEF1!")
        self.assertFalse(valide)
        self.assertIn("minuscule", msg)

    def test_mot_de_passe_sans_chiffre(self):
        """Un mot de passe sans chiffre doit être refusé."""
        valide, msg = valider_force_mot_de_passe("Abcdefgh!")
        self.assertFalse(valide)
        self.assertIn("chiffre", msg)

    def test_mot_de_passe_sans_caractere_special(self):
        """Un mot de passe sans caractère spécial doit être refusé."""
        valide, msg = valider_force_mot_de_passe("Abcdefg12")
        self.assertFalse(valide)
        self.assertIn("spécial", msg)

    # -------------------------------------------------------------
    # Point 5 : Tests d'isolation du profil Formateur
    # -------------------------------------------------------------
    def test_formateur_bloque_sur_api_clients(self):
        """Le formateur doit recevoir un 403 Forbidden sur l'API des clients."""
        self.connecter(self.formateur_user)
        res = self.client.get("/api/clients")
        self.assertEqual(res.status_code, 403)

    def test_formateur_bloque_sur_api_detail_client(self):
        """Le formateur doit recevoir un 403 Forbidden sur l'API de détail d'un client."""
        self.connecter(self.formateur_user)
        res = self.client.get(f"/api/clients/{self.client_corp.id}")
        self.assertEqual(res.status_code, 403)

    def test_formateur_bloque_sur_api_formateurs(self):
        """Le formateur doit recevoir un 403 Forbidden sur l'API de liste des autres formateurs."""
        self.connecter(self.formateur_user)
        res = self.client.get("/api/formateurs")
        self.assertEqual(res.status_code, 403)

    def test_formateur_redirige_pages_web_clients_et_formateurs(self):
        """Le formateur tentant d'accéder aux vues web /clients ou /formateurs est redirigé."""
        self.connecter(self.formateur_user)
        res_clients = self.client.get("/clients")
        self.assertEqual(res_clients.status_code, 302)
        self.assertIn("/dashboard-formateur", res_clients.location)

        res_formateurs = self.client.get("/formateurs")
        self.assertEqual(res_formateurs.status_code, 302)
        self.assertIn("/dashboard-formateur", res_formateurs.location)

    # -------------------------------------------------------------
    # Point 1 & 2 : Intégration activation avec mot de passe fort
    # -------------------------------------------------------------
    def test_activation_rejetee_si_mot_de_passe_faible(self):
        """L'activation de compte doit refuser un mot de passe non conforme."""
        self.connecter(self.admin)
        res = self.client.post(
            "/api/utilisateurs",
            json={
                "nom": "User Test Activation",
                "email": "activation.test@test.ma",
                "role_id": self.gestionnaire_role.id,
            },
        )
        self.assertEqual(res.status_code, 201)
        token = res.get_json()["token_activation"]

        # Tentative d'activation avec un mot de passe trop simple
        res_act = self.client.post(
            "/api/auth/activer-compte",
            json={"token": token, "mot_de_passe": "simple"},
        )
        self.assertEqual(res_act.status_code, 400)
        self.assertIn("caractères", res_act.get_json().get("erreur", "").lower())

        # Tentative d'activation avec un mot de passe conforme
        res_act_ok = self.client.post(
            "/api/auth/activer-compte",
            json={"token": token, "mot_de_passe": "Securise2026!"},
        )
        self.assertEqual(res_act_ok.status_code, 200)
        self.assertIn("succès", res_act_ok.get_json().get("message", "").lower())

