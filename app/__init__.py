from flask import Flask
from app.config import Config
from app.extensions import db, login_manager, migrate

def create_app():
	"""
	Fonction "factory" : construit et retourne une application Flask
	complètement configurée. On utilise ce patron plutôt que de créer
	l'app directement au niveau du fichier, pour pouvoir créer plusieurs
	instances de l'app facilement (utile notamment pour les tests, qui
	ont besoin d'une configuration différente de la production).
	"""
	app = Flask(__name__)
	app.config.from_object(Config)

	# Branche les extensions (créées dans extensions.py) à cette app précise
	db.init_app(app)
	login_manager.init_app(app)
	migrate.init_app(app, db)

	# Les imports de modèles se font ICI, à l'intérieur de la factory,
	# et non en haut du fichier : ça évite les imports circulaires
	# (les modèles ont besoin de "db", qui vient d'être initialisé juste au-dessus)
	from app import models

	# Indique à Flask-Login comment recharger un utilisateur à partir
	# de l'ID stocké dans son cookie de session à chaque requête
	@login_manager.user_loader
	def load_user(user_id):
		return models.Utilisateur.query.get(int(user_id))

	# Enregistrement des blueprints (groupes de routes)
	from app.routes.auth import auth_bp
	app.register_blueprint(auth_bp)

	from app.routes.formations import formations_bp
	app.register_blueprint(formations_bp)

	from app.routes.domaines import domaines_bp
	app.register_blueprint(domaines_bp)

	from app.routes.clients import clients_bp
	app.register_blueprint(clients_bp)

	from app.routes.formateurs import formateurs_bp
	app.register_blueprint(formateurs_bp)

	from app.routes.participants import participants_bp
	app.register_blueprint(participants_bp)

	from app.routes.sessions import sessions_bp
	app.register_blueprint(sessions_bp)

	from app.routes.inscriptions import inscriptions_bp
	app.register_blueprint(inscriptions_bp)

	from app.routes.utilisateurs import utilisateurs_bp
	app.register_blueprint(utilisateurs_bp)

	return app
