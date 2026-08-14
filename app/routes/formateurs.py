from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import Formateur, Domaine, Utilisateur
from app.services.permissions import gestionnaire_ou_admin_required, admin_required

formateurs_bp = Blueprint("formateurs", __name__, url_prefix="/api/formateurs")

def formateur_vers_dict(formateur):
    return {
        "id": formateur.id,
        "nom": formateur.nom,
        "email": formateur.email,
        "telephone": formateur.telephone,
        "domaine": {
            "id": formateur.domaine.id,
            "nom": formateur.domaine.nom,
        },
        # a_un_compte : pratique côté frontend pour savoir si ce formateur
        # peut se connecter à l'application ou non
        "a_un_compte": formateur.utilisateur_id is not None,
    }

@formateurs_bp.route("", methods=["GET"])
@login_required
def liste_formateurs():
    formateurs = Formateur.query.all()
    return jsonify([formateur_vers_dict(f) for f in formateurs]), 200

@formateurs_bp.route("/<int:formateur_id>", methods=["GET"])
@login_required
def detail_formateur(formateur_id):
    formateur = Formateur.query.get_or_404(formateur_id)
    return jsonify(formateur_vers_dict(formateur)), 200

@formateurs_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_formateur():
    """
    Crée un formateur. Le lien vers un compte Utilisateur (utilisateur_id)
    est optionnel : un gestionnaire peut d'abord enregistrer un formateur
    externe, et lui créer un compte plus tard seulement s'il en a besoin.
    """
    donnees = request.get_json()
    nom = donnees.get("nom")
    domaine_id = donnees.get("domaine_id")

    if not nom or not domaine_id:
        return jsonify({"erreur": "nom et domaine_id sont obligatoires"}), 400

    if not Domaine.query.get(domaine_id):
        return jsonify({"erreur": "domaine_id invalide"}), 400

    utilisateur_id = donnees.get("utilisateur_id")
    if utilisateur_id:
        if not Utilisateur.query.get(utilisateur_id):
            return jsonify({"erreur": "utilisateur_id invalide"}), 400
        if Formateur.query.filter_by(utilisateur_id=utilisateur_id).first():
            return jsonify({"erreur": "ce compte utilisateur est déjà lié à un autre formateur"}), 409

    formateur = Formateur(
        nom=nom,
        email=donnees.get("email"),
        telephone=donnees.get("telephone"),
        domaine_id=domaine_id,
        utilisateur_id=utilisateur_id,
    )
    db.session.add(formateur)
    db.session.commit()
    return jsonify(formateur_vers_dict(formateur)), 201

@formateurs_bp.route("/<int:formateur_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_formateur(formateur_id):
    formateur = Formateur.query.get_or_404(formateur_id)
    donnees = request.get_json()

    if "nom" in donnees:
        formateur.nom = donnees["nom"]
    if "email" in donnees:
        formateur.email = donnees["email"]
    if "telephone" in donnees:
        formateur.telephone = donnees["telephone"]
    if "domaine_id" in donnees:
        if not Domaine.query.get(donnees["domaine_id"]):
            return jsonify({"erreur": "domaine_id invalide"}), 400
        formateur.domaine_id = donnees["domaine_id"]

    db.session.commit()
    return jsonify(formateur_vers_dict(formateur)), 200
