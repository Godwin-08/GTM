# Galaxy Training Manager (GTM)

Un outil pour suivre et analyser l'activité de formation de Galaxy Solutions.

Il rassemble en un seul endroit toutes les infos sur les formations, les sessions,
les inscriptions, les clients et les formateurs. Il permet aussi de calculer des
chiffres utiles (comme le taux de remplissage des sessions) pour aider à mieux
gérer l'activité.

## Technologies utilisées

- **Backend** : Python, avec le framework Flask et SQLAlchemy (pour parler à la base de données)
- **Base de données** : MySQL
- **Connexion des utilisateurs** : Flask-Login (garde en mémoire qui est connecté)
- **Suivi des changements de la base** : Flask-Migrate

## Comment installer le projet

### 1. Récupérer le projet et créer un environnement virtuel

Un environnement virtuel sert à installer les librairies Python seulement pour ce
projet, sans toucher au reste de ta machine.

```bash
git clone <url-du-depot>
cd galaxy_solutions_app
python -m venv venv
venv\Scripts\Activate.ps1    # sous Windows PowerShell
```

### 2. Installer les librairies nécessaires

```bash
pip install -r requirements.txt
```

### 3. Configurer les informations de connexion

Crée un fichier `.env` à la racine du projet, avec ce contenu (remplace par tes
vraies valeurs) :
```
SECRET_KEY=une_cle_secrete_a_toi

DB_USER=root

DB_PASSWORD=ton_mot_de_passe_mysql

DB_HOST=localhost

DB_NAME=galaxy_solutions

FLASK_ENV=development
```

### 4. Créer la base de données et la remplir

Dans MySQL Workbench, exécute ces deux fichiers dans cet ordre :

```bash
database/schema_galaxy_solutions.sql   # crée les tables (vides)
database/seed_demo_data.sql            # ajoute des données de test réalistes
```

### 5. Démarrer l'application

```bash
python run.py
```

Le serveur démarre à l'adresse `http://127.0.0.1:5000`.

## Comptes pour tester l'application

| Rôle | Email | Mot de passe |
|---|---|---|
| Admin | admin@galaxysolutions.ma | Admin@2026 |
| Gestionnaire | sofia.amrani@galaxysolutions.ma | Sofia@2026 |
| Gestionnaire | yassine.el.idrissi@galaxysolutions.ma | Yassine@2026 |
| Formateur | karim.bensouda@galaxysolutions.ma | Karim@2026 |
| Formateur | nadia.chraibi@galaxysolutions.ma | Nadia@2026 |
| Formateur | hicham.berrada@galaxysolutions.ma | Hicham@2026 |

## Qui peut faire quoi

| Rôle | Ce qu'il peut faire |
|---|---|
| **admin** | Tout, y compris créer et gérer les comptes des autres utilisateurs |
| **gestionnaire** | Créer et modifier les formations, sessions, clients, formateurs, participants, inscriptions |
| **formateur** | Seulement consulter (voir les données, sans pouvoir les modifier) |

## Les endpoints de l'API

Un "endpoint" est une adresse précise de l'application qu'on peut appeler pour
récupérer ou modifier des données. Toutes les réponses sont au format JSON.

Il faut être connecté pour utiliser presque tous les endpoints (sauf la connexion
elle-même).

### Connexion — `/api/auth`

| Méthode | Adresse | Ce que ça fait | Qui peut l'utiliser |
|---|---|---|---|
| POST | `/api/auth/login` | Se connecter (avec email + mot de passe) | Tout le monde |
| POST | `/api/auth/logout` | Se déconnecter | Une personne connectée |
| GET | `/api/auth/me` | Voir les infos de la personne connectée | Une personne connectée |

**Exemple — se connecter avec POST `/api/auth/login`**

Ce qu'on envoie :
```json
{ "email": "admin@galaxysolutions.ma", "mot_de_passe": "Admin@2026" }
```

Ce qu'on reçoit si ça marche :
```json
{
  "message": "Connexion réussie",
  "utilisateur": { "id": 1, "nom": "Admin Galaxy", "email": "admin@galaxysolutions.ma", "role": "admin" }
}
```

### Formations — `/api/formations`

| Méthode | Adresse | Ce que ça fait | Qui peut l'utiliser |
|---|---|---|---|
| GET | `/api/formations` | Voir toutes les formations | Connecté |
| GET | `/api/formations/<id>` | Voir une formation précise | Connecté |
| POST | `/api/formations` | Créer une formation | Gestionnaire ou Admin |
| PUT | `/api/formations/<id>` | Modifier une formation | Gestionnaire ou Admin |

**Pour créer une formation, il faut envoyer** : `titre`, `domaine_id`, `duree_jours`
(entre 2 et 5 jours) — ces 3 champs sont obligatoires. `description` est facultatif.

### Domaines — `/api/domaines`

| Méthode | Adresse | Ce que ça fait | Qui peut l'utiliser |
|---|---|---|---|
| GET | `/api/domaines` | Voir les 3 domaines existants | Connecté |
| GET | `/api/domaines/<id>` | Voir un domaine précis | Connecté |
| POST | `/api/domaines` | Créer un domaine | Gestionnaire ou Admin |
| PUT | `/api/domaines/<id>` | Modifier un domaine | Gestionnaire ou Admin |

### Clients — `/api/clients`

| Méthode | Adresse | Ce que ça fait | Qui peut l'utiliser |
|---|---|---|---|
| GET | `/api/clients` | Voir tous les clients | Connecté |
| GET | `/api/clients/<id>` | Voir un client précis | Connecté |
| POST | `/api/clients` | Créer un client | Gestionnaire ou Admin |
| PUT | `/api/clients/<id>` | Modifier un client | Gestionnaire ou Admin |

**Pour créer un client** : `nom_entreprise` est obligatoire. `secteur` et
`contact_email` sont facultatifs.

### Formateurs — `/api/formateurs`

| Méthode | Adresse | Ce que ça fait | Qui peut l'utiliser |
|---|---|---|---|
| GET | `/api/formateurs` | Voir tous les formateurs | Connecté |
| GET | `/api/formateurs/<id>` | Voir un formateur précis | Connecté |
| POST | `/api/formateurs` | Créer un formateur | Gestionnaire ou Admin |
| PUT | `/api/formateurs/<id>` | Modifier un formateur | Gestionnaire ou Admin |

**Pour créer un formateur** : `nom` et `domaine_id` sont obligatoires. `email`,
`telephone` et `utilisateur_id` (si le formateur a un compte) sont facultatifs.

### Participants — `/api/participants`

| Méthode | Adresse | Ce que ça fait | Qui peut l'utiliser |
|---|---|---|---|
| GET | `/api/participants` | Voir les participants (on peut filtrer par client avec `?client_id=`) | Connecté |
| GET | `/api/participants/<id>` | Voir un participant précis | Connecté |
| POST | `/api/participants` | Créer un participant | Gestionnaire ou Admin |
| PUT | `/api/participants/<id>` | Modifier un participant | Gestionnaire ou Admin |

**Pour créer un participant, il faut** : `nom`, `email`, `client_id` (tous obligatoires).

### Sessions — `/api/sessions`

| Méthode | Adresse | Ce que ça fait | Qui peut l'utiliser |
|---|---|---|---|
| GET | `/api/sessions` | Voir les sessions (filtres possibles : `?statut=` ou `?formateur_id=`) | Connecté |
| GET | `/api/sessions/<id>` | Voir une session précise, avec son taux de remplissage | Connecté |
| POST | `/api/sessions` | Créer une session | Gestionnaire ou Admin |
| PUT | `/api/sessions/<id>` | Modifier une session | Gestionnaire ou Admin |

**Pour créer une session, il faut** : `formation_id`, `formateur_id`, `date_debut`
(format `AAAA-MM-JJ`), `date_fin`, `type` (`intra` ou `inter`), `capacite_max`.
`lieu` et `statut` sont facultatifs.

**Trois informations calculées automatiquement** (pas stockées dans la base, juste
calculées à chaque fois qu'on demande la session) : `nb_inscrits_confirmes` (nombre
de personnes vraiment inscrites), `taux_remplissage` (pourcentage de la capacité
remplie), `est_complete` (vrai ou faux, si la session est pleine).

### Inscriptions — `/api/inscriptions`

| Méthode | Adresse | Ce que ça fait | Qui peut l'utiliser |
|---|---|---|---|
| GET | `/api/inscriptions` | Voir les inscriptions (filtre possible : `?session_id=`) | Connecté |
| POST | `/api/inscriptions` | Inscrire un participant à une session | Gestionnaire ou Admin |
| PUT | `/api/inscriptions/<id>` | Changer le statut d'une inscription | Gestionnaire ou Admin |

**Pour créer une inscription, il faut** : `session_id`, `participant_id`
(obligatoires), `statut` (facultatif, `confirmee` par défaut).

### Utilisateurs — `/api/utilisateurs`

| Méthode | Adresse | Ce que ça fait | Qui peut l'utiliser |
|---|---|---|---|
| GET | `/api/utilisateurs` | Voir tous les comptes | Admin seulement |
| GET | `/api/utilisateurs/<id>` | Voir un compte précis | Admin seulement |
| POST | `/api/utilisateurs` | Créer un compte | Admin seulement |
| PUT | `/api/utilisateurs/<id>` | Modifier un compte | Admin seulement |

**Pour créer un compte, il faut** : `nom`, `email`, `mot_de_passe`, `role_id`
(tous obligatoires).

## Les codes d'erreur que tu peux rencontrer

| Code | Ce que ça veut dire |
|---|---|
| 400 | La requête est mal formée (un champ manque ou est incorrect) |
| 401 | Il faut se connecter d'abord |
| 403 | Tu es connecté, mais ton rôle ne te donne pas le droit de faire ça |
| 404 | La donnée demandée n'existe pas |
| 409 | Conflit — par exemple, un email déjà utilisé par un autre compte |

## Comment le projet est organisé

``` 

galaxy_solutions_app/

├── app/

│   ├── models/       # Les 9 entités de la base de données (une classe par entité)

│   ├── routes/       # Les endpoints de l'API (un fichier par entité)

│   ├── services/      # La logique métier (permissions, calculs de stats)

│   └── config.py      # La configuration (lit le fichier .env)

├── database/          # Les scripts SQL (création des tables + données de test)

├── scripts/           # Le script qui génère les données de démonstration

└── run.py             # Le fichier qui démarre l'application

```
