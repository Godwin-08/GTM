from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import Inscription, Session, Participant
from app.services.permissions import gestionnaire_ou_admin_required

inscriptions_bp = Blueprint("inscriptions", __name__, url_prefix="/api/inscriptions")

STATUTS_VALIDES = ["confirmee", "annulee", "liste_attente"]

def inscription_vers_dict(inscription):
    return {
        "id": inscription.id,
        "date_inscription": inscription.date_inscription.isoformat(),
        "statut": inscription.statut,
        "session_id": inscription.session_id,
        "participant": {
            "id": inscription.participant.id,
            "nom": inscription.participant.nom,
        },
    }

@inscriptions_bp.route("", methods=["GET"])
@login_required
def liste_inscriptions():
    """Filtre optionnel : /api/inscriptions?session_id=5"""
    query = Inscription.query
    session_id = request.args.get("session_id", type=int)
    if session_id:
        query = query.filter_by(session_id=session_id)
    inscriptions = query.all()
    return jsonify([inscription_vers_dict(i) for i in inscriptions]), 200

@inscriptions_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_inscription():
    donnees = request.get_json()
    session_id = donnees.get("session_id")
    participant_id = donnees.get("participant_id")

    if not session_id or not participant_id:
        return jsonify({"erreur": "session_id et participant_id sont obligatoires"}), 400

    session = Session.query.get(session_id)
    if not session:
        return jsonify({"erreur": "session_id invalide"}), 400

    if not Participant.query.get(participant_id):
        return jsonify({"erreur": "participant_id invalide"}), 400

    deja_inscrit = Inscription.query.filter_by(
        session_id=session_id, participant_id=participant_id
    ).first()
    if deja_inscrit:
        return jsonify({"erreur": "ce participant est déjà inscrit à cette session"}), 409

    statut = donnees.get("statut", "confirmee")
    if statut not in STATUTS_VALIDES:
        return jsonify({"erreur": f"statut doit être parmi {STATUTS_VALIDES}"}), 400

    inscription = Inscription(
        session_id=session_id,
        participant_id=participant_id,
        statut=statut,
    )
    db.session.add(inscription)
    db.session.commit()
    return jsonify(inscription_vers_dict(inscription)), 201

@inscriptions_bp.route("/<int:inscription_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_inscription(inscription_id):
    """
    Sert surtout à changer le statut : confirmer, annuler,
    ou mettre en liste d'attente une inscription existante.
    """
    inscription = Inscription.query.get_or_404(inscription_id)
    donnees = request.get_json()

    if "statut" in donnees:
        if donnees["statut"] not in STATUTS_VALIDES:
            return jsonify({"erreur": f"statut doit être parmi {STATUTS_VALIDES}"}), 400
        inscription.statut = donnees["statut"]

    db.session.commit()
    return jsonify(inscription_vers_dict(inscription)), 200
