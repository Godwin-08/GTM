"""
Tests d'audit de cohérence globale technique et fonctionnelle (Phases 1 + 2).
Vérifie la parfaite harmonie métier, analytique et sécuritaire de l'application.
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
from app.services.client_activity_service import nombre_clients_actifs, statut_activite_client
from app.services.points_attention_service import get_points_attention
from app.services.stats_service import kpi_globaux
from scripts.generate_seed_data import generer_donnees_seed, OUTPUT_FILE


class CoherenceGlobaleTestCase(unittest.TestCase):
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
        
        self.domaine_web = Domaine(nom="Web & Data")
        self.domaine_cyber = Domaine(nom="Cybersécurité")
        db.session.add_all([self.domaine_web, self.domaine_cyber])
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin User",
            email="admin@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=admin_role,
        )
        self.user_f1 = Utilisateur(
            nom="Formateur 1",
            email="f1@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=formateur_role,
        )
        self.user_f2 = Utilisateur(
            nom="Formateur 2",
            email="f2@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=formateur_role,
        )
        db.session.add_all([self.admin, self.user_f1, self.user_f2])
        db.session.flush()

        self.f1 = Formateur(nom="Formateur 1", domaine=self.domaine_web, utilisateur=self.user_f1)
        self.f2 = Formateur(nom="Formateur 2", domaine=self.domaine_cyber, utilisateur=self.user_f2)
        self.form_web = Formation(titre="Python Web", domaine=self.domaine_web, duree_jours=3)
        self.form_cyber = Formation(titre="Cyber Deep", domaine=self.domaine_cyber, duree_jours=2)
        self.client_a = Client(nom_entreprise="Alpha Corp", secteur="Tech")
        self.client_b = Client(nom_entreprise="Beta Corp", secteur="Finance")

        db.session.add_all([self.f1, self.f2, self.form_web, self.form_cyber, self.client_a, self.client_b])
        db.session.flush()

        today = date.today()
        # Session Web animée par F1
        self.s_web = Session(
            formation=self.form_web, formateur=self.f1,
            date_debut=today - timedelta(days=10), date_fin=today - timedelta(days=7),
            type="intra", capacite_max=10, statut="terminee"
        )
        # Session Cyber animée par F2
        self.s_cyber = Session(
            formation=self.form_cyber, formateur=self.f2,
            date_debut=today - timedelta(days=5), date_fin=today - timedelta(days=3),
            type="inter", capacite_max=10, statut="terminee"
        )
        db.session.add_all([self.s_web, self.s_cyber])
        db.session.flush()

        self.p_a = Participant(nom="Part A", email="pa@test.ma", client=self.client_a)
        self.p_b = Participant(nom="Part B", email="pb@test.ma", client=self.client_b)
        db.session.add_all([self.p_a, self.p_b])
        db.session.flush()

        db.session.add_all([
            Inscription(session=self.s_web, participant=self.p_a, statut="confirmee"),
            Inscription(session=self.s_cyber, participant=self.p_b, statut="confirmee"),
        ])
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter(self, user):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(user.id)
            session["_fresh"] = True

    def test_coherence_activite_client_kpi_et_points_attention(self):
        today = date.today()
        # 1. Nombre de clients actifs
        nb_actifs = nombre_clients_actifs(today)
        self.assertEqual(nb_actifs, 2)

        # 2. Statut unifié pour client_a
        statut_a = statut_activite_client(self.client_a.id, today)
        self.assertEqual(statut_a["statut"], "actif")
        self.assertEqual(statut_a["label"], "Actif")

        # 3. Points d'attention : aucun client inactif détecté (les deux sont actifs)
        points = get_points_attention()
        clients_inactifs_points = [item for item in points["items"] if item["type"] == "client_inactif"]
        self.assertEqual(len(clients_inactifs_points), 0)

    def test_coherence_dashboard_filtres_et_sessions_api(self):
        self.connecter(self.admin)

        # 1. KPI filtrés sur le domaine Web
        kpi_web = self.client.get(f"/api/stats/kpi-globaux?domaine_id={self.domaine_web.id}").get_json()
        
        # 2. Liste des sessions filtrées par l'API sessions sur le même domaine
        sessions_web = self.client.get(f"/api/sessions?domaine_id={self.domaine_web.id}").get_json()

        # Cohérence parfaite : le nombre de sessions actives dans les KPI égale la taille du sous-ensemble
        self.assertEqual(kpi_web["sessions_actives"], len(sessions_web))
        self.assertEqual(kpi_web["sessions_actives"], 1)

    def test_coherence_isolation_rbac_multi_ressources(self):
        self.connecter(self.user_f1)

        # Formateur 1 ne voit que la session Web
        sessions = self.client.get("/api/sessions").get_json()
        self.assertEqual([s["id"] for s in sessions], [self.s_web.id])

        # Accès direct aux ressources de Formateur 2 -> 403 Forbidden
        res_s2 = self.client.get(f"/api/sessions/{self.s_cyber.id}")
        self.assertEqual(res_s2.status_code, 403)

        res_p2 = self.client.get(f"/api/participants/{self.p_b.id}")
        self.assertEqual(res_p2.status_code, 403)

    def test_execution_reelle_et_chargement_du_seed_sql(self):
        # Exécution du générateur de seed
        generer_donnees_seed()
        sql_content = OUTPUT_FILE.read_text(encoding="utf-8")

        # Chargement et exécution dans une base SQLite fraiche pour vérifier la validité SQL des instructions
        db.drop_all()
        db.create_all()

        # Nettoyage des lignes de commentaires SQL
        lines_clean = [
            l for l in sql_content.splitlines()
            if not l.strip().startswith("--") and not l.strip().startswith("USE") and not l.strip().startswith("SET")
        ]
        sql_clean = "\n".join(lines_clean)

        statements = [stmt.strip() for stmt in sql_clean.split(";") if stmt.strip()]

        from sqlalchemy import text
        import re

        for statement in statements:
            if statement:
                # Normalisation des noms de tables en minuscules (ex: Client -> client) pour compatibilité SQLite
                if statement.startswith("TRUNCATE TABLE"):
                    table_name = statement.split()[2].lower()
                    statement = f"DELETE FROM {table_name}"
                else:
                    statement = re.sub(
                        r"INSERT INTO ([A-Za-z_]+)",
                        lambda m: f"INSERT INTO {m.group(1).lower()}",
                        statement
                    )
                db.session.execute(text(statement))
        db.session.commit()

        # Vérification des invariants réels après exécution SQL
        self.assertEqual(Client.query.count(), 30)
        self.assertEqual(Participant.query.count(), 150)
        self.assertEqual(Formation.query.count(), 12)
        self.assertEqual(Session.query.count(), 60)
        self.assertGreaterEqual(Inscription.query.count(), 400)


if __name__ == "__main__":
    unittest.main()
