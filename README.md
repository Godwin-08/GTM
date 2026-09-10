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
- [20. Exports métier](#20-exports-métier)
- [21. Profil utilisateur](#21-profil-utilisateur)
- [22. API REST](#22-api-rest)
- [23. Installation](#23-installation)
- [24. Cloner le projet](#24-cloner-le-projet)
- [25. Créer l'environnement virtuel](#25-créer-lenvironnement-virtuel)
- [26. Installer les dépendances](#26-installer-les-dépendances)
- [27. Configuration](#27-configuration)
- [28. Préparer la base de données](#28-préparer-la-base-de-données)
- [29. Charger les données de démonstration](#29-charger-les-données-de-démonstration)
- [30. Lancer l'application](#30-lancer-lapplication)
- [31. Comptes de démonstration](#31-comptes-de-démonstration)
- [32. Tests](#32-tests)
- [33. Gestion des erreurs](#33-gestion-des-erreurs)
- [34. Sécurité](#34-sécurité)
- [35. Responsive et expérience utilisateur](#35-responsive-et-expérience-utilisateur)
- [36. Démonstration recommandée](#36-démonstration-recommandée)
- [37. Limites connues et perspectives](#37-limites-connues-et-perspectives)
- [38. État du projet](#38-état-du-projet)
- [39. Conclusion](#39-conclusion)

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
- exporter les données métier en CSV, Excel stylisé et PDF ;
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
- supprimer une formation (uniquement si aucune session n'y est associée) ;
- consulter le détail d'une formation et l'historique de ses sessions ;
- exporter le catalogue de formations en CSV et Excel.

Une formation est obligatoirement rattachée à un domaine d'expertise.

---

### 4.2 Gestion des sessions
Une session correspond à une planification réelle d'une formation.

L'application permet de :
- consulter l'ensemble des sessions ;
- rechercher et filtrer les sessions par critères croisés ;
- créer une nouvelle session (dates, lieu, type intra/inter, capacité maximale, formateur référent) ;
- modifier les caractéristiques d'une session ;
- supprimer une session (uniquement si aucune inscription n'y est associée) ;
- consulter les participants inscrits et leur statut ;
- suivre le nombre de places confirmées et la capacité maximale ;
- calculer le taux de remplissage en temps réel ;
- exporter les sessions en CSV, Excel et PDF (feuille d'émargement).

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
- créer un nouveau client ;
- modifier un client existant ;
- supprimer un client (uniquement s'il n'a aucun participant rattaché) ;
- consulter la fiche détaillée d'un client ;
- exporter la liste des clients en CSV et Excel.

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
- créer un nouveau participant ;
- modifier un participant existant ;
- supprimer un participant (uniquement s'il n'a aucune inscription associée) ;
- consulter la fiche détaillée d'un participant ;
- voir son historique d'inscriptions et son statut pour chaque session ;
- exporter les participants en CSV et Excel.

---

### 4.5 Gestion des formateurs
L'application permet de :
- consulter la liste des formateurs ;
- rechercher un formateur ;
- filtrer par domaine de compétence et par type (interne / externe) ;
- créer un nouveau formateur (avec liaison optionnelle à un compte utilisateur) ;
- modifier un formateur existant ;
- consulter la fiche d'un formateur (sessions animées, taux de remplissage moyen, domaine).

---

### 4.6 Gestion des inscriptions
Les inscriptions associent un participant à une session de formation.

Depuis la fiche d'une session, un utilisateur autorisé (Admin / Gestionnaire) peut :
- ajouter un participant à la session ;
- choisir le statut initial de l'inscription ;
- modifier le statut d'une inscription existante avec confirmation et état de chargement ;
- consulter le tableau des inscrits ;
- exporter les inscriptions en CSV et Excel.

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
- **Flask-Migrate 4.1.0** & **Alembic 1.19** (migrations de schéma)
- **PyMySQL 1.2.0** (Connecteur MySQL)
- **python-dotenv 1.2.2** (chargement de la configuration `.env`)
- **Werkzeug 3.1.8** (hachage PBKDF2-SHA256, utilitaires HTTP)

### Frontend
- **HTML5**
- **Tailwind CSS** (mise en page moderne et utilitaire)
- **Alpine.js 3.x** (réactivité frontend sans rechargement de page)
- **JavaScript (ES6+)**
- **Chart.js 4.x** (graphiques interactifs)
- **Lucide Icons** (icônes d'interface)

### Exports & Documents
- **openpyxl 3.1.5** (exports Excel XLSX stylisés)
- **ReportLab 5.0.1** (génération de rapports PDF et feuilles d'émargement)

### Analyse & Data
- **NumPy 2.4+** & **Pandas 3.0+** (calculs vectoriels et décomposition factorielle en algebre linéaire `np.linalg.eigh` pour l'ACP)
- **Scikit-learn 1.9+** (inclus dans l'environnement pour extensions analytiques futures)

### Tests & Qualité
- **Pytest 9.x** & **Python `unittest`** (suite de 120 tests automatisés)

### Gestion de version
- **Git** & **GitHub**

---

## 7. Structure du projet

```text
PFA_galaxy_solutions/
│
├── app/
│   ├── __init__.py                # Factory Flask et enregistrement des Blueprints
│   ├── config.py                  # Configuration centralisée (.env, DB, mail)
│   ├── extensions.py              # Extensions Flask (db, login_manager, migrate)
│   │
│   ├── blueprints/                # Routes pour le rendu des pages HTML Jinja2
│   │   └── pages.py               # Contrôleur principal des vues web (19 routes)
│   │
│   ├── models/                    # Modèles SQLAlchemy (9 entités ORM)
│   │   ├── __init__.py            # Registre des modèles
│   │   ├── role.py                # Rôle utilisateur (admin, gestionnaire, formateur)
│   │   ├── utilisateur.py         # Utilisateur avec onboarding (token, activation)
│   │   ├── domaine.py             # Domaine d'expertise
│   │   ├── formation.py           # Formation au catalogue
│   │   ├── formateur.py           # Formateur (interne lié à un utilisateur / externe)
│   │   ├── client.py              # Entreprise cliente
│   │   ├── participant.py         # Salarié rattaché à un client
│   │   ├── session.py             # Session de formation planifiée
│   │   └── inscription.py         # Inscription d'un participant à une session
│   │
│   ├── routes/                    # Contrôleurs API REST (Réponses JSON)
│   │   ├── auth.py                # Authentification, activation, changement de mot de passe
│   │   ├── sessions.py            # CRUD sessions + exports CSV/XLSX/PDF
│   │   ├── inscriptions.py        # CRUD inscriptions + exports CSV/XLSX
│   │   ├── clients.py             # CRUD clients + exports CSV/XLSX
│   │   ├── participants.py        # CRUD participants + exports CSV/XLSX
│   │   ├── formateurs.py          # CRUD formateurs
│   │   ├── formations.py          # CRUD formations + exports CSV/XLSX
│   │   ├── domaines.py            # Liste des domaines
│   │   ├── utilisateurs.py        # Gestion des comptes (Admin) + onboarding
│   │   └── stats.py               # KPI, graphiques, points d'attention, ACP, PDF dashboard
│   │
│   ├── services/                  # Services métier et règles de gestion découplés
│   │   ├── access_service.py              # Contrôle d'accès et scope des requêtes par rôle
│   │   ├── permissions.py                 # Décorateurs de restriction d'accès RBAC
│   │   ├── activation_service.py          # Génération et validation des tokens d'activation
│   │   ├── mail_service.py                # Service de messagerie (Console / SMTP)
│   │   ├── client_activity_service.py     # Calcul des statuts d'activité client
│   │   ├── query_validation_service.py    # Validation robuste des paramètres GET
│   │   ├── session_validation_service.py  # Validation des règles de création/modification session
│   │   ├── stats_service.py               # Agrégations et calculs des KPI
│   │   ├── acp_service.py                 # Calculs statistiques ACP (NumPy & Pandas)
│   │   ├── points_attention_service.py    # Génération des alertes et notifications
│   │   └── export_service.py              # Exports CSV, Excel stylisé et PDF (ReportLab)
│   │
│   ├── static/                    # Ressources statiques
│   │   ├── css/app.css            # Styles additionnels
│   │   ├── img/                   # Images et icônes (favicon.svg, gtm-logo.svg)
│   │   └── js/                    # Scripts JS réactifs Alpine.js (16 modules)
│   │       ├── dashboard.js           # Tableau de bord KPI et graphiques
│   │       ├── sessions.js            # Page liste des sessions
│   │       ├── session_detail.js      # Fiche détail session et inscriptions
│   │       ├── formations.js          # Page liste des formations
│   │       ├── formation_detail.js    # Fiche détail formation
│   │       ├── clients.js             # Page liste des clients
│   │       ├── client_detail.js       # Fiche détail client
│   │       ├── participants.js        # Page liste des participants
│   │       ├── participant_detail.js  # Fiche détail participant
│   │       ├── formateurs.js          # Page liste des formateurs
│   │       ├── inscriptions.js        # Page liste des inscriptions
│   │       ├── utilisateurs.js        # Page gestion des utilisateurs
│   │       ├── utilisateur_detail.js  # Fiche détail utilisateur
│   │       ├── notifications.js       # Centre de notifications
│   │       ├── points_attention.js    # Widget points d'attention
│   │       └── acp.js                 # Module Analyse en Composantes Principales
│   │
│   ├── templates/                 # Templates HTML Jinja2 (20 fichiers)
│   │   ├── base.html              # Layout principal (Sidebar, Header, Profil, Toasts)
│   │   ├── login.html             # Page de connexion
│   │   ├── dashboard.html         # Tableau de bord principal
│   │   ├── notifications.html     # Centre d'alertes
│   │   ├── design-system-preview.html  # Aperçu du design system
│   │   ├── auth/
│   │   │   └── activation.html         # Page d'activation de compte
│   │   ├── analytics/
│   │   │   └── acp.html                # Module Analyse ACP
│   │   ├── components/
│   │   │   └── empty_state.html        # Composant état vide réutilisable
│   │   ├── sessions/
│   │   │   ├── liste.html              # Liste des sessions
│   │   │   └── detail.html             # Fiche détail session
│   │   ├── formations/
│   │   │   ├── liste.html              # Catalogue des formations
│   │   │   └── detail.html             # Fiche détail formation
│   │   ├── clients/
│   │   │   ├── liste.html              # Liste des clients
│   │   │   └── detail.html             # Fiche détail client
│   │   ├── participants/
│   │   │   ├── liste.html              # Annuaire des participants
│   │   │   └── detail.html             # Fiche détail participant
│   │   ├── formateurs/
│   │   │   └── liste.html              # Liste des formateurs
│   │   ├── inscriptions/
│   │   │   └── liste.html              # Liste des inscriptions
│   │   └── utilisateurs/
│   │       ├── liste.html              # Gestion des comptes (Admin)
│   │       └── detail.html             # Fiche détail utilisateur
│   │
│   └── utils/                     # Utilitaires techniques
│       └── __init__.py
│
├── database/
│   ├── schema_galaxy_solutions.sql  # Schéma SQL DDL officiel
│   └── seed_demo_data.sql           # Données de démonstration déterministes (536 inscriptions)
│
├── scripts/
│   ├── generate_seed_data.py        # Script Python de génération du Seed SQL
│   └── migrate_onboarding_columns.py  # Migration des colonnes onboarding
│
├── tests/                           # Suite de 120 tests unitaires et d'intégration (18 fichiers)
│   ├── test_auth.py                 # Authentification et login
│   ├── test_permissions.py          # Autorisations RBAC
│   ├── test_sessions.py             # CRUD sessions
│   ├── test_client_activity.py      # Calcul d'activité client
│   ├── test_api_errors.py           # Gestion des erreurs API
│   ├── test_filters.py              # Filtres combinés
│   ├── test_acp.py                  # Analyse en Composantes Principales
│   ├── test_dashboard.py            # KPI et tableau de bord
│   ├── test_onboarding.py           # Parcours d'onboarding
│   ├── test_mail_service.py         # Service de messagerie
│   ├── test_e2e_onboarding_lifecycle.py  # Cycle de vie onboarding E2E
│   ├── test_coherence_globale.py    # Cohérence inter-entités
│   ├── test_feedback.py             # Feedback utilisateur
│   ├── test_homepage.py             # Page d'accueil et redirections
│   ├── test_seed_generator.py       # Générateur de données de démo
│   ├── test_exports.py              # Exports CSV, Excel et PDF
│   └── test_phase1_fiabilisation.py # Fiabilisation phase 1
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
- Dispose d'un **tableau de bord personnalisé** (`/dashboard-formateur`) affichant ses propres indicateurs d'activité (voir section 14.1).

Le contrôle des autorisations est **systématiquement exécuté côté backend** (dans les contrôleurs Flask et les services de permission). Masquer un bouton dans l'interface frontend ne constitue qu'un confort d'ergonomie et non une mesure de sécurité.

### 9.1 Parcours d'Onboarding & Cycle d'Activation Sécurisé

GTM implémente un parcours d'onboarding utilisateur d'entreprise sécurisé, sans manipulation manuelle de mots de passe temporaires :

```text
ADMIN
  ↓ Crée l'utilisateur (Nom + Email pro + Rôle)
GTM
  ↓ Génère un compte "En attente d'activation" (actif=False)
  ↓ Génère un token cryptographique aléatoire unique (secrets, validité 48h)
  ↓ Stocke uniquement le hash SHA-256 en base (aucun token en clair)
SERVICE MESSAGERIE
  ├── Mode Console (démo locale / soutenance) : lien affiché dans les logs + copiable dans l'UI
  └── Mode SMTP (production) : envoi du courriel transactionnel charté Galaxy Solutions
COLLABORATEUR
  ↓ Reçoit l'invitation et clique sur /activation/<token>
  ↓ Vérification de validité et de non-expiration en temps constant
  ↓ Définit son propre mot de passe sécurisé (min. 8 caractères)
GTM
  ↓ Hache le mot de passe (PBKDF2-SHA256), active le compte (actif=True) et purge le token
COLLABORATEUR
  ↓ Se connecte sur /login et accède à son espace selon son rôle RBAC
```

**Points forts de sécurité de l'onboarding :**
- **Zéro mot de passe temporaire en clair** : Le mot de passe final est choisi exclusivement par le collaborateur.
- **Token à usage unique** : Purge irréversible après activation avec protection anti-rejeu.
- **Durée de vie limitée** : Expiration automatique après 48h (renouvelable en un clic par l'Admin via l'action *« Renvoyer l'invitation »*).
- **Résilience SMTP** : Si le serveur SMTP est injoignable, le compte reste créé en statut *« En attente »*, l'Admin peut copier le lien direct d'activation et réexpédier l'invitation dès le rétablissement du réseau.

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

### 10.6 Suppression sécurisée
Les suppressions suivent des règles d'intégrité référentielle :
- Une **formation** ne peut être supprimée que si aucune session n'y est associée.
- Une **session** ne peut être supprimée que si aucune inscription n'y est associée.
- Un **client** ne peut être supprimé que si aucun participant n'y est rattaché.
- Un **participant** ne peut être supprimé que si aucune inscription n'y est associée.

En cas de tentative de suppression violant ces contraintes, l'API retourne un code `409 Conflict` avec un message explicite indiquant le nombre d'entités liées.

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

Le dashboard intègre également des **graphiques interactifs** (Chart.js) :
- Activité par domaine
- Activité par client
- Activité par formateur
- Évolution des inscriptions
- Taux de remplissage global

### 14.1 Dashboard Formateur (`/dashboard-formateur`)

En complément du tableau de bord global réservé aux rôles Admin et Gestionnaire, le rôle **Formateur** dispose d'un **espace de synthèse personnalisé** accessible à `/dashboard-formateur`. C'est la page d'accueil du formateur après connexion.

Il restitue **4 indicateurs KPI personnels** :

1. **Mes sessions** : Nombre total de sessions animées (non annulées).
2. **À venir** : Nombre de sessions planifiées à partir d'aujourd'hui.
3. **Taux de remplissage moyen** : Moyenne des taux de remplissage de ses propres sessions, avec jauge visuelle.
4. **Participants formés** : Nombre de participants distincts ayant une inscription confirmée sur ses sessions.

Il affiche également :
- **Répartition par domaine** : Barres de progression proportionnelles au nombre de sessions par domaine.
- **Mes prochaines sessions** : Liste des 5 prochaines sessions avec date, lieu, ratio inscrits/capacité et badge de remplissage coloré.

> Les données sont chargées via `GET /api/stats/kpi-formateur`, un endpoint strictement isolé : il ne renvoie que les données du formateur connecté et renvoie `403 Forbidden` à tout autre rôle.

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
- **Inscriptions** : `q`, `statut`, `session_id`, `formation_id`, `client_id`, `participant_id`, `date_debut_min`, `date_debut_max`.

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

Le badge de la cloche de notification dans le header affiche un **compteur numérique** du nombre d'alertes actives, avec gestion de l'état « déjà vu » via `sessionStorage`.

---

## 19. Analyse ACP

Module accessible sur `/analytics/acp`.

L'**Analyse en Composantes Principales (ACP)** est un outil d'**analyse exploratoire et de synthèse descriptive multidimensionnelle** (et non un modèle prédictif).

Développée avec **NumPy et Pandas** (`app/services/acp_service.py`), elle calcule la matrice de corrélation $R$ et exécute une recherche de valeurs/vecteurs propres (`np.linalg.eigh`) pour réduire les dimensions des données d'inscriptions (Clients × Formations) et projeter les entités sur deux axes factoriels principaux.

Elle propose une **interface pédagogique avec l'identité visuelle Violet Analytics (`#7C3AED`)** :
- **Zone pédagogique "Qu'est-ce que vous regardez ?"** : explications claires des axes F1/F2, de la proximité des points et de la distance du centre ;
- **Qualité de représentation ($\cos^2$) vulgarisée en %** avec badges d'évaluation ("Excellente 87%", "Bonne 55%", "Faible 32%") ;
- **Poids sur les tendances (CTR %)** explicités et qualifiés ("Majeur", "Moyen", "Faible") ;
- **Synthèse automatique des profils** : détection visuelle des profils atypiques et des paires de clients les plus similaires ;
- **Bandeau de périmètre global** rappelant que l'ACP analyse l'intégralité du portefeuille de l'entreprise.

---

## 20. Exports métier

GTM propose un système d'export complet pour l'ensemble des entités métier :

### 20.1 Export CSV (UTF-8 avec BOM)
Tous les modules disposent d'un export CSV compatible Excel, LibreOffice et Google Sheets :
- Sessions, Formations, Clients, Participants, Inscriptions.
- Encodage `utf-8-sig` pour un affichage correct des caractères accentués dans Excel.

### 20.2 Export Excel (XLSX stylisé)
Exports Excel avec mise en forme professionnelle (openpyxl) :
- En-têtes colorés Emerald Galaxy Solutions (`#047857`).
- Alternance de couleurs de lignes, bordures fines, largeurs de colonnes ajustées.
- Sessions, Formations, Clients, Participants, Inscriptions.

### 20.3 Export PDF
- **Feuille d'émargement PDF** : Générée depuis la fiche détail d'une session, contenant la liste des inscrits, les informations de la session et un espace de signature.
- **Rapport de synthèse et pilotage décisionnel PDF** : Exporté depuis le tableau de bord avec les KPI globaux, les points d'attention et les filtres actifs appliqués.

Les exports sont générés par le service `app/services/export_service.py` via **ReportLab** (PDF) et **openpyxl** (XLSX).

---

## 21. Profil utilisateur

Chaque utilisateur connecté dispose d'un **modal de profil** accessible depuis le header de l'application, présentant :
- Son identité (nom, email, rôle).
- Un formulaire sécurisé de **changement de mot de passe** nécessitant la saisie de l'ancien mot de passe, la définition d'un nouveau mot de passe (min. 8 caractères) et la vérification que le nouveau mot de passe est différent de l'ancien.

---

## 22. API REST

L'application expose une API REST complète au format JSON sous le préfixe `/api/`.

### Authentification & Compte
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Authentification par session sécurisée |
| `POST` | `/api/auth/logout` | Déconnexion et invalidation de session |
| `GET` | `/api/auth/me` | Informations de l'utilisateur connecté |
| `POST` | `/api/auth/changer-mot-de-passe` | Changement de mot de passe sécurisé |
| `POST` | `/api/auth/activer-compte` | Activation de compte par token unique |
| `GET` | `/api/auth/verifier-token/<token>` | Pré-vérification de validité d'un lien d'activation |

### Utilisateurs (Admin uniquement)
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/utilisateurs` | Répertoire des utilisateurs internes |
| `GET` | `/api/utilisateurs/<id>` | Détail d'un utilisateur |
| `POST` | `/api/utilisateurs` | Création d'un utilisateur + invitation d'activation |
| `PUT` | `/api/utilisateurs/<id>` | Modification d'un utilisateur |
| `POST` | `/api/utilisateurs/<id>/renvoyer-invitation` | Régénération et réexpédition de l'invitation |

### Sessions
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/sessions` | Liste des sessions (avec filtres GET combinables) |
| `GET` | `/api/sessions/<id>` | Détail d'une session |
| `POST` | `/api/sessions` | Création d'une session |
| `PUT` | `/api/sessions/<id>` | Modification d'une session |
| `DELETE` | `/api/sessions/<id>` | Suppression (si aucune inscription) |
| `GET` | `/api/sessions/export/csv` | Export sessions filtrées en CSV |
| `GET` | `/api/sessions/export/xlsx` | Export sessions filtrées en Excel |
| `GET` | `/api/sessions/<id>/export/pdf` | Feuille d'émargement officielle en PDF |

### Formations
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/formations` | Liste des formations (avec filtres) |
| `GET` | `/api/formations/<id>` | Détail d'une formation |
| `POST` | `/api/formations` | Création d'une formation |
| `PUT` | `/api/formations/<id>` | Modification d'une formation |
| `DELETE` | `/api/formations/<id>` | Suppression (si aucune session) |
| `GET` | `/api/formations/export/csv` | Export catalogue en CSV |
| `GET` | `/api/formations/export/xlsx` | Export catalogue en Excel |

### Clients
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/clients` | Liste des clients (avec filtres) |
| `GET` | `/api/clients/<id>` | Détail d'un client |
| `POST` | `/api/clients` | Création d'un client |
| `PUT` | `/api/clients/<id>` | Modification d'un client |
| `DELETE` | `/api/clients/<id>` | Suppression (si aucun participant) |
| `GET` | `/api/clients/export/csv` | Export clients filtrés en CSV |
| `GET` | `/api/clients/export/xlsx` | Export clients filtrés en Excel |

### Participants
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/participants` | Liste des participants (avec filtres) |
| `GET` | `/api/participants/<id>` | Détail d'un participant |
| `POST` | `/api/participants` | Création d'un participant |
| `PUT` | `/api/participants/<id>` | Modification d'un participant |
| `DELETE` | `/api/participants/<id>` | Suppression (si aucune inscription) |
| `GET` | `/api/participants/export/csv` | Export participants en CSV |
| `GET` | `/api/participants/export/xlsx` | Export participants en Excel |

### Formateurs
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/formateurs` | Liste des formateurs (avec filtres) |
| `GET` | `/api/formateurs/<id>` | Détail d'un formateur |
| `POST` | `/api/formateurs` | Création d'un formateur |
| `PUT` | `/api/formateurs/<id>` | Modification d'un formateur |

### Inscriptions
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/inscriptions` | Liste des inscriptions (avec filtres combinables) |
| `POST` | `/api/inscriptions` | Création d'une inscription |
| `PUT` | `/api/inscriptions/<id>` | Modification du statut d'une inscription |
| `GET` | `/api/inscriptions/export/csv` | Export inscriptions filtrées en CSV |
| `GET` | `/api/inscriptions/export/xlsx` | Export inscriptions filtrées en Excel |

### Domaines
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/domaines` | Liste des domaines d'expertise |

### Statistiques & Dashboard
| Méthode | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/stats/kpi-globaux` | Indicateurs KPI du Dashboard (Admin & Gestionnaire) |
| `GET` | `/api/stats/kpi-formateur` | KPIs personnels du formateur connecté (Formateur uniquement) |
| `GET` | `/api/stats/remplissage` | Taux de remplissage global |
| `GET` | `/api/stats/activite-domaine` | Activité par domaine |
| `GET` | `/api/stats/activite-client` | Activité par client |
| `GET` | `/api/stats/activite-formateur` | Activité par formateur |
| `GET` | `/api/stats/evolution-inscriptions` | Évolution temporelle des inscriptions |
| `GET` | `/api/stats/points-attention` | Points d'attention et alertes |
| `GET` | `/api/stats/pca` | Données factorielles de l'ACP |
| `GET` | `/api/stats/export/pdf` | Rapport de synthèse & pilotage décisionnel en PDF |

### Format des erreurs JSON :
En cas d'erreur, l'API renvoie un objet JSON standard :
```json
{
  "erreur": "Description explicite du problème métier ou de validation"
}
```

Codes d'erreur HTTP retournés : `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `500 Internal Error`.

---

## 23. Installation

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

## 24. Cloner le projet

```bash
git clone <URL_DU_REPOSITORY>
cd PFA_galaxy_solutions
```

---

## 25. Créer l'environnement virtuel

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

## 26. Installer les dépendances

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 27. Configuration

Copier le fichier modèle `.env.example` vers `.env` :

```powershell
Copy-Item .env.example .env
```

Éditer le fichier `.env` avec vos paramètres locaux :

```env
# Base de données
SECRET_KEY=votre_cle_secrete_production_ici
DB_USER=root
DB_PASSWORD=votre_mot_de_passe_mysql
DB_HOST=localhost
DB_NAME=galaxy_solutions
FLASK_ENV=development

# Messagerie transactionnelle Onboarding
# Mode local / démo : console (aucun serveur SMTP requis, lien affiché dans les logs)
# Mode production : smtp
MAIL_BACKEND=console
MAIL_SERVER=localhost
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=Galaxy Training Manager <no-reply@gtm.galaxysolutions.ma>
APP_BASE_URL=http://127.0.0.1:5000
# En production : APP_BASE_URL=https://gtm.galaxysolutions.ma
```

*Le fichier `.env` contient vos secrets locaux et ne doit jamais être commité dans Git.*

---

## 28. Préparer la base de données

Créer la base de données MySQL dans votre serveur (ex: via MySQL Workbench ou ligne de commande) :

```sql
CREATE DATABASE galaxy_solutions CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 29. Charger les données de démonstration

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

## 30. Lancer l'application

Démarrer le serveur de développement Flask :

```powershell
.\venv\Scripts\python.exe run.py
```

L'application est immédiatement accessible à l'adresse :
```text
http://127.0.0.1:5000
```

---

## 31. Comptes de démonstration

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

## 32. Tests

Le projet inclut une suite de tests automatisés exhaustive couvrant l'authentification, le parcours d'onboarding, les autorisations RBAC, les filtres, l'activité client, les erreurs API, les inscriptions, les exports métier (Excel/PDF/CSV) et la cohérence des données.

Lancer la suite de tests complète :

```powershell
.\venv\Scripts\pytest.exe
```

Résultat du dernier lancement sur la version finale :
```text
============================ 120 passed in 34.65s =============================
OK (120 tests validés, 100% de réussite)
```

---

## 33. Gestion des erreurs

L'application gère les erreurs HTTP avec des réponses structurées :
- `400 Bad Request` : Paramètre GET invalide, token expiré/invalide ou données JSON manquantes.
- `401 Unauthorized` : Session non authentifiée ou compte non encore activé.
- `403 Forbidden` : Tentative d'accès hors privilèges RBAC.
- `404 Not Found` : Ressource introuvable.
- `409 Conflict` : Violation d'une règle métier (session pleine, doublon, suppression avec dépendances).
- `500 Internal Server Error` : Erreur interne (les détails d'exception ne sont pas divulgués à l'utilisateur).

---

## 34. Sécurité

Les dispositifs de sécurité mis en œuvre comprennent :
- Authentification sécurisée par cookie de session Flask-Login ;
- Mots de passe stockés sous forme de hash fort (PBKDF2:SHA256 via Werkzeug) ;
- **Parcours d'onboarding sans mot de passe initial** avec token cryptographique aléatoire unique (48h) et comparaison en temps constant (`hmac.compare_digest`) ;
- **Changement de mot de passe sécurisé** avec vérification de l'ancien mot de passe et validation de la force du nouveau ;
- Contrôle d'accès RBAC vérifié au niveau backend sur chaque route API ;
- Isolation stricte des données du Formateur ;
- Protection contre les doublons d'inscription par contrainte d'unicité SQL ;
- Protection contre la suppression d'entités ayant des dépendances (intégrité référentielle) ;
- Fichier de configuration `.env` exclu du dépôt Git (`.gitignore`).

---

## 35. Responsive et expérience utilisateur

L'interface web est entièrement responsive et adaptée aux écrans desktop et mobiles :
- Navigation latérale (Sidebar) rétractable sur mobile ;
- Indicateurs de chargement (spinners Lucide) lors des appels asynchrones ;
- Notification Toasts réactives en bas à droite de l'écran ;
- Transitions CSS Tailwind légères (150-200ms) sans surcharge visuelle ;
- Composant état vide (`empty_state`) pour les listes sans résultat ;
- Badge compteur numérique sur la cloche de notifications.

### 35.1 Identité visuelle — Logo G-Growth

GTM dispose d'une identité visuelle propre : le logo **G-Growth**, un monogramme G construit avec trois barres ascendantes symbolisant la progression des compétences.

- **Couleurs** : Orange `#F26B1F` (marque Galaxy Solutions) + fond Ardoise `#0F172A`
- **Format** : SVG vectoriel, décliné en version transparente (`gtm-logo.svg`) et favicon (`favicon.svg`)
- **Intégration** : Sidebar, page de connexion (`login.html`), page d'activation (`activation.html`), email transactionnel

### 35.2 Animations du Dashboard

Le tableau de bord applique des animations professionnelles et sobres, adaptées au contexte B2B :
- **Entrée en fondu décalée** : Les 6 cartes KPI apparaissent en séquence avec un délai de 40 ms entre chaque (`@keyframes gtmFadeInUp`, classes `.gtm-fade-in` + `.gtm-delay-1` à `.gtm-delay-6`)
- **Survol des cartes KPI** : Légère élévation (`translateY(-2px)`) et accentuation de l'ombre portée au survol
- **Graphiques Chart.js animés** : Barre par domaine (couleurs emerald/blue/orange/purple), animation `easeOutQuart` 650 ms ; courbe d'inscriptions en vert emerald, animation 750 ms ; tooltips sombres (`#0F172A`, police Inter)

### 35.3 Cartes de formations colorées

La page catalogue des formations (`/formations`) présente chaque formation avec un bandeau de couleur par domaine :

| Domaine | Couleur | Icône |
| :--- | :--- | :--- |
| Cybersécurité | Emerald `#059669` | `shield-check` |
| Web & Data | Bleu `#2563EB` | `code-2` |
| Management Agile | Orange `#F26B1F` | `zap` |

Au survol, la carte se lève légèrement et le titre de la formation passe en orange.

### 35.4 Effet de survol des lignes de tableau

Sur tous les tableaux de l'application, le passage de la souris sur une ligne déclenche un effet d'attention discret :
- **Fond teinté** : `slate-100` avec transition fluide 150 ms
- **Texte renforcé** : Passage en `slate-900` pour un meilleur contraste
- **Liseré orange** : Bordure de 3 px sur le bord gauche de la première cellule (`box-shadow: inset 3px 0 0 var(--gtm-primary)`) — effet de sélection professionnel

---

## 36. Démonstration recommandée

Consultez le fichier [RECETTE_SOUTENANCE.md](RECETTE_SOUTENANCE.md) pour obtenir le protocole de démonstration pas-à-pas destiné au jury et à la démonstration orale.

---

## 37. Limites connues et perspectives

L'application répond intégralement au cahier des charges du PFA. Dans une évolution future de production, les axes d'amélioration pourraient inclure :
- un système de pagination côté serveur pour les très grands volumes (> 10 000 entrées) ;
- la mise en place d'une suite de tests E2E automatisés (Cypress / Playwright).

---

## 38. État du projet

```text
Gestion métier            ✅ Validé (CRUD complet avec suppression sécurisée)
Authentification & RBAC   ✅ Validé (Isolation Formateur hermétique sur sessions, clients, participants et agrégats)
Onboarding & Activation   ✅ Validé (Token unique 48h, service messagerie Console/SMTP, mot de passe choisi par l'utilisateur)
Profil & Mot de passe     ✅ Validé (Modal profil utilisateur avec changement de mot de passe sécurisé)
Fiches détail             ✅ Validé (Sessions, Formations, Clients, Participants, Utilisateurs)
Filtres & URL state       ✅ Validé
Dashboard & KPI           ✅ Validé (6 KPI + 5 graphiques interactifs Chart.js)
Points d'attention        ✅ Validé (Badge compteur numérique, gestion état vu/non vu)
Exports Métier            ✅ Validé (CSV UTF-8, Excel stylisé openpyxl, Rapports PDF ReportLab, Feuilles d'émargement PDF)
Analyse ACP               ✅ Validé (Interprétation business en 1ère position, projection 2D et détails mathématiques)
Suite de tests (pytest)   ✅ 120 / 120 tests réussis (100%)
Documentation & Recette   ✅ Validé (Protocole RECETTE_SOUTENANCE.md & README)
```

---

## 39. Conclusion

GTM (Galaxy Training Manager) offre à **Galaxy Solutions** un outil centralisé, moderne et sécurisé pour piloter l'ensemble de ses activités de formation.

En combinant **gestion opérationnelle**, **sécurité RBAC**, **tableau de bord décisionnel**, **exports professionnels** et **analyse exploratoire ACP**, GTM transforme la donnée de formation en un levier d'efficacité et d'aide à la décision.
