from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import Formation, Domaine, Session
from app.services.permissions import gestionnaire_ou_admin_required
from app.services.access_service import formations_visibles, exiger_acces
from app.services.query_validation_service import ErreurFiltre, entier_positif

formations_bp = Blueprint("formations", __name__, url_prefix="/api/formations")

def formation_vers_dict(formation):
    """
    Convertit un objet Formation en dictionnaire simple, prêt à être
    transformé en JSON.
    """
    return {
        "id": formation.id,
        "titre": formation.titre,
        "duree_jours": formation.duree_jours,
        "description": formation.description,
        "domaine": {
            "id": formation.domaine.id,
            "nom": formation.domaine.nom,
        } if formation.domaine else None,
    }

@formations_bp.route("", methods=["GET"])
@login_required
def liste_formations():
    """
    Renvoie les formations avec filtres optionnels combinés (AND) :
    /api/formations?domaine_id=1&q=python
    """
    query = formations_visibles(current_user)

    try:
        domaine_id = entier_positif(request.args, "domaine_id")
    except ErreurFiltre as erreur:
        return jsonify({"erreur": str(erreur)}), 400
    if domaine_id is not None:
        query = query.filter(Formation.domaine_id == domaine_id)

    q = request.args.get("q", "").strip()
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Formation.titre.ilike(pattern),
                Formation.description.ilike(pattern)
            )
        )

    formations = query.all()
    return jsonify([formation_vers_dict(f) for f in formations]), 200

@formations_bp.route("/<int:formation_id>", methods=["GET"])
@login_required
def detail_formation(formation_id):
    """Renvoie une formation précise, ou une erreur 404 si elle n'existe pas."""
    formation = exiger_acces(formations_visibles(current_user), formation_id, current_user)
    return jsonify(formation_vers_dict(formation)), 200

@formations_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_formation():
    donnees = request.get_json()

    titre = donnees.get("titre")
    domaine_id = donnees.get("domaine_id")
    duree_jours = donnees.get("duree_jours")

    if not titre or not domaine_id or not duree_jours:
        return jsonify({"erreur": "titre, domaine_id et duree_jours sont obligatoires"}), 400

    if not (2 <= duree_jours <= 5):
        return jsonify({"erreur": "duree_jours doit être entre 2 et 5"}), 400

    if not db.session.get(Domaine, domaine_id):
        return jsonify({"erreur": "domaine_id invalide"}), 400

    if Formation.query.filter_by(titre=titre).first():
        return jsonify({"erreur": "une formation avec ce titre existe déjà"}), 409

    formation = Formation(
        titre=titre,
        domaine_id=domaine_id,
        duree_jours=duree_jours,
        description=donnees.get("description"),
    )
    db.session.add(formation)
    db.session.commit()

    return jsonify(formation_vers_dict(formation)), 201

@formations_bp.route("/<int:formation_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_formation(formation_id):
    formation = db.get_or_404(Formation, formation_id)
    donnees = request.get_json()

    if "titre" in donnees:
        existe = Formation.query.filter_by(titre=donnees["titre"]).first()
        if existe and existe.id != formation_id:
            return jsonify({"erreur": "une formation avec ce titre existe déjà"}), 409
        formation.titre = donnees["titre"]

    if "domaine_id" in donnees:
        if not db.session.get(Domaine, donnees["domaine_id"]):
            return jsonify({"erreur": "domaine_id invalide"}), 400
        formation.domaine_id = donnees["domaine_id"]

    if "duree_jours" in donnees:
        if not (2 <= donnees["duree_jours"] <= 5):
            return jsonify({"erreur": "duree_jours doit être entre 2 et 5"}), 400
        formation.duree_jours = donnees["duree_jours"]

    if "description" in donnees:
        formation.description = donnees["description"]

    db.session.commit()
    return jsonify(formation_vers_dict(formation)), 200

@formations_bp.route("/<int:formation_id>", methods=["DELETE"])
@gestionnaire_ou_admin_required
def supprimer_formation(formation_id):
    formation = db.get_or_404(Formation, formation_id)

    session_associee = Session.query.filter_by(formation_id=formation_id).first()
    if session_associee is not None:
        nb_sessions = Session.query.filter_by(formation_id=formation_id).count()
        return jsonify({
            "erreur": f"Impossible de supprimer cette formation : {nb_sessions} session(s) y sont associée(s)."
        }), 409

    db.session.delete(formation)
    db.session.commit()
    return "", 204
