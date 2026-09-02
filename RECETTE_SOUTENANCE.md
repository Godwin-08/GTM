# Protocole de Recette & Script de Démonstration (Soutenance PFA)

Ce document constitue le **script de scène officiel** pour la démonstration orale de l'application **Galaxy Training Manager (GTM)** devant le jury.

---

## 🔑 Identifiants des Comptes de Démonstration Officiels

| Rôle | Email / Identifiant | Mot de passe | Statut de validation |
| :--- | :--- | :--- | :---: |
| **Admin** | `admin@galaxysolutions.ma` | `Admin@2026` | ✅ Login testé & validé |
| **Gestionnaire** | `sofia.amrani@galaxysolutions.ma` | `Sofia@2026` | ✅ Login testé & validé |
| **Formateur** | `karim.bensouda@galaxysolutions.ma` | `Karim@2026` | ✅ Login testé & validé |

---

## 🎯 Données de référence pour la démonstration

- **Session ouverte (non complète)** : Session 1 (*Sécurité Web OWASP*) — Capacité 15, Inscrits < 15.
- **Session complète (`session.est_complete == True`)** : Session 5 — Capacité 10, Inscrits 10 (badge orange *Session complète*).

---

## 🎬 Scénario 1 : Parcours Admin / Gestionnaire (20 min)

### Étape 1 : Authentification & Vue d'ensemble
- **ACTION** : Ouvrir `http://127.0.0.1:5000/`, saisir `admin@galaxysolutions.ma` / `Admin@2026` et cliquer sur *Se connecter*.
- **À OBSERVER** : Redirection fluide vers `/dashboard`. Les 6 cartes KPI, les filtres croisés, le bloc *Points d'attention* et les graphiques d'activité s'affichent.
- **À EXPLIQUER AU JURY** : « L'authentification utilise un cookie de session Flask-Login sécurisé. L'Admin accède à l'ensemble du tableau de bord de pilotage en temps réel. »
- **RÉSULTAT ATTENDU** : Connexion réussie, session active, données chargées.

### Étape 2 : Filtrage dynamique du Dashboard
- **ACTION** : Sélectionner le Domaine **Cybersécurité** et l'Année **2026**, puis cliquer sur **Appliquer**.
- **À OBSERVER** : Mise à jour instantanée des cartes KPI (sessions, clients actifs, participants formés) et réalignement des graphiques Chart.js sans rechargement de page.
- **À EXPLIQUER AU JURY** : « Les filtres sont exécutés côté backend via l'API `/api/stats/kpi-globaux` pour garantir la rigueur des données. Le frontend Alpine.js met à jour l'affichage de manière réactive. »
- **RÉSULTAT ATTENDU** : Les métriques s'ajustent au périmètre Cybersécurité 2026.

### Étape 3 : Consultation des Sessions & Inscription dynamique sur session ouverte
- **ACTION** : Naviguer sur `/sessions` et ouvrir la fiche de la Session #1 (ouverte).
- **À OBSERVER** : Affichage des dates, du formateur référent, du lieu, de la carte KPI remplissage et du tableau des inscrits.
- **ACTION** : Cliquer sur **+ Ajouter un participant**.
- **À OBSERVER** : La modale s'ouvre. Le statut par défaut est positionné automatiquement sur `confirmée`.
- **ACTION** : Sélectionner le Client *TechCorp Maroc*.
- **À OBSERVER** : Appel automatique `GET /api/participants?client_id=X`. La liste des participants se charge de manière ciblée pour ce client.
- **ACTION** : Choisir un participant et cliquer sur **Confirmer l'inscription**.
- **À OBSERVER** : Toast de succès vert, fermeture de la modale, réactualisation immédiate de la liste des inscrits ET du KPI de remplissage.
- **À EXPLIQUER AU JURY** : « Nous avons optimisé la performance en chargeant les participants uniquement à la demande par client, plutôt que d'effectuer un dump massif de la base de données. »
- **RÉSULTAT ATTENDU** : Participant inscrit, KPI de remplissage mis à jour.

### Étape 4 : Gestion de Session Complète & Liste d'attente
- **ACTION** : Ouvrir la fiche de la Session #5 (marquée *Session complète*).
- **ACTION** : Cliquer sur **+ Ajouter un participant**.
- **À OBSERVER** : La modale affiche un avertissement visuel et positionne le statut initial par défaut sur `liste_attente`.
- **ACTION** : Choisir un client/participant, laisser sur `liste_attente` et valider.
- **À OBSERVER** : Inscription enregistrée avec succès sans consommer de place confirmée.
- **ACTION** : Tenter d'inscrire un participant en forçant le statut sur `confirmée` sur cette session complète.
- **À OBSERVER** : Refus du backend (`409 Conflict`) et affichage du Toast d'erreur backend exact.
- **À EXPLIQUER AU JURY** : « Le frontend guide l'utilisateur en proposant la liste d'attente par défaut, mais c'est le serveur qui reste l'autorité absolue et rejette toute surréservation confirmée non autorisée. »
- **RÉSULTAT ATTENDU** : Liste d'attente acceptée (201), confirmation forcée rejetée (409).

### Étape 5 : Modification de statut avec Rollback Alpine.js
- **ACTION** : Dans le tableau des inscrits d'une session, modifier la valeur du sélecteur de statut d'une ligne.
- **À OBSERVER** : Le bouton de confirmation `✓` apparaît uniquement sur la ligne modifiée.
- **ACTION** : Cliquer sur `✓`.
- **À OBSERVER** : Le bouton passe immédiatement à l'état désactivé (`:disabled`) avec un spinner `loader-2` (anti-double-clic).
- **À EXPLIQUER AU JURY** : « Si le serveur renvoie une erreur, Alpine.js restaure automatiquement le statut précédent pour éviter toute désynchronisation visuelle entre l'interface et la base de données. »
- **RÉSULTAT ATTENDU** : Validation explicite et résilience de l'état local.

### Étape 6 : Analyse ACP (Analyse en Composantes Principales)
- **ACTION** : Naviguer sur `/analytics-acp`.
- **À OBSERVER** : Affichage du graphique factoriel (Axe 1 vs Axe 2), de la variance expliquée et de la matrice de corrélation.
- **À EXPLIQUER AU JURY** : « L'ACP est un outil d'analyse exploratoire et de synthèse descriptive calculé avec NumPy et Pandas. Elle permet d'identifier visuellement la proximité des profils d'activité clients et l'orientation des formations. »
- **RÉSULTAT ATTENDU** : Restitution claire des axes factoriels et de la synthèse descriptive.

### Étape 7 : Déconnexion
- **ACTION** : Cliquer sur le profil en bas de la sidebar puis sur **Déconnexion**.
- **À OBSERVER** : Fermeture de session et redirection vers `/`.
- **RÉSULTAT ATTENDU** : Déconnexion sécurisée.

---

## 🎬 Scénario 2 : Parcours Formateur (5 min — Étanchéité & Sécurité RBAC)

### Étape 1 : Connexion Formateur
- **ACTION** : Se connecter avec `karim.bensouda@galaxysolutions.ma` / `Karim@2026`.
- **À OBSERVER** : Redirection vers l'espace Formateur.

### Étape 2 : Contrôle de l'Interface (UI Scoping)
- **ACTION** : Naviguer sur `/sessions`.
- **À OBSERVER** : Le Formateur ne voit que les sessions dont il est le formateur référent.
- **ACTION** : Ouvrir la fiche d'une session.
- **À OBSERVER** : Le bouton **+ Ajouter un participant** et les sélecteurs de statut du tableau sont **masqués** (filtrés côté Jinja2).
- **À EXPLIQUER AU JURY** : « Pour l'ergonomie, l'interface masque les boutons de gestion qui ne concernent pas le formateur. »

### Étape 3 : Tentative de contournement API (Sécurité Backend)
- **ACTION** : Émettre une requête directe `POST /api/inscriptions` ou `PUT /api/inscriptions/1` avec la session du Formateur (ex: via console navigateur).
- **À OBSERVER** : Réponse HTTP `403 Forbidden` (`{"erreur": "Accès interdit"}`).
- **À EXPLIQUER AU JURY** : « Le masque visuel ne suffit pas : le backend vérifie systématiquement le rôle et bloque toute écriture non autorisée avec un code 403. »
- **RÉSULTAT ATTENDU** : Étanchéité RBAC backend 100% vérifiée.

---

## 📊 Synthèse d'évaluation de la recette soutenance

- [x] Connexion & déconnexion des 3 rôles validées.
- [x] Filtres Dashboard et URL state réactifs.
- [x] Inscription dynamique avec filtrage `client_id` testée.
- [x] Inscription sur session complète (liste d'attente / refus 409) démontrée.
- [x] Bouton `✓` anti-double-clic et rollback Alpine.js validés.
- [x] Sécurité RBAC Formateur (UI + API 403) testée.
- [x] 93 tests automatisés exécutés et verts.
