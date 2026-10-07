"""
==============================================================================
Script d'Initialisation & Peuplement de la Base de Données (Production / Cloud)
==============================================================================
Usage :
    python init_db.py [--seed]

Architecture :
    1. Base : Connexion brute PyMySQL pour créer le schéma si absent.
    2. DDL : Si --seed, réinitialisation ordonnée (drop_all -> create_all).
    3. DML : Insertion transactionnelle du seed avec contraintes FK actives (=1).
    4. Rebasage TiDB : ALTER TABLE <table> AUTO_INCREMENT = 0 (bloquant).
    5. Test post-rebasage : Insertion implicite sans ID pour valider que id > MAX(seed).
    6. Audit final : Comptages, plages d'IDs, unicité réelle, 9 FKs, admin.
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()


# =============================================================================
# ÉTAPE PRÉLIMINAIRE : Créer la base si absente (connexion directe sans base)
# =============================================================================
def creer_base_si_absente():
    """Connexion PyMySQL sans base pour créer le schéma si inexistant."""
    import pymysql

    db_host = os.environ.get("DB_HOST", "localhost")
    db_port = int(os.environ.get("DB_PORT", "3306"))
    db_user = os.environ.get("DB_USER", "root")
    db_password = os.environ.get("DB_PASSWORD", "")
    db_name = os.environ.get("DB_NAME", "galaxy_solutions")
    db_use_ssl = os.environ.get("DB_USE_SSL", "false").lower() in ("true", "1", "yes")

    ssl_opts = None
    if db_use_ssl:
        ssl_opts = {}
        try:
            import certifi
            ssl_opts["ca"] = certifi.where()
        except ImportError:
            for ca_path in [
                "/etc/ssl/certs/ca-certificates.crt",
                "/etc/pki/tls/certs/ca-bundle.crt",
            ]:
                if os.path.exists(ca_path):
                    ssl_opts["ca"] = ca_path
                    break

    try:
        print(f">>> Connexion à TiDB ({db_host}:{db_port}) sans base de données...")
        conn_args = {
            "host": db_host,
            "port": db_port,
            "user": db_user,
            "password": db_password,
            "connect_timeout": 10,
        }
        if ssl_opts is not None:
            conn_args["ssl"] = ssl_opts

        conn = pymysql.connect(**conn_args)
        with conn.cursor() as cursor:
            sql = f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            cursor.execute(sql)
            conn.commit()
        conn.close()
        print(f"    [OK] Base de données `{db_name}` prête.")
        return True
    except Exception as e:
        print(f"    [ERREUR] Impossible de créer la base : {e}")
        return False


# =============================================================================
# PARSER SQL ROBUSTE (gère les commentaires -- et les ; dans les chaînes)
# =============================================================================
def decouper_instructions_sql(sql_texte):
    """
    Supprime les commentaires SQL en ligne (--) hors des chaînes de caractères
    et découpe les requêtes par point-virgule (;) sans couper à l'intérieur
    des chaînes '...' ou "...".
    """
    instructions = []
    current_stmt = []
    in_single_quote = False
    in_double_quote = False
    i = 0
    n = len(sql_texte)

    while i < n:
        char = sql_texte[i]

        # Détection et saut des commentaires mono-ligne "-- " hors des chaînes
        if not in_single_quote and not in_double_quote and char == '-' and i + 1 < n and sql_texte[i + 1] == '-':
            while i < n and sql_texte[i] != '\n':
                i += 1
            continue

        # Gestion des guillemets simples
        if char == "'" and not in_double_quote:
            if i > 0 and sql_texte[i - 1] == '\\':
                pass
            else:
                in_single_quote = not in_single_quote
            current_stmt.append(char)
            i += 1
            continue

        # Gestion des guillemets doubles
        if char == '"' and not in_single_quote:
            if i > 0 and sql_texte[i - 1] == '\\':
                pass
            else:
                in_double_quote = not in_double_quote
            current_stmt.append(char)
            i += 1
            continue

        # Découpage par point-virgule UNIQUEMENT hors des chaînes
        if char == ';' and not in_single_quote and not in_double_quote:
            stmt = "".join(current_stmt).strip()
            if stmt:
                instructions.append(stmt)
            current_stmt = []
            i += 1
            continue

        current_stmt.append(char)
        i += 1

    reste = "".join(current_stmt).strip()
    if reste:
        instructions.append(reste)

    return instructions


# =============================================================================
# INITIALISATION ET PEUPLEMENT
# =============================================================================
def initialiser_base():
    from app import create_app
    from app.extensions import db
    from app.models import Role, Utilisateur
    from sqlalchemy import text

    app = create_app()

    with app.app_context():
        avec_seed = "--seed" in sys.argv

        # ---------------------------------------------------------------------
        # 1. PHASE DDL (STRUCTURE DES TABLES)
        # ---------------------------------------------------------------------
        if avec_seed:
            print("\n>>> Réinitialisation ordonnée du schéma (--seed demandé)...")
            try:
                # SQLAlchemy supprime dans l'ordre inverse topologique des FK
                db.drop_all()
                print("    [OK] Tables existantes supprimées dans l'ordre inverse des FK.")
                # Puis recrée dans l'ordre topologique direct des FK
                db.create_all()
                print("    [OK] Tables recréées à neuf avec compteurs réinitialisés.")
            except Exception as e:
                print(f"❌ [ERREUR DDL] Échec de réinitialisation du schéma : {e}")
                sys.exit(1)
        else:
            print("\n>>> Vérification / Création des tables (mode sans --seed)...")
            db.create_all()
            print("    [OK] Schéma en place.")

            # Rôles initiaux a minima si la table est vide
            if not Role.query.first():
                print(">>> Insertion des rôles de base...")
                r_admin = Role(nom="admin")
                r_gest = Role(nom="gestionnaire")
                r_form = Role(nom="formateur")
                db.session.add_all([r_admin, r_gest, r_form])
                db.session.commit()
                print("    [OK] Rôles créés.")
            else:
                print("    [INFO] Rôles déjà présents.")

        # ---------------------------------------------------------------------
        # 2. PHASE DML (PEUPLEMENT TRANSACTIONNEL DU SEED)
        # ---------------------------------------------------------------------
        if avec_seed:
            seed_file = os.path.join(os.path.dirname(__file__), "database", "seed_demo_data.sql")
            if not os.path.exists(seed_file):
                print(f"❌ [ERREUR] Fichier introuvable : {seed_file}")
                sys.exit(1)

            print(f">>> Lecture et parsing de {seed_file}...")
            with open(seed_file, "r", encoding="utf-8") as f:
                sql_brut = f.read()

            instructions_brutes = decouper_instructions_sql(sql_brut)

            # Les tables étant neuves, on retire les directives superflues.
            # FOREIGN_KEY_CHECKS reste actif (= 1) pour contrôler chaque insertion.
            instructions_a_executer = []
            for stmt in instructions_brutes:
                u = stmt.upper().strip()
                if u.startswith("USE "):
                    continue
                if "FOREIGN_KEY_CHECKS" in u:
                    continue
                if u.startswith("TRUNCATE") or u.startswith("DELETE FROM"):
                    continue
                instructions_a_executer.append(stmt)

            print(f"    [INFO] {len(instructions_a_executer)} requêtes INSERT prêtes à être exécutées.")

            print(">>> Exécution transactionnelle du seed (avec contrôles FK actifs)...")
            try:
                with db.engine.begin() as conn:
                    for idx, stmt in enumerate(instructions_a_executer, 1):
                        try:
                            conn.execute(text(stmt))
                        except Exception as err:
                            print(f"\n❌ [ERREUR DML] Échec à l'instruction #{idx} :")
                            print("--------------------------------------------------")
                            print(stmt[:400] + ("..." if len(stmt) > 400 else ""))
                            print("--------------------------------------------------")
                            print(f"Détail : {err}\n")
                            raise err

                print("    [OK] Transaction validée (COMMIT global réussi sans violation de contrainte).")

            except Exception:
                print("❌ [ROLLBACK] Transaction annulée. Aucune donnée partielle n'a été conservée.")
                sys.exit(1)

            # -----------------------------------------------------------------
            # 3. REBASAGE AUTO_INCREMENT (Spécifique TiDB Cloud - BLOQUANT)
            # Rebase les allocateurs TiDB (ALTER TABLE <table> AUTO_INCREMENT = 0)
            # pour purger les caches d'IDs distribués.
            # -----------------------------------------------------------------
            print("\n>>> Rebasage des compteurs AUTO_INCREMENT TiDB...")
            tables_rebasage = [
                "Role",
                "Domaine",
                "Utilisateur",
                "Formateur",
                "Formation",
                "Client",
                "Participant",
                "Session"
            ]
            with db.engine.connect() as conn:
                for tbl in tables_rebasage:
                    try:
                        conn.execute(text(f"ALTER TABLE `{tbl}` AUTO_INCREMENT = 0;"))
                        conn.commit()
                        print(f"  [OK] AUTO_INCREMENT {tbl.ljust(15)} : cache rebasé")
                    except Exception as e:
                        print(f"\n❌ [ERREUR CRITIQUE] Échec du rebasage AUTO_INCREMENT pour `{tbl}` : {e}")
                        sys.exit(1)

            # -----------------------------------------------------------------
            # 4. TEST DU COMPORTEMENT POST-REBASAGE (Test automatique sans déchet)
            # Vérifie qu'une insertion implicite génère un ID > MAX(seed)
            # -----------------------------------------------------------------
            print("\n>>> Test du comportement de l'allocateur post-rebasage...")
            with db.engine.begin() as conn:
                max_role_seed = conn.execute(text("SELECT MAX(id) FROM `Role`")).scalar()
                # Insertion de test sans spécifier de colonne 'id'
                conn.execute(text("INSERT INTO `Role` (nom) VALUES ('_test_allocateur_temp_')"))
                nouveau_role_id = conn.execute(text("SELECT id FROM `Role` WHERE nom = '_test_allocateur_temp_'")).scalar()
                # Suppression immédiate du rôle de test
                conn.execute(text("DELETE FROM `Role` WHERE nom = '_test_allocateur_temp_'"))

                if nouveau_role_id and nouveau_role_id > max_role_seed:
                    print(f"  [OK] Test allocateur : ID auto-généré ({nouveau_role_id}) > MAX du seed ({max_role_seed}). Aucune collision.")
                else:
                    print(f"  ❌ [ÉCHEC CRITIQUE] L'allocateur a généré l'ID {nouveau_role_id} <= MAX du seed ({max_role_seed}) !")
                    sys.exit(1)

        # ---------------------------------------------------------------------
        # 5. PHASE AUDIT & CONTRÔLES D'INTÉGRITÉ STRICTS
        # ---------------------------------------------------------------------
        print("\n================ VÉRIFICATION DES TABLES & PLAGES D'IDS ================")
        attentes_tables = [
            ("Role", 3, 1, 3),
            ("Domaine", 3, 1, 3),
            ("Utilisateur", 6, 1, 6),
            ("Formateur", 10, 1, 10),
            ("Formation", 12, 1, 12),
            ("Client", 30, 1, 30),
            ("Participant", 150, 1, 150),
            ("Session", 60, 1, 60),
            ("Inscription", 536, None, None),
        ]

        erreurs_detectees = 0

        with db.engine.connect() as conn:
            for tbl, exp_cnt, exp_min, exp_max in attentes_tables:
                row = conn.execute(text(f"SELECT COUNT(*), MIN(id), MAX(id) FROM `{tbl}`")).fetchone()
                cnt, min_id, max_id = row[0], row[1], row[2]

                cnt_ok = (cnt == exp_cnt) if avec_seed else (cnt >= exp_cnt if tbl == "Role" else True)
                min_ok = (min_id == exp_min) if (avec_seed and exp_min is not None) else True
                max_ok = (max_id == exp_max) if (avec_seed and exp_max is not None) else True

                if cnt_ok and min_ok and max_ok:
                    plage_str = f"IDs [{min_id}..{max_id}]" if min_id is not None else "IDs auto"
                    print(f"  [OK] {tbl.ljust(15)} : COUNT={cnt} | {plage_str}")
                else:
                    print(f"  ❌ [ÉCHEC] {tbl.ljust(15)} : COUNT={cnt} (attendu {exp_cnt}) | MIN={min_id} (attendu {exp_min}) | MAX={max_id} (attendu {exp_max})")
                    erreurs_detectees += 1

            # -----------------------------------------------------------------
            # Vérification de l'absence de doublons (contraintes UNIQUE réelles)
            # -----------------------------------------------------------------
            print("\n>>> Vérification de l'absence de doublons (contraintes UNIQUE réelles)...")
            controles_unicite = [
                ("Role.nom", "SELECT nom, COUNT(*) c FROM Role GROUP BY nom HAVING c > 1"),
                ("Domaine.nom", "SELECT nom, COUNT(*) c FROM Domaine GROUP BY nom HAVING c > 1"),
                ("Utilisateur.email", "SELECT email, COUNT(*) c FROM Utilisateur GROUP BY email HAVING c > 1"),
                ("Client.nom_entreprise", "SELECT nom_entreprise, COUNT(*) c FROM Client GROUP BY nom_entreprise HAVING c > 1"),
                ("Participant.email", "SELECT email, COUNT(*) c FROM Participant GROUP BY email HAVING c > 1"),
                ("Formateur.utilisateur_id", "SELECT utilisateur_id, COUNT(*) c FROM Formateur WHERE utilisateur_id IS NOT NULL GROUP BY utilisateur_id HAVING c > 1"),
                ("Inscription (session_id, participant_id)", "SELECT session_id, participant_id, COUNT(*) c FROM Inscription GROUP BY session_id, participant_id HAVING c > 1"),
            ]
            for libelle, sql_u in controles_unicite:
                doublons = conn.execute(text(sql_u)).fetchall()
                if not doublons:
                    print(f"  [OK] Unicité {libelle} : respectée")
                else:
                    print(f"  ❌ [ÉCHEC] Doublons sur {libelle} : {doublons}")
                    erreurs_detectees += 1

            # -----------------------------------------------------------------
            # Vérification des 9 clés étrangères
            # -----------------------------------------------------------------
            print("\n>>> Vérification de l'intégrité des clés étrangères...")
            controles_fk = [
                ("Utilisateur.role_id -> Role.id",
                 "SELECT COUNT(*) FROM Utilisateur u LEFT JOIN Role r ON u.role_id = r.id WHERE r.id IS NULL"),
                ("Formateur.domaine_id -> Domaine.id",
                 "SELECT COUNT(*) FROM Formateur f LEFT JOIN Domaine d ON f.domaine_id = d.id WHERE d.id IS NULL"),
                ("Formateur.utilisateur_id -> Utilisateur.id",
                 "SELECT COUNT(*) FROM Formateur f LEFT JOIN Utilisateur u ON f.utilisateur_id = u.id WHERE f.utilisateur_id IS NOT NULL AND u.id IS NULL"),
                ("Formation.domaine_id -> Domaine.id",
                 "SELECT COUNT(*) FROM Formation f LEFT JOIN Domaine d ON f.domaine_id = d.id WHERE d.id IS NULL"),
                ("Participant.client_id -> Client.id",
                 "SELECT COUNT(*) FROM Participant p LEFT JOIN Client c ON p.client_id = c.id WHERE c.id IS NULL"),
                ("Session.formation_id -> Formation.id",
                 "SELECT COUNT(*) FROM Session s LEFT JOIN Formation f ON s.formation_id = f.id WHERE f.id IS NULL"),
                ("Session.formateur_id -> Formateur.id",
                 "SELECT COUNT(*) FROM Session s LEFT JOIN Formateur f ON s.formateur_id = f.id WHERE f.id IS NULL"),
                ("Inscription.session_id -> Session.id",
                 "SELECT COUNT(*) FROM Inscription i LEFT JOIN Session s ON i.session_id = s.id WHERE s.id IS NULL"),
                ("Inscription.participant_id -> Participant.id",
                 "SELECT COUNT(*) FROM Inscription i LEFT JOIN Participant p ON i.participant_id = p.id WHERE p.id IS NULL"),
            ]
            for libelle, sql_fk in controles_fk:
                orphelins = conn.execute(text(sql_fk)).scalar()
                if orphelins == 0:
                    print(f"  [OK] {libelle} : 0 orphelin")
                else:
                    print(f"  ❌ [ÉCHEC] {libelle} : {orphelins} orphelin(s) !")
                    erreurs_detectees += 1

        # -----------------------------------------------------------------
        # Vérification du compte administrateur
        # -----------------------------------------------------------------
        print("\n>>> Vérification de l'administrateur...")
        admin = Utilisateur.query.filter_by(email="admin@galaxysolutions.ma").first()
        if not admin:
            print("  ❌ [ÉCHEC] Compte admin@galaxysolutions.ma introuvable !")
            erreurs_detectees += 1
        elif not admin.role:
            print("  ❌ [ÉCHEC] Le compte admin n'a AUCUN rôle associé (admin.role is None) !")
            erreurs_detectees += 1
        elif admin.role.nom != "admin":
            print(f"  ❌ [ÉCHEC] Le rôle associé est '{admin.role.nom}' au lieu de 'admin' !")
            erreurs_detectees += 1
        elif not admin.actif:
            print("  ❌ [ÉCHEC] Le compte admin n'est pas actif !")
            erreurs_detectees += 1
        else:
            print(f"  [OK] Administrateur valide : {admin.nom} (id={admin.id}, role={admin.role.nom}, actif={admin.actif})")

        # -----------------------------------------------------------------
        # Bilan final
        # -----------------------------------------------------------------
        if erreurs_detectees > 0:
            print(f"\n❌ ARRÊT : {erreurs_detectees} test(s) de cohérence ont échoué.\n")
            sys.exit(1)
        else:
            print("\n>>> Initialisation & validation terminées avec succès (100% cohérent) !\n")


if __name__ == "__main__":
    if creer_base_si_absente():
        initialiser_base()
    else:
        sys.exit(1)
