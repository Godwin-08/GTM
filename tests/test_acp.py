"""Tests unitaires pour la Sous-étape 2.4 — Consolidation & Sécurisation de l'Analyse en Composantes Principales (ACP)."""

import unittest
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Client, Domaine, Formateur, Formation, Inscription, Participant, Role, Session, Utilisateur
from app.services.acp_service import get_acp_complete


class AcpTestCase(unittest.TestCase):
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
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin.id)
            session["_fresh"] = True

    def test_acp_matrice_vide_ou_donnees_insuffisantes(self):
        # 0 clients et 0 formations -> Fallback sécurisé sans exception
        res = get_acp_complete()
        self.assertEqual(res["nb_clients"], 0)
        self.assertEqual(res["nb_formations"], 0)
        self.assertFalse(res["interpretation"]["peut_conclure"])

    def test_acp_donnees_normales_et_structure_json(self):
        domaine = Domaine.query.first()

        c1 = Client(nom_entreprise="Client A")
        c2 = Client(nom_entreprise="Client B")
        c3 = Client(nom_entreprise="Client C")
        db.session.add_all([c1, c2, c3])

        f1 = Formation(titre="Python", domaine=domaine, duree_jours=3)
        f2 = Formation(titre="SQL", domaine=domaine, duree_jours=2)
        formateur = Formateur(nom="Formateur Test", domaine=domaine)
        db.session.add_all([f1, f2, formateur])
        db.session.flush()

        today = date.today()
        s1 = Session(formation=f1, formateur=formateur, date_debut=today - timedelta(days=10), date_fin=today - timedelta(days=8), type="intra", capacite_max=10, statut="terminee")
        s2 = Session(formation=f2, formateur=formateur, date_debut=today - timedelta(days=10), date_fin=today - timedelta(days=8), type="inter", capacite_max=10, statut="terminee")
        db.session.add_all([s1, s2])
        db.session.flush()

        p1 = Participant(nom="P1", email="p1@test.ma", client=c1)
        p2 = Participant(nom="P2", email="p2@test.ma", client=c2)
        p3 = Participant(nom="P3", email="p3@test.ma", client=c3)
        db.session.add_all([p1, p2, p3])
        db.session.flush()

        db.session.add_all([
            Inscription(session=s1, participant=p1, statut="confirmee"),
            Inscription(session=s1, participant=p2, statut="confirmee"),
            Inscription(session=s2, participant=p3, statut="confirmee"),
        ])
        db.session.commit()

        res = get_acp_complete()
        self.assertEqual(res["nb_clients"], 3)
        self.assertEqual(res["nb_formations"], 2)
        self.assertIn("variance_expliquee", res)
        self.assertIn("clients", res)
        self.assertIn("formations", res)
        self.assertIn("interpretation", res)

    def test_acp_endpoint_api(self):
        self.connecter()
        response = self.client.get("/api/stats/pca")
        self.assertEqual(response.status_code, 200)
        json_data = response.get_json()
        self.assertIn("nb_clients", json_data)
        self.assertIn("interpretation", json_data)


if __name__ == "__main__":
    unittest.main()

