"""
==============================================================================
Configuration Globale de l'Application — Galaxy Training Manager (GTM)
==============================================================================
Ce module charge les variables d'environnement depuis le fichier .env et définit
la classe Config qui centralise :
- La sécurité des sessions et clés secrètes Flask
- Les paramètres de connexion SQLAlchemy à la base de données MySQL
- Les réglages de la messagerie transactionnelle (Mode Console / Démo vs SMTP Production)
- L'URL de base pour les liens d'activation et notifications
"""

import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Charge les variables définies dans le fichier .env local
# et les injecte dans os.environ pour y accéder de manière standard
load_dotenv()


class Config:
    """Classe de configuration standardisée lue par l'Application Factory de Flask."""

    # -------------------------------------------------------------------------
    # 1. Sécurité Applicative & Sessions
    # -------------------------------------------------------------------------
    # Clé secrète utilisée par Flask pour signer cryptographiquement les cookies
    # de session et se prémunir contre les attaques CSRF
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-a-changer")

    # -------------------------------------------------------------------------
    # 2. Base de Données Relationnelle MySQL / MariaDB via SQLAlchemy
    # -------------------------------------------------------------------------
    DB_USER = os.environ.get("DB_USER")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_NAME = os.environ.get("DB_NAME")

    # Encodage sécurisé du mot de passe (quote_plus protège contre les caractères
    # réservés dans les URLs comme '@', ':', '/', '%', etc.)
    DB_PASSWORD = quote_plus(os.environ.get("DB_PASSWORD", ""))

    # URI de connexion officielle SQLAlchemy au format :
    # mysql+pymysql://<user>:<password>@<host>/<database>
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )

    # Désactivation du suivi superflu des modifications SQLAlchemy (économise de la mémoire)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # -------------------------------------------------------------------------
    # 3. Service de Messagerie Transactionnelle (Onboarding / Invitations)
    # -------------------------------------------------------------------------
    # Modes d'envoi :
    # - "console" : Mode local / soutenance (logs sécurisés sans serveur SMTP requis)
    # - "smtp"    : Mode production (envoi réel de courriels)
    MAIL_BACKEND = os.environ.get("MAIL_BACKEND", "console").lower()
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_FROM = os.environ.get("MAIL_FROM", "Galaxy Training Manager <no-reply@gtm.galaxysolutions.ma>")

    # URL publique ou locale racine pour générer les liens absolus d'activation
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://127.0.0.1:5000")
