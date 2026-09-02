"""Tests unitaires pour la Sous-étape 2.3 — Filtres Dashboard globaux et entités Clients/Participants."""

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


class FiltersTestCase(unittest.TestCase):
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
        self.user_formateur_1 = Utilisateur(
            nom="Formateur Un",
            email="f1@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=formateur_role,
        )
        self.user_formateur_2 = Utilisateur(
            nom="Formateur Deux",
            email="f2@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=formateur_role,
        )
        db.session.add_all([self.admin, self.user_formateur_1, self.user_formateur_2])
        db.session.flush()

        self.formateur_1 = Formateur(
            nom="Formateur Un", domaine=self.domaine_web, utilisateur=self.user_formateur_1
        )
        self.formateur_2 = Formateur(
            nom="Formateur Deux", domaine=self.domaine_cyber, utilisateur=self.user_formateur_2
        )
        self.formateur_externe = Formateur(
            nom="Formateur Externe", domaine=self.domaine_web, utilisateur=None
        )
        self.formation_web = Formation(titre="Python Web", domaine=self.domaine_web, duree_jours=3)
        self.formation_cyber = Formation(titre="Sécurité Reseau", domaine=self.domaine_cyber, duree_jours=2)

        self.client_corp = Client(nom_entreprise="Galaxy Corp", secteur="Technologies", contact_email="contact@galaxy.ma")
        self.client_other = Client(nom_entreprise="Alpha Finance", secteur="Finance", contact_email="contact@alpha.ma")
        db.session.add_all([
            self.formateur_1, self.formateur_2, self.formateur_externe,
            self.formation_web, self.formation_cyber,
            self.client_corp, self.client_other,
        ])
        db.session.flush()

        today = date.today()
        # Session 1: Web, Formateur 1, planifiee, intra, capacite 10, 0 inscrits (0% -> sous_remplie)
        self.s1 = Session(
            formation=self.formation_web,
            formateur=self.formateur_1,
            date_debut=today + timedelta(days=5),
            date_fin=today + timedelta(days=8),
            type="intra",
            capacite_max=10,
            lieu="Casablanca",
            statut="planifiee",
        )
        # Session 2: Cyber, Formateur 2, en_cours, inter, capacite 10, 6 inscrits (60% -> nominale)
        self.s2 = Session(
            formation=self.formation_cyber,
            formateur=self.formateur_2,
            date_debut=today - timedelta(days=1),
            date_fin=today + timedelta(days=2),
            type="inter",
            capacite_max=10,
            lieu="Rabat",
            statut="en_cours",
        )
        # Session 3: Web, Formateur 1, terminee, inter, capacite 10, 9 inscrits (90% -> complete)
        self.s3 = Session(
            formation=self.formation_web,
            formateur=self.formateur_1,
            date_debut=today - timedelta(days=20),
            date_fin=today - timedelta(days=17),
            type="inter",
            capacite_max=10,
            lieu="Casablanca",
            statut="terminee",
        )

        db.session.add_all([self.s1, self.s2, self.s3])
        db.session.flush()

        # Inscriptions pour s2 (6 inscrits Galaxy Corp)
        self.parts_s2 = []
        for i in range(6):
            p = Participant(nom=f"Part S2-{i}", email=f"p2_{i}@test.ma", client=self.client_corp)
            db.session.add(p)
            db.session.flush()
            self.parts_s2.append(p)
            db.session.add(Inscription(session=self.s2, participant=p, statut="confirmee"))

        # Inscriptions pour s3 (9 inscrits Galaxy Corp)
        self.parts_s3 = []
        for i in range(9):
            p = Participant(nom=f"Part S3-{i}", email=f"p3_{i}@test.ma", client=self.client_corp)
            db.session.add(p)
            db.session.flush()
            self.parts_s3.append(p)
            db.session.add(Inscription(session=self.s3, participant=p, statut="confirmee"))

        # Participant client_other inscrit à s3 avec statut "annulee"
        self.part_other = Participant(nom="Part Alpha", email="alpha@finance.ma", client=self.client_other)
        db.session.add(self.part_other)
        db.session.flush()
        db.session.add(Inscription(session=self.s3, participant=self.part_other, statut="annulee"))

        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter(self, utilisateur):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(utilisateur.id)
            session["_fresh"] = True

    def test_filtres_combines_and(self):
        self.connecter(self.admin)

        # 1. Filtre par domaine + statut (Web + planifiee) -> s1 uniquement
        res1 = self.client.get(f"/api/sessions?domaine_id={self.domaine_web.id}&statut=planifiee").get_json()
        self.assertEqual([s["id"] for s in res1], [self.s1.id])

        # 2. Filtre par type + lieu (q="Rabat" + inter) -> s2 uniquement
        res2 = self.client.get("/api/sessions?q=Rabat&type=inter").get_json()
        self.assertEqual([s["id"] for s in res2], [self.s2.id])

        # 3. Filtre combiné à résultat vide (Web + Cyber -> impossible car AND)
        res3 = self.client.get(f"/api/sessions?domaine_id={self.domaine_web.id}&formation_id={self.formation_cyber.id}").get_json()
        self.assertEqual(res3, [])

    def test_interface_sessions_expose_tous_les_controles_backend(self):
        self.connecter(self.admin)
        page = self.client.get("/sessions")
        self.assertEqual(page.status_code, 200)
        contenu = page.data.decode("utf-8")
        for critere in (
            "filtres.q",
            "filtres.date_debut_min",
            "filtres.date_debut_max",
            "filtres.domaine_id",
            "filtres.formation_id",
            "filtres.type",
            "filtres.statut",
            "filtres.formateur_id",
            "filtres.remplissage",
        ):
            self.assertIn(critere, contenu)
        self.assertIn("appliquerFiltres()", contenu)
        self.assertIn("reinitialiserFiltres()", contenu)

    def test_filtre_remplissage_categories(self):
        self.connecter(self.admin)

        # sous_remplie (<50%) -> s1 (0%)
        res_sous = self.client.get("/api/sessions?remplissage=sous_remplie").get_json()
        self.assertEqual([s["id"] for s in res_sous], [self.s1.id])

        # nominale (50-89%) -> s2 (60%)
        res_nom = self.client.get("/api/sessions?remplissage=nominale").get_json()
        self.assertEqual([s["id"] for s in res_nom], [self.s2.id])

        # complete (>=90%) -> s3 (90%)
        res_comp = self.client.get("/api/sessions?remplissage=complete").get_json()
        self.assertEqual([s["id"] for s in res_comp], [self.s3.id])

    def test_formateur_filtre_ne_contourne_pas_l_isolation(self):
        # Formateur 1 tente d'exécuter un filtre demandant formateur_id = Formateur 2
        self.client = self.app.test_client()
        self.connecter(self.user_formateur_1)

        res = self.client.get(f"/api/sessions?formateur_id={self.formateur_2.id}").get_json()
        # Doit retourner [] et non les sessions du Formateur 2 !
        self.assertEqual(res, [])

    def test_filtres_dashboard_globaux(self):
        self.connecter(self.admin)

        # KPI sans filtre
        kpi_tous = self.client.get("/api/stats/kpi-globaux").get_json()
        self.assertEqual(kpi_tous["sessions_actives"], 3)
        self.assertEqual(kpi_tous["formations_catalogue"], 2)

        # KPI filtrés par domaine Cybersécurité
        kpi_cyber = self.client.get(f"/api/stats/kpi-globaux?domaine_id={self.domaine_cyber.id}").get_json()
        self.assertEqual(kpi_cyber["sessions_actives"], 1)
        self.assertEqual(kpi_cyber["formations_catalogue"], 1)
        self.assertEqual(kpi_cyber["formateurs_mobilises"], 1)

    def test_filtres_entites_clients_et_participants(self):
        self.connecter(self.admin)

        # Filtre client par secteur
        res_clients_sec = self.client.get("/api/clients?secteur=Finance").get_json()
        self.assertEqual([c["id"] for c in res_clients_sec], [self.client_other.id])

        # Filtre participant par q (recherche textuelle)
        res_parts_q = self.client.get("/api/participants?q=Part S2-0").get_json()
        self.assertEqual(len(res_parts_q), 1)
        self.assertEqual(res_parts_q[0]["nom"], "Part S2-0")

    def test_filtres_formations_et_formateurs_sont_sql_et_combinables(self):
        self.connecter(self.admin)

        formations = self.client.get(
            f"/api/formations?domaine_id={self.domaine_web.id}&q=Python"
        ).get_json()
        self.assertEqual([formation["id"] for formation in formations], [self.formation_web.id])

        formateurs = self.client.get(
            f"/api/formateurs?domaine_id={self.domaine_cyber.id}&q=Deux"
        ).get_json()
        self.assertEqual([formateur["id"] for formateur in formateurs], [self.formateur_2.id])

        vide = self.client.get(
            f"/api/formations?domaine_id={self.domaine_web.id}&q=Reseau"
        )
        self.assertEqual(vide.status_code, 200)
        self.assertEqual(vide.get_json(), [])

        invalide = self.client.get("/api/formateurs?domaine_id=abc")
        self.assertEqual(invalide.status_code, 400)

    def test_formateurs_filtre_type_interne_externe_et_combinaisons(self):
        self.connecter(self.admin)

        # 1. Filtre par type = interne (doit retourner formateur_1 et formateur_2)
        res_interne = self.client.get("/api/formateurs?type=interne").get_json()
        ids_interne = {f["id"] for f in res_interne}
        self.assertIn(self.formateur_1.id, ids_interne)
        self.assertIn(self.formateur_2.id, ids_interne)
        self.assertNotIn(self.formateur_externe.id, ids_interne)

        # 2. Filtre par type = externe (doit retourner formateur_externe uniquement)
        res_externe = self.client.get("/api/formateurs?type=externe").get_json()
        self.assertEqual([f["id"] for f in res_externe], [self.formateur_externe.id])

        # 3. Combinaison domaine + type + q
        res_combo = self.client.get(
            f"/api/formateurs?domaine_id={self.domaine_web.id}&type=externe&q=Externe"
        ).get_json()
        self.assertEqual([f["id"] for f in res_combo], [self.formateur_externe.id])

        # 4. Combinaison vide (Cyber + externe -> aucun résultat car formateur_externe est Web)
        res_vide = self.client.get(
            f"/api/formateurs?domaine_id={self.domaine_cyber.id}&type=externe"
        ).get_json()
        self.assertEqual(res_vide, [])

        # 5. Type invalide -> 400
        res_bad = self.client.get("/api/formateurs?type=autre")
        self.assertEqual(res_bad.status_code, 400)

    def test_inscriptions_combinaison_formation_et_session_valide(self):
        self.connecter(self.admin)
        # Formation Web + Session 3 (s3 appartient bien à Formation Web)
        res = self.client.get(
            f"/api/inscriptions?formation_id={self.formation_web.id}&session_id={self.s3.id}"
        )
        self.assertEqual(res.status_code, 200)
        inscriptions = res.get_json()
        self.assertEqual(len(inscriptions), 10)  # 9 confirmee Galaxy Corp + 1 annulee Alpha
        self.assertTrue(all(i["session"]["id"] == self.s3.id for i in inscriptions))
        self.assertTrue(all(i["session"]["formation"]["id"] == self.formation_web.id for i in inscriptions))

    def test_inscriptions_combinaison_formation_et_session_incoherente(self):
        self.connecter(self.admin)
        # Formation Web + Session 2 (s2 appartient à Cyber, pas à Web)
        res = self.client.get(
            f"/api/inscriptions?formation_id={self.formation_web.id}&session_id={self.s2.id}"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), [])

    def test_inscriptions_combinaison_client_et_participant_valide(self):
        self.connecter(self.admin)
        # Client Alpha Finance + Participant Alpha
        res = self.client.get(
            f"/api/inscriptions?client_id={self.client_other.id}&participant_id={self.part_other.id}"
        )
        self.assertEqual(res.status_code, 200)
        inscriptions = res.get_json()
        self.assertEqual(len(inscriptions), 1)
        self.assertEqual(inscriptions[0]["participant"]["id"], self.part_other.id)
        self.assertEqual(inscriptions[0]["participant"]["client"]["id"], self.client_other.id)

    def test_inscriptions_combinaison_client_et_participant_incoherente(self):
        self.connecter(self.admin)
        # Client Alpha Finance + Participant de Galaxy Corp
        part_corp = self.parts_s2[0]
        res = self.client.get(
            f"/api/inscriptions?client_id={self.client_other.id}&participant_id={part_corp.id}"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), [])

    def test_inscriptions_combinaison_statut_et_formation(self):
        self.connecter(self.admin)
        # Statut annulee + Formation Web -> uniquement part_other sur s3
        res_annulee = self.client.get(
            f"/api/inscriptions?statut=annulee&formation_id={self.formation_web.id}"
        ).get_json()
        self.assertEqual(len(res_annulee), 1)
        self.assertEqual(res_annulee[0]["participant"]["id"], self.part_other.id)

        # Statut confirmee + Formation Web -> 9 inscriptions
        res_confirmee = self.client.get(
            f"/api/inscriptions?statut=confirmee&formation_id={self.formation_web.id}"
        ).get_json()
        self.assertEqual(len(res_confirmee), 9)

        # Statut liste_attente + Formation Web -> 0
        res_attente = self.client.get(
            f"/api/inscriptions?statut=liste_attente&formation_id={self.formation_web.id}"
        ).get_json()
        self.assertEqual(res_attente, [])

    def test_inscriptions_combinaison_periode_et_session(self):
        self.connecter(self.admin)
        today = date.today()
        debut_min = (today - timedelta(days=25)).isoformat()
        debut_max = (today - timedelta(days=15)).isoformat()

        # Plage couvrant s3 (-20 jours) + Session s3 -> retourne 10 inscriptions
        res = self.client.get(
            f"/api/inscriptions?date_debut_min={debut_min}&date_debut_max={debut_max}&session_id={self.s3.id}"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.get_json()), 10)

        # Plage couvrant s3 mais demandant session s2 -> 0 inscriptions
        res_incoherent = self.client.get(
            f"/api/inscriptions?date_debut_min={debut_min}&date_debut_max={debut_max}&session_id={self.s2.id}"
        )
        self.assertEqual(res_incoherent.status_code, 200)
        self.assertEqual(res_incoherent.get_json(), [])

    def test_rbac_formateur_isole_completement_inscriptions_et_referentiels(self):
        self.client = self.app.test_client()
        connexion = self.client.post(
            "/api/auth/login",
            json={"email": "f1@test.ma", "mot_de_passe": "Secret123"},
        )
        self.assertEqual(connexion.status_code, 200)

        # Formateur 1 ne voit que ses formations (Python Web), ses formateurs (lui-même), et ses inscriptions
        formations = self.client.get("/api/formations").get_json()
        self.assertEqual([f["id"] for f in formations], [self.formation_web.id])

        formateurs = self.client.get("/api/formateurs").get_json()
        self.assertEqual([f["id"] for f in formateurs], [self.formateur_1.id])

        # Requête pour session de Formateur 2 -> 0 résultats
        inscriptions_s2 = self.client.get(f"/api/inscriptions?session_id={self.s2.id}").get_json()
        self.assertEqual(inscriptions_s2, [])

        # Requête pour formation Cyber -> 0 résultats
        inscriptions_cyber = self.client.get(
            f"/api/inscriptions?formation_id={self.formation_cyber.id}"
        ).get_json()
        self.assertEqual(inscriptions_cyber, [])

        # Requête légitime pour formation Web -> ses inscriptions visibles (10 sur s3)
        inscriptions_web = self.client.get(
            f"/api/inscriptions?formation_id={self.formation_web.id}"
        ).get_json()
        self.assertEqual(len(inscriptions_web), 10)

    def test_interfaces_formations_formateurs_inscriptions_exposent_filtres(self):
        self.connecter(self.admin)

        # Page Formations
        page_formations = self.client.get("/formations")
        self.assertEqual(page_formations.status_code, 200)
        contenu_f = page_formations.data.decode("utf-8")
        self.assertIn("filtres.q", contenu_f)
        self.assertIn("filtres.domaine_id", contenu_f)
        self.assertIn("reinitialiserFiltres()", contenu_f)

        # Page Formateurs
        page_formateurs = self.client.get("/formateurs")
        self.assertEqual(page_formateurs.status_code, 200)
        contenu_fmt = page_formateurs.data.decode("utf-8")
        self.assertIn("filtres.q", contenu_fmt)
        self.assertIn("filtres.domaine_id", contenu_fmt)
        self.assertIn("filtres.type", contenu_fmt)
        self.assertIn("reinitialiserFiltres()", contenu_fmt)

        # Page Inscriptions
        page_inscriptions = self.client.get("/inscriptions")
        self.assertEqual(page_inscriptions.status_code, 200)
        contenu_i = page_inscriptions.data.decode("utf-8")
        self.assertIn("filtres.formation_id", contenu_i)
        self.assertIn("filtres.session_id", contenu_i)
        self.assertIn("filtres.client_id", contenu_i)
        self.assertIn("filtres.participant_id", contenu_i)
        self.assertIn("filtres.statut", contenu_i)
        self.assertIn("reinitialiserFiltres()", contenu_i)
    def test_url_deep_linking_and_restauration_filtres(self):
        self.connecter(self.admin)

        # Simulation d'un lien partagé / rechargement F5 vers Sessions
        res_sessions = self.client.get(
            f"/api/sessions?domaine_id={self.domaine_web.id}&statut=planifiee"
        )
        self.assertEqual(res_sessions.status_code, 200)
        self.assertEqual([s["id"] for s in res_sessions.get_json()], [self.s1.id])

        # Simulation d'un lien partagé vers Formateurs
        res_formateurs = self.client.get(
            f"/api/formateurs?domaine_id={self.domaine_web.id}&type=externe"
        )
        self.assertEqual(res_formateurs.status_code, 200)
        self.assertEqual([f["id"] for f in res_formateurs.get_json()], [self.formateur_externe.id])

        # Simulation d'un lien partagé vers Formations
        res_formations = self.client.get(
            f"/api/formations?domaine_id={self.domaine_web.id}&q=Python"
        )
        self.assertEqual(res_formations.status_code, 200)
        self.assertEqual([f["id"] for f in res_formations.get_json()], [self.formation_web.id])

        # Simulation d'un lien partagé vers Inscriptions
        res_inscriptions = self.client.get(
            f"/api/inscriptions?formation_id={self.formation_web.id}&statut=annulee"
        )
        self.assertEqual(res_inscriptions.status_code, 200)
        self.assertEqual(len(res_inscriptions.get_json()), 1)
        self.assertEqual(res_inscriptions.get_json()[0]["participant"]["id"], self.part_other.id)

    def test_url_manipulation_manuelle_formateur_isole(self):
        # Un utilisateur formateur tente de modifier les paramètres d'URL pour voir des entités hors scope
        self.client = self.app.test_client()
        connexion = self.client.post(
            "/api/auth/login",
            json={"email": "f1@test.ma", "mot_de_passe": "Secret123"},
        )
        self.assertEqual(connexion.status_code, 200)

        # Tentative d'accéder aux sessions du formateur 2 via URL
        res_sessions = self.client.get(f"/api/sessions?formateur_id={self.formateur_2.id}").get_json()
        self.assertEqual(res_sessions, [])

        # Tentative d'accéder aux inscriptions de la formation Cyber via URL
        res_inscriptions = self.client.get(f"/api/inscriptions?formation_id={self.formation_cyber.id}").get_json()
        self.assertEqual(res_inscriptions, [])

    def test_scripts_contiennent_popstate_et_synchro_url(self):
        import os
        base_dir = self.app.root_path
        fichiers_js = ["formations.js", "formateurs.js", "sessions.js", "inscriptions.js", "clients.js", "participants.js"]

        for nom in fichiers_js:
            chemin = os.path.join(base_dir, "static", "js", nom)
            self.assertTrue(os.path.exists(chemin), f"Fichier {nom} introuvable")
            with open(chemin, "r", encoding="utf-8") as f:
                code = f.read()
                self.assertIn("popstate", code, f"{nom} ne gère pas popstate")
                self.assertIn("lireFiltresDepuisUrl", code, f"{nom} ne contient pas lireFiltresDepuisUrl")
                self.assertIn("synchroniserUrlNavigateur", code, f"{nom} ne contient pas synchroniserUrlNavigateur")

    def test_clients_filtres_combines_et_statut_activite_metier(self):
        self.connecter(self.admin)

        # 1. Filtre par recherche textuelle q (sur nom ou contact_email)
        res_q = self.client.get("/api/clients?q=Galaxy").get_json()
        self.assertEqual([c["id"] for c in res_q], [self.client_corp.id])

        # 2. Filtre par secteur
        res_secteur = self.client.get("/api/clients?secteur=Technologies").get_json()
        self.assertEqual([c["id"] for c in res_secteur], [self.client_corp.id])

        # 3. Filtre par statut d'activité calculé par client_activity_service
        res_actif = self.client.get("/api/clients?statut_activite=actif").get_json()
        self.assertIsInstance(res_actif, list)
        for c in res_actif:
            self.assertEqual(c["statut_activite"], "actif")

        # 4. Statut d'activité invalide -> 400
        res_bad_statut = self.client.get("/api/clients?statut_activite=inconnu")
        self.assertEqual(res_bad_statut.status_code, 400)

        # 5. Combinaison q + secteur + statut_activite
        res_combo = self.client.get(
            "/api/clients?q=Alpha&secteur=Finance&statut_activite=inactif"
        ).get_json()
        self.assertIsInstance(res_combo, list)

    def test_participants_filtres_combines_et_rejets(self):
        self.connecter(self.admin)

        # 1. Filtre par recherche textuelle q
        res_q = self.client.get("/api/participants?q=Part S2-0").get_json()
        self.assertTrue(len(res_q) >= 1)
        self.assertIn("Part S2-0", [p["nom"] for p in res_q])

        # 2. Filtre par client_id valide
        res_client = self.client.get(f"/api/participants?client_id={self.client_other.id}").get_json()
        self.assertEqual([p["id"] for p in res_client], [self.part_other.id])

        # 3. Client inexistant -> liste vide []
        res_empty = self.client.get("/api/participants?client_id=99999").get_json()
        self.assertEqual(res_empty, [])

        # 4. client_id invalide -> 400
        res_bad = self.client.get("/api/participants?client_id=abc")
        self.assertEqual(res_bad.status_code, 400)

        # 5. Combinaison q + client_id
        res_combo = self.client.get(f"/api/participants?client_id={self.client_other.id}&q=Alpha").get_json()
        self.assertEqual([p["id"] for p in res_combo], [self.part_other.id])

    def test_rbac_formateur_isole_clients_et_participants(self):
        # Connexion Formateur 2 (associé à session 2)
        self.client = self.app.test_client()
        connexion = self.client.post(
            "/api/auth/login",
            json={"email": "f2@test.ma", "mot_de_passe": "Secret123"},
        )
        self.assertEqual(connexion.status_code, 200)

        # Formateur 2 ne doit voir que les clients et participants associés à ses sessions (s2 -> parts_s2 sur client_corp)
        clients = self.client.get("/api/clients").get_json()
        self.assertEqual([c["id"] for c in clients], [self.client_corp.id])

        # Tentative d'accès aux participants du client_other via client_id parameter -> 0 résultat (RBAC préservé)
        res_parts = self.client.get(f"/api/participants?client_id={self.client_other.id}").get_json()
        self.assertEqual(res_parts, [])

    def test_interfaces_clients_et_participants_exposent_filtres(self):
        self.connecter(self.admin)

        # Page Clients
        page_clients = self.client.get("/clients")
        self.assertEqual(page_clients.status_code, 200)
        contenu_c = page_clients.data.decode("utf-8")
        self.assertIn("filtres.q", contenu_c)
        self.assertIn("filtres.secteur", contenu_c)
        self.assertIn("filtres.statut_activite", contenu_c)
        self.assertIn("reinitialiserFiltres()", contenu_c)

        # Page Participants
        page_parts = self.client.get("/participants")
        self.assertEqual(page_parts.status_code, 200)
        contenu_p = page_parts.data.decode("utf-8")
        self.assertIn("filtres.q", contenu_p)
        self.assertIn("filtres.client_id", contenu_p)
        self.assertIn("reinitialiserFiltres()", contenu_p)


if __name__ == "__main__":
    unittest.main()

