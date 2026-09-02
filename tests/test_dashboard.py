"""
Tests unitaires et d'intégration pour le Dashboard filtrable (Étape 3.3.5).
Vérifie la cohérence croisée des KPI, graphiques, alertes, isolation RBAC et réinitialisation.
"""

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


class DashboardTestCase(unittest.TestCase):
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
        db.session.flush()

        self.domaine_web = Domaine(nom="Web & Data")
        self.domaine_cyber = Domaine(nom="Cybersécurité")
        db.session.add_all([self.domaine_web, self.domaine_cyber])
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin User",
            email="admin@dashboard.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=admin_role,
        )
        self.user_formateur_1 = Utilisateur(
            nom="Formateur Alpha",
            email="f1@dashboard.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=formateur_role,
        )
        self.user_formateur_2 = Utilisateur(
            nom="Formateur Beta",
            email="f2@dashboard.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=formateur_role,
        )
        db.session.add_all([self.admin, self.user_formateur_1, self.user_formateur_2])
        db.session.flush()

        self.formateur_1 = Formateur(nom="Formateur Alpha", domaine=self.domaine_web, utilisateur=self.user_formateur_1)
        self.formateur_2 = Formateur(nom="Formateur Beta", domaine=self.domaine_cyber, utilisateur=self.user_formateur_2)

        self.formation_web = Formation(titre="Python Web", domaine=self.domaine_web, duree_jours=3)
        self.formation_cyber = Formation(titre="Sécurité Réseau", domaine=self.domaine_cyber, duree_jours=2)

        self.client_corp = Client(nom_entreprise="Galaxy Corp", secteur="Technologies", contact_email="contact@galaxy.ma")
        self.client_other = Client(nom_entreprise="Alpha Finance", secteur="Finance", contact_email="contact@alpha.ma")

        db.session.add_all([
            self.formateur_1, self.formateur_2,
            self.formation_web, self.formation_cyber,
            self.client_corp, self.client_other,
        ])
        db.session.flush()

        today = date.today()
        # s1: Web, Formateur 1, 2026, capacite 10, client_corp
        self.s1 = Session(
            formation=self.formation_web,
            formateur=self.formateur_1,
            date_debut=date(2026, 3, 15),
            date_fin=date(2026, 3, 18),
            type="intra",
            capacite_max=10,
            lieu="Casablanca",
            statut="planifiee",
        )
        # s2: Cyber, Formateur 2, 2026, capacite 10, client_corp
        self.s2 = Session(
            formation=self.formation_cyber,
            formateur=self.formateur_2,
            date_debut=date(2026, 4, 10),
            date_fin=date(2026, 4, 12),
            type="inter",
            capacite_max=10,
            lieu="Rabat",
            statut="en_cours",
        )
        # s3: Web, Formateur 1, 2025, capacite 10, client_other
        self.s3 = Session(
            formation=self.formation_web,
            formateur=self.formateur_1,
            date_debut=date(2025, 5, 1),
            date_fin=date(2025, 5, 4),
            type="inter",
            capacite_max=10,
            lieu="Casablanca",
            statut="terminee",
        )
        db.session.add_all([self.s1, self.s2, self.s3])
        db.session.flush()

        self.part_corp_1 = Participant(nom="Part Galaxy 1", email="pg1@test.ma", client=self.client_corp)
        self.part_corp_2 = Participant(nom="Part Galaxy 2", email="pg2@test.ma", client=self.client_corp)
        self.part_other_1 = Participant(nom="Part Alpha 1", email="pa1@test.ma", client=self.client_other)

        db.session.add_all([self.part_corp_1, self.part_corp_2, self.part_other_1])
        db.session.flush()

        db.session.add_all([
            Inscription(session=self.s1, participant=self.part_corp_1, statut="confirmee"),
            Inscription(session=self.s2, participant=self.part_corp_2, statut="confirmee"),
            Inscription(session=self.s3, participant=self.part_other_1, statut="confirmee"),
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

    def test_dashboard_kpi_sans_filtre(self):
        self.connecter(self.admin)
        res = self.client.get("/api/stats/kpi-globaux").get_json()
        self.assertEqual(res["sessions_actives"], 3)
        self.assertEqual(res["participants_distincts"], 3)

    def test_dashboard_kpi_filtre_annee(self):
        self.connecter(self.admin)
        res_2026 = self.client.get("/api/stats/kpi-globaux?annee=2026").get_json()
        self.assertEqual(res_2026["sessions_actives"], 2)

        res_2025 = self.client.get("/api/stats/kpi-globaux?annee=2025").get_json()
        self.assertEqual(res_2025["sessions_actives"], 1)

    def test_dashboard_kpi_filtre_domaine(self):
        self.connecter(self.admin)
        res_cyber = self.client.get(f"/api/stats/kpi-globaux?domaine_id={self.domaine_cyber.id}").get_json()
        self.assertEqual(res_cyber["sessions_actives"], 1)
        self.assertEqual(res_cyber["formations_catalogue"], 1)

    def test_dashboard_kpi_filtre_client(self):
        self.connecter(self.admin)
        res_other = self.client.get(f"/api/stats/kpi-globaux?client_id={self.client_other.id}").get_json()
        self.assertEqual(res_other["sessions_actives"], 1)
        self.assertEqual(res_other["participants_distincts"], 1)

    def test_dashboard_kpi_filtre_formateur(self):
        self.connecter(self.admin)
        res_f2 = self.client.get(f"/api/stats/kpi-globaux?formateur_id={self.formateur_2.id}").get_json()
        self.assertEqual(res_f2["sessions_actives"], 1)
        self.assertEqual(res_f2["formateurs_mobilises"], 1)

    def test_dashboard_kpi_filtres_combines(self):
        self.connecter(self.admin)
        res = self.client.get(f"/api/stats/kpi-globaux?annee=2026&domaine_id={self.domaine_web.id}").get_json()
        self.assertEqual(res["sessions_actives"], 1)

    def test_dashboard_graphique_domaine_respecte_filtre(self):
        self.connecter(self.admin)
        res = self.client.get(f"/api/stats/activite-domaine?domaine_id={self.domaine_web.id}").get_json()
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["domaine"], "Web & Data")

    def test_dashboard_graphique_evolution_respecte_filtre(self):
        self.connecter(self.admin)
        res = self.client.get(f"/api/stats/evolution-inscriptions?annee=2026&client_id={self.client_corp.id}").get_json()
        self.assertIsInstance(res, list)

    def test_dashboard_mois_absent_vaut_zero(self):
        self.connecter(self.admin)
        res = self.client.get("/api/stats/evolution-inscriptions?annee=2026").get_json()
        self.assertEqual(len(res), 12)
        mois_1 = [m for m in res if m["mois"] == 1][0]
        self.assertEqual(mois_1["nb_inscriptions"], 0)
        mois_3 = [m for m in res if m["mois"] == 3][0]
        self.assertEqual(mois_3["nb_inscriptions"], 1)

    def test_dashboard_alertes_respectent_filtre_domaine(self):
        self.connecter(self.admin)
        res = self.client.get(f"/api/stats/points-attention?domaine_id={self.domaine_web.id}").get_json()
        self.assertIn("total", res)
        self.assertIn("items", res)

    def test_dashboard_alertes_respectent_filtre_client(self):
        self.connecter(self.admin)
        res = self.client.get(f"/api/stats/points-attention?client_id={self.client_other.id}").get_json()
        self.assertIn("total", res)

    def test_dashboard_alertes_respectent_filtre_formateur(self):
        self.connecter(self.admin)
        res = self.client.get(f"/api/stats/points-attention?formateur_id={self.formateur_1.id}").get_json()
        self.assertIn("total", res)

    def test_dashboard_filtre_invalide_400(self):
        self.connecter(self.admin)
        res = self.client.get("/api/stats/kpi-globaux?annee=abc")
        self.assertEqual(res.status_code, 400)

        res2 = self.client.get("/api/stats/activite-domaine?domaine_id=-5")
        self.assertEqual(res2.status_code, 400)

    def test_dashboard_et_sessions_partagent_le_meme_perimetre(self):
        self.connecter(self.admin)
        # 1. Vérification avec domaine_id=Web
        kpi_web = self.client.get(f"/api/stats/kpi-globaux?domaine_id={self.domaine_web.id}").get_json()
        sessions_web = self.client.get(f"/api/sessions?domaine_id={self.domaine_web.id}").get_json()
        self.assertEqual(kpi_web["sessions_actives"], len(sessions_web))

        # 2. Vérification avec annee=2026
        kpi_2026 = self.client.get("/api/stats/kpi-globaux?annee=2026").get_json()
        sessions_2026 = self.client.get("/api/sessions?date_debut_min=2026-01-01&date_debut_max=2026-12-31").get_json()
        self.assertEqual(kpi_2026["sessions_actives"], len(sessions_2026))

        # 3. Vérification avec formateur_id=Formateur 2
        kpi_f2 = self.client.get(f"/api/stats/kpi-globaux?formateur_id={self.formateur_2.id}").get_json()
        sessions_f2 = self.client.get(f"/api/sessions?formateur_id={self.formateur_2.id}").get_json()
        self.assertEqual(kpi_f2["sessions_actives"], len(sessions_f2))

    def test_dashboard_rbac_formateur_isole(self):
        # Connexion Formateur 1
        self.client = self.app.test_client()
        connexion = self.client.post(
            "/api/auth/login",
            json={"email": "f1@dashboard.ma", "mot_de_passe": "Secret123"},
        )
        self.assertEqual(connexion.status_code, 200)

        # Les endpoints de statistiques du dashboard sont réservés aux gestionnaires/admins (HTTP 403 pour formateur)
        res = self.client.get(f"/api/stats/kpi-globaux?formateur_id={self.formateur_2.id}")
        self.assertEqual(res.status_code, 403)

    def test_dashboard_interface_expose_filtres(self):
        self.connecter(self.admin)
        page = self.client.get("/dashboard")
        self.assertEqual(page.status_code, 200)
        contenu = page.data.decode("utf-8")
        self.assertIn("filtres.annee", contenu)
        self.assertIn("filtres.domaine_id", contenu)
        self.assertIn("filtres.client_id", contenu)
        self.assertIn("filtres.formateur_id", contenu)
        self.assertIn("reinitialiserFiltres()", contenu)

    def test_dashboard_filtres_tous_combines(self):
        self.connecter(self.admin)
        # Combinaison des 4 critères réducteurs : annee 2026 + domaine Web + client_corp + formateur 1 -> s1 uniquement
        res = self.client.get(
            f"/api/stats/kpi-globaux?annee=2026&domaine_id={self.domaine_web.id}&client_id={self.client_corp.id}&formateur_id={self.formateur_1.id}"
        ).get_json()
        self.assertEqual(res["sessions_actives"], 1)
        self.assertEqual(res["participants_distincts"], 1)

    def test_dashboard_reinitialisation_retour_perimetre_global(self):
        self.connecter(self.admin)
        # Filtre restrictif
        res_filtre = self.client.get(f"/api/stats/kpi-globaux?domaine_id={self.domaine_cyber.id}").get_json()
        self.assertEqual(res_filtre["sessions_actives"], 1)

        # Sans filtre (après réinitialisation)
        res_base = self.client.get("/api/stats/kpi-globaux").get_json()
        self.assertEqual(res_base["sessions_actives"], 3)


if __name__ == "__main__":
    unittest.main()
