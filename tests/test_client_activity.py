"""Tests unitaires pour le service centralisé d'activité client."""

import unittest
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Client, Domaine, Formateur, Formation, Inscription, Participant, Role, Session, Utilisateur
from app.services.client_activity_service import nombre_clients_actifs, statut_activite_client


class ClientActivityTestCase(unittest.TestCase):
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
        self.formateur = Formateur(nom="Formateur Test", domaine=domaine)
        self.formation = Formation(titre="Formation Test", domaine=domaine, duree_jours=2)
        db.session.add_all([self.admin, self.formateur, self.formation])
        db.session.flush()

        # Clients de test
        self.client_actif = Client(nom_entreprise="Actif Corp")
        self.client_futur = Client(nom_entreprise="Futur Corp")
        self.client_annule = Client(nom_entreprise="Annule Corp")
        self.client_inactif = Client(nom_entreprise="Inactif Corp")

        db.session.add_all([self.client_actif, self.client_futur, self.client_annule, self.client_inactif])
        db.session.flush()

        today = date.today()

        # Session active (passée récente)
        s_active = Session(
            formation=self.formation, formateur=self.formateur,
            date_debut=today - timedelta(days=15), date_fin=today - timedelta(days=10),
            type="inter", capacite_max=10, statut="terminee"
        )
        # Session future
        s_future = Session(
            formation=self.formation, formateur=self.formateur,
            date_debut=today + timedelta(days=10), date_fin=today + timedelta(days=15),
            type="inter", capacite_max=10, statut="planifiee"
        )
        # Session annulée
        s_annulee = Session(
            formation=self.formation, formateur=self.formateur,
            date_debut=today - timedelta(days=15), date_fin=today - timedelta(days=10),
            type="inter", capacite_max=10, statut="annulee"
        )
        # Session inoffensive ancienne (> 6 mois)
        s_ancienne = Session(
            formation=self.formation, formateur=self.formateur,
            date_debut=today - timedelta(days=220), date_fin=today - timedelta(days=215),
            type="inter", capacite_max=10, statut="terminee"
        )

        db.session.add_all([s_active, s_future, s_annulee, s_ancienne])
        db.session.flush()

        p_actif = Participant(nom="P Actif", email="p1@test.ma", client=self.client_actif)
        p_futur = Participant(nom="P Futur", email="p2@test.ma", client=self.client_futur)
        p_annule = Participant(nom="P Annule", email="p3@test.ma", client=self.client_annule)
        p_inactif = Participant(nom="P Inactif", email="p4@test.ma", client=self.client_inactif)

        db.session.add_all([p_actif, p_futur, p_annule, p_inactif])
        db.session.flush()

        db.session.add_all([
            Inscription(session=s_active, participant=p_actif, statut="confirmee"),
            Inscription(session=s_future, participant=p_futur, statut="confirmee"),
            Inscription(session=s_annulee, participant=p_annule, statut="confirmee"),
            Inscription(session=s_ancienne, participant=p_inactif, statut="confirmee"),
        ])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def test_regle_client_actif_et_comptage(self):
        today = date.today()
        # Seul client_actif doit compter
        self.assertEqual(nombre_clients_actifs(today), 1)

        # Vérification des détails de statut
        res_actif = statut_activite_client(self.client_actif.id, today)
        self.assertEqual(res_actif["statut"], "actif")

        res_futur = statut_activite_client(self.client_futur.id, today)
        self.assertEqual(res_futur["statut"], "aucune")

        res_annule = statut_activite_client(self.client_annule.id, today)
        self.assertEqual(res_annule["statut"], "aucune")

        res_inactif = statut_activite_client(self.client_inactif.id, today)
        self.assertEqual(res_inactif["statut"], "inactif")
        self.assertIn("Inactif ·", res_inactif["label"])


if __name__ == "__main__":
    unittest.main()

