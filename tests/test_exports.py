"""Tests unitaires pour les exports CSV filtrés et la parité JSON / CSV."""

import csv
import io
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


class ExportsTestCase(unittest.TestCase):
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

        # roles
        self.admin_role = Role(nom="admin")
        self.gestionnaire_role = Role(nom="gestionnaire")
        self.formateur_role = Role(nom="formateur")
        db.session.add_all([self.admin_role, self.gestionnaire_role, self.formateur_role])
        db.session.flush()

        # users
        self.admin = Utilisateur(
            nom="Admin Test", email="admin@test.fr", mot_de_passe_hash=generate_password_hash("pass"), role_id=self.admin_role.id
        )
        self.formateur_user = Utilisateur(
            nom="Karim Formateur", email="karim@test.fr", mot_de_passe_hash=generate_password_hash("pass"), role_id=self.formateur_role.id
        )
        db.session.add_all([self.admin, self.formateur_user])
        db.session.flush()

        # domaines & formations
        self.domaine = Domaine(nom="Web & Data")
        db.session.add(self.domaine)
        db.session.flush()

        self.formation = Formation(titre="Python Pro", domaine_id=self.domaine.id, duree_jours=3)
        db.session.add(self.formation)
        db.session.flush()

        # formateurs
        self.formateur_1 = Formateur(nom="Karim Formateur", email="karim@test.fr", utilisateur_id=self.formateur_user.id, domaine_id=self.domaine.id)
        self.formateur_2 = Formateur(nom="Autre Formateur", email="autre@test.fr", domaine_id=self.domaine.id)
        db.session.add_all([self.formateur_1, self.formateur_2])
        db.session.flush()

        # sessions
        self.session_1 = Session(
            formation_id=self.formation.id,
            formateur_id=self.formateur_1.id,
            date_debut=date.today() + timedelta(days=5),
            date_fin=date.today() + timedelta(days=8),
            type="inter",
            capacite_max=10,
            lieu="Paris",
            statut="planifiee",
        )
        self.session_2 = Session(
            formation_id=self.formation.id,
            formateur_id=self.formateur_2.id,
            date_debut=date.today() + timedelta(days=10),
            date_fin=date.today() + timedelta(days=13),
            type="intra",
            capacite_max=8,
            lieu="Lyon",
            statut="en_cours",
        )
        db.session.add_all([self.session_1, self.session_2])
        db.session.flush()

        # clients & participants
        self.client_1 = Client(nom_entreprise="Alpha Corp", secteur="Informatique", contact_email="alpha@corp.fr")
        self.client_2 = Client(nom_entreprise="Beta LLC", secteur="Finance", contact_email="beta@llc.fr")
        db.session.add_all([self.client_1, self.client_2])
        db.session.flush()

        self.part_1 = Participant(nom="Alice Dupont", email="alice@alpha.fr", client_id=self.client_1.id)
        self.part_2 = Participant(nom="Bob Martin", email="bob@beta.fr", client_id=self.client_2.id)
        db.session.add_all([self.part_1, self.part_2])
        db.session.flush()

        # inscriptions
        self.insc_1 = Inscription(session_id=self.session_1.id, participant_id=self.part_1.id, statut="confirmee")
        self.insc_2 = Inscription(session_id=self.session_2.id, participant_id=self.part_2.id, statut="confirmee")
        db.session.add_all([self.insc_1, self.insc_2])
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def _login(self, user):
        with self.client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)

    def _parse_csv(self, response):
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.headers["Content-Type"])
        self.assertIn("attachment; filename=", response.headers["Content-Disposition"])
        content = response.data.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        return list(reader)

    def test_export_sessions_id_matching(self):
        """Vérifie que /api/sessions et /api/sessions/export/csv renvoient exactement les mêmes IDs."""
        self._login(self.admin)

        # 1. Sans filtre
        json_resp = self.client.get("/api/sessions")
        csv_resp = self.client.get("/api/sessions/export/csv")
        json_ids = [s["id"] for s in json_resp.get_json()]
        csv_rows = self._parse_csv(csv_resp)
        csv_ids = [int(r["ID Session"]) for r in csv_rows]
        self.assertEqual(json_ids, csv_ids)

        # 2. Avec filtres combinés (type=inter&statut=planifiee)
        query_str = "type=inter&statut=planifiee"
        json_resp = self.client.get(f"/api/sessions?{query_str}")
        csv_resp = self.client.get(f"/api/sessions/export/csv?{query_str}")
        json_ids = [s["id"] for s in json_resp.get_json()]
        csv_rows = self._parse_csv(csv_resp)
        csv_ids = [int(r["ID Session"]) for r in csv_rows]
        self.assertEqual(json_ids, csv_ids)

    def test_export_clients_id_matching(self):
        """Vérifie que /api/clients et /api/clients/export/csv renvoient exactement les mêmes IDs."""
        self._login(self.admin)

        query_str = "secteur=Informatique"
        json_resp = self.client.get(f"/api/clients?{query_str}")
        csv_resp = self.client.get(f"/api/clients/export/csv?{query_str}")
        self.assertEqual(json_resp.status_code, 200)
        json_ids = [c["id"] for c in json_resp.get_json()]
        csv_rows = self._parse_csv(csv_resp)
        csv_ids = [int(r["ID Client"]) for r in csv_rows]
        self.assertEqual(json_ids, csv_ids)

    def test_export_clients_invalid_filter_400(self):
        """Vérifie qu'un filtre invalide sur /api/clients/export/csv renvoie un 400 Bad Request."""
        self._login(self.admin)
        csv_resp = self.client.get("/api/clients/export/csv?statut_activite=invalide")
        self.assertEqual(csv_resp.status_code, 400)

    def test_export_participants_id_matching(self):
        """Vérifie que /api/participants et /api/participants/export/csv renvoient exactement les mêmes IDs."""
        self._login(self.admin)
        json_resp = self.client.get("/api/participants")
        csv_resp = self.client.get("/api/participants/export/csv")
        json_ids = [p["id"] for p in json_resp.get_json()]
        csv_rows = self._parse_csv(csv_resp)
        csv_ids = [int(r["ID Participant"]) for r in csv_rows]
        self.assertEqual(json_ids, csv_ids)

    def test_export_inscriptions_id_matching(self):
        """Vérifie que /api/inscriptions et /api/inscriptions/export/csv renvoient exactement les mêmes IDs."""
        self._login(self.admin)
        query_str = "statut=confirmee"
        json_resp = self.client.get(f"/api/inscriptions?{query_str}")
        csv_resp = self.client.get(f"/api/inscriptions/export/csv?{query_str}")
        json_ids = [i["id"] for i in json_resp.get_json()]
        csv_rows = self._parse_csv(csv_resp)
        csv_ids = [int(r["ID Inscription"]) for r in csv_rows]
        self.assertEqual(json_ids, csv_ids)

    def test_export_formateur_rbac_isolation(self):
        """Vérifie que le rôle Formateur ne peut exporter que son périmètre autorisé."""
        self._login(self.formateur_user)

        json_resp = self.client.get("/api/sessions")
        csv_resp = self.client.get("/api/sessions/export/csv")
        json_ids = [s["id"] for s in json_resp.get_json()]
        csv_rows = self._parse_csv(csv_resp)
        csv_ids = [int(r["ID Session"]) for r in csv_rows]
        
        self.assertEqual(json_ids, csv_ids)
        self.assertEqual(csv_ids, [self.session_1.id])
        self.assertNotIn(self.session_2.id, csv_ids)
