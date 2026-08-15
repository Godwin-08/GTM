"""
Génère le jeu de données de démonstration pour Galaxy Solutions.
Produit un fichier SQL (INSERT INTO ...) prêt à exécuter dans MySQL Workbench.

Attention portée à la cohérence :
- L'ordre des INSERT respecte les dépendances de clés étrangères.
- Session.date_fin = date_debut + (duree_jours de la Formation liée - 1).
- Session.statut est déduit des dates par rapport à "aujourd'hui" (2 août 2026),
  pas choisi au hasard : une session déjà terminée dans le passé ne peut pas
  être "planifiee", par exemple.
- Le formateur assigné à une session a le même domaine que la formation.
- Les inscriptions respectent un taux de remplissage variable et réaliste
  (certaines sessions presque vides, d'autres complètes, certaines avec
  liste d'attente une fois la capacité atteinte), avec quelques statuts
  "annulee" dispersés.
- Aucun participant n'est inscrit deux fois à la même session
  (contrainte uq_session_participant respectée dès la génération).
"""

import random
import unicodedata
from datetime import date, timedelta
from werkzeug.security import generate_password_hash

# Mot de passe en clair -> conservé ici UNIQUEMENT parce que c'est un jeu
# de données de démonstration (jamais de mot de passe en clair dans un
# vrai projet en production). Sert à générer un vrai hash Werkzeug pour
# chaque compte, avec un mot de passe DIFFÉRENT par utilisateur.
MOTS_DE_PASSE_DEMO = {
    "admin@galaxysolutions.ma": "Admin@2026",
    "sofia.amrani@galaxysolutions.ma": "Sofia@2026",
    "yassine.el.idrissi@galaxysolutions.ma": "Yassine@2026",
    "karim.bensouda@galaxysolutions.ma": "Karim@2026",
    "nadia.chraibi@galaxysolutions.ma": "Nadia@2026",
    "hicham.berrada@galaxysolutions.ma": "Hicham@2026",
}


def hash_pour(email):
    """Renvoie un vrai hash Werkzeug (pbkdf2:sha256) pour l'email donné."""
    mdp = MOTS_DE_PASSE_DEMO.get(email, "MotDePasse@2026")  # valeur de repli si jamais un email n'est pas dans la liste
    return generate_password_hash(mdp, method="pbkdf2:sha256")

random.seed(42)  # reproductibilité : mêmes données à chaque exécution

AUJOURDHUI = date(2026, 8, 2)

# ------------------------------------------------------------------
# Utilitaire : échapper les apostrophes pour le SQL
# ------------------------------------------------------------------
def esc(texte):
    if texte is None:
        return "NULL"
    return "'" + str(texte).replace("'", "''") + "'"


# ------------------------------------------------------------------
# Utilitaire : retirer les accents pour générer des emails valides
# (un nom affiché peut garder ses accents, un email non)
# ------------------------------------------------------------------
def sans_accents(texte):
    nfkd = unicodedata.normalize("NFKD", texte)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def email_depuis_nom(nom, domaine_email, suffixe=""):
    base = sans_accents(nom).lower().replace(" ", ".").replace("'", "")
    return f"{base}{suffixe}@{domaine_email}"


# ------------------------------------------------------------------
# Génère un numéro de téléphone marocain plausible : +212 6XX-XXXXXX
# ------------------------------------------------------------------
def telephone_maroc():
    prefixe = random.choice(["6", "7"])  # mobile marocain
    reste = "".join(str(random.randint(0, 9)) for _ in range(8))
    return f"+212 {prefixe}{reste[:1]}-{reste[1:]}"


# ------------------------------------------------------------------
# Pools de noms marocains réalistes (prénoms / noms de famille courants)
# ------------------------------------------------------------------
PRENOMS_M = [
    "Youssef", "Omar", "Mehdi", "Amine", "Karim", "Rachid", "Hicham", "Anas",
    "Tarik", "Ayoub", "Bilal", "Zakaria", "Adil", "Nabil", "Samir", "Younes",
    "Reda", "Walid", "Ismail", "Othmane",
]
PRENOMS_F = [
    "Salma", "Nadia", "Sofia", "Leila", "Fatima-Zahra", "Ghita", "Amina",
    "Meryem", "Khadija", "Zineb", "Imane", "Hasna", "Rania", "Sara", "Loubna",
    "Wafaa", "Asmae", "Ibtissam", "Karima", "Naima",
]
NOMS_FAMILLE = [
    "Bensouda", "El Idrissi", "Tazi", "Fassi", "Alaoui", "Bouzid", "Kabbaj",
    "Chraibi", "Berrada", "Benali", "El Fassi", "Amrani", "Benkirane", "Idrissi",
    "Lahlou", "Squalli", "Bennani", "El Ouazzani", "Cherkaoui", "Sbai",
    "El Yousfi", "Ziani", "Guessous", "Belkadi", "Ouahbi", "Rifai",
]


def nom_marocain():
    genre = random.choice(["M", "F"])
    prenom = random.choice(PRENOMS_M if genre == "M" else PRENOMS_F)
    nom_fam = random.choice(NOMS_FAMILLE)
    return f"{prenom} {nom_fam}"


lines = []
lines.append("-- ============================================")
lines.append("-- Jeu de données de démonstration : Galaxy Solutions")
lines.append("-- Généré automatiquement — ne pas éditer à la main, relancer le script Python à la place")
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

# ============================================
# 1. Role
# ============================================
roles = ["admin", "gestionnaire", "formateur"]
lines.append("-- Role")
lines.append(
    "INSERT INTO Role (nom) VALUES\n"
    + ",\n".join(f"({esc(r)})" for r in roles)
    + ";"
)
lines.append("")
ROLE_ID = {nom: i + 1 for i, nom in enumerate(roles)}

# ============================================
# 2. Domaine
# ============================================
domaines = ["Web & Data", "Management Agile", "Cybersécurité"]
lines.append("-- Domaine")
lines.append(
    "INSERT INTO Domaine (nom) VALUES\n"
    + ",\n".join(f"({esc(d)})" for d in domaines)
    + ";"
)
lines.append("")
DOMAINE_ID = {nom: i + 1 for i, nom in enumerate(domaines)}

# ============================================
# 3. Utilisateur (admin + gestionnaires + formateurs-avec-compte)
# ============================================
utilisateurs = []  # (nom, email, hash, role_id)
email_admin = "admin@galaxysolutions.ma"
utilisateurs.append(("Admin Galaxy", email_admin, hash_pour(email_admin), ROLE_ID["admin"]))
gestionnaires_noms = ["Sofia Amrani", "Yassine El Idrissi"]
for nom in gestionnaires_noms:
    email = email_depuis_nom(nom, "galaxysolutions.ma")
    utilisateurs.append((nom, email, hash_pour(email), ROLE_ID["gestionnaire"]))

# 3 formateurs auront un compte utilisateur (les autres formateurs n'en auront pas)
formateurs_avec_compte_noms = ["Karim Bensouda", "Nadia Chraibi", "Hicham Berrada"]
for nom in formateurs_avec_compte_noms:
    email = email_depuis_nom(nom, "galaxysolutions.ma")
    utilisateurs.append((nom, email, hash_pour(email), ROLE_ID["formateur"]))

lines.append("-- Utilisateur")
lines.append(
    "INSERT INTO Utilisateur (nom, email, mot_de_passe_hash, role_id, actif) VALUES\n"
    + ",\n".join(
        f"({esc(nom)}, {esc(email)}, {esc(h)}, {rid}, TRUE)"
        for nom, email, h, rid in utilisateurs
    )
    + ";"
)
lines.append("")
# id des utilisateurs formateurs (pour les relier plus bas), dans l'ordre d'insertion
UTIL_ID_FORMATEUR = {
    nom: 1 + len(gestionnaires_noms) + 1 + i  # +1 pour l'admin
    for i, nom in enumerate(formateurs_avec_compte_noms)
}

# ============================================
# 4. Formateur (8 au total : 3 avec compte, 5 sans)
# ============================================
formateurs = []  # (nom, email, telephone, domaine_nom, utilisateur_id_ou_None)

for nom in formateurs_avec_compte_noms:
    domaine = random.choice(domaines)
    email = email_depuis_nom(nom, "galaxysolutions.ma")
    formateurs.append((nom, email, telephone_maroc(), domaine, UTIL_ID_FORMATEUR[nom]))

formateurs_sans_compte_noms = [
    "Amine Tazi", "Leila Fassi", "Mehdi Alaoui", "Salma Bouzid", "Rachid Kabbaj"
]
for nom in formateurs_sans_compte_noms:
    domaine = random.choice(domaines)
    email = email_depuis_nom(nom, "formateur-externe.ma")
    formateurs.append((nom, email, telephone_maroc(), domaine, None))

# S'assurer qu'il y a au moins 2 formateurs par domaine (sinon on force le réajustement)
for d in domaines:
    count = sum(1 for f in formateurs if f[3] == d)
    if count < 2:
        # force le domaine sur les 2 premiers formateurs sans compte non encore ajustés
        for i, f in enumerate(formateurs):
            if f[4] is None and count < 2:
                formateurs[i] = (f[0], f[1], f[2], d, f[4])
                count += 1

lines.append("-- Formateur")
lines.append(
    "INSERT INTO Formateur (nom, email, telephone, domaine_id, utilisateur_id) VALUES\n"
    + ",\n".join(
        f"({esc(nom)}, {esc(email)}, {esc(tel)}, {DOMAINE_ID[dom]}, {uid if uid else 'NULL'})"
        for nom, email, tel, dom, uid in formateurs
    )
    + ";"
)
lines.append("")
FORMATEUR_IDS_PAR_DOMAINE = {d: [] for d in domaines}
for i, (nom, email, tel, dom, uid) in enumerate(formateurs, start=1):
    FORMATEUR_IDS_PAR_DOMAINE[dom].append(i)

# ============================================
# 5. Formation (9 au total, 3 par domaine)
# ============================================
titres_par_domaine = {
    "Web & Data": [
        "Python niveau débutant",
        "SQL avancé et modélisation de données",
        "Développement web full-stack",
    ],
    "Management Agile": [
        "Scrum Master fondamentaux",
        "Gestion de projet agile (Kanban/Scrum)",
        "Leadership et animation d'équipe agile",
    ],
    "Cybersécurité": [
        "Cybersécurité niveau 1 : fondamentaux",
        "Sécurisation des infrastructures réseau",
        "Audit de sécurité et gestion des incidents",
    ],
}

formations = []  # (titre, domaine_nom, duree_jours, description)
for dom, titres in titres_par_domaine.items():
    for titre in titres:
        duree = random.choice([2, 3, 4, 5])
        description = f"Formation professionnelle : {titre.lower()}, destinée aux salariés d'entreprises clientes de Galaxy Solutions."
        formations.append((titre, dom, duree, description))

lines.append("-- Formation")
lines.append(
    "INSERT INTO Formation (titre, domaine_id, duree_jours, description) VALUES\n"
    + ",\n".join(
        f"({esc(titre)}, {DOMAINE_ID[dom]}, {duree}, {esc(desc)})"
        for titre, dom, duree, desc in formations
    )
    + ";"
)
lines.append("")
FORMATION_INFO = []  # (id, titre, domaine_nom, duree_jours)
for i, (titre, dom, duree, desc) in enumerate(formations, start=1):
    FORMATION_INFO.append((i, titre, dom, duree))

# ============================================
# 6. Client (10 entreprises marocaines réalistes)
# ============================================
clients_data = [
    ("Maroc Telecom", "Télécommunications"),
    ("OCP Group", "Industrie minière"),
    ("Attijariwafa Bank", "Banque & Finance"),
    ("Bank Of Africa", "Banque & Finance"),
    ("Saint-Gobain Maroc", "Industrie / Matériaux"),
    ("Marjane Holding", "Grande distribution"),
    ("Managem", "Industrie minière"),
    ("Royal Air Maroc", "Transport aérien"),
    ("Wafabail", "Services financiers"),
    ("Akdital", "Santé"),
]

lines.append("-- Client")
lines.append(
    "INSERT INTO Client (nom_entreprise, secteur, contact_email) VALUES\n"
    + ",\n".join(
        f"({esc(nom)}, {esc(secteur)}, {esc('contact@' + nom.lower().replace(chr(39), '').replace(' ', '') + '.ma')})"
        for nom, secteur in clients_data
    )
    + ";"
)
lines.append("")
CLIENT_IDS = list(range(1, len(clients_data) + 1))

# ============================================
# 7. Participant (40 au total, répartis entre les 10 clients)
# ============================================
participants = []  # (nom, email, client_id)
noms_utilises = set()

for _ in range(40):
    client_id = random.choice(CLIENT_IDS)
    nom = nom_marocain()
    while nom in noms_utilises:
        nom = nom_marocain()
    noms_utilises.add(nom)
    email = email_depuis_nom(nom, "example.ma", suffixe=str(random.randint(1, 999)))
    participants.append((nom, email, client_id))

lines.append("-- Participant")
lines.append(
    "INSERT INTO Participant (nom, email, client_id) VALUES\n"
    + ",\n".join(
        f"({esc(nom)}, {esc(email)}, {cid})" for nom, email, cid in participants
    )
    + ";"
)
lines.append("")
PARTICIPANT_IDS_PAR_CLIENT = {cid: [] for cid in CLIENT_IDS}
for i, (nom, email, cid) in enumerate(participants, start=1):
    PARTICIPANT_IDS_PAR_CLIENT[cid].append(i)

TOTAL_PARTICIPANTS = len(participants)

# ============================================
# 8. Session (25 au total, réparties sur 10 mois, statuts cohérents avec les dates)
# ============================================
villes = ["Casablanca", "Rabat", "Mohammedia", "Marrakech", "Tanger", "Fès"]

sessions = []  # (formation_id, formateur_id, date_debut, date_fin, type, capacite_max, lieu, statut)

# Étale les sessions entre janvier 2026 et décembre 2026, pour avoir
# un mélange de sessions passées (terminées), en cours, et futures (planifiées)
date_min = date(2026, 1, 15)
date_max = date(2026, 12, 15)
ecart_total = (date_max - date_min).days

for _ in range(25):
    form_id, titre, dom, duree = random.choice(FORMATION_INFO)
    formateur_id = random.choice(FORMATEUR_IDS_PAR_DOMAINE[dom])

    jour_debut = date_min + timedelta(days=random.randint(0, ecart_total))
    date_debut = jour_debut
    date_fin = date_debut + timedelta(days=duree - 1)

    type_session = random.choice(["intra", "inter", "inter", "intra"])  # léger biais vers un mélange équilibré
    capacite_max = random.choice([8, 10, 12, 15, 18, 20])
    lieu = f"Galaxy Solutions, {random.choice(villes)}"

    # Statut déduit des dates par rapport à aujourd'hui (2026-08-02)
    if date_fin < AUJOURDHUI:
        # Session déjà passée : très majoritairement terminée, rare annulation a posteriori
        statut = random.choices(["terminee", "annulee"], weights=[92, 8])[0]
    elif date_debut <= AUJOURDHUI <= date_fin:
        statut = "en_cours"
    else:
        # Session future : majoritairement planifiée, quelques annulations anticipées
        statut = random.choices(["planifiee", "annulee"], weights=[88, 12])[0]

    sessions.append((form_id, formateur_id, date_debut, date_fin, type_session, capacite_max, lieu, statut))

lines.append("-- Session")
lines.append(
    "INSERT INTO Session (formation_id, formateur_id, date_debut, date_fin, type, capacite_max, lieu, statut) VALUES\n"
    + ",\n".join(
        f"({fid}, {tid}, {esc(db.isoformat())}, {esc(df.isoformat())}, {esc(t)}, {cap}, {esc(lieu)}, {esc(st)})"
        for fid, tid, db, df, t, cap, lieu, st in sessions
    )
    + ";"
)
lines.append("")

# ============================================
# 9. Inscription
# Taux de remplissage volontairement variés : certaines sessions peu remplies,
# d'autres complètes, certaines dépassant la capacité (liste d'attente).
# ============================================
inscription_lines = []
inscription_count = 0

for i, (fid, tid, db, df, t, cap, lieu, statut) in enumerate(sessions, start=1):
    # Sessions annulées : peu ou pas d'inscriptions (les gens se sont désistés)
    if statut == "annulee":
        nb_a_inscrire = random.randint(0, max(1, cap // 4))
    else:
        # Taux de remplissage réaliste et varié : entre 30% et 110% de la capacité
        taux = random.choice([0.3, 0.45, 0.6, 0.75, 0.9, 1.0, 1.1])
        nb_a_inscrire = round(cap * taux)

    nb_a_inscrire = min(nb_a_inscrire, TOTAL_PARTICIPANTS)  # sécurité
    participants_choisis = random.sample(range(1, TOTAL_PARTICIPANTS + 1), nb_a_inscrire)

    for rang, pid in enumerate(participants_choisis):
        # Date d'inscription : quelque temps avant le début de la session
        jours_avant = random.randint(5, 60)
        date_inscription = db - timedelta(days=jours_avant)
        # Ne pas antidater avant une date raisonnable
        if date_inscription < date(2025, 11, 1):
            date_inscription = date(2025, 11, 1)

        if rang < cap:
            # Dans la capacité : très majoritairement confirmée, un peu d'annulation
            statut_inscription = random.choices(
                ["confirmee", "annulee"], weights=[90, 10]
            )[0]
        else:
            # Au-delà de la capacité : liste d'attente
            statut_inscription = "liste_attente"

        inscription_lines.append(
            f"({i}, {pid}, {esc(date_inscription.isoformat())}, {esc(statut_inscription)})"
        )
        inscription_count += 1

lines.append("-- Inscription")
lines.append(
    "INSERT INTO Inscription (session_id, participant_id, date_inscription, statut) VALUES\n"
    + ",\n".join(inscription_lines)
    + ";"
)
lines.append("")

lines.append(f"-- Total inscriptions générées : {inscription_count}")

# ============================================
# Écriture du fichier final
# ============================================
with open("/home/claude/seed_demo_data.sql", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Fichier généré : seed_demo_data.sql")
print(f"Role: {len(roles)} | Domaine: {len(domaines)} | Utilisateur: {len(utilisateurs)}")
print(f"Formateur: {len(formateurs)} | Formation: {len(formations)} | Client: {len(clients_data)}")
print(f"Participant: {len(participants)} | Session: {len(sessions)} | Inscription: {inscription_count}")

# Vérifications de cohérence
print("\n--- Vérifications ---")
for fid, tid, db, df, t, cap, lieu, st in sessions:
    assert df >= db, "date_fin doit être >= date_debut"
print("OK : toutes les dates de session sont cohérentes (date_fin >= date_debut)")

# Vérifie qu'aucune session n'a le même participant inscrit deux fois
from collections import Counter
seen = Counter()
for line in inscription_lines:
    # extrait session_id, participant_id du début de la ligne "(sid, pid, ..."
    inner = line.strip("()").split(",")
    sid, pid = inner[0].strip(), inner[1].strip()
    seen[(sid, pid)] += 1
doublons = [k for k, v in seen.items() if v > 1]
assert not doublons, f"Doublons détectés (session, participant) : {doublons}"
print("OK : aucun participant inscrit deux fois à la même session")
