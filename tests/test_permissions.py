"""Tests unitaires et d'intégration pour les permissions et l'isolation Formateur."""

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


class PermissionsTestCase(unittest.TestCase):
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
        formateur_role = Role(nom="formateur")
        db.session.add_all([admin_role, formateur_role])
        domaine = Domaine(nom="Web & Data")
        db.session.add(domaine)
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin User",
            email="admin@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=admin_role,
        )
        self.user_formateur_1 = Utilisateur(
            nom="Formateur 1",
            email="formateur1@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=formateur_role,
        )
        self.user_formateur_2 = Utilisateur(
            nom="Formateur 2",
            email="formateur2@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=formateur_role,
        )
        db.session.add_all([self.admin, self.user_formateur_1, self.user_formateur_2])
        db.session.flush()

        self.formateur_1 = Formateur(
            nom="Formateur 1", domaine=domaine, utilisateur=self.user_formateur_1
        )
        self.formateur_2 = Formateur(
            nom="Formateur 2", domaine=domaine, utilisateur=self.user_formateur_2
        )
        self.formation_1 = Formation(titre="Python Advanced", domaine=domaine, duree_jours=3)
        self.formation_2 = Formation(titre="SQL Expert", domaine=domaine, duree_jours=2)

        self.client_1 = Client(nom_entreprise="Entreprise A")
        self.client_2 = Client(nom_entreprise="Entreprise B")

        db.session.add_all([
            self.formateur_1, self.formateur_2,
            self.formation_1, self.formation_2,
            self.client_1, self.client_2,
        ])
        db.session.flush()

        aujourd_hui = date.today()
        self.session_1 = Session(
            formation=self.formation_1,
            formateur=self.formateur_1,
            date_debut=aujourd_hui - timedelta(days=5),
            date_fin=aujourd_hui - timedelta(days=2),
            type="inter",
            capacite_max=10,
            statut="terminee",
        )
        self.session_2 = Session(
            formation=self.formation_2,
            formateur=self.formateur_2,
            date_debut=aujourd_hui - timedelta(days=5),
            date_fin=aujourd_hui - timedelta(days=2),
            type="inter",
            capacite_max=10,
            statut="terminee",
        )
        self.participant_1 = Participant(
            nom="Part 1", email="p1@test.ma", client=self.client_1
        )
        self.participant_2 = Participant(
            nom="Part 2", email="p2@test.ma", client=self.client_2
        )
        db.session.add_all([
            self.session_1, self.session_2,
            self.participant_1, self.participant_2,
        ])
        db.session.flush()

        db.session.add_all([
            Inscription(session=self.session_1, participant=self.participant_1, statut="confirmee"),
            Inscription(session=self.session_2, participant=self.participant_2, statut="confirmee"),
        ])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter(self, utilisateur):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(utilisateur.id)
            session["_fresh"] = True

    def test_formateur_listes_et_acces_direct_securise(self):
        self.connecter(self.user_formateur_1)

        # 1. Vérification des listes filtrées
        sessions = self.client.get("/api/sessions").get_json()
        participants = self.client.get("/api/participants").get_json()
        clients = self.client.get("/api/clients").get_json()
        formations = self.client.get("/api/formations").get_json()

        self.assertEqual([s["id"] for s in sessions], [self.session_1.id])
        self.assertEqual([p["id"] for p in participants], [self.participant_1.id])
        self.assertEqual([c["id"] for c in clients], [self.client_1.id])
        self.assertEqual([f["id"] for f in formations], [self.formation_1.id])

        # 2. Vérification des rejets 403 Forbidden sur accès direct par ID aux ressources d'autrui
        res_session = self.client.get(f"/api/sessions/{self.session_2.id}")
        self.assertEqual(res_session.status_code, 403)

        res_participant = self.client.get(f"/api/participants/{self.participant_2.id}")
        self.assertEqual(res_participant.status_code, 403)

        res_client = self.client.get(f"/api/clients/{self.client_2.id}")
        self.assertEqual(res_client.status_code, 403)

        res_formation = self.client.get(f"/api/formations/{self.formation_2.id}")
        self.assertEqual(res_formation.status_code, 403)


if __name__ == "__main__":
    unittest.main()

