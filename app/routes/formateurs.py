from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import Formateur, Domaine, Utilisateur
from app.services.permissions import gestionnaire_ou_admin_required, admin_required
from app.services.access_service import formateurs_visibles, exiger_acces
from app.services.query_validation_service import ErreurFiltre, entier_positif, valeur_parmi

formateurs_bp = Blueprint("formateurs", __name__, url_prefix="/api/formateurs")

def formateur_vers_dict(formateur):
    sessions_valides = [s for s in formateur.sessions if s.statut != "annulee"]
    nb_sessions = len(sessions_valides)
    nb_planifiees = len([s for s in sessions_valides if s.statut in ["planifiee", "en_cours"]])
    nb_terminees = len([s for s in sessions_valides if s.statut == "terminee"])
    return {
        "id": formateur.id,
        "nom": formateur.nom,
        "email": formateur.email,
        "telephone": formateur.telephone,
        "domaine": {
            "id": formateur.domaine.id,
            "nom": formateur.domaine.nom,
        } if formateur.domaine else None,
        "nb_sessions": nb_sessions,
        "nb_planifiees": nb_planifiees,
        "nb_terminees": nb_terminees,
        "a_un_compte": formateur.utilisateur_id is not None,
    }

@formateurs_bp.route("", methods=["GET"])
@login_required
def liste_formateurs():
    """
    Renvoie les formateurs avec filtres optionnels combinés (AND) :
    /api/formateurs?domaine_id=1&type=interne&q=youssef
    """
    query = formateurs_visibles(current_user)

    try:
        domaine_id = entier_positif(request.args, "domaine_id")
        type_formateur = valeur_parmi(request.args, "type", {"interne", "externe"})
    except ErreurFiltre as erreur:
        return jsonify({"erreur": str(erreur)}), 400
    if domaine_id is not None:
        query = query.filter(Formateur.domaine_id == domaine_id)
    if type_formateur == "interne":
        query = query.filter(Formateur.utilisateur_id.isnot(None))
    elif type_formateur == "externe":
        query = query.filter(Formateur.utilisateur_id.is_(None))

    q = request.args.get("q", "").strip()
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Formateur.nom.ilike(pattern),
                Formateur.email.ilike(pattern)
            )
        )

    formateurs = query.all()
    return jsonify([formateur_vers_dict(f) for f in formateurs]), 200

@formateurs_bp.route("/<int:formateur_id>", methods=["GET"])
@login_required
def detail_formateur(formateur_id):
    formateur = exiger_acces(formateurs_visibles(current_user), formateur_id, current_user)
    return jsonify(formateur_vers_dict(formateur)), 200

@formateurs_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_formateur():
    donnees = request.get_json()
    nom = donnees.get("nom")
    domaine_id = donnees.get("domaine_id")

    if not nom or not domaine_id:
        return jsonify({"erreur": "nom et domaine_id sont obligatoires"}), 400

    if not db.session.get(Domaine, domaine_id):
        return jsonify({"erreur": "domaine_id invalide"}), 400

    utilisateur_id = donnees.get("utilisateur_id")
    if utilisateur_id:
        if not db.session.get(Utilisateur, utilisateur_id):
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
    formateur = db.get_or_404(Formateur, formateur_id)
    donnees = request.get_json()

    if "nom" in donnees:
        formateur.nom = donnees["nom"]
    if "email" in donnees:
        formateur.email = donnees["email"]
    if "telephone" in donnees:
        formateur.telephone = donnees["telephone"]
    if "domaine_id" in donnees:
        if not db.session.get(Domaine, donnees["domaine_id"]):
            return jsonify({"erreur": "domaine_id invalide"}), 400
        formateur.domaine_id = donnees["domaine_id"]

    db.session.commit()
    return jsonify(formateur_vers_dict(formateur)), 200
