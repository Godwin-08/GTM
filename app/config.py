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
    DATABASE_URL = os.environ.get("DATABASE_URL")

    DB_USER = os.environ.get("DB_USER", "root")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "galaxy_solutions")
    DB_PASSWORD = quote_plus(os.environ.get("DB_PASSWORD", ""))

    # Support SSL (requis par TiDB Cloud, Aiven, etc.)
    DB_USE_SSL = os.environ.get("DB_USE_SSL", "false").lower() in ("true", "1", "yes")
    DB_SSL_CA = os.environ.get("DB_SSL_CA", "")

    # Construction de l'URI SQLAlchemy
    if DATABASE_URL:
        # Normalisation du protocole si nécessaire (ex: mysql:// -> mysql+pymysql://)
        if DATABASE_URL.startswith("mysql://"):
            SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("mysql://", "mysql+pymysql://", 1)
        else:
            SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        # URI de connexion officielle SQLAlchemy avec port :
        # mysql+pymysql://<user>:<password>@<host>:<port>/<database>
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

    # Options de connexion au moteur SQLAlchemy (SSL, pool pre-ping, etc.)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    if DB_USE_SSL:
        # PyMySQL 1.x + SQLAlchemy : format flat (ssl_ca, ssl_verify_cert, ssl_verify_identity)
        # Le format {"ssl": {"ca": ...}} ne fonctionne pas correctement avec PyMySQL 1.2+
        ca_path = None
        if DB_SSL_CA and os.path.exists(DB_SSL_CA):
            ca_path = DB_SSL_CA
        else:
            try:
                import certifi
                ca_path = certifi.where()
            except ImportError:
                for _p in [
                    "/etc/ssl/certs/ca-certificates.crt",
                    "/etc/pki/tls/certs/ca-bundle.crt",
                    "/etc/ssl/ca-bundle.pem",
                ]:
                    if os.path.exists(_p):
                        ca_path = _p
                        break

        if ca_path:
            SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
                "ssl_ca": ca_path,
                "ssl_verify_cert": True,
                "ssl_verify_identity": True,
            }
        else:
            # Fallback : impose SSL sans vérifier le certificat
            SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = {
                "ssl": {"ssl_mode": "REQUIRED"}
            }

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
