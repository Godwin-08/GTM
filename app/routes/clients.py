from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import Client, Participant
from app.services.permissions import gestionnaire_ou_admin_required

clients_bp = Blueprint("clients", __name__, url_prefix="/api/clients")

def client_vers_dict(client):
    return {
        "id": client.id,
        "nom_entreprise": client.nom_entreprise,
        "secteur": client.secteur,
        "contact_email": client.contact_email,
        # nb_participants : pratique pour un futur affichage, sans avoir
        # à faire un appel séparé juste pour compter
        "nb_participants": len(client.participants),
    }

@clients_bp.route("", methods=["GET"])
@login_required
def liste_clients():
    clients = Client.query.all()
    return jsonify([client_vers_dict(c) for c in clients]), 200

@clients_bp.route("/<int:client_id>", methods=["GET"])
@login_required
def detail_client(client_id):
    client = Client.query.get_or_404(client_id)
    return jsonify(client_vers_dict(client)), 200

@clients_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_client():
    donnees = request.get_json()
    nom_entreprise = donnees.get("nom_entreprise")

    if not nom_entreprise:
        return jsonify({"erreur": "nom_entreprise est obligatoire"}), 400

    if Client.query.filter_by(nom_entreprise=nom_entreprise).first():
        return jsonify({"erreur": "ce client existe déjà"}), 409

    client = Client(
        nom_entreprise=nom_entreprise,
        secteur=donnees.get("secteur"),
        contact_email=donnees.get("contact_email"),
    )
    db.session.add(client)
    db.session.commit()
    return jsonify(client_vers_dict(client)), 201

@clients_bp.route("/<int:client_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_client(client_id):
    client = Client.query.get_or_404(client_id)
    donnees = request.get_json()

    if "nom_entreprise" in donnees:
        client.nom_entreprise = donnees["nom_entreprise"]
    if "secteur" in donnees:
        client.secteur = donnees["secteur"]
    if "contact_email" in donnees:
        client.contact_email = donnees["contact_email"]

    db.session.commit()
    return jsonify(client_vers_dict(client)), 200

@clients_bp.route("/<int:client_id>", methods=["DELETE"])
@gestionnaire_ou_admin_required
def supprimer_client(client_id):
    client = Client.query.get_or_404(client_id)

    participant_existant = Participant.query.filter_by(client_id=client_id).first()
    if participant_existant is not None:
        nb_participants = Participant.query.filter_by(client_id=client_id).count()
        return jsonify({
            "erreur": f"Impossible de supprimer ce client : {nb_participants} participant(s) y sont associé(s)."
        }), 409

    db.session.delete(client)
    db.session.commit()
    return "", 204

