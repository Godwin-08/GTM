"""
==============================================================================
Extensions Flask Globales — Galaxy Training Manager (GTM)
==============================================================================
Ce fichier instancie les objets d'extension Flask sans les lier immédiatement
à une instance d'application (principe de l'Application Factory).
Les extensions sont ensuite initialisées dans app/__init__.py via .init_app(app).
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# 1. ORM SQLAlchemy : gestion des entités relationnelles, requêtes et transactions SQL
db = SQLAlchemy()

# 2. Flask-Login : gestion de la session utilisateur, du cookie d'authentification et de current_user
login_manager = LoginManager()

# 3. Flask-Migrate (Alembic) : gestion des migrations et évolutions de schéma de la base MySQL
migrate = Migrate()

