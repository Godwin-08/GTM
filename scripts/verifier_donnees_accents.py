"""
==============================================================================
Script de Vérification des Données Accentuées — Galaxy Training Manager
==============================================================================
Ce script vérifie les données réellement stockées en base, la réponse brute
de l'API, et fournit des instructions pour vérifier le navigateur.

Niveau 1 : données en base (SELECT + HEX)
Niveau 2 : réponse brute de l'API Flask
Niveau 3 : instructions pour le navigateur

Usage :
    # Terminal 1 : démarrer l'application
    .\\venv\\Scripts\\python.exe run.py

    # Terminal 2 : lancer ce script
    .\\venv\\Scripts\\python.exe -X utf8 scripts\\verifier_donnees_accents.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()

OK   = "[OK] "
WARN = "[WARN]"
ERR  = "[ERR] "
INFO = "[INFO]"

def titre(texte):
    print(f"\n{'='*60}")
    print(f"  {texte}")
    print(f"{'='*60}")

def connexion_pymysql():
    import pymysql
    try:
        conn = pymysql.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME"),
            charset="utf8mb4",
        )
        return conn
    except Exception as e:
        print(f"\n{ERR} Impossible de se connecter a MySQL : {e}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Niveau 1 — Données réellement stockées en base
# ---------------------------------------------------------------------------
def verifier_donnees_base(conn):
    titre("NIVEAU 1 — Donnees en base (SELECT + HEX)")

    # Caracteres accentues attendus en UTF-8 correct
    # é = C3A9, è = C3A8, ê = C3AA, à = C3A0, ç = C3A7, û = C3BB
    ACCENTS_UTF8 = {
        "é": "C3A9", "è": "C3A8", "ê": "C3AA",
        "à": "C3A0", "â": "C3A2", "ç": "C3A7",
        "î": "C3AE", "ô": "C3B4", "û": "C3BB",
        "É": "C389", "È": "C388",
    }

    # Tables et colonnes a inspecter
    requetes = [
        ("domaine",    "SELECT id, nom, HEX(nom) FROM domaine ORDER BY id"),
        ("formation",  "SELECT id, titre, HEX(titre) FROM formation ORDER BY id LIMIT 5"),
        ("client",     "SELECT id, nom_entreprise, HEX(nom_entreprise) FROM client ORDER BY id LIMIT 5"),
        ("utilisateur","SELECT id, nom, HEX(nom) FROM utilisateur ORDER BY id LIMIT 5"),
        ("formateur",  "SELECT id, nom, HEX(nom) FROM formateur ORDER BY id LIMIT 5"),
    ]

    problemes = []
    cursor = conn.cursor()

    for table, sql, in requetes:
        print(f"\n  Table : {table}")
        print(f"  {'-'*55}")
        try:
            cursor.execute(sql)
            lignes = cursor.fetchall()
            if not lignes:
                print(f"  {INFO} Table vide.")
                continue
            for row in lignes:
                id_val, texte, hex_val = row
                # Détection des séquences HEX corrompues
                # latin1 mal décodé : é devient C383C2A9 ou C383A9
                corruption = False
                if "C383" in hex_val:
                    corruption = True  # double-encodage UTF-8/latin1 typique
                if "3F" in hex_val and any(ord(c) > 127 for c in texte):
                    corruption = True  # remplacement par '?' (point d'interrogation)

                statut = ERR if corruption else OK
                print(f"  {statut} id={id_val:<4} texte={texte!r:<30} HEX={hex_val[:40]}")
                if corruption:
                    problemes.append(f"table={table} id={id_val} texte={texte!r}")
                    print(f"         CORRUPTION DETECTEE : HEX contient C383 (double-encodage) ou 3F (?).")

        except Exception as e:
            print(f"  {WARN} Impossible de lire {table} : {e}")

    cursor.close()
    return problemes


# ---------------------------------------------------------------------------
# Niveau 2 — Réponse brute de l'API Flask
# ---------------------------------------------------------------------------
def verifier_api_flask():
    titre("NIVEAU 2 — Reponse brute de l'API Flask")

    try:
        import urllib.request
        import urllib.error
    except ImportError:
        print(f"  {ERR} urllib non disponible.")
        return []

    endpoints = [
        ("GET /api/domaines",   "http://127.0.0.1:5000/api/domaines"),
        ("GET /api/formations", "http://127.0.0.1:5000/api/formations"),
    ]

    problemes = []

    print(f"\n  IMPORTANT : l'application Flask doit etre demarree")
    print(f"  (.\\venv\\Scripts\\python.exe run.py) pour ce test.\n")

    for label, url in endpoints:
        print(f"  Test : {label}")
        try:
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/json")

            with urllib.request.urlopen(req, timeout=3) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw_bytes = resp.read()

                # Verification du Content-Type
                if "utf-8" in content_type.lower() or "utf8" in content_type.lower():
                    print(f"  {OK} Content-Type : {content_type}")
                else:
                    print(f"  {WARN} Content-Type : {content_type}  [charset UTF-8 non declare]")
                    problemes.append(f"Content-Type sans charset: {label}")

                # Decodage des octets bruts
                try:
                    texte_utf8 = raw_bytes.decode("utf-8")
                    data = json.loads(texte_utf8)
                    print(f"  {OK} Decodage UTF-8 reussi ({len(raw_bytes)} octets)")

                    # Recherche des accents dans les donnees retournees
                    texte_json = texte_utf8
                    accents_trouves = [c for c in "éèêàâçîôûÉÈ" if c in texte_json]
                    echap_trouves = [s for s in ["\\u00e9","\\u00e8","\\u00e0","\\u00e7"]
                                     if s in texte_json]

                    if accents_trouves:
                        print(f"  {OK} Accents presents en clair dans le JSON : {accents_trouves}")
                    elif echap_trouves:
                        print(f"  {INFO} Accents en sequences unicode (\\uXXXX) : {echap_trouves}")
                        print(f"         -> Valide JSON, mais moins lisible. Ajouter ensure_ascii=False si voulu.")
                    else:
                        print(f"  {INFO} Pas d'accent detecte dans les donnees retournees.")

                    # Affichage d'un extrait pour verification visuelle
                    if isinstance(data, list) and len(data) > 0:
                        print(f"\n  Extrait des donnees recues (3 premiers) :")
                        for item in data[:3]:
                            for cle, val in item.items():
                                if isinstance(val, str) and len(val) > 0:
                                    print(f"    {cle}: {val!r}")
                            print()

                except UnicodeDecodeError as ude:
                    print(f"  {ERR} Decodage UTF-8 echoue : {ude}")
                    print(f"         Les octets bruts commencent par : {raw_bytes[:20].hex()}")
                    problemes.append(f"UnicodeDecodeError: {label}")

        except urllib.error.URLError as e:
            print(f"  {WARN} Impossible de joindre {url}")
            print(f"         L'application n'est peut-etre pas demarree. ({e})")
        except Exception as e:
            print(f"  {ERR} Erreur inattendue : {e}")

        print()

    return problemes


# ---------------------------------------------------------------------------
# Niveau 3 — Instructions pour le navigateur
# ---------------------------------------------------------------------------
def instructions_navigateur():
    titre("NIVEAU 3 — Verification dans le navigateur (manuelle)")

    print("""
  Pour localiser precisement le probleme chez votre encadrant :

  A. Verifier l'API directement dans le navigateur
  -------------------------------------------------
  1. Ouvrir Chrome ou Firefox
  2. Aller sur : http://127.0.0.1:5000/api/domaines
  3. Verifier que les accents s'affichent correctement dans le JSON brut
     - Si oui  : le probleme vient de l'affichage JavaScript/HTML
     - Si non  : le probleme vient de Flask ou de la base

  B. Verifier les en-tetes HTTP (Chrome DevTools)
  ------------------------------------------------
  1. F12 -> Onglet "Network"
  2. Recharger la page
  3. Cliquer sur la requete /api/domaines (ou /api/formations)
  4. Verifier l'en-tete "Content-Type" dans "Response Headers"
     - Attendu : application/json; charset=utf-8 ou application/json
     - Si absent ou "charset=latin1" : probleme cote Flask

  C. Test rapide dans la Console JavaScript
  ------------------------------------------
  Ouvrir la console (F12 -> Console) et coller :
  
      fetch('/api/domaines')
        .then(r => r.json())
        .then(d => console.log(d.map(x => x.nom)))

  Si les noms s'affichent correctement dans la console,
  le probleme vient du rendu HTML/template, pas de l'API.

  D. Demander a l'encadrant
  -------------------------
  Lui demander de faire une capture d'ecran montrant :
  1. L'URL exacte ou il voit les accents corrompus
  2. Si ce sont les donnees de l'API (/api/...) ou l'interface HTML
  Cela permettra de cibler immediatement le bon maillon.
""")


# ---------------------------------------------------------------------------
# Point d'entree
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  VERIFICATION DONNEES ACCENTUEES — GTM")
    print("="*60)

    conn = connexion_pymysql()
    problemes = []

    problemes += verifier_donnees_base(conn)
    conn.close()

    problemes += verifier_api_flask()

    instructions_navigateur()

    titre("RESUME")
    if not problemes:
        print(f"""
  {OK} Aucune corruption detectee dans les donnees en base.
  {OK} Si l'API est accessible, les accents sont bien transmis.

  Conclusion provisoire :
  Le probleme d'encodage signale par l'encadrant est probablement
  lie a une des causes suivantes :
    1. Donnees importees (seed SQL) depuis un terminal non-UTF-8
    2. Configuration differente sur la machine de l'encadrant
    3. Affichage HTML/JavaScript (moins probable)

  Prochaine etape : demander a l'encadrant ou exactement
  il voit les accents corrompus (URL + capture d'ecran).
""")
    else:
        print(f"\n  {ERR} Problemes detectes ({len(problemes)}) :\n")
        for i, p in enumerate(problemes, 1):
            print(f"    {i}. {p}")
        print(f"\n  Consultez les sections ci-dessus pour les details.\n")

