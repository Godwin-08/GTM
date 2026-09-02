"""Tests unitaires pour la gestion standardisée des erreurs API, l'intégrité et la prévention des doublons."""

import unittest
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Client, Domaine, Formateur, Formation, Inscription, Participant, Role, Session, Utilisateur


class ApiErrorsAndIntegrityTestCase(unittest.TestCase):
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
        self.client_ent = Client(nom_entreprise="Test Client")
        self.participant = Participant(nom="Test Part", email="p@test.ma", client=self.client_ent)
        self.formateur = Formateur(nom="Test Formateur", domaine=domaine)
        self.formation = Formation(titre="Test Formation", domaine=domaine, duree_jours=2)

        db.session.add_all([self.admin, self.client_ent, self.participant, self.formateur, self.formation])
        db.session.flush()

        today = date.today()
        # Session ouverte (planifiee) pour les tests de création d'inscription
        self.session_planifiee = Session(
            formation=self.formation,
            formateur=self.formateur,
            date_debut=today + timedelta(days=10),
            date_fin=today + timedelta(days=12),
            type="inter",
            capacite_max=2,
            statut="planifiee",
        )
        # Session terminée pour tester le rejet
        self.session_terminee = Session(
            formation=self.formation,
            formateur=self.formateur,
            date_debut=today - timedelta(days=10),
            date_fin=today - timedelta(days=8),
            type="inter",
            capacite_max=10,
            statut="terminee",
        )
        # Session annulée pour tester le rejet
        self.session_annulee = Session(
            formation=self.formation,
            formateur=self.formateur,
            date_debut=today + timedelta(days=5),
            date_fin=today + timedelta(days=7),
            type="inter",
            capacite_max=10,
            statut="annulee",
        )
        # Participants supplémentaires pour le test de capacité
        self.participant2 = Participant(nom="Part 2", email="p2@test.ma", client=self.client_ent)
        self.participant3 = Participant(nom="Part 3", email="p3@test.ma", client=self.client_ent)
        db.session.add_all([
            self.session_planifiee, self.session_terminee, self.session_annulee,
            self.participant2, self.participant3,
        ])
        # Alias de compatibilité pour les anciens tests
        self.session = self.session_planifiee
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin.id)
            session["_fresh"] = True

    def test_erreurs_json_sur_api(self):
        self.connecter()

        # 1. 404 sur API -> JSON avec "erreur"
        res_404 = self.client.get("/api/clients/99999")
        self.assertEqual(res_404.status_code, 404)
        self.assertIn("erreur", res_404.get_json())
        self.assertEqual(res_404.get_json()["erreur"], "Ressource introuvable.")

    def test_suppression_client_avec_participants_renvoie_409(self):
        self.connecter()

        # Suppression d'un client possédant encore un participant -> 409 Conflict
        res_del = self.client.delete(f"/api/clients/{self.client_ent.id}")
        self.assertEqual(res_del.status_code, 409)
        self.assertIn("participant", res_del.get_json()["erreur"].lower())

    def test_doublon_inscription_renvoie_409(self):
        self.connecter()

        donnees = {
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant.id,
            "statut": "confirmee",
        }

        # Première inscription -> 201 Created
        res1 = self.client.post("/api/inscriptions", json=donnees)
        self.assertEqual(res1.status_code, 201)

        # Deuxième inscription identique -> 409 Conflict
        res2 = self.client.post("/api/inscriptions", json=donnees)
        self.assertEqual(res2.status_code, 409)

    def test_inscription_session_terminee_renvoie_409(self):
        self.connecter()

        res = self.client.post("/api/inscriptions", json={
            "session_id": self.session_terminee.id,
            "participant_id": self.participant.id,
            "statut": "confirmee",
        })
        self.assertEqual(res.status_code, 409)
        self.assertIn("terminée", res.get_json()["erreur"])

    def test_inscription_session_annulee_renvoie_409(self):
        self.connecter()

        res = self.client.post("/api/inscriptions", json={
            "session_id": self.session_annulee.id,
            "participant_id": self.participant.id,
            "statut": "confirmee",
        })
        self.assertEqual(res.status_code, 409)
        self.assertIn("annulée", res.get_json()["erreur"])

    def test_capacite_atteinte_confirmee_renvoie_409(self):
        """La session planifiée a capacite_max=2 ; on la remplit puis on tente une 3e inscription."""
        self.connecter()

        self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant.id,
            "statut": "confirmee",
        })
        self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant2.id,
            "statut": "confirmee",
        })

        # 3e inscription confirmee -> 409
        res = self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant3.id,
            "statut": "confirmee",
        })
        self.assertEqual(res.status_code, 409)
        self.assertIn("complète", res.get_json()["erreur"])

    def test_liste_attente_acceptee_meme_si_session_complete(self):
        """Une inscription en liste_attente est autorisée même si la capacité est atteinte."""
        self.connecter()

        self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant.id,
            "statut": "confirmee",
        })
        self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant2.id,
            "statut": "confirmee",
        })

        # Inscription en liste_attente -> 201 même si session complète
        res = self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant3.id,
            "statut": "liste_attente",
        })
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.get_json()["statut"], "liste_attente")

    def test_put_statut_valide(self):
        """PUT sur une inscription existante avec un statut valide -> 200."""
        self.connecter()

        # Créer une inscription
        res_post = self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant.id,
            "statut": "confirmee",
        })
        self.assertEqual(res_post.status_code, 201)
        inscription_id = res_post.get_json()["id"]

        # Modifier le statut
        res_put = self.client.put(f"/api/inscriptions/{inscription_id}", json={
            "statut": "annulee",
        })
        self.assertEqual(res_put.status_code, 200)
        self.assertEqual(res_put.get_json()["statut"], "annulee")

    def test_put_statut_invalide_renvoie_400(self):
        self.connecter()

        res_post = self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant.id,
            "statut": "confirmee",
        })
        inscription_id = res_post.get_json()["id"]

        res_put = self.client.put(f"/api/inscriptions/{inscription_id}", json={
            "statut": "statut_invalide",
        })
        self.assertEqual(res_put.status_code, 400)

    def test_put_inscription_inexistante_renvoie_404(self):
        self.connecter()

        res = self.client.put("/api/inscriptions/99999", json={"statut": "annulee"})
        self.assertEqual(res.status_code, 404)

    def test_put_confirmer_depasse_capacite_renvoie_409(self):
        """Passer une inscription de liste_attente à confirmee alors que la session est pleine -> 409."""
        self.connecter()

        # Remplir la session (capacite_max=2)
        self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant.id,
            "statut": "confirmee",
        })
        self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant2.id,
            "statut": "confirmee",
        })

        # Ajouter en liste_attente
        res_attente = self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant3.id,
            "statut": "liste_attente",
        })
        self.assertEqual(res_attente.status_code, 201)
        inscription_id = res_attente.get_json()["id"]

        # Tenter de confirmer -> 409
        res_put = self.client.put(f"/api/inscriptions/{inscription_id}", json={
            "statut": "confirmee",
        })
        self.assertEqual(res_put.status_code, 409)

    def test_inscription_valide_retourne_201(self):
        """Création d'une inscription valide -> 201 avec les données attendues."""
        self.connecter()

        res = self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": self.participant.id,
            "statut": "confirmee",
        })
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["statut"], "confirmee")
        self.assertEqual(data["session_id"], self.session_planifiee.id)

    def test_inscription_participant_inexistant_renvoie_400(self):
        self.connecter()

        res = self.client.post("/api/inscriptions", json={
            "session_id": self.session_planifiee.id,
            "participant_id": 99999,
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("participant_id", res.get_json()["erreur"])

    def test_inscription_session_inexistante_renvoie_400(self):
        self.connecter()

        res = self.client.post("/api/inscriptions", json={
            "session_id": 99999,
            "participant_id": self.participant.id,
        })
        self.assertEqual(res.status_code, 400)
        self.assertIn("session_id", res.get_json()["erreur"])


if __name__ == "__main__":
    unittest.main()
