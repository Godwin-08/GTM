import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Charge les variables définies dans le fichier .env
# et les rend accessibles via os.environ.get(...)
load_dotenv()

class Config:
    # Clé secrète utilisée par Flask pour sécuriser les sessions
    # (cookies signés, protection CSRF, etc.)
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-a-changer")

    # Les 4 informations de connexion à la base MySQL,
    # récupérées séparément depuis le .env
    DB_USER = os.environ.get("DB_USER")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_NAME = os.environ.get("DB_NAME")

    # quote_plus() encode les caractères spéciaux du mot de passe
    # (comme le @) pour qu'ils ne cassent pas l'URL de connexion
    DB_PASSWORD = quote_plus(os.environ.get("DB_PASSWORD", ""))

    # Construit l'URL complète de connexion attendue par SQLAlchemy,
    # au format : mysql+pymysql://utilisateur:motdepasse@hote/nom_de_la_base
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    )

    # Désactive un système de suivi des modifications de SQLAlchemy
    # qu'on n'utilise pas ici (évite un warning inutile au démarrage)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Configuration du service de messagerie transactionnelle (Onboarding)
    # Mode par défaut : "console" (mode local / soutenance, sans dépendance SMTP)
    # Mode production : "smtp"
    MAIL_BACKEND = os.environ.get("MAIL_BACKEND", "console").lower()
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "localhost")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ("true", "1", "yes")
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_FROM = os.environ.get("MAIL_FROM", "Galaxy Training Manager <no-reply@galaxysolutions.ma>")
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "")