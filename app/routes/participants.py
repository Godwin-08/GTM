from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import Participant, Client
from app.services.permissions import gestionnaire_ou_admin_required

participants_bp = Blueprint("participants", __name__, url_prefix="/api/participants")

def participant_vers_dict(participant):
    return {
        "id": participant.id,
        "nom": participant.nom,
        "email": participant.email,
        "client": {
            "id": participant.client.id,
            "nom_entreprise": participant.client.nom_entreprise,
        },
    }

@participants_bp.route("", methods=["GET"])
@login_required
def liste_participants():
    """
    Renvoie tous les participants, avec un filtre optionnel par client :
    /api/participants?client_id=3
    """
    client_id = request.args.get("client_id", type=int)
    query = Participant.query
    if client_id:
        query = query.filter_by(client_id=client_id)
    participants = query.all()
    return jsonify([participant_vers_dict(p) for p in participants]), 200

@participants_bp.route("/<int:participant_id>", methods=["GET"])
@login_required
def detail_participant(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    return jsonify(participant_vers_dict(participant)), 200

@participants_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_participant():
    donnees = request.get_json()
    nom = donnees.get("nom")
    email = donnees.get("email")
    client_id = donnees.get("client_id")

    if not nom or not email or not client_id:
        return jsonify({"erreur": "nom, email et client_id sont obligatoires"}), 400

    if not Client.query.get(client_id):
        return jsonify({"erreur": "client_id invalide"}), 400

    if Participant.query.filter_by(email=email).first():
        return jsonify({"erreur": "un participant avec cet email existe déjà"}), 409

    participant = Participant(nom=nom, email=email, client_id=client_id)
    db.session.add(participant)
    db.session.commit()
    return jsonify(participant_vers_dict(participant)), 201

@participants_bp.route("/<int:participant_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_participant(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    donnees = request.get_json()

    if "nom" in donnees:
        participant.nom = donnees["nom"]
    if "email" in donnees:
        participant.email = donnees["email"]
    if "client_id" in donnees:
        if not Client.query.get(donnees["client_id"]):
            return jsonify({"erreur": "client_id invalide"}), 400
        participant.client_id = donnees["client_id"]

    db.session.commit()
    return jsonify(participant_vers_dict(participant)), 200
