"""Tests unitaires pour la validation des dates et statuts de session."""

import unittest
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Domaine, Formateur, Formation, Role, Session, Utilisateur
from app.services.session_validation_service import (
    ErreurValidationSession,
    valider_dates_et_statut,
    convertir_date,
)


class SessionsValidationTestCase(unittest.TestCase):
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
        domaine = Domaine(nom="Web & Data")
        db.session.add(domaine)
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin User",
            email="admin@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=admin_role,
        )
        db.session.add(self.admin)
        db.session.flush()

        self.formateur = Formateur(nom="Formateur Test", domaine=domaine)
        self.formation = Formation(titre="Formation Test", domaine=domaine, duree_jours=2)
        db.session.add_all([self.formateur, self.formation])
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin.id)
            session["_fresh"] = True

    def test_valider_dates_et_statut_regles_métier(self):
        today = date(2026, 8, 24)

        # 1. date_fin < date_debut -> Erreur
        with self.assertRaises(ErreurValidationSession):
            valider_dates_et_statut(date(2026, 8, 25), date(2026, 8, 24), "planifiee", reference_date=today)

        # 2. planifiee -> date_debut > today
        valider_dates_et_statut(date(2026, 8, 25), date(2026, 8, 26), "planifiee", reference_date=today)
        with self.assertRaises(ErreurValidationSession):
            valider_dates_et_statut(date(2026, 8, 23), date(2026, 8, 25), "planifiee", reference_date=today)

        # 3. en_cours -> date_debut <= today <= date_fin
        valider_dates_et_statut(date(2026, 8, 24), date(2026, 8, 24), "en_cours", reference_date=today)
        valider_dates_et_statut(date(2026, 8, 23), date(2026, 8, 25), "en_cours", reference_date=today)

        # 4. terminee -> date_fin < today
        valider_dates_et_statut(date(2026, 8, 20), date(2026, 8, 23), "terminee", reference_date=today)
        with self.assertRaises(ErreurValidationSession):
            valider_dates_et_statut(date(2026, 8, 20), date(2026, 8, 24), "terminee", reference_date=today)

        # 5. annulee -> statut d'exception valide quelle que soit la période
        valider_dates_et_statut(date(2026, 8, 20), date(2026, 8, 23), "annulee", reference_date=today)
        valider_dates_et_statut(date(2026, 8, 25), date(2026, 8, 27), "annulee", reference_date=today)

    def test_endpoint_creation_session_validation_iso(self):
        self.connecter()
        today = date.today()
        debut = today + timedelta(days=5)
        fin = debut + timedelta(days=2)

        donnees_invalides_format = {
            "formation_id": self.formation.id,
            "formateur_id": self.formateur.id,
            "date_debut": "2026-13-45",
            "date_fin": fin.isoformat(),
            "type": "intra",
            "capacite_max": 10,
            "statut": "planifiee",
        }
        res = self.client.post("/api/sessions", json=donnees_invalides_format)
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()

