"""Tests unitaires et d'intégration spécifiques à la Vague 3 : Logique Métier Formateur & Sessions.
- Point 3 : Formateur Interne (lié à Utilisateur) vs Formateur Externe, et filtrage des comptes formateurs
- Point 10 : Calcul dynamique du statut de session à la création
"""

import unittest
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Utilisateur, Role, Formateur, Domaine, Formation, Session
from app.services.session_validation_service import calculer_statut_depuis_dates


class Vague3FormateursTestCase(unittest.TestCase):
    """Vérification des fonctionnalités de la Vague 3."""

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

        self.domaine = Domaine(nom="Web & Data")
        db.session.add(self.domaine)
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin User",
            email="admin.v3@test.ma",
            mot_de_passe_hash=generate_password_hash("AdminPass123!"),
            role=self.admin_role,
            actif=True,
        )
        self.user_formateur_1 = Utilisateur(
            nom="Youssef Formateur",
            email="youssef.v3@test.ma",
            mot_de_passe_hash=generate_password_hash("Pass123!"),
            role=self.formateur_role,
            actif=True,
        )
        self.user_formateur_libre = Utilisateur(
            nom="Salma Formateur Libre",
            email="salma.v3@test.ma",
            mot_de_passe_hash=generate_password_hash("Pass123!"),
            role=self.formateur_role,
            actif=True,
        )
        self.user_gestionnaire = Utilisateur(
            nom="Karim Gestionnaire",
            email="karim.v3@test.ma",
            mot_de_passe_hash=generate_password_hash("Pass123!"),
            role=self.gestionnaire_role,
            actif=True,
        )
        db.session.add_all([self.admin, self.user_formateur_1, self.user_formateur_libre, self.user_gestionnaire])
        db.session.flush()

        # Profil formateur déjà lié à user_formateur_1
        self.formateur_existant = Formateur(
            nom=self.user_formateur_1.nom,
            email=self.user_formateur_1.email,
            domaine=self.domaine,
            utilisateur=self.user_formateur_1,
        )
        db.session.add(self.formateur_existant)

        # Formation pour test de session
        self.formation = Formation(
            titre="Développement Web Moderne",
            description="Apprendre le Web",
            duree_jours=3,
            domaine=self.domaine,
        )
        db.session.add(self.formation)
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter_admin(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin.id)
            session["_fresh"] = True

    # -------------------------------------------------------------
    # Point 3 : Filtrage des utilisateurs et création Formateur
    # -------------------------------------------------------------
    def test_api_utilisateurs_filtre_par_role_formateur(self):
        """L'API /api/utilisateurs?role=formateur ne doit renvoyer que les formateurs."""
        self.connecter_admin()
        res = self.client.get("/api/utilisateurs?role=formateur")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        roles = {u["role"]["nom"] for u in data}
        self.assertEqual(roles, {"formateur"})
        self.assertEqual(len(data), 2)  # youssef et salma

    def test_api_utilisateurs_sans_profil_formateur(self):
        """L'API /api/utilisateurs?role=formateur&sans_profil_formateur=1 ne renvoie que ceux non rattachés."""
        self.connecter_admin()
        res = self.client.get("/api/utilisateurs?role=formateur&sans_profil_formateur=1")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.user_formateur_libre.id)

    def test_creation_formateur_interne_succes(self):
        """Création d'un formateur interne en rattachant l'utilisateur libre."""
        self.connecter_admin()
        res = self.client.post(
            "/api/formateurs",
            json={
                "nom": self.user_formateur_libre.nom,
                "domaine_id": self.domaine.id,
                "email": self.user_formateur_libre.email,
                "utilisateur_id": self.user_formateur_libre.id,
            },
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data["a_un_compte"])
        self.assertEqual(data["nom"], self.user_formateur_libre.nom)

    def test_creation_formateur_externe_succes(self):
        """Création d'un formateur externe sans compte utilisateur."""
        self.connecter_admin()
        res = self.client.post(
            "/api/formateurs",
            json={
                "nom": "Consultant Externe Pro",
                "domaine_id": self.domaine.id,
                "email": "consultant@externe.ma",
                "telephone": "0661000000",
            },
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertFalse(data["a_un_compte"])
        self.assertEqual(data["nom"], "Consultant Externe Pro")

    def test_creation_formateur_interne_deja_lie_rejette_409(self):
        """Tentative de rattachement à un utilisateur déjà associé doit renvoyer 409."""
        self.connecter_admin()
        res = self.client.post(
            "/api/formateurs",
            json={
                "nom": "Doublon",
                "domaine_id": self.domaine.id,
                "utilisateur_id": self.user_formateur_1.id,
            },
        )
        self.assertEqual(res.status_code, 409)

    # -------------------------------------------------------------
    # Point 10 : Calcul du statut session à la création
    # -------------------------------------------------------------
    def test_calculer_statut_depuis_dates(self):
        """Vérifie les 3 cas de calcul automatique du statut."""
        aujourd_hui = date.today()
        # Futur -> planifiee
        self.assertEqual(
            calculer_statut_depuis_dates(aujourd_hui + timedelta(days=5), aujourd_hui + timedelta(days=10)),
            "planifiee"
        )
        # En cours -> en_cours
        self.assertEqual(
            calculer_statut_depuis_dates(aujourd_hui - timedelta(days=1), aujourd_hui + timedelta(days=2)),
            "en_cours"
        )
        # Passé -> terminee
        self.assertEqual(
            calculer_statut_depuis_dates(aujourd_hui - timedelta(days=10), aujourd_hui - timedelta(days=5)),
            "terminee"
        )

    def test_creation_session_statut_calcule_automatiquement(self):
        """Création d'une session sans spécifier 'statut' : doit être déduit des dates sans erreur."""
        self.connecter_admin()
        date_deb = (date.today() + timedelta(days=15)).isoformat()
        date_f = (date.today() + timedelta(days=18)).isoformat()

        res = self.client.post(
            "/api/sessions",
            json={
                "formation_id": self.formation.id,
                "formateur_id": self.formateur_existant.id,
                "date_debut": date_deb,
                "date_fin": date_f,
                "type": "intra",
                "capacite_max": 12,
                "lieu": "Casablanca",
            },
        )
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["statut"], "planifiee")

