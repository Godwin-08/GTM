"""Tests d'intégration globaux et des parcours nominaux pour la Phase 1."""

import unittest
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import (
    Client,
    Domaine,
    Formateur,
    Formation,
    Inscription,
    Participant,
    Role,
    Session,
    Utilisateur,
)


class Phase1FiabilisationTestCase(unittest.TestCase):
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
        gestionnaire_role = Role(nom="gestionnaire")
        formateur_role = Role(nom="formateur")
        db.session.add_all([admin_role, gestionnaire_role, formateur_role])
        domaine = Domaine(nom="Web & Data")
        db.session.add(domaine)
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin User",
            email="admin@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=admin_role,
        )
        self.gestionnaire = Utilisateur(
            nom="Gestionnaire User",
            email="gest@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=gestionnaire_role,
        )
        self.compte_formateur = Utilisateur(
            nom="Formateur User",
            email="formateur@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=formateur_role,
        )
        db.session.add_all([self.admin, self.gestionnaire, self.compte_formateur])
        db.session.flush()

        self.formateur = Formateur(
            nom="Formateur User", domaine=domaine, utilisateur=self.compte_formateur
        )
        self.formation = Formation(titre="Python Advanced", domaine=domaine, duree_jours=3)
        self.client_corp = Client(nom_entreprise="Galaxy Corp")
        db.session.add_all([self.formateur, self.formation, self.client_corp])
        db.session.flush()

        today = date.today()
        self.session_unit = Session(
            formation=self.formation,
            formateur=self.formateur,
            date_debut=today - timedelta(days=10),
            date_fin=today - timedelta(days=8),
            type="inter",
            capacite_max=10,
            statut="terminee",
        )
        self.participant_unit = Participant(
            nom="John Doe", email="john@galaxy.ma", client=self.client_corp
        )
        db.session.add_all([self.session_unit, self.participant_unit])
        db.session.flush()

        db.session.add(
            Inscription(
                session=self.session_unit,
                participant=self.participant_unit,
                statut="confirmee",
            )
        )
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter(self, utilisateur):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(utilisateur.id)
            session["_fresh"] = True

    def test_parcours_nominal_admin(self):
        self.connecter(self.admin)
        endpoints = [
            "/api/stats/kpi-globaux",
            "/api/sessions",
            f"/api/sessions/{self.session_unit.id}",
            "/api/clients",
            f"/api/clients/{self.client_corp.id}",
            "/api/formations",
            f"/api/formations/{self.formation.id}",
            "/api/participants",
            f"/api/participants/{self.participant_unit.id}",
        ]
        for ep in endpoints:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200, f"Erreur sur {ep}")

    def test_parcours_nominal_formateur(self):
        self.connecter(self.compte_formateur)
        endpoints_autorises = [
            "/api/sessions",
            f"/api/sessions/{self.session_unit.id}",
            "/api/clients",
            f"/api/clients/{self.client_corp.id}",
            "/api/formations",
            f"/api/formations/{self.formation.id}",
            "/api/participants",
            f"/api/participants/{self.participant_unit.id}",
        ]
        for ep in endpoints_autorises:
            res = self.client.get(ep)
            self.assertEqual(res.status_code, 200, f"Erreur sur {ep}")


if __name__ == "__main__":
    unittest.main()
