from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import Participant, Client, Inscription
from app.services.permissions import gestionnaire_ou_admin_required
from app.services.access_service import participants_visibles, exiger_acces

participants_bp = Blueprint("participants", __name__, url_prefix="/api/participants")

def participant_vers_dict(participant):
    """
    Transforme un objet Participant en dict JSON avec métriques d'activité :
    - nb_inscriptions : nombre d'inscriptions valides (statut != 'annulee')
    - nb_formations : nombre de formations distinctes suivies via ces inscriptions valides
    """
    inscriptions_valides = [i for i in participant.inscriptions if i.statut != "annulee"]
    nb_inscriptions = len(inscriptions_valides)
    
    # Formations distinctes suivies via les sessions des inscriptions valides
    formations_ids = {
        i.session.formation_id for i in inscriptions_valides if i.session and i.session.formation_id
    }
    nb_formations = len(formations_ids)

    return {
        "id": participant.id,
        "nom": participant.nom,
        "email": participant.email,
        "client": {
            "id": participant.client.id,
            "nom_entreprise": participant.client.nom_entreprise,
        } if participant.client else None,
        "nb_inscriptions": nb_inscriptions,
        "nb_formations": nb_formations,
    }

from app.services.query_validation_service import ErreurFiltre, entier_positif

def obtenir_participants_filtres(user, args):
    query = participants_visibles(user)

    try:
        client_id = entier_positif(args, "client_id")
    except ErreurFiltre as erreur:
        return None, (jsonify({"erreur": str(erreur)}), 400)

    if client_id is not None:
        query = query.filter(Participant.client_id == client_id)

    q = args.get("q", "").strip()
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Participant.nom.ilike(pattern),
                Participant.email.ilike(pattern)
            )
        )

    participants = query.order_by(Participant.nom.asc()).all()
    return participants, None

@participants_bp.route("", methods=["GET"])
@login_required
def liste_participants():
    """
    Renvoie tous les participants, avec filtres optionnels :
    /api/participants?client_id=3&q=alex
    """
    participants, err = obtenir_participants_filtres(current_user, request.args)
    if err:
        return err
    return jsonify([participant_vers_dict(p) for p in participants]), 200

from datetime import date

@participants_bp.route("/export/csv", methods=["GET"])
@login_required
def export_participants_csv():
    from app.services.export_service import generer_csv_response
    participants, err = obtenir_participants_filtres(current_user, request.args)
    if err:
        return err
    en_tetes = {
        "id": "ID Participant",
        "nom": "Nom",
        "email": "Email",
        "entreprise": "Entreprise",
        "nb_inscriptions": "Nb Inscriptions",
        "nb_formations": "Nb Formations",
    }
    lignes = []
    for p in participants:
        inscriptions_valides = [i for i in p.inscriptions if i.statut != "annulee"]
        formations_ids = {i.session.formation_id for i in inscriptions_valides if i.session and i.session.formation_id}
        lignes.append({
            "id": p.id,
            "nom": p.nom,
            "email": p.email,
            "entreprise": p.client.nom_entreprise if p.client else "",
            "nb_inscriptions": len(inscriptions_valides),
            "nb_formations": len(formations_ids),
        })
    date_str = date.today().isoformat()
    return generer_csv_response(f"participants_export_{date_str}.csv", en_tetes, lignes)

@participants_bp.route("/<int:participant_id>", methods=["GET"])
@login_required
def detail_participant(participant_id):
    participant = exiger_acces(participants_visibles(current_user), participant_id, current_user)
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

    if not db.session.get(Client, client_id):
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
    participant = db.get_or_404(Participant, participant_id)
    donnees = request.get_json()

    if "nom" in donnees:
        participant.nom = donnees["nom"]
    if "email" in donnees:
        participant.email = donnees["email"]
    if "client_id" in donnees:
        if not db.session.get(Client, donnees["client_id"]):
            return jsonify({"erreur": "client_id invalide"}), 400
        participant.client_id = donnees["client_id"]

    db.session.commit()
    return jsonify(participant_vers_dict(participant)), 200

@participants_bp.route("/<int:participant_id>", methods=["DELETE"])
@gestionnaire_ou_admin_required
def supprimer_participant(participant_id):
    participant = db.get_or_404(Participant, participant_id)

    inscription_existante = Inscription.query.filter_by(participant_id=participant_id).first()

    if inscription_existante is not None:
        nb_inscriptions = Inscription.query.filter_by(participant_id=participant_id).count()
        return jsonify({
            "erreur": f"Impossible de supprimer ce participant : {nb_inscriptions} inscription(s) y sont associée(s)."
        }), 409

    db.session.delete(participant)
    db.session.commit()

    return "", 204
