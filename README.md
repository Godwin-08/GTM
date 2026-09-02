# GTM — Galaxy Training Manager

## Sommaire
- [1. Présentation](#1-présentation)
- [2. Contexte du projet](#2-contexte-du-projet)
- [3. Objectifs](#3-objectifs)
- [4. Fonctionnalités principales](#4-fonctionnalités-principales)
- [5. Architecture générale](#5-architecture-générale)
- [6. Technologies utilisées](#6-technologies-utilisées)
- [7. Structure du projet](#7-structure-du-projet)
- [8. Modèle de données](#8-modèle-de-données)
- [9. Rôles et permissions](#9-rôles-et-permissions)
- [10. Règles métier importantes](#10-règles-métier-importantes)
- [11. Statuts des sessions](#11-statuts-des-sessions)
- [12. Gestion des inscriptions](#12-gestion-des-inscriptions)
- [13. Taux de remplissage](#13-taux-de-remplissage)
- [14. Dashboard](#14-dashboard)
- [15. Filtres du Dashboard](#15-filtres-du-dashboard)
- [16. Filtres des autres pages](#16-filtres-des-autres-pages)
- [17. URL et navigation](#17-url-et-navigation)
- [18. Points d'attention](#18-points-dattention)
- [19. Analyse ACP](#19-analyse-acp)
- [20. API REST](#20-api-rest)
- [21. Installation](#21-installation)
- [22. Cloner le projet](#22-cloner-le-projet)
- [23. Créer l'environnement virtuel](#23-créer-lenvironnement-virtuel)
- [24. Installer les dépendances](#24-installer-les-dépendances)
- [25. Configuration](#25-configuration)
- [26. Préparer la base de données](#26-préparer-la-base-de-données)
- [27. Charger les données de démonstration](#27-charger-les-données-de-démonstration)
- [28. Lancer l'application](#28-lancer-lapplication)
- [29. Comptes de démonstration](#29-comptes-de-démonstration)
- [30. Tests](#30-tests)
- [31. Gestion des erreurs](#31-gestion-des-erreurs)
- [32. Sécurité](#32-sécurité)
- [33. Responsive et expérience utilisateur](#33-responsive-et-expérience-utilisateur)
- [34. Démonstration recommandée](#34-démonstration-recommandée)
- [35. Limites connues et perspectives](#35-limites-connues-et-perspectives)
- [36. État du projet](#36-état-du-projet)
- [37. Conclusion](#37-conclusion)

---

## 1. Présentation

**GTM (Galaxy Training Manager)** est une application web développée pour **Galaxy Solutions** afin de centraliser la gestion et le pilotage des activités de formation professionnelle.

L'objectif principal est de remplacer une gestion dispersée des données par un outil unique permettant de :

- gérer les formations ;
- gérer les sessions ;
- gérer les clients ;
- gérer les participants ;
- gérer les formateurs ;
- gérer les inscriptions ;
- suivre l'activité grâce à un tableau de bord réactif ;
- détecter les points d'attention et alertes de gestion ;
- analyser les profils d'activité avec une Analyse en Composantes Principales (ACP).

L'application permet ainsi de passer d'une simple saisie de données à une réelle logique de **pilotage et d'aide à la décision**.

---

## 2. Contexte du projet

Galaxy Solutions propose des formations professionnelles continues destinées principalement aux entreprises B2B.

Les données liées aux formations, aux clients, aux participants et aux sessions de formation sont volumineuses. Lorsqu'elles sont gérées dans des tableaux séparés, il devient difficile de :

- retrouver rapidement une information ;
- suivre la réactivité et l'historique d'un client ;
- connaître en temps réel le taux de remplissage d'une session ;
- identifier les clients inactifs pour la relance commercial ;
- suivre les inscriptions confirmées et les listes d'attente ;
- comparer la dynamique des différents domaines de formation ;
- prendre rapidement des décisions éclairées.

GTM a donc été conçu pour **centraliser l'ensemble de ces informations dans une seule application web sécurisée**.

---

## 3. Objectifs

Les objectifs majeurs du projet sont :

### Objectif 1 — Centraliser
Regrouper les données de formation dans une base de données MySQL structurée et normalisée.

### Objectif 2 — Gérer
Permettre aux utilisateurs autorisés de créer, modifier et suivre l'ensemble des entités métier (formations, sessions, clients, participants, formateurs, inscriptions).

### Objectif 3 — Sécuriser
Sécuriser les accès et restreindre les privilèges selon le rôle de l'utilisateur (RBAC).

### Objectif 4 — Piloter
Fournir des indicateurs clés (KPI) et un système d'alertes dans un tableau de bord synthétique.

### Objectif 5 — Analyser
Utiliser les données disponibles pour analyser les tendances de performance des formateurs et des domaines de formation (via l'ACP).

---

## 4. Fonctionnalités principales

### 4.1 Gestion des formations
L'application permet de :
- consulter la liste des formations au catalogue ;
- rechercher une formation par mot-clé ;
- filtrer les formations par domaine ;
- créer une nouvelle formation (durée, titre, domaine) ;
- modifier une formation existante ;
- consulter le détail d'une formation et l'historique de ses sessions.

Une formation est obligatoirement rattachée à un domaine d'expertise.

---

### 4.2 Gestion des sessions
Une session correspond à une planification réelle d'une formation.

L'application permet de :
- consulter l'ensemble des sessions ;
- rechercher et filtrer les sessions par critères croisés ;
- créer une nouvelle session (dates, lieu, type intra/inter, capacité maximale, formateur référent) ;
- modifier les caractéristiques d'une session ;
- consulter les participants inscrits et leur statut ;
- suivre le nombre de places confirmées et la capacité maximale ;
- calculer le taux de remplissage en temps réel.

Les filtres Sessions peuvent être combinés :
- recherche textuelle `q` ;
- date minimale (`date_debut_min`) et date maximale (`date_debut_max`) ;
- domaine ;
- formation ;
- type (intra / inter) ;
- statut de session (planifiée, en cours, terminée, annulée) ;
- formateur référent ;
- niveau de remplissage (sous-remplie, nominale, complète).

---

### 4.3 Gestion des clients
L'application permet de :
- consulter les entreprises clientes ;
- rechercher un client par nom ou secteur ;
- filtrer par secteur d'activité et statut de réactivité ;
- consulter la fiche détaillée d'un client.

La fiche client présente notamment :
- le nombre de sessions suivies ;
- le nombre de salariés inscrits ;
- le nombre de formations distinctes ;
- la date de dernière activité ;
- l'historique des sessions et la liste des salariés (participants) associés.

---

### 4.4 Gestion des participants
Un participant représente un salarié rattaché à une entreprise cliente.

L'application permet de :
- consulter l'annuaire des participants ;
- rechercher un participant par nom ou email ;
- filtrer par entreprise cliente ;
- consulter la fiche détaillée d'un participant ;
- voir son historique d'inscriptions et son statut pour chaque session.

---

### 4.5 Gestion des formateurs
L'application permet de :
- consulter la liste des formateurs ;
- rechercher un formateur ;
- filtrer par domaine de compétence ;
- consulter la fiche d'un formateur (sessions animées, taux de remplissage moyen, domaine).

---

### 4.6 Gestion des inscriptions
Les inscriptions associent un participant à une session de formation.

Depuis la fiche d'une session, un utilisateur autorisé (Admin / Gestionnaire) peut :
- ajouter un participant à la session ;
- choisir le statut initial de l'inscription ;
- modifier le statut d'une inscription existante avec confirmation et état de chargement ;
- consulter le tableau des inscrits.

Les statuts d'inscription disponibles sont :
- `confirmee` : place réservée comptabilisée dans la capacité.
- `liste_attente` : inscription enregistrée sans consommer de place confirmée.
- `annulee` : inscription annulée conservée dans l'historique.

Une inscription annulée n'est pas supprimée physiquement de la base de données.

---

## 5. Architecture générale

L'application suit une architecture MVC/REST propre et modulaire en couches :

```text
┌─────────────────────────────────────────────────────────┐
│                    Interface Utilisateur                │
│    Jinja2 HTML5  +  Tailwind CSS  +  Alpine.js réactif  │
└────────────────────────────┬────────────────────────────┘
                             │ (Requêtes HTTP & Fetch JSON)
                             ↓
┌─────────────────────────────────────────────────────────┐
│                    API / Contrôleurs                    │
│        Routes REST JSON (app/routes/)                   │
│        Blueprints HTML (app/blueprints/)                │
└────────────────────────────┬────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────┐
│                     Logique Métier                      │
│     Services métier, validations & permissions          │
│     (app/services/)                                     │
└────────────────────────────┬────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────┐
│                     Accès aux données                   │
│     SQLAlchemy ORM (app/models/) & Flask-Login          │
└────────────────────────────┬────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────┐
│                    Base de données                      │
│                 MySQL 8.0 / PyMySQL                     │
└─────────────────────────────────────────────────────────┘
```

Cette séparation nette des responsabilités garantit la maintenabilité du code, la sécurité des accès et la réutilisabilité des services.

---

## 6. Technologies utilisées

### Backend
- **Python 3.11+**
- **Flask 3.1.3**
- **Flask-Login 0.6.3** (gestion des sessions utilisateur)
- **Flask-SQLAlchemy 3.1.1** & **SQLAlchemy 2.0.51** (ORM DB)
- **PyMySQL 1.2.0** (Connecteur MySQL)
- **python-dotenv 1.2.2** (chargement de la configuration `.env`)

### Frontend
- **HTML5**
- **Tailwind CSS** (mise en page moderne et utilitaire)
- **Alpine.js 3.x** (réactivité frontend sans rechargement de page)
- **JavaScript (ES6+)**
- **Chart.js 4.x** (graphiques interactifs)
- **Lucide Icons** (icônes d'interface)

### Analyse & Data
- **NumPy 2.4+** & **Pandas 3.0+** (calculs vectoriels et décomposition factorielle en algebre linéaire `np.linalg.eigh` pour l'ACP)
- **Scikit-learn 1.9+** (inclus dans l'environnement pour extensions analytiques futures)

### Tests & Qualité
- **Python `unittest`** (suite de 93 tests automatisés)

### Gestion de version
- **Git** & **GitHub**

---

## 7. Structure du projet

```text
PFA_galaxy_solutions/
│
├── app/
│   ├── __init__.py                # Initialisation de l'application Flask et enregistrement des Blueprints
│   ├── config.py                  # Configuration centralisée de l'application (.env)
│   ├── extensions.py              # Extensions Flask (db, login_manager, migrate)
│   │
│   ├── blueprints/                # Routes pour le rendu des pages HTML Jinja2
│   │   ├── pages.py               # Contrôleur principal des vues web
│   │   └── ...
│   │
│   ├── models/                    # Modèles SQLAlchemy (9 entités ORM)
│   │   ├── user.py, role.py, domaine.py, formation.py, formateur.py
│   │   └── client.py, participant.py, session.py, inscription.py
│   │
│   ├── routes/                    # Contrôleurs API REST (Réponses JSON)
│   │   ├── auth.py, sessions.py, inscriptions.py, clients.py, participants.py
│   │   └── formateurs.py, formations.py, domaines.py, utilisateurs.py, stats.py
│   │
│   ├── services/                  # Services métier et règles de gestion découplés
│   │   ├── access_service.py              # Contrôle d'accès et scope des requêtes
│   │   ├── client_activity.py           # Calcul des statuts d'activité client
│   │   ├── query_validation_service.py   # Validation robuste des paramètres GET
│   │   ├── session_validation_service.py # Validation des règles de création/modification session
│   │   ├── stats_service.py              # Agrégations et calculs des KPI
│   │   ├── acp_service.py                # Calculs statistiques ACP (NumPy & Pandas)
│   │   └── points_attention_service.py   # Génération des alertes et notifications
│   │
│   ├── static/                    # Ressources statiques
│   │   ├── css/app.css            # Styles additionnels
│   │   └── js/                    # Scripts JS réactifs Alpine.js
│   │       ├── dashboard.js, session_detail.js, inscriptions.js, clients.js...
│   │
│   └── templates/                 # Templates HTML Jinja2
│       ├── base.html              # Layout principal (Sidebar, Header, Toasts)
│       ├── dashboard.html, notifications.html, analytics_acp.html
│       ├── sessions/ (detail.html, liste.html)
│       ├── formations/, clients/, formateurs/, participants/, utilisateurs/
│       └── index.html             # Page d'accueil / Landing page
│
├── database/
│   ├── schema_galaxy_solutions.sql  # Schéma SQL DDL officiel
│   └── seed_demo_data.sql           # Données de démonstration déterministes (536 inscriptions)
│
├── scripts/
│   └── generate_seed_data.py        # Script Python de génération du Seed SQL
│
├── tests/                           # Suite de 93 tests unitaires et d'intégration
│   ├── test_auth.py, test_permissions.py, test_sessions.py, test_client_activity.py
│   ├── test_api_errors.py, test_filters.py, test_acp.py, test_dashboard.py
│   ├── test_coherence_globale.py, test_feedback.py, test_homepage.py, test_seed_generator.py...
│
├── .env.example                     # Modèle d'exemple des variables d'environnement
├── .gitignore                       # Exclusions Git (.env, venv, pycache...)
├── requirements.txt                 # Dépendances Python au format UTF-8
├── README.md                        # Documentation officielle du projet
├── RECETTE_SOUTENANCE.md            # Protocole et scénarios de démonstration pour le jury
└── run.py                           # Point d'entrée serveur Flask (python run.py)
```

---

## 8. Modèle de données

Les entités sont organisées selon le schéma relationnel suivant :

```text
Role (1)
 └── Utilisateur (N)
        │
        └── Formateur (0..1)

Domaine (1)
 └── Formation (N)
        │
        └── Session (N)
                │
                └── Inscription (N)
                       │
                       └── Participant (N)
                              │
                              └── Client (1)
```

### Relations clés
```text
Client
 ↓ (1..N)
Participant
 ↓ (1..N)
Inscription
 ↓ (N..1)
Session
 ↓ (N..1)
Formation
 ↓ (N..1)
Domaine
```

Cette modélisation garantit la traçabilité complète de l'inscription d'un salarié jusqu'au domaine de la formation suivie.

---

## 9. Rôles et permissions

L'accès à l'application est gouverné par trois rôles utilisateur.

### Admin
- Droits d'accès globaux et d'administration.
- Seul rôle autorisé à gérer les comptes utilisateurs (`/utilisateurs` & `/api/utilisateurs`).
- Accès complet aux opérations CRUD sur toutes les entités métier.

### Gestionnaire
- Gestionnaire opérationnel de la formation.
- Droits de création, modification et suppression sur les formations, sessions, clients, participants, formateurs et inscriptions.
- Accès au tableau de bord, aux alertes et à l'ACP.

### Formateur
- Accès restreint en **consultation seule** (mode lecture).
- Accès limité aux sessions dont il est le formateur référent et aux inscrits rattachés.
- **Interdiction stricte d'écriture** : Toute tentative d'exécuter un POST, PUT ou DELETE sur l'API renvoie un code HTTP `403 Forbidden`.

Le contrôle des autorisations est **systématiquement exécuté côté backend** (dans les contrôleurs Flask et les services de permission). Masquer un bouton dans l'interface frontend ne constitue qu'un confort d'ergonomie et non une mesure de sécurité.

---

## 10. Règles métier importantes

### 10.1 Client actif
Un client est qualifié de **Client actif** lorsqu'il possède au moins une inscription `confirmee` associée à une session non annulée dont la date de début (`date_debut`) se situe dans les **6 derniers mois** par rapport à la date actuelle.

```text
Inscription confirmée
  + Session non annulée
  + date_debut entre (aujourd'hui - 6 mois) et aujourd'hui
===========================================================
= Client actif
```

### 10.2 Client inactif
Un client est qualifié de **Client inactif** s'il possède un historique d'inscriptions confirmées dans le passé, mais aucune inscription confirmée sur les 6 derniers mois.

### 10.3 Aucune activité
Un client est classé **Aucune activité** s'il est enregistré en base de données sans aucune inscription confirmée associée.

### 10.4 Session complète
Une session est considérée comme complète (`session.est_complete == True`) dès que :
```text
nb_inscrits_confirmes >= capacite_max
```

### 10.5 Liste d'attente
Une inscription avec le statut `liste_attente` :
- ne consomme pas de place sur la `capacite_max` de la session ;
- peut être enregistrée même si la session est complète ;
- permet de constituer un réservoir de participants en cas de désistement.

---

## 11. Statuts des sessions

Les sessions évoluent selon quatre statuts :
- `planifiee` : Session dont la `date_debut` se situe dans le futur.
- `en_cours` : Session dont la date actuelle est comprise entre `date_debut` et `date_fin`.
- `terminee` : Session dont la `date_fin` est passée.
- `annulee` : Session annulée de manière explicite par un gestionnaire.

Les règles temporelles sont calculées automatiquement, sauf pour le statut `annulee` qui résulte d'une décision d'annulation explicite.

---

## 12. Gestion des inscriptions

Lors de la création d'une inscription, le backend applique une séquence de contrôles stricts :

1. **Session annulée ou terminée** : Inscription impossible (retourne `409 Conflict`).
2. **Doublon de participant** : Un participant ne peut pas être inscrit deux fois à la même session. La table `inscriptions` comporte une contrainte d'unicité `(session_id, participant_id)`. Une tentative de doublon retourne un code `409 Conflict`.
3. **Capacité maximale et statut** :
   - Si la session est complète et que le statut demandé est `confirmee`, le serveur rejette la demande (`409 Conflict`).
   - Si le statut demandé est `liste_attente`, l'inscription est acceptée (`201 Created`).

---

## 13. Taux de remplissage

Le taux de remplissage d'une session est calculé exclusivement à partir des inscriptions confirmées :

$$\text{Taux de remplissage} = \frac{\text{Nombre d'inscrits confirmés}}{\text{Capacité maximale}}$$

Dans les filtres de recherche et l'affichage :
- **Sous-remplie** : Taux < 50 %
- **Nominale** : Taux entre 50 % et < 90 %
- **Complète** : Taux ≥ 90 % (ou `est_complete == True`)

Pour l'affichage de la jauge visuelle HTML, la largeur est limitée visuellement entre `0%` et `100%` (`Math.min(100, Math.max(0, ...))`), tout en conservant l'affichage textuel de la valeur numérique exacte (ex: `110%` en cas de surréservation).

---

## 14. Dashboard

Le tableau de bord principal (`/dashboard`) restitue six indicateurs KPI clés :

1. **Sessions actives** : Nombre de sessions non annulées.
2. **Clients actifs** : Nombre d'entreprises clientes ayant eu une activité confirmée dans les 6 derniers mois.
3. **Participants distincts** : Nombre de salariés uniques ayant au moins une inscription confirmée (un participant inscrit à 3 sessions est compté une seule fois).
4. **Taux moyen de remplissage** : Moyenne des taux de remplissage de l'ensemble des sessions du périmètre.
5. **Formations** : Affiche les *Formations au catalogue* (catalogue global) ou les *Formations dispensées* (si un filtre est actif).
6. **Formateurs mobilisés** : Nombre de formateurs distincts ayant animé au moins une session sur le périmètre.

---

## 15. Filtres du Dashboard

Le Dashboard propose 4 filtres croisés :
- **Année**
- **Domaine**
- **Client**
- **Formateur**

Ces filtres sont combinés avec une logique `AND` et sont appliqués **côté backend** via l'API `/api/stats/kpi-globaux`. Le navigateur ne recalcule pas les indicateurs locaux.

---

## 16. Filtres des autres pages

Chaque page de liste propose des filtres URL combinables :
- **Sessions** : `q`, `date_debut_min`, `date_debut_max`, `domaine_id`, `formation_id`, `type`, `statut`, `formateur_id`, `remplissage`.
- **Formations** : `q`, `domaine_id`.
- **Formateurs** : `q`, `domaine_id`, `type`.
- **Clients** : `q`, `secteur`, `statut_activite`.
- **Participants** : `q`, `client_id`.
- **Inscriptions** : `statut`, `session_id`, `formation_id`, `client_id`, `participant_id`, `date_debut_min`, `date_debut_max`.

---

## 17. URL et navigation

Les filtres appliqués sur les pages de liste sont automatiquement synchronisés dans les paramètres d'URL de votre navigateur (`URLSearchParams`, `window.history.pushState`).

Cela permet de :
- conserver vos filtres actifs lors du rafraîchissement de la page (F5) ;
- partager une URL pré-filtrée ;
- utiliser l'historique du navigateur (boutons Précédent / Suivant).

---

## 18. Points d'attention

Le centre d'alertes et de notifications (`/notifications` et composant cloche du header) génère automatiquement des points d'attention :
- **Sessions planifiées sous-remplies** : Capacity < 40 % à moins de 15 jours de l'échéance (niveau `warning`).
- **Sessions en surréservation** : Remplissage > 100 % (niveau `danger`).
- **Clients inactifs à relancer** : Clients sans activité récente (niveau `info`).

Les alertes s'adaptent dynamiquement au périmètre de filtres sélectionné.

---

## 19. Analyse ACP

Module accessible sur `/analytics-acp`.

L'**Analyse en Composantes Principales (ACP)** est un outil d'**analyse exploratoire et de synthèse descriptive multidimensionnelle** (et non un modèle prédictif).

Développée avec **NumPy et Pandas** (`app/services/acp_service.py`), elle calcule la matrice de corrélation $R$ et exécute une recherche de valeurs/vecteurs propres (`np.linalg.eigh`) pour réduire les dimensions des données d'inscriptions (Clients × Formations) et projeter les entités sur deux axes factoriels principaux.

Elle permet d'analyser visuellement :
- la proximité des profils d'activité clients ;
- la variance expliquée par chaque axe ;
- les qualités de représentation ($\cos^2$) et contributions ($ctr$).

---

## 20. API REST

L'application expose une API REST complète au format JSON sous le préfixe `/api/`.

### Exemples d'endpoints principaux :
- `POST /api/auth/login` — Authentification
- `GET /api/sessions` — Liste des sessions (avec filtres GET)
- `POST /api/sessions` — Création d'une session
- `GET /api/inscriptions` — Inscriptions (avec `?session_id=`)
- `POST /api/inscriptions` — Création d'une inscription
- `PUT /api/inscriptions/<id>` — Modification d'un statut d'inscription
- `GET /api/participants` — Liste des participants (avec `?client_id=`)
- `GET /api/stats/kpi-globaux` — Indicateurs KPI du Dashboard
- `GET /api/stats/points-attention` — Points d'attention
- `GET /api/stats/pca` — Données factorielles de l'ACP

### Format des erreurs JSON :
En cas d'erreur, l'API renvoie un objet JSON standard :
```json
{
  "erreur": "Description explicite du problème métier ou de validation"
}
```

Codes d'erreur HTTP retournés : `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `500 Internal Error`.

---

## 21. Installation

### Prérequis
- Python 3.11 ou supérieur
- Serveur MySQL 8.0+
- Git

Vérification des versions :
```bash
python --version
mysql --version
```

---

## 22. Cloner le projet

```bash
git clone <URL_DU_REPOSITORY>
cd PFA_galaxy_solutions
```

---

## 23. Créer l'environnement virtuel

Sous Windows (PowerShell) :
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Sous Linux / macOS :
```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 24. Installer les dépendances

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 25. Configuration

Copier le fichier modèle `.env.example` vers `.env` :

```powershell
Copy-Item .env.example .env
```

Éditer le fichier `.env` avec vos paramètres locaux :

```env
SECRET_KEY=votre_cle_secrete_production_ici
DB_USER=root
DB_PASSWORD=votre_mot_de_passe_mysql
DB_HOST=localhost
DB_NAME=galaxy_solutions
FLASK_ENV=development
```

*Le fichier `.env` contient vos secrets locaux et ne doit jamais être commité dans Git.*

---

## 26. Préparer la base de données

Créer la base de données MySQL dans votre serveur (ex: via MySQL Workbench ou ligne de commande) :

```sql
CREATE DATABASE galaxy_solutions CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 27. Charger les données de démonstration

Exécuter le script de génération ou importer le fichier SQL fourni dans `database/` :

Dans MySQL Workbench ou CLI :
1. Exécuter `database/schema_galaxy_solutions.sql` (Structure DDL des tables)
2. Exécuter `database/seed_demo_data.sql` (Jeu de données de démo)

Ou régénérer le seed via le script Python :
```powershell
.\venv\Scripts\python.exe scripts/generate_seed_data.py
```

Le jeu de démonstration comprend exactement :
- **3** Rôles
- **3** Domaines
- **6** Utilisateurs
- **10** Formateurs
- **12** Formations
- **30** Clients
- **150** Participants
- **60** Sessions
- **536** Inscriptions

---

## 28. Lancer l'application

Démarrer le serveur de développement Flask :

```powershell
.\venv\Scripts\python.exe run.py
```

L'application est immédiatement accessible à l'adresse :
```text
http://127.0.0.1:5000
```

---

## 29. Comptes de démonstration

Les comptes ci-dessous sont intégrés au Seed officiel pour tester l'application :

| Rôle | Email | Mot de passe | Périmètre de test |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@galaxysolutions.ma` | `Admin@2026` | Privilèges globaux et gestion utilisateurs |
| **Gestionnaire** | `sofia.amrani@galaxysolutions.ma` | `Sofia@2026` | Operations métier et CRUD complet |
| **Gestionnaire** | `yassine.el.idrissi@galaxysolutions.ma` | `Yassine@2026` | Second compte de gestion |
| **Formateur** | `karim.bensouda@galaxysolutions.ma` | `Karim@2026` | Vue restreinte à ses sessions |
| **Formateur** | `nadia.chraibi@galaxysolutions.ma` | `Nadia@2026` | Second compte formateur |
| **Formateur** | `hicham.berrada@galaxysolutions.ma` | `Hicham@2026` | Troisième compte formateur |

---

## 30. Tests

Le projet inclut une suite de tests automatisés couvrant l'authentification, les autorisations RBAC, les filtres, l'activité client, les erreurs API, les inscriptions et la cohérence des données.

Lancer la suite de tests :

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests
```

Résultat du dernier lancement sur la version finale :
```text
Ran 93 tests in 24.823s
OK (0 échec, 0 erreur)
```

---

## 31. Gestion des erreurs

L'application gère les erreurs HTTP avec des réponses structurées :
- `400 Bad Request` : Paramètre GET invalide ou données JSON manquantes.
- `401 Unauthorized` : Session non authentifiée.
- `403 Forbidden` : Tentative d'accès hors privilèges RBAC.
- `404 Not Found` : Ressource introuvable.
- `409 Conflict` : Violation d'une règle métier (session pleine, doublon).
- `500 Internal Server Error` : Erreur interne (les détails d'exception ne sont pas divulgués à l'utilisateur).

---

## 32. Sécurité

Les dispositifs de sécurité mis en œuvre comprennent :
- Authentification sécurisée par cookie de session Flask-Login ;
- Mots de passe stockés sous forme de hash fort (Werkzeug `generate_password_hash`) ;
- Contrôle d'accès RBAC vérifié au niveau backend sur chaque route API ;
- Isolation stricte des données du Formateur ;
- Protection contre les doublons d'inscription par contrainte d'unicité SQL ;
- Fichier de configuration `.env` exclu du dépôt Git (`.gitignore`).

---

## 33. Responsive et expérience utilisateur

L'interface web est entièrement responsive et adaptée aux écrans desktop et mobiles :
- Navigation latérale (Sidebar) rétractable sur mobile ;
- Indicateurs de chargement (spinners Lucide) lors des appels asynchrones ;
- Notification Toasts réactives en bas à droite de l'écran ;
- Transitions CSS Tailwind légères (150-200ms) sans surcharge visuelle.

---

## 34. Démonstration recommandée

Consultez le fichier [RECETTE_SOUTENANCE.md](RECETTE_SOUTENANCE.md) pour obtenir le protocole de démonstration pas-à-pas destiné au jury et à la démonstration orale.

---

## 35. Limites connues et perspectives

L'application répond intégralement au cahier des charges du PFA. Dans une évolution future de production, les axes d'amélioration pourraient inclure :
- un système de pagination côté serveur pour les très grands volumes (> 10 000 entrées) ;
- l'envoi automatisé de convocations et notifications par e-mail SMTP ;
- la mise en place d'une suite de tests E2E automatisés (Cypress / Playwright).

---

## 36. État du projet

```text
Gestion métier            ✅ Validé
Authentification & RBAC   ✅ Validé
Fiches détail             ✅ Validé
Filtres & URL state       ✅ Validé
Dashboard & KPI           ✅ Validé
Points d'attention        ✅ Validé
Analyse ACP               ✅ Validé
CRUD Inscriptions         ✅ Validé
Seed de démonstration     ✅ Validé
Landing page              ✅ Validé
Toasts & Feedback UI      ✅ Validé
Micro-interactions        ✅ Validé
Tests automatisés (93/93) ✅ Validé
Documentation README      ✅ Validé
```

---

## 37. Conclusion

GTM (Galaxy Training Manager) offre à **Galaxy Solutions** un outil centralisé, moderne et sécurisé pour piloter l'ensemble de ses activités de formation.

En combinant **gestion opérationnelle**, **sécurité RBAC**, **tableau de bord décisionnel** et **analyse exploratoire ACP**, GTM transforme la donnée de formation en un levier d'efficacité et d'aide à la décision.
