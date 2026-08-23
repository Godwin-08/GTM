# Galaxy Training Manager (GTM)

**Galaxy Training Manager (GTM)** est une application web pour gérer et analyser l'activité de formation de l'entreprise **Galaxy Solutions**.

L'application permet de centraliser la gestion des formations, des sessions, des inscriptions, des clients, des formateurs, des participants et des comptes utilisateurs. Elle calcule aussi des indicateurs clés (comme le taux de remplissage des sessions) pour faciliter la prise de décision.

---

## 🛠️ Technologies utilisées

- **Backend** : Python 3, Flask, SQLAlchemy (ORM pour MySQL)
- **Base de données** : MySQL
- **Authentification & Sécurité** : Flask-Login (gestion des sessions utilisateur)
- **Migrations** : Flask-Migrate (Alembic)
- **Frontend** : HTML5, Tailwind CSS, Alpine.js (JS réactif léger), Lucide Icons

---

## 🚀 Installation et démarrage

### 1. Cloner le projet et créer un environnement virtuel

Un environnement virtuel permet d'installer les dépendances isolément du reste du système.

```bash
git clone <url-du-depot>
cd PFA_galaxy_solutions

# Création de l'environnement virtuel
python -m venv venv

# Activation (Windows PowerShell)
venv\Scripts\Activate.ps1

# Activation (Linux / macOS)
source venv/bin/activate
```

### 2. Installer les dépendances Python

```bash
pip install -r requirements.txt
```

### 3. Configurer les variables d'environnement

Créez un fichier `.env` à la racine du projet en vous inspirant du modèle suivant :

```env
SECRET_KEY=votre_cle_secrete_ici
DB_USER=root
DB_PASSWORD=votre_mot_de_passe_mysql
DB_HOST=localhost
DB_NAME=galaxy_solutions
FLASK_ENV=development
```

### 4. Initialiser la base de données MySQL

Dans MySQL Workbench ou en ligne de commande, exécutez les scripts SQL du dossier `database/` dans cet ordre :

1. `database/schema_galaxy_solutions.sql` : crée la structure de la base de données.
2. `database/seed_demo_data.sql` : insère des données de démonstration réalistes.

### 5. Démarrer l'application

```bash
python run.py
```

L'application sera disponible sur `http://127.0.0.1:5000/`.

---

## 👥 Comptes de démonstration

Voici les identifiants préconfigurés pour tester les différents rôles :

| Rôle | Email | Mot de passe |
|---|---|---|
| **Admin** | `admin@galaxysolutions.ma` | `Admin@2026` |
| **Gestionnaire** | `sofia.amrani@galaxysolutions.ma` | `Sofia@2026` |
| **Gestionnaire** | `yassine.el.idrissi@galaxysolutions.ma` | `Yassine@2026` |
| **Formateur** | `karim.bensouda@galaxysolutions.ma` | `Karim@2026` |
| **Formateur** | `nadia.chraibi@galaxysolutions.ma` | `Nadia@2026` |
| **Formateur** | `hicham.berrada@galaxysolutions.ma` | `Hicham@2026` |

---

## 🔐 Rôles et autorisations

- **Admin** : Accès complet. Seul rôle autorisé à gérer les comptes utilisateurs (`/utilisateurs`).
- **Gestionnaire** : Création, modification et suppression des formations, sessions, clients, formateurs, participants et inscriptions.
- **Formateur** : Consultation seule des informations (mode lecture).

---

## 🖥️ Pages de l'application (Frontend)

L'interface est construite avec un rendu Jinja2 couplé à **Alpine.js** pour des interactions fluides sans rechargement de page.

### Vues principales (Listes & Dashboards)
- `/dashboard` : Tableau de bord principal avec indicateurs globaux et alertes.
- `/formations` : Catalogue des formations et filtre par domaine.
- `/sessions` : Liste des sessions de formation et filtres par statut / formateur.
- `/clients` : Répertoire des entreprises clientes.
- `/formateurs` : Liste des formateurs internes et externes.
- `/participants` : Répertoire des salariés inscrits.
- `/notifications` : Points d'attention et alertes de gestion.
- `/utilisateurs` : Gestion des comptes utilisateurs (Admin uniquement).

### Vues de détail
- `/sessions/<id>` : Détail d'une session (dates, remplissage, formateur, lieu) et tableau des participants inscrits avec leur statut d'inscription.
- `/clients/<id>` : Fiche d'un client et liste de ses salariés inscrits.
- `/formations/<id>` : Présentation d'une formation et historique de toutes ses sessions.
- `/participants/<id>` : Fiche d'un participant et liste de ses inscriptions aux formations.
- `/utilisateurs/<id>` : Informations sur le compte utilisateur et affichage de la fiche Formateur associée si le compte appartient à un formateur.

---

## 🔌 API REST (Endpoints)

Toutes les réponses de l'API sont envoyées au format JSON. La connexion est obligatoire pour accéder aux endpoints (sauf la connexion `/api/auth/login`).

### Authentification — `/api/auth`
- `POST /api/auth/login` : Connexion (email + mot de passe).
- `POST /api/auth/logout` : Déconnexion.
- `GET /api/auth/me` : Obtenir le profil de l'utilisateur connecté.

### Formations — `/api/formations`
- `GET /api/formations` : Obtenir toutes les formations.
- `GET /api/formations/<id>` : Obtenir le détail d'une formation.
- `POST /api/formations` : Créer une formation (`titre`, `domaine_id`, `duree_jours` entre 2 et 5).
- `PUT /api/formations/<id>` : Modifier une formation.
- `DELETE /api/formations/<id>` : Supprimer une formation.

### Domaines — `/api/domaines`
- `GET /api/domaines` : Obtenir les domaines de formation.
- `GET /api/domaines/<id>` : Obtenir un domaine spécifique.
- `POST /api/domaines` : Créer un domaine.
- `PUT /api/domaines/<id>` : Modifier un domaine.

### Sessions — `/api/sessions`
- `GET /api/sessions` : Obtenir la liste des sessions.  
  *Filtres disponibles* : `?statut=`, `?formateur_id=`, `?formation_id=`
- `GET /api/sessions/<id>` : Obtenir une session avec ses indicateurs (`nb_inscrits_confirmes`, `taux_remplissage`, `est_complete`).
- `POST /api/sessions` : Créer une session (`formation_id`, `formateur_id`, `date_debut`, `date_fin`, `type`, `capacite_max`).
- `PUT /api/sessions/<id>` : Modifier une session.
- `DELETE /api/sessions/<id>` : Supprimer une session.

### Inscriptions — `/api/inscriptions`
- `GET /api/inscriptions` : Obtenir les inscriptions.  
  *Filtres disponibles* : `?session_id=`, `?participant_id=`
- `POST /api/inscriptions` : Inscrire un participant (`session_id`, `participant_id`, `statut`).
- `PUT /api/inscriptions/<id>` : Modifier le statut d'une inscription (`confirmee`, `annulee`, `liste_attente`).

### Clients — `/api/clients`
- `GET /api/clients` : Obtenir la liste des clients.
- `GET /api/clients/<id>` : Obtenir un client spécifique.
- `POST /api/clients` : Créer un client (`nom_entreprise` obligatoire).
- `PUT /api/clients/<id>` : Modifier un client.
- `DELETE /api/clients/<id>` : Supprimer un client.

### Participants — `/api/participants`
- `GET /api/participants` : Obtenir les participants (*Filtre* : `?client_id=`).
- `GET /api/participants/<id>` : Obtenir un participant spécifique.
- `POST /api/participants` : Créer un participant (`nom`, `email`, `client_id`).
- `PUT /api/participants/<id>` : Modifier un participant.
- `DELETE /api/participants/<id>` : Supprimer un participant.

### Formateurs — `/api/formateurs`
- `GET /api/formateurs` : Obtenir les formateurs.
- `GET /api/formateurs/<id>` : Obtenir un formateur spécifique.
- `POST /api/formateurs` : Créer un formateur (`nom`, `domaine_id`).
- `PUT /api/formateurs/<id>` : Modifier un formateur.

### Utilisateurs — `/api/utilisateurs` *(Admin uniquement)*
- `GET /api/utilisateurs` : Obtenir la liste des comptes.
- `GET /api/utilisateurs/<id>` : Obtenir un compte spécifique.
- `POST /api/utilisateurs` : Créer un compte (`nom`, `email`, `mot_de_passe`, `role_id`).
- `PUT /api/utilisateurs/<id>` : Modifier un compte ou réinitialiser le mot de passe.

---

## 🚦 Codes d'erreur HTTP

| Code | Signification |
|---|---|
| **400** | Requête invalide (données manquantes ou incorrectes). |
| **401** | Non authentifié (connexion requise). |
| **403** | Accès interdit (droits insuffisants). |
| **404** | Ressource introuvable. |
| **409** | Conflit (ex: doublon d'email ou suppression impossible d'une donnée liée). |

---

## 📁 Structure du projet

```text
PFA_galaxy_solutions/
├── app/
│   ├── blueprints/    # Routes des pages HTML (render_template)
│   ├── models/        # Modèles SQLAlchemy (9 entités)
│   ├── routes/        # Contrôleurs API REST (JSON)
│   ├── services/      # Logique métier et permissions
│   ├── static/        # Fichiers statiques (CSS, JS Alpine.js)
│   ├── templates/     # Templates HTML Jinja2
│   ├── config.py      # Configuration de l'application
│   └── extensions.py  # Extensions Flask (db, login_manager, migrate)
├── database/          # Schemas et données SQL de démonstration
├── scripts/           # Generator de données de test
├── run.py             # Point d'entrée pour démarrer le serveur
└── requirements.txt   # Dépendances Python
```
