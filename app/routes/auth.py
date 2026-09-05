from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app.extensions import db
from app.models import Utilisateur
from app.services.activation_service import (
    hasher_token,
    est_token_expire,
    valider_force_mot_de_passe,
)

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
    donnees = request.get_json() or {}
    email = donnees.get("email")
    mot_de_passe = donnees.get("mot_de_passe")

    utilisateur = Utilisateur.query.filter_by(email=email).first()

    if not utilisateur or not utilisateur.actif or not utilisateur.mot_de_passe_hash:
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

@auth_bp.route("/activer-compte", methods=["POST"])
def activer_compte():
    """
    Active un compte utilisateur en vérifiant son token à usage unique
    et en enregistrant son mot de passe choisi.
    Payload attendu : { "token": "...", "mot_de_passe": "..." }
    """
    donnees = request.get_json() or {}
    token = donnees.get("token")
    mot_de_passe = donnees.get("mot_de_passe")

    if not token or not mot_de_passe:
        return jsonify({"erreur": "Le token et le mot de passe sont obligatoires."}), 400

    valide, msg_erreur = valider_force_mot_de_passe(mot_de_passe)
    if not valide:
        return jsonify({"erreur": msg_erreur}), 400

    token_hash = hasher_token(token)
    utilisateur = Utilisateur.query.filter_by(token_activation_hash=token_hash).first()

    if not utilisateur:
        return jsonify({"erreur": "Ce lien d'activation est invalide ou a déjà été utilisé."}), 400

    if est_token_expire(utilisateur.expiration_token):
        return jsonify({"erreur": "Ce lien d'activation a expiré. Veuillez contacter un administrateur."}), 400

    if utilisateur.actif:
        return jsonify({"erreur": "Ce compte a déjà été activé."}), 400

    # Activation définitive et invalidation irréversible du token
    utilisateur.mot_de_passe_hash = generate_password_hash(mot_de_passe, method="pbkdf2:sha256")
    utilisateur.actif = True
    utilisateur.token_activation_hash = None
    utilisateur.expiration_token = None

    db.session.commit()

    return jsonify({
        "message": "Votre compte a été activé avec succès. Vous pouvez maintenant vous connecter.",
        "email": utilisateur.email,
        "nom": utilisateur.nom,
    }), 200

@auth_bp.route("/verifier-token/<token>", methods=["GET"])
def verifier_token(token):
    """
    Vérifie la validité d'un token d'activation (pour affichage initial sur la page d'activation).
    """
    if not token:
        return jsonify({"valide": False, "erreur": "Token manquant."}), 400

    token_hash = hasher_token(token)
    utilisateur = Utilisateur.query.filter_by(token_activation_hash=token_hash).first()

    if not utilisateur:
        return jsonify({"valide": False, "erreur": "Ce lien d'activation est invalide ou a déjà été utilisé."}), 404

    if est_token_expire(utilisateur.expiration_token):
        return jsonify({"valide": False, "erreur": "Ce lien d'activation a expiré. Veuillez demander un nouveau lien."}), 400

    return jsonify({
        "valide": True,
        "nom": utilisateur.nom,
        "email": utilisateur.email,
        "role": utilisateur.role.nom,
    }), 200

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
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

@auth_bp.route("/changer-mot-de-passe", methods=["POST"])
@login_required
def changer_mot_de_passe():
    """
    Permet à l'utilisateur connecté de modifier son mot de passe.
    Payload : { "ancien_mot_de_passe": "...", "nouveau_mot_de_passe": "..." }
    """
    donnees = request.get_json() or {}
    ancien = donnees.get("ancien_mot_de_passe")
    nouveau = donnees.get("nouveau_mot_de_passe")

    if not ancien or not nouveau:
        return jsonify({"erreur": "L'ancien mot de passe et le nouveau mot de passe sont obligatoires."}), 400

    if not check_password_hash(current_user.mot_de_passe_hash, ancien):
        return jsonify({"erreur": "L'ancien mot de passe est incorrect."}), 400

    valide, msg_erreur = valider_force_mot_de_passe(nouveau)
    if not valide:
        return jsonify({"erreur": msg_erreur}), 400

    if check_password_hash(current_user.mot_de_passe_hash, nouveau):
        return jsonify({"erreur": "Le nouveau mot de passe doit être différent de l'ancien."}), 400

    current_user.mot_de_passe_hash = generate_password_hash(nouveau, method="pbkdf2:sha256")
    db.session.commit()

    return jsonify({"message": "Votre mot de passe a été modifié avec succès."}), 200
