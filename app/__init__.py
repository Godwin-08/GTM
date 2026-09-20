"""
==============================================================================
Package Applicatif Principal — Factory Flask & Enregistrement des Blueprints
==============================================================================
Ce module configure et initialise l'instance de l'application Flask via le
patron de conception "Application Factory". Il associe les extensions
(SQLAlchemy, LoginManager, Migrate), enregistre les gestionnaires d'erreurs
centralisés (400, 403, 404, 409, 500) et raccorde l'ensemble des blueprints
de l'API REST et des pages HTML.
"""

from flask import Flask, jsonify, redirect, request, url_for
from flask_login import current_user, logout_user
from sqlalchemy.exc import IntegrityError
from app.config import Config
from app.extensions import db, login_manager, migrate


def create_app():
	"""
	Fonction "factory" : construit, configure et retourne l'application Flask.
	
	Avantages du patron Factory :
	- Permet d'instancier plusieurs applications isolées (essentiel pour les suites de tests unitaires).
	- Évite les effets de bord liés à l'état global au niveau module.
	- Diffère l'import des modèles pour prévenir les cycles d'importation circulaires.
	
	:return: Instance configurée de Flask (app)
	"""
	app = Flask(__name__)
	# Chargement de tous les paramètres depuis la classe Config (config.py)
	app.config.from_object(Config)

	# -------------------------------------------------------------------------
	# 1. Initialisation des extensions Flask
	# -------------------------------------------------------------------------
	db.init_app(app)
	login_manager.init_app(app)
	# Redirige les requêtes HTML non authentifiées vers le formulaire de connexion
	login_manager.login_view = "pages.login_page"
	migrate.init_app(app, db)

	# Import des modèles SQLAlchemy à l'intérieur de la factory pour éviter les imports circulaires
	from app import models

	def est_requete_api():
		"""Détermine si la requête courante cible les points de terminaison de l'API (/api/...)."""
		return request.path.startswith("/api/")

	@app.before_request
	def invalider_session_compte_desactive():
		"""Révoque immédiatement les sessions des comptes désactivés."""
		if not current_user.is_authenticated or current_user.actif:
			return None

		logout_user()
		if est_requete_api():
			return jsonify({"erreur": "Votre compte a été désactivé. Contactez un administrateur."}), 401
		return redirect(url_for("pages.login_page", compte_desactive=1))

	# -------------------------------------------------------------------------
	# 2. Gestionnaires d'erreurs d'authentification et HTTP (JSON vs Redirection)
	# -------------------------------------------------------------------------
	@login_manager.unauthorized_handler
	def utilisateur_non_connecte():
		"""Gère les accès non authentifiés : 401 JSON pour l'API, redirection HTML pour les vues."""
		if est_requete_api():
			return jsonify({"erreur": "Connexion requise."}), 401
		return redirect(url_for("pages.login_page"))

	@app.errorhandler(400)
	def erreur_requete_invalide(erreur):
		"""Erreur 400 Bad Request : validation de formulaire ou de payload JSON échouée."""
		if est_requete_api():
			return jsonify({"erreur": getattr(erreur, "description", "Requête invalide.")}), 400
		return erreur

	@app.errorhandler(403)
	def erreur_acces_interdit(erreur):
		"""Erreur 403 Forbidden : permissions ou rôle insuffisant (RBAC)."""
		if est_requete_api():
			return jsonify({"erreur": getattr(erreur, "description", "Accès interdit.")}), 403
		return erreur

	@app.errorhandler(404)
	def erreur_introuvable(erreur):
		"""Erreur 404 Not Found : ressource ou identifiant inexistant."""
		if est_requete_api():
			return jsonify({"erreur": "Ressource introuvable."}), 404
		return erreur

	@app.errorhandler(IntegrityError)
	def erreur_integrite(erreur):
		"""Erreur 409 Conflict : contrainte d'unicité ou clé étrangère violée dans la base MySQL."""
		db.session.rollback()
		if est_requete_api():
			return jsonify({"erreur": "Conflit avec une donnée existante ou liée."}), 409
		raise erreur

	@app.errorhandler(500)
	def erreur_interne(erreur):
		"""Erreur 500 Internal Server Error : exception inattendue côté serveur."""
		db.session.rollback()
		if est_requete_api():
			return jsonify({"erreur": "Une erreur interne est survenue."}), 500
		return erreur

	# -------------------------------------------------------------------------
	# 3. Chargement de session utilisateur Flask-Login
	# -------------------------------------------------------------------------
	@login_manager.user_loader
	def load_user(user_id):
		"""Charge l'objet Utilisateur à partir de l'ID stocké dans le cookie de session."""
		return db.session.get(models.Utilisateur, int(user_id))

	# -------------------------------------------------------------------------
	# 4. Enregistrement des Blueprints (Routes API et Pages Web)
	# -------------------------------------------------------------------------
	# Module d'authentification et gestion de session (/api/auth)
	from app.routes.auth import auth_bp
	app.register_blueprint(auth_bp)

	# Vues et templates frontend (/dashboard, /formations, etc.)
	from app.blueprints.pages import pages_bp
	app.register_blueprint(pages_bp)

	# API Catalogue des Formations (/api/formations)
	from app.routes.formations import formations_bp
	app.register_blueprint(formations_bp)

	# API Domaines d'expertise (/api/domaines)
	from app.routes.domaines import domaines_bp
	app.register_blueprint(domaines_bp)

	# API Entreprises Clientes (/api/clients)
	from app.routes.clients import clients_bp
	app.register_blueprint(clients_bp)

	# API Formateurs et Intervenants (/api/formateurs)
	from app.routes.formateurs import formateurs_bp
	app.register_blueprint(formateurs_bp)

	# API Participants / Salariés (/api/participants)
	from app.routes.participants import participants_bp
	app.register_blueprint(participants_bp)

	# API Sessions planifiées et calendrier (/api/sessions)
	from app.routes.sessions import sessions_bp
	app.register_blueprint(sessions_bp)

	# API Inscriptions et affectations (/api/inscriptions)
	from app.routes.inscriptions import inscriptions_bp
	app.register_blueprint(inscriptions_bp)

	# API Gestion des Comptes Utilisateurs (/api/utilisateurs)
	from app.routes.utilisateurs import utilisateurs_bp
	app.register_blueprint(utilisateurs_bp)

	# API Référentiel des Rôles (/api/roles)
	from app.routes.roles import roles_bp
	app.register_blueprint(roles_bp)

	# API Statistiques décisionnelles et Analyse ACP (/api/stats)
	from app.routes.stats import stats_bp
	app.register_blueprint(stats_bp)

	return app

