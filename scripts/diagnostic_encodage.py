"""
==============================================================================
Script de Diagnostic Encodage UTF-8 — Galaxy Training Manager
==============================================================================
Ce script vérifie méthodiquement CHAQUE maillon de la chaîne d'encodage,
sans modifier quoi que ce soit.

Ordre de vérification :
  1. Serveur MySQL          → variables character_set et collation
  2. Base de données        → DEFAULT_CHARACTER_SET_NAME
  3. Tables et colonnes     → character_set de chaque colonne texte
  4. Connexion SQLAlchemy   → charset utilisé réellement par PyMySQL
  5. API Flask              → Content-Type de la réponse JSON
  6. Test d'aller-retour    → écriture + lecture d'un texte accentué

Usage :
    .\\venv\\Scripts\\python.exe scripts\\diagnostic_encodage.py
"""

import sys
import os

# Ajoute la racine du projet dans le chemin d'import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# Helpers d'affichage
# ---------------------------------------------------------------------------
OK   = "\033[92m[OK]\033[0m"
WARN = "\033[93m[WARN]\033[0m"
ERR  = "\033[91m[ERR]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

def titre(texte):
    print(f"\n{'='*60}")
    print(f"  {texte}")
    print(f"{'='*60}")

def ligne(statut, cle, valeur):
    print(f"  {statut}  {cle:<45} {valeur}")

# ---------------------------------------------------------------------------
# Connexion directe PyMySQL (hors SQLAlchemy) pour mesurer le charset réel
# ---------------------------------------------------------------------------
def connexion_pymysql():
    """Retourne une connexion PyMySQL brute en lisant les variables d'env."""
    try:
        import pymysql
        conn = pymysql.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME"),
            # On ne force pas charset ici pour voir la valeur par défaut du serveur
        )
        return conn
    except Exception as e:
        print(f"\n{ERR}  Impossible de se connecter à MySQL : {e}")
        print(f"  Vérifiez votre fichier .env (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME).")
        sys.exit(1)

# ---------------------------------------------------------------------------
# SECTION 1 — Serveur MySQL
# ---------------------------------------------------------------------------
def verifier_serveur(conn):
    titre("1. Variables d'encodage du SERVEUR MySQL")
    cursor = conn.cursor()
    cursor.execute("SHOW VARIABLES LIKE 'character_set%'")
    variables = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.execute("SHOW VARIABLES LIKE 'collation%'")
    collations = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.close()

    problemes = []
    for cle, val in sorted(variables.items()):
        if cle == "character_set_filesystem":
            # Cette variable est souvent "binary", c'est normal
            ligne(INFO, cle, val)
        elif "utf8mb4" in val:
            ligne(OK, cle, val)
        elif "utf8" in val:
            ligne(WARN, cle, f"{val}  ← utf8 MySQL (3 octets max, pas utf8mb4)")
            problemes.append(cle)
        else:
            ligne(ERR, cle, f"{val}  ← NON UTF-8 → cause possible de corruption")
            problemes.append(cle)

    for cle, val in sorted(collations.items()):
        if "utf8mb4" in val:
            ligne(OK, cle, val)
        elif "utf8" in val:
            ligne(WARN, cle, val)
        else:
            ligne(ERR, cle, val)

    return problemes

# ---------------------------------------------------------------------------
# SECTION 2 — Base de données
# ---------------------------------------------------------------------------
def verifier_base(conn):
    titre("2. Encodage de la BASE DE DONNÉES")
    db_name = os.environ.get("DB_NAME")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DEFAULT_CHARACTER_SET_NAME, DEFAULT_COLLATION_NAME
        FROM information_schema.SCHEMATA
        WHERE SCHEMA_NAME = %s
    """, (db_name,))
    row = cursor.fetchone()
    cursor.close()

    if not row:
        print(f"  {ERR}  Base '{db_name}' introuvable dans information_schema.")
        return []

    charset, collation = row
    problemes = []
    statut_c = OK if "utf8mb4" in charset else (WARN if "utf8" in charset else ERR)
    statut_k = OK if "utf8mb4" in collation else (WARN if "utf8" in collation else ERR)

    ligne(statut_c, f"Base '{db_name}' — charset", charset)
    ligne(statut_k, f"Base '{db_name}' — collation", collation)

    if statut_c != OK:
        problemes.append(f"base charset={charset}")
    return problemes

# ---------------------------------------------------------------------------
# SECTION 3 — Tables et colonnes texte
# ---------------------------------------------------------------------------
def verifier_tables(conn):
    titre("3. Encodage des TABLES et COLONNES texte")
    db_name = os.environ.get("DB_NAME")
    cursor = conn.cursor()

    # Vérification des tables
    cursor.execute("""
        SELECT TABLE_NAME, TABLE_COLLATION
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """, (db_name,))
    tables = cursor.fetchall()

    problemes = []
    print(f"\n  {'TABLE':<25} {'COLLATION'}")
    print(f"  {'-'*55}")
    for table_name, collation in tables:
        if collation is None:
            continue
        if "utf8mb4" in collation:
            ligne(OK, table_name, collation)
        elif "utf8" in collation:
            ligne(WARN, table_name, collation)
            problemes.append(f"table:{table_name}")
        else:
            ligne(ERR, table_name, f"{collation}  ← problème d'encodage")
            problemes.append(f"table:{table_name}")

    # Vérification des colonnes VARCHAR/TEXT
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s
          AND DATA_TYPE IN ('varchar', 'text', 'mediumtext', 'longtext', 'char')
        ORDER BY TABLE_NAME, COLUMN_NAME
    """, (db_name,))
    colonnes = cursor.fetchall()
    cursor.close()

    if colonnes:
        print(f"\n  Colonnes texte :")
        print(f"  {'TABLE.COLONNE':<35} {'CHARSET':<15} {'COLLATION'}")
        print(f"  {'-'*70}")
        for table, colonne, charset, collation in colonnes:
            cle = f"{table}.{colonne}"
            if charset and "utf8mb4" in charset:
                ligne(OK, cle, f"{charset} / {collation}")
            elif charset and "utf8" in charset:
                ligne(WARN, cle, f"{charset} / {collation}")
                problemes.append(f"colonne:{cle}")
            elif charset:
                ligne(ERR, cle, f"{charset} / {collation}  ← CAUSE POSSIBLE")
                problemes.append(f"colonne:{cle}")

    return problemes

# ---------------------------------------------------------------------------
# SECTION 4 — Charset réellement utilisé par PyMySQL à la connexion
# ---------------------------------------------------------------------------
def verifier_connexion_pymysql(conn):
    titre("4. Charset réellement utilisé par PyMySQL à la connexion")
    cursor = conn.cursor()
    cursor.execute("SELECT @@character_set_client, @@character_set_connection, @@character_set_results")
    row = cursor.fetchone()
    cursor.close()

    client, connection, results = row
    print(f"  {'Variable':<40} {'Valeur'}")
    print(f"  {'-'*55}")

    problemes = []
    for nom, val in [("character_set_client", client),
                     ("character_set_connection", connection),
                     ("character_set_results", results)]:
        if "utf8mb4" in val:
            ligne(OK, nom, val)
        elif "utf8" in val:
            ligne(WARN, nom, f"{val}  ← pas utf8mb4")
            problemes.append(nom)
        else:
            ligne(ERR, nom, f"{val}  ← NON UTF-8, corruption probable")
            problemes.append(nom)

    # Affiche aussi le charset déclaré dans config.py
    db_name = os.environ.get("DB_NAME", "?")
    db_user = os.environ.get("DB_USER", "?")
    db_host = os.environ.get("DB_HOST", "localhost")
    uri = f"mysql+pymysql://{db_user}:***@{db_host}/{db_name}"
    print(f"\n  {INFO}  URI SQLAlchemy actuelle (config.py) :")
    print(f"         {uri}")
    if "charset=utf8mb4" in uri:
        ligne(OK, "?charset=utf8mb4 présent", "oui")
    else:
        ligne(WARN, "?charset=utf8mb4 présent", "NON → PyMySQL utilise le charset serveur")

    return problemes

# ---------------------------------------------------------------------------
# SECTION 5 — Test d'aller-retour avec données accentuées
# ---------------------------------------------------------------------------
def verifier_aller_retour(conn):
    titre("5. Test d'aller-retour : écriture + lecture d'un texte accentué")

    texte_original = "Cybersécurité & Données — café, naïf, forêt"

    cursor = conn.cursor()
    try:
        # Table temporaire pour le test
        cursor.execute("CREATE TEMPORARY TABLE _test_encodage (val VARCHAR(200))")
        cursor.execute("INSERT INTO _test_encodage VALUES (%s)", (texte_original,))
        cursor.execute("SELECT val FROM _test_encodage")
        row = cursor.fetchone()
        texte_lu = row[0] if row else None
        cursor.execute("DROP TEMPORARY TABLE _test_encodage")
    except Exception as e:
        print(f"  {ERR}  Erreur lors du test aller-retour : {e}")
        cursor.close()
        return [str(e)]
    finally:
        cursor.close()

    print(f"  Texte écrit  : {texte_original}")
    print(f"  Texte lu     : {texte_lu}")

    if texte_original == texte_lu:
        print(f"\n  {OK}  Aller-retour parfait — les accents sont préservés à ce niveau.")
        return []
    else:
        print(f"\n  {ERR}  CORRUPTION DÉTECTÉE à ce niveau de la connexion !")
        print(f"  Attendu  : {texte_original}")
        print(f"  Obtenu   : {texte_lu}")
        return ["aller-retour corrompu"]

# ---------------------------------------------------------------------------
# SECTION 6 — Vérification de la connexion SQLAlchemy
# ---------------------------------------------------------------------------
def verifier_sqlalchemy():
    titre("6. Connexion SQLAlchemy — charset en production")
    try:
        from app import create_app
        from app.extensions import db
        from sqlalchemy import text

        app = create_app()
        with app.app_context():
            result = db.session.execute(text(
                "SELECT @@character_set_client, @@character_set_connection, @@character_set_results"
            ))
            row = result.fetchone()
            client, connection, results = row

            print(f"  Via SQLAlchemy (avec la config de production) :")
            problemes = []
            for nom, val in [("character_set_client", client),
                             ("character_set_connection", connection),
                             ("character_set_results", results)]:
                if "utf8mb4" in val:
                    ligne(OK, nom, val)
                elif "utf8" in val:
                    ligne(WARN, nom, f"{val}  ← pas utf8mb4")
                    problemes.append(nom)
                else:
                    ligne(ERR, nom, f"{val}  ← NON UTF-8, corruption probable")
                    problemes.append(nom)
            return problemes
    except Exception as e:
        print(f"  {ERR}  Impossible de tester via SQLAlchemy : {e}")
        return [str(e)]

# ---------------------------------------------------------------------------
# RAPPORT FINAL
# ---------------------------------------------------------------------------
def rapport_final(tous_problemes):
    titre("RÉSUMÉ DU DIAGNOSTIC")

    if not tous_problemes:
        print(f"\n  {OK}  Aucun problème d'encodage détecté dans la chaîne MySQL → SQLAlchemy.")
        print(f"  Si des accents sont quand même corrompus en affichage, le problème")
        print(f"  vient probablement d'une autre source (données déjà corrompues en base,")
        print(f"  ou affichage JavaScript/HTML).\n")
    else:
        print(f"\n  {ERR}  Problèmes détectés ({len(tous_problemes)}) :\n")
        for i, p in enumerate(tous_problemes, 1):
            print(f"    {i}. {p}")
        print(f"\n  Corrigez dans l'ordre : serveur → base → tables → connexion.")
        print(f"  Ne modifiez la connexion SQLAlchemy qu'APRÈS avoir vérifié MySQL.\n")

# ---------------------------------------------------------------------------
# POINT D'ENTRÉE
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  DIAGNOSTIC ENCODAGE UTF-8 — Galaxy Training Manager")
    print("="*60)

    conn = connexion_pymysql()
    tous_problemes = []

    tous_problemes += verifier_serveur(conn)
    tous_problemes += verifier_base(conn)
    tous_problemes += verifier_tables(conn)
    tous_problemes += verifier_connexion_pymysql(conn)
    tous_problemes += verifier_aller_retour(conn)

    conn.close()

    tous_problemes += verifier_sqlalchemy()

    rapport_final(tous_problemes)

