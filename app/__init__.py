from flask import Flask, jsonify, redirect, request, url_for
from sqlalchemy.exc import IntegrityError
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
	# Redirige les utilisateurs non connectés vers la page de connexion HTML.
	login_manager.login_view = "pages.login_page"
	migrate.init_app(app, db)

	# Les imports de modèles se font ICI, à l'intérieur de la factory,
	# et non en haut du fichier : ça évite les imports circulaires
	# (les modèles ont besoin de "db", qui vient d'être initialisé juste au-dessus)
	from app import models

	def est_requete_api():
		return request.path.startswith("/api/")

	@login_manager.unauthorized_handler
	def utilisateur_non_connecte():
		if est_requete_api():
			return jsonify({"erreur": "Connexion requise."}), 401
		return redirect(url_for("pages.login_page"))

	@app.errorhandler(400)
	def erreur_requete_invalide(erreur):
		if est_requete_api():
			return jsonify({"erreur": getattr(erreur, "description", "Requête invalide.")}), 400
		return erreur

	@app.errorhandler(403)
	def erreur_acces_interdit(erreur):
		if est_requete_api():
			return jsonify({"erreur": getattr(erreur, "description", "Accès interdit.")}), 403
		return erreur

	@app.errorhandler(404)
	def erreur_introuvable(erreur):
		if est_requete_api():
			return jsonify({"erreur": "Ressource introuvable."}), 404
		return erreur

	@app.errorhandler(IntegrityError)
	def erreur_integrite(erreur):
		db.session.rollback()
		if est_requete_api():
			return jsonify({"erreur": "Conflit avec une donnée existante ou liée."}), 409
		raise erreur

	@app.errorhandler(500)
	def erreur_interne(erreur):
		db.session.rollback()
		if est_requete_api():
			return jsonify({"erreur": "Une erreur interne est survenue."}), 500
		return erreur

	# Indique à Flask-Login comment recharger un utilisateur à partir
	# de l'ID stocké dans son cookie de session à chaque requête
	@login_manager.user_loader
	def load_user(user_id):
		return db.session.get(models.Utilisateur, int(user_id))

	# Enregistrement des blueprints (groupes de routes)
	from app.routes.auth import auth_bp
	app.register_blueprint(auth_bp)

	# Pages HTML (templates côté frontend)
	from app.blueprints.pages import pages_bp
	app.register_blueprint(pages_bp)

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

	from app.routes.stats import stats_bp
	app.register_blueprint(stats_bp)

	return app
