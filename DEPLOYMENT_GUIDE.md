# 🚀 Guide de Déploiement Gratuit (0 €) — Galaxy Training Manager (GTM)

Ce guide explique comment mettre en ligne votre application **Galaxy Training Manager** gratuitement sur **Render.com** avec une base **MySQL Cloud** managée.

---

## 📋 Prérequis (Gratuits)

1. Un compte **GitHub** (votre code doit être sur un dépôt public ou privé).
2. Un compte gratuit sur **[Render.com](https://render.com/)** (Hébergement web).
3. Un compte gratuit sur un fournisseur MySQL Cloud :
   - **[Aiven.io](https://aiven.io/)** (Offre un tier gratuit MySQL managé)
   - ou **[TiDB Cloud Serverless](https://tidbcloud.com/)** (Compatible MySQL 8, gratuit à vie).

---

## 🛠️ Étape 1 : Créer la Base de Données MySQL Gratuite

1. Sur **Aiven.io** ou **TiDB Cloud**, créez un nouveau service **MySQL** (choisissez le plan gratuit / Free Tier).
2. Récupérez les identifiants de connexion :
   - **Host** (ex: `mysql-xxxx.aivencloud.com`)
   - **Port** (ex: `15200` ou `3306`)
   - **User** (ex: `avnadmin` ou `root`)
   - **Password** (votre mot de passe généré)
   - **Database Name** (ex: `defaultdb` ou `galaxy_solutions_db`)

---

## 🌐 Étape 2 : Déployer l'application sur Render.com

1. Connectez-vous sur **[dashboard.render.com](https://dashboard.render.com/)**.
2. Cliquez sur **New +** > **Web Service**.
3. Liez votre dépôt GitHub **PFA_galaxy_solutions**.
4. Remplissez les informations de base :
   - **Name** : `galaxy-training-manager`
   - **Language** : `Python 3`
   - **Branch** : `main` (ou votre branche de travail)
   - **Region** : `Frankfurt (EU Central)` (la plus proche pour une latence minimale)
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120`
   - **Instance Type** : `Free`

5. Dans la section **Environment Variables** (Variables d'environnement), ajoutez :

| Variable | Valeur |
| :--- | :--- |
| `SECRET_KEY` | *(Cliquez sur Generate pour une clé aléatoire)* |
| `FLASK_DEBUG` | `false` |
| `DB_HOST` | *L'adresse Host de votre MySQL Cloud* |
| `DB_USER` | *L'utilisateur de votre MySQL Cloud* |
| `DB_PASSWORD` | *Le mot de passe de votre MySQL Cloud* |
| `DB_NAME` | *Le nom de la base de votre MySQL Cloud* |
| `MAIL_BACKEND` | `console` *(ou smtp si vous avez un serveur mail)* |
| `APP_BASE_URL` | `https://galaxy-training-manager.onrender.com` *(l'URL fournie par Render)* |

6. Cliquez sur **Create Web Service**.

---

## 🗄️ Étape 3 : Initialiser les Tables et Données

Une fois le déploiement terminé sur Render :
1. Sur le dashboard de votre Web Service sur Render, ouvrez l'onglet **Shell**.
2. Exécutez la commande d'initialisation :
   ```bash
   python init_db.py --seed
   ```
3. Cela créera automatiquement toutes les tables SQLAlchemy et insèrera les données de démonstration !

---

## 🎉 C'est en ligne !

Votre application est maintenant accessible mondialement en **HTTPS** sur votre URL Render (ex: `https://galaxy-training-manager.onrender.com`).

