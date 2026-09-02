from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import Domaine
from app.services.permissions import gestionnaire_ou_admin_required

domaines_bp = Blueprint("domaines", __name__, url_prefix="/api/domaines")

def domaine_vers_dict(domaine):
    return {"id": domaine.id, "nom": domaine.nom}

@domaines_bp.route("", methods=["GET"])
@login_required
def liste_domaines():
    """Renvoie les 3 domaines (Web & Data, Management Agile, Cybersécurité)."""
    domaines = Domaine.query.all()
    return jsonify([domaine_vers_dict(d) for d in domaines]), 200

@domaines_bp.route("/<int:domaine_id>", methods=["GET"])
@login_required
def detail_domaine(domaine_id):
    domaine = db.get_or_404(Domaine, domaine_id)
    return jsonify(domaine_vers_dict(domaine)), 200

@domaines_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_domaine():
    """
    Rarement utilisé en pratique (les 3 domaines sont fixés dès le départ),
    mais présent pour respecter le principe "création, consultation, mise
    à jour" demandé sur toutes les entités par le cahier des charges.
    """
    donnees = request.get_json()
    nom = donnees.get("nom")

    if not nom:
        return jsonify({"erreur": "nom est obligatoire"}), 400

    if Domaine.query.filter_by(nom=nom).first():
        return jsonify({"erreur": "ce domaine existe déjà"}), 409

    domaine = Domaine(nom=nom)
    db.session.add(domaine)
    db.session.commit()
    return jsonify(domaine_vers_dict(domaine)), 201

@domaines_bp.route("/<int:domaine_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_domaine(domaine_id):
    domaine = db.get_or_404(Domaine, domaine_id)
    donnees = request.get_json()

    if "nom" in donnees:
        domaine.nom = donnees["nom"]

    db.session.commit()
    return jsonify(domaine_vers_dict(domaine)), 200
