from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import Utilisateur, Role, Formateur
from app.services.permissions import admin_required

utilisateurs_bp = Blueprint("utilisateurs", __name__, url_prefix="/api/utilisateurs")

def utilisateur_vers_dict(utilisateur):
    """
    Ne renvoie JAMAIS mot_de_passe_hash, même haché : ce champ n'a aucune
    raison de sortir de la base de données vers l'extérieur, même vers
    un admin. Personne n'a besoin de le voir, ni de le vérifier à l'œil.
    """
    formateur = Formateur.query.filter_by(utilisateur_id=utilisateur.id).first()
    return {
        "id": utilisateur.id,
        "nom": utilisateur.nom,
        "email": utilisateur.email,
        "actif": utilisateur.actif,
        "date_creation": utilisateur.date_creation.isoformat(),
        "role": {
            "id": utilisateur.role.id,
            "nom": utilisateur.role.nom,
        },
        "formateur": {
            "id": formateur.id,
            "nom": formateur.nom,
            "telephone": formateur.telephone,
            "domaine": {
                "id": formateur.domaine.id,
                "nom": formateur.domaine.nom,
            } if formateur.domaine else None,
        } if formateur else None,
    }

@utilisateurs_bp.route("", methods=["GET"])
@admin_required
def liste_utilisateurs():
    utilisateurs = Utilisateur.query.all()
    return jsonify([utilisateur_vers_dict(u) for u in utilisateurs]), 200

@utilisateurs_bp.route("/<int:utilisateur_id>", methods=["GET"])
@admin_required
def detail_utilisateur(utilisateur_id):
    utilisateur = Utilisateur.query.get_or_404(utilisateur_id)
    return jsonify(utilisateur_vers_dict(utilisateur)), 200

@utilisateurs_bp.route("", methods=["POST"])
@admin_required
def creer_utilisateur():
    donnees = request.get_json()
    nom = donnees.get("nom")
    email = donnees.get("email")
    mot_de_passe = donnees.get("mot_de_passe")
    role_id = donnees.get("role_id")

    if not all([nom, email, mot_de_passe, role_id]):
        return jsonify({"erreur": "nom, email, mot_de_passe et role_id sont obligatoires"}), 400

    if not Role.query.get(role_id):
        return jsonify({"erreur": "role_id invalide"}), 400

    if Utilisateur.query.filter_by(email=email).first():
        return jsonify({"erreur": "un compte avec cet email existe déjà"}), 409

    utilisateur = Utilisateur(
        nom=nom,
        email=email,
        mot_de_passe_hash=generate_password_hash(mot_de_passe, method="pbkdf2:sha256"),
        role_id=role_id,
    )
    db.session.add(utilisateur)
    db.session.commit()
    return jsonify(utilisateur_vers_dict(utilisateur)), 201

@utilisateurs_bp.route("/<int:utilisateur_id>", methods=["PUT"])
@admin_required
def modifier_utilisateur(utilisateur_id):
    utilisateur = Utilisateur.query.get_or_404(utilisateur_id)
    donnees = request.get_json()

    if "nom" in donnees:
        utilisateur.nom = donnees["nom"]
    if "email" in donnees:
        if Utilisateur.query.filter(
            Utilisateur.email == donnees["email"], Utilisateur.id != utilisateur_id
        ).first():
            return jsonify({"erreur": "cet email est déjà utilisé par un autre compte"}), 409
        utilisateur.email = donnees["email"]
    if "role_id" in donnees:
        if not Role.query.get(donnees["role_id"]):
            return jsonify({"erreur": "role_id invalide"}), 400
        utilisateur.role_id = donnees["role_id"]
    if "actif" in donnees:
        if utilisateur.id == current_user.id and donnees["actif"] is False:
            return jsonify({"erreur": "vous ne pouvez pas désactiver votre propre compte"}), 400
        utilisateur.actif = donnees["actif"]
    if "mot_de_passe" in donnees and donnees["mot_de_passe"]:
        utilisateur.mot_de_passe_hash = generate_password_hash(
            donnees["mot_de_passe"], method="pbkdf2:sha256"
        )

    db.session.commit()
    return jsonify(utilisateur_vers_dict(utilisateur)), 200
