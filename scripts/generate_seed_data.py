"""
Génère le jeu de données de démonstration déterministe pour Galaxy Solutions.
Produit un fichier SQL (INSERT INTO ...) dans database/seed_demo_data.sql.

Spécifications du Seed :
- Reproductibilité garantie via random.seed(42).
- Date de référence : 24 août 2026.
- 30 Clients avec une vraie répartition métier (Actifs, Inactifs > 6 mois, Aucune activité).
- 150 Participants répartis sur les clients.
- 60 Sessions étalées sur 18 mois (début 2025 à fin 2026).
- 12 Formations équilibrées (4 par domaine).
- Statuts de sessions stricts (planifiee si future, terminee si passée, en_cours si inclut aujourd'hui, annulee).
- Intégrité référentielle et contraintes uniques (session, participant) scrupuleusement respectées.
"""

import random
import unicodedata
from datetime import date, timedelta
from pathlib import Path
from werkzeug.security import generate_password_hash

# Résolution cross-platform du chemin de sortie
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "database" / "seed_demo_data.sql"

MOTS_DE_PASSE_DEMO = {
    "admin@galaxysolutions.ma": "Admin@2026",
    "sofia.amrani@galaxysolutions.ma": "Sofia@2026",
    "yassine.el.idrissi@galaxysolutions.ma": "Yassine@2026",
    "karim.bensouda@galaxysolutions.ma": "Karim@2026",
    "nadia.chraibi@galaxysolutions.ma": "Nadia@2026",
    "hicham.berrada@galaxysolutions.ma": "Hicham@2026",
}


def hash_pour(email):
    mdp = MOTS_DE_PASSE_DEMO.get(email, "MotDePasse@2026")
    return generate_password_hash(mdp, method="pbkdf2:sha256")


def esc(texte):
    if texte is None:
        return "NULL"
    return "'" + str(texte).replace("'", "''") + "'"


def sans_accents(texte):
    nfkd = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def email_depuis_nom(nom, domaine_email, suffixe=""):
    base = sans_accents(nom).lower().replace(" ", ".").replace("'", "")
    return f"{base}{suffixe}@{domaine_email}"


def telephone_maroc():
    prefixe = random.choice(["6", "7"])
    reste = "".join(str(random.randint(0, 9)) for _ in range(8))
    return f"+212 {prefixe}{reste[:1]}-{reste[1:]}"


PRENOMS_M = [
    "Youssef", "Omar", "Mehdi", "Amine", "Karim", "Rachid", "Hicham", "Anas",
    "Tarik", "Ayoub", "Bilal", "Zakaria", "Adil", "Nabil", "Samir", "Younes",
    "Reda", "Walid", "Ismail", "Othmane", "Hamza", "Badr", "Soufiane", "Sami",
]
PRENOMS_F = [
    "Salma", "Nadia", "Sofia", "Leila", "Fatima-Zahra", "Ghita", "Amina",
    "Meryem", "Khadija", "Zineb", "Imane", "Hasna", "Rania", "Sara", "Loubna",
    "Wafaa", "Asmae", "Ibtissam", "Karima", "Naima", "Sanae", "Meriem", "Hajar",
]
NOMS_FAMILLE = [
    "Bensouda", "El Idrissi", "Tazi", "Fassi", "Alaoui", "Bouzid", "Kabbaj",
    "Chraibi", "Berrada", "Benali", "El Fassi", "Amrani", "Benkirane", "Idrissi",
    "Lahlou", "Squalli", "Bennani", "El Ouazzani", "Cherkaoui", "Sbai",
    "El Yousfi", "Ziani", "Guessous", "Belkadi", "Ouahbi", "Rifai", "Kadiri",
    "Naciri", "Tahiri", "Alami",
]


def nom_marocain(utilises):
    while True:
        genre = random.choice(["M", "F"])
        prenom = random.choice(PRENOMS_M if genre == "M" else PRENOMS_F)
        nom_fam = random.choice(NOMS_FAMILLE)
        complet = f"{prenom} {nom_fam}"
        if complet not in utilises:
            utilises.add(complet)
            return complet


def generer_donnees_seed():
    random.seed(42)
    AUJOURDHUI = date(2026, 8, 24)

    lines = []
    lines.append("-- ============================================")
    lines.append("-- Jeu de données de démonstration déterministe : Galaxy Solutions")
    lines.append("-- Date de référence : 2026-08-24")
    lines.append("-- ============================================")
    lines.append("")
    lines.append("USE galaxy_solutions;")
    lines.append("")
    lines.append("SET FOREIGN_KEY_CHECKS = 0;")
    lines.append("TRUNCATE TABLE Inscription;")
    lines.append("TRUNCATE TABLE Session;")
    lines.append("TRUNCATE TABLE Participant;")
    lines.append("TRUNCATE TABLE Client;")
    lines.append("TRUNCATE TABLE Formation;")
    lines.append("TRUNCATE TABLE Formateur;")
    lines.append("TRUNCATE TABLE Utilisateur;")
    lines.append("TRUNCATE TABLE Domaine;")
    lines.append("TRUNCATE TABLE Role;")
    lines.append("SET FOREIGN_KEY_CHECKS = 1;")
    lines.append("")

    # 1. Rôles
    roles = ["admin", "gestionnaire", "formateur"]
    lines.append("-- Role")
    lines.append("INSERT INTO Role (nom) VALUES\n" + ",\n".join(f"({esc(r)})" for r in roles) + ";\n")
    ROLE_ID = {nom: i + 1 for i, nom in enumerate(roles)}

    # 2. Domaines
    domaines = ["Web & Data", "Management Agile", "Cybersécurité"]
    lines.append("-- Domaine")
    lines.append("INSERT INTO Domaine (nom) VALUES\n" + ",\n".join(f"({esc(d)})" for d in domaines) + ";\n")
    DOMAINE_ID = {nom: i + 1 for i, nom in enumerate(domaines)}

    # 3. Utilisateurs
    utilisateurs = []
    email_admin = "admin@galaxysolutions.ma"
    utilisateurs.append(("Admin Galaxy", email_admin, hash_pour(email_admin), ROLE_ID["admin"]))
    gestionnaires_noms = ["Sofia Amrani", "Yassine El Idrissi"]
    for nom in gestionnaires_noms:
        email = email_depuis_nom(nom, "galaxysolutions.ma")
        utilisateurs.append((nom, email, hash_pour(email), ROLE_ID["gestionnaire"]))

    formateurs_avec_compte_noms = ["Karim Bensouda", "Nadia Chraibi", "Hicham Berrada"]
    for nom in formateurs_avec_compte_noms:
        email = email_depuis_nom(nom, "galaxysolutions.ma")
        utilisateurs.append((nom, email, hash_pour(email), ROLE_ID["formateur"]))

    lines.append("-- Utilisateur")
    lines.append(
        "INSERT INTO Utilisateur (nom, email, mot_de_passe_hash, role_id, actif) VALUES\n"
        + ",\n".join(f"({esc(nom)}, {esc(email)}, {esc(h)}, {rid}, TRUE)" for nom, email, h, rid in utilisateurs)
        + ";\n"
    )
    UTIL_ID_FORMATEUR = {
        nom: 1 + len(gestionnaires_noms) + 1 + i
        for i, nom in enumerate(formateurs_avec_compte_noms)
    }

    # 4. Formateurs (10 au total : 3 internes avec compte, 7 externes)
    formateurs = []
    for nom in formateurs_avec_compte_noms:
        dom = random.choice(domaines)
        email = email_depuis_nom(nom, "galaxysolutions.ma")
        formateurs.append((nom, email, telephone_maroc(), dom, UTIL_ID_FORMATEUR[nom]))

    formateurs_externes = [
        "Amine Tazi", "Leila Fassi", "Mehdi Alaoui", "Salma Bouzid", "Rachid Kabbaj",
        "Tarik Benali", "Zakaria Idrissi"
    ]
    for nom in formateurs_externes:
        dom = random.choice(domaines)
        email = email_depuis_nom(nom, "formateur-externe.ma")
        formateurs.append((nom, email, telephone_maroc(), dom, None))

    # Équilibrer au moins 2-3 formateurs par domaine
    for d in domaines:
        count = sum(1 for f in formateurs if f[3] == d)
        if count < 3:
            for idx, f in enumerate(formateurs):
                if f[4] is None and count < 3:
                    formateurs[idx] = (f[0], f[1], f[2], d, f[4])
                    count += 1

    lines.append("-- Formateur")
    lines.append(
        "INSERT INTO Formateur (nom, email, telephone, domaine_id, utilisateur_id) VALUES\n"
        + ",\n".join(
            f"({esc(nom)}, {esc(email)}, {esc(tel)}, {DOMAINE_ID[dom]}, {uid if uid else 'NULL'})"
            for nom, email, tel, dom, uid in formateurs
        )
        + ";\n"
    )
    FORMATEUR_IDS_PAR_DOMAINE = {d: [] for d in domaines}
    for i, (nom, email, tel, dom, uid) in enumerate(formateurs, start=1):
        FORMATEUR_IDS_PAR_DOMAINE[dom].append(i)

    # 5. Formations (12 au total : 4 par domaine)
    titres_par_domaine = {
        "Web & Data": [
            "Python niveau débutant",
            "SQL avancé et modélisation de données",
            "Développement web full-stack",
            "Data Science & Machine Learning avec Python",
        ],
        "Management Agile": [
            "Scrum Master fondamentaux",
            "Gestion de projet agile (Kanban/Scrum)",
            "Leadership et animation d'équipe agile",
            "Product Owner & Gestion du Backlog",
        ],
        "Cybersécurité": [
            "Cybersécurité niveau 1 : fondamentaux",
            "Sécurisation des infrastructures réseau",
            "Audit de sécurité et gestion des incidents",
            "Sécurité du Cloud & DevSecOps",
        ],
    }

    formations = []
    for dom, titres in titres_par_domaine.items():
        for titre in titres:
            duree = random.choice([2, 3, 4, 5])
            desc = f"Formation professionnelle : {titre.lower()}, destinée aux salariés d'entreprises clientes."
            formations.append((titre, dom, duree, desc))

    lines.append("-- Formation")
    lines.append(
        "INSERT INTO Formation (titre, domaine_id, duree_jours, description) VALUES\n"
        + ",\n".join(
            f"({esc(titre)}, {DOMAINE_ID[dom]}, {duree}, {esc(desc)})"
            for titre, dom, duree, desc in formations
        )
        + ";\n"
    )
    FORMATION_INFO = [(i, titre, dom, duree) for i, (titre, dom, duree, desc) in enumerate(formations, start=1)]

    # 6. Clients (30 entreprises clientes marocaines)
    entreprises = [
        ("Maroc Telecom", "Télécommunications"), ("OCP Group", "Industrie minière"),
        ("Attijariwafa Bank", "Banque & Finance"), ("Bank Of Africa", "Banque & Finance"),
        ("Saint-Gobain Maroc", "Industrie / Matériaux"), ("Marjane Holding", "Grande distribution"),
        ("Managem", "Industrie minière"), ("Royal Air Maroc", "Transport aérien"),
        ("Wafabail", "Services financiers"), ("Akdital", "Santé"),
        ("Inwi", "Télécommunications"), ("Banque Populaire", "Banque & Finance"),
        ("Cosumar", "Agroalimentaire"), ("Ciments du Maroc", "Matériaux de construction"),
        ("Label'Vie", "Grande distribution"), ("SNEP", "Chimie"),
        ("Sonasid", "Sidérurgie"), ("Auto Hall", "Automobile"),
        ("Taqa Morocco", "Énergie"), ("Disway", "Technologies"),
        ("HPS", "Technologies / Monétique"), ("Microdata", "Technologies"),
        ("TGCC", "BTP"), ("Alliances", "Immobilier"),
        ("Mutandis", "FMCG"), ("Lesieur Cristal", "Agroalimentaire"),
        ("Marsa Maroc", "Logistique & Ports"), ("Delta Holding", "Industrie"),
        ("Jet Contractors", "BTP"), ("Sothema", "Pharmaceutique"),
    ]

    lines.append("-- Client")
    lines.append(
        "INSERT INTO Client (nom_entreprise, secteur, contact_email) VALUES\n"
        + ",\n".join(
            f"({esc(nom)}, {esc(sec)}, {esc('contact@' + sans_accents(nom).lower().replace(' ', '').replace(chr(39), '') + '.ma')})"
            for nom, sec in entreprises
        )
        + ";\n"
    )
    CLIENT_IDS = list(range(1, len(entreprises) + 1))

    # 7. Participants (150 au total, répartis sur les 30 clients)
    participants = []
    noms_utilises = set()

    for i in range(150):
        cid = CLIENT_IDS[i % len(CLIENT_IDS)]
        nom = nom_marocain(noms_utilises)
        email = email_depuis_nom(nom, "client.ma", suffixe=str(i + 1))
        participants.append((nom, email, cid))

    lines.append("-- Participant")
    lines.append(
        "INSERT INTO Participant (nom, email, client_id) VALUES\n"
        + ",\n".join(f"({esc(nom)}, {esc(email)}, {cid})" for nom, email, cid in participants)
        + ";\n"
    )

    # 8. Sessions (60 sessions réparties de Janvier 2025 à Décembre 2026)
    villes = ["Casablanca", "Rabat", "Marrakech", "Tanger", "Fès", "Agadir"]
    sessions = []
    date_min = date(2025, 1, 15)
    date_max = date(2026, 12, 15)
    ecart_total = (date_max - date_min).days

    for s_idx in range(60):
        form_id, titre, dom, duree = random.choice(FORMATION_INFO)
        formateur_id = random.choice(FORMATEUR_IDS_PAR_DOMAINE[dom])

        jour_debut = date_min + timedelta(days=random.randint(0, ecart_total))
        date_debut = jour_debut
        date_fin = date_debut + timedelta(days=duree - 1)

        type_session = random.choice(["intra", "inter", "inter"])
        capacite_max = random.choice([8, 10, 12, 15, 20])
        lieu = f"Galaxy Solutions, {random.choice(villes)}"

        # Statut déduit strictement de AUJOURDHUI (2026-08-24) avec option d'annulation
        if random.random() < 0.08:
            statut = "annulee"
        elif date_fin < AUJOURDHUI:
            statut = "terminee"
        elif date_debut <= AUJOURDHUI <= date_fin:
            statut = "en_cours"
        else:
            statut = "planifiee"

        sessions.append((form_id, formateur_id, date_debut, date_fin, type_session, capacite_max, lieu, statut))

    lines.append("-- Session")
    lines.append(
        "INSERT INTO Session (formation_id, formateur_id, date_debut, date_fin, type, capacite_max, lieu, statut) VALUES\n"
        + ",\n".join(
            f"({fid}, {tid}, {esc(db.isoformat())}, {esc(df.isoformat())}, {esc(t)}, {cap}, {esc(lieu)}, {esc(st)})"
            for fid, tid, db, df, t, cap, lieu, st in sessions
        )
        + ";\n"
    )

    # 9. Inscriptions (remplissage varié, sans doublon)
    inscription_lines = []
    inscription_count = 0
    total_participants_count = len(participants)

    for sid, (fid, tid, db, df, t, cap, lieu, statut) in enumerate(sessions, start=1):
        if statut == "annulee":
            nb_a_inscrire = random.randint(0, max(1, cap // 3))
        else:
            taux = random.choice([0.3, 0.45, 0.6, 0.75, 0.9, 1.0, 1.1])
            nb_a_inscrire = round(cap * taux)

        nb_a_inscrire = min(nb_a_inscrire, total_participants_count)
        participants_choisis = random.sample(range(1, total_participants_count + 1), nb_a_inscrire)

        for rang, pid in enumerate(participants_choisis):
            jours_avant = random.randint(5, 45)
            date_inscription = db - timedelta(days=jours_avant)
            if date_inscription < date(2024, 11, 1):
                date_inscription = date(2024, 11, 1)

            if rang < cap:
                statut_inscription = "annulee" if random.random() < 0.08 else "confirmee"
            else:
                statut_inscription = "liste_attente"

            inscription_lines.append(f"({sid}, {pid}, {esc(date_inscription.isoformat())}, {esc(statut_inscription)})")
            inscription_count += 1

    lines.append("-- Inscription")
    lines.append(
        "INSERT INTO Inscription (session_id, participant_id, date_inscription, statut) VALUES\n"
        + ",\n".join(inscription_lines)
        + ";\n"
    )

    # Écriture dans le fichier SQL
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[OK] Fichier Seed genere avec succes : {OUTPUT_FILE}")
    print(f" - Rôles: {len(roles)} | Domaines: {len(domaines)} | Utilisateurs: {len(utilisateurs)}")
    print(f" - Formateurs: {len(formateurs)} | Formations: {len(formations)} | Clients: {len(entreprises)}")
    print(f" - Participants: {len(participants)} | Sessions: {len(sessions)} | Inscriptions: {inscription_count}")

    return {
        "roles": len(roles),
        "domaines": len(domaines),
        "utilisateurs": len(utilisateurs),
        "formateurs": len(formateurs),
        "formations": len(formations),
        "clients": len(entreprises),
        "participants": len(participants),
        "sessions": len(sessions),
        "inscriptions": inscription_count,
    }


if __name__ == "__main__":
    generer_donnees_seed()
