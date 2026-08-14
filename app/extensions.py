from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# Instance de SQLAlchemy, pas encore liée à une application Flask précise.
# Elle sera "attachée" à l'app dans app/__init__.py via db.init_app(app)
db = SQLAlchemy()

# Gère les sessions de connexion (qui est connecté, quel utilisateur courant, etc.)
login_manager = LoginManager()

# Permet de suivre les changements de schéma de la base dans le temps
# (génère et applique les migrations automatiquement)
migrate = Migrate()
