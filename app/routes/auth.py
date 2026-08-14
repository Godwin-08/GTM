from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash
from app.models import Utilisateur

# Un blueprint regroupe les routes liées à un même thème (ici : l'authentification)
# et permet de les enregistrer toutes ensemble dans app/__init__.py
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Connecte un utilisateur à partir de son email et mot de passe,
    envoyés en JSON dans le corps de la requête :
    { "email": "...", "mot_de_passe": "..." }
    """
    donnees = request.get_json()
    email = donnees.get("email")
    mot_de_passe = donnees.get("mot_de_passe")

    utilisateur = Utilisateur.query.filter_by(email=email).first()

    if not utilisateur or not utilisateur.actif:
        return jsonify({"erreur": "Identifiants invalides"}), 401

    if not check_password_hash(utilisateur.mot_de_passe_hash, mot_de_passe):
        return jsonify({"erreur": "Identifiants invalides"}), 401

    login_user(utilisateur)

    return jsonify({
        "message": "Connexion réussie",
        "utilisateur": {
            "id": utilisateur.id,
            "nom": utilisateur.nom,
            "email": utilisateur.email,
            "role": utilisateur.role.nom,
        }
    }), 200

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Déconnexion réussie"}), 200

@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    """Renvoie les infos de l'utilisateur actuellement connecté (utile pour le frontend)."""
    return jsonify({
        "id": current_user.id,
        "nom": current_user.nom,
        "email": current_user.email,
        "role": current_user.role.nom,
    }), 200
