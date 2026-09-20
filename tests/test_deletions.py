"""
Tests unitaires pour la suppression sécurisée des Clients et Participants.
Vérifie la conformité HTTP (204, 409, 403, 404) et l'intégrité référentielle.
"""

import unittest
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Client, Participant, Inscription, Session, Formation, Domaine, Formateur, Role, Utilisateur


class DeletionsTestCase(unittest.TestCase):
    """Suite de tests pour les suppressions sécurisées (Clients et Participants)."""

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
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin User",
            email="admin@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=admin_role,
        )
        self.formateur_user = Utilisateur(
            nom="Formateur User",
            email="formateur@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=formateur_role,
        )
        domaine = Domaine(nom="Data")
        db.session.add_all([self.admin, self.formateur_user, domaine])
        db.session.flush()

        self.formateur = Formateur(nom="Formateur", domaine=domaine, utilisateur=self.formateur_user)
        self.formation = Formation(titre="Python", domaine=domaine, duree_jours=3)
        db.session.add_all([self.formateur, self.formation])
        db.session.flush()

        self.session = Session(
            formation=self.formation,
            formateur=self.formateur,
            date_debut=date.today(),
            date_fin=date.today() + timedelta(days=2),
            type="inter",
            capacite_max=10,
            statut="planifiee",
        )
        db.session.add(self.session)
        db.session.flush()

        # Clients de test
        self.client_isole = Client(nom_entreprise="Entreprise Sans Salarié", secteur="Tech")
        self.client_avec_salaries = Client(nom_entreprise="Entreprise Avec Salariés", secteur="Banque")
        db.session.add_all([self.client_isole, self.client_avec_salaries])
        db.session.flush()

        # Participants de test
        self.participant_isole = Participant(
            nom="Participant Sans Inscription",
            email="isole@test.ma",
            client=self.client_avec_salaries,
        )
        self.participant_inscrit = Participant(
            nom="Participant Inscrit",
            email="inscrit@test.ma",
            client=self.client_avec_salaries,
        )
        db.session.add_all([self.participant_isole, self.participant_inscrit])
        db.session.flush()

        self.inscription = Inscription(
            session=self.session,
            participant=self.participant_inscrit,
            statut="confirmee",
        )
        db.session.add(self.inscription)
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter(self, user):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(user.id)
            session["_fresh"] = True

    # -------------------------------------------------------------------------
    # Tests Suppression Client
    # -------------------------------------------------------------------------

    def test_suppression_client_sans_participants_succes(self):
        """Un client sans participants rattachés peut être supprimé avec succès (204)."""
        self.connecter(self.admin)
        client_id = self.client_isole.id

        res = self.client.delete(f"/api/clients/{client_id}")
        self.assertEqual(res.status_code, 204)

        # Vérification en base
        self.assertIsNone(db.session.get(Client, client_id))

    def test_suppression_client_avec_participants_bloquee_409(self):
        """Un client ayant des participants rattachés ne peut pas être supprimé (409)."""
        self.connecter(self.admin)
        client_id = self.client_avec_salaries.id

        res = self.client.delete(f"/api/clients/{client_id}")
        self.assertEqual(res.status_code, 409)
        data = res.get_json()
        self.assertIn("participant(s) y sont associé(s)", data.get("erreur", ""))

        # Vérification en base : non supprimé
        self.assertIsNotNone(db.session.get(Client, client_id))

    def test_suppression_client_par_formateur_interdite_403(self):
        """Un formateur n'a pas les droits pour supprimer un client (403)."""
        self.connecter(self.formateur_user)
        res = self.client.delete(f"/api/clients/{self.client_isole.id}")
        self.assertEqual(res.status_code, 403)

    # -------------------------------------------------------------------------
    # Tests Suppression Participant
    # -------------------------------------------------------------------------

    def test_suppression_participant_sans_inscriptions_succes(self):
        """Un participant sans inscriptions peut être supprimé avec succès (204)."""
        self.connecter(self.admin)
        part_id = self.participant_isole.id

        res = self.client.delete(f"/api/participants/{part_id}")
        self.assertEqual(res.status_code, 204)

        # Vérification en base
        self.assertIsNone(db.session.get(Participant, part_id))

    def test_suppression_participant_avec_inscriptions_bloquee_409(self):
        """Un participant ayant des inscriptions actives ne peut pas être supprimé (409)."""
        self.connecter(self.admin)
        part_id = self.participant_inscrit.id

        res = self.client.delete(f"/api/participants/{part_id}")
        self.assertEqual(res.status_code, 409)
        data = res.get_json()
        self.assertIn("inscription(s) y sont associée(s)", data.get("erreur", ""))

        # Vérification en base : non supprimé
        self.assertIsNotNone(db.session.get(Participant, part_id))

    def test_suppression_inscription_par_admin_succes(self):
        """Un admin peut supprimer une inscription depuis le détail du participant."""
        self.connecter(self.admin)

        res = self.client.delete(f"/api/inscriptions/{self.inscription.id}")
        self.assertEqual(res.status_code, 204)
        self.assertIsNone(db.session.get(Inscription, self.inscription.id))

    def test_suppression_multiple_participants_sans_inscriptions_succes(self):
        """Un admin peut supprimer plusieurs participants sans inscriptions."""
        self.connecter(self.admin)
        autre_participant = Participant(
            nom="Autre participant isolé",
            email="autre.isole@test.ma",
            client=self.client_avec_salaries,
        )
        db.session.add(autre_participant)
        db.session.commit()

        res = self.client.delete(
            "/api/participants",
            json={"ids": [self.participant_isole.id, autre_participant.id]},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(db.session.get(Participant, self.participant_isole.id))
        self.assertIsNone(db.session.get(Participant, autre_participant.id))

    def test_suppression_multiple_participants_ignore_les_inscrits(self):
        """Une sélection supprime les participants isolés et conserve les inscrits."""
        self.connecter(self.admin)
        res = self.client.delete(
            "/api/participants",
            json={"ids": [self.participant_isole.id, self.participant_inscrit.id]},
        )
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(db.session.get(Participant, self.participant_isole.id))
        self.assertIsNotNone(db.session.get(Participant, self.participant_inscrit.id))
        self.assertEqual(res.get_json()["supprimees"], [self.participant_isole.id])
        self.assertEqual(res.get_json()["bloquees"][0]["id"], self.participant_inscrit.id)

    def test_suppression_inscription_par_formateur_interdite_403(self):
        """Un formateur n'a pas les droits pour supprimer une inscription."""
        self.connecter(self.formateur_user)

        res = self.client.delete(f"/api/inscriptions/{self.inscription.id}")
        self.assertEqual(res.status_code, 403)

    def test_suppression_multiple_inscriptions_par_admin_succes(self):
        """Un admin peut supprimer plusieurs inscriptions d'un coup."""
        self.connecter(self.admin)

        autre_inscription = Inscription(
            session=self.session,
            participant=self.participant_isole,
            statut="liste_attente",
        )
        db.session.add(autre_inscription)
        db.session.commit()

        res = self.client.delete("/api/inscriptions", json={"ids": [self.inscription.id, autre_inscription.id]})
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(db.session.get(Inscription, self.inscription.id))
        self.assertIsNone(db.session.get(Inscription, autre_inscription.id))

    def test_suppression_multiple_sessions_par_admin_succes(self):
        """Un admin peut supprimer plusieurs sessions vides d'un coup."""
        self.connecter(self.admin)

        session_libre_1 = Session(
            formation=self.formation,
            formateur=self.formateur,
            date_debut=date.today() + timedelta(days=10),
            date_fin=date.today() + timedelta(days=12),
            type="inter",
            capacite_max=8,
            statut="planifiee",
        )
        session_libre_2 = Session(
            formation=self.formation,
            formateur=self.formateur,
            date_debut=date.today() + timedelta(days=20),
            date_fin=date.today() + timedelta(days=22),
            type="inter",
            capacite_max=10,
            statut="planifiee",
        )
        db.session.add_all([session_libre_1, session_libre_2])
        db.session.commit()

        res = self.client.delete("/api/sessions", json={"ids": [session_libre_1.id, session_libre_2.id]})
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(db.session.get(Session, session_libre_1.id))
        self.assertIsNone(db.session.get(Session, session_libre_2.id))

    def test_suppression_participant_par_formateur_interdite_403(self):
        """Un formateur n'a pas les droits pour supprimer un participant (403)."""
        self.connecter(self.formateur_user)
        res = self.client.delete(f"/api/participants/{self.participant_isole.id}")
        self.assertEqual(res.status_code, 403)


if __name__ == "__main__":
    unittest.main()
