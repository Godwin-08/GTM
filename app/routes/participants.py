"""
Routes API pour la gestion des participants aux formations.

Ce module expose les endpoints RESTful permettant :
- La recherche et le filtrage des stagiaires/participants par entreprise cliente ou mot-clé.
- L'exportation de l'annuaire des participants en formats CSV et Excel (XLSX).
- La consultation du profil individuel avec métriques d'inscriptions filtrées par habilitation.
- La création, modification et suppression sécurisée des participants.
"""

from datetime import date
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import Participant, Client, Inscription
from app.services.permissions import gestionnaire_ou_admin_required
from app.services.access_service import participants_visibles, exiger_acces, est_formateur, _formateur_id
from app.services.query_validation_service import ErreurFiltre, entier_positif

# Déclaration du Blueprint Flask pour l'API des participants
participants_bp = Blueprint("participants", __name__, url_prefix="/api/participants")


def participant_vers_dict(participant, user=None):
    """
    Transforme une instance de Participant en dictionnaire avec calcul des métriques de parcours.
    Si l'utilisateur connecté est un formateur, restreint les statistiques de suivi
    à son périmètre d'habilitation strict.

    :param participant: Instance SQLAlchemy de Participant.
    :param user: Utilisateur connecté pour le filtrage contextualisé des inscriptions.
    :return: Dictionnaire JSON représentant le participant.
    """
    inscriptions = participant.inscriptions
    if user and est_formateur(user):
        fid = _formateur_id(user)
        inscriptions = [i for i in inscriptions if i.session and i.session.formateur_id == fid]

    inscriptions_valides = [i for i in inscriptions if i.statut != "annulee"]
    nb_inscriptions = len(inscriptions_valides)

    # Décompte des formations distinctes suivies au travers des sessions valides
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


def obtenir_participants_filtres(user, args):
    """
    Construit et exécute la requête filtrée des participants autorisés.

    :param user: Utilisateur actuel.
    :param args: Dictionnaire des paramètres de requête.
    :return: Tuple (liste_participants, erreur_reponse_ou_None).
    """
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
    Renvoie tous les participants accessibles avec filtres optionnels :
    /api/participants?client_id=3&q=alex
    """
    participants, err = obtenir_participants_filtres(current_user, request.args)
    if err:
        return err
    return jsonify([participant_vers_dict(p, current_user) for p in participants]), 200


@participants_bp.route("/export/csv", methods=["GET"])
@login_required
def export_participants_csv():
    """
    Génère un fichier d'export CSV de l'annuaire des participants selon le périmètre RBAC.
    """
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
        d = participant_vers_dict(p, current_user)
        lignes.append({
            "id": d["id"],
            "nom": d["nom"],
            "email": d["email"],
            "entreprise": d["client"]["nom_entreprise"] if d["client"] else "",
            "nb_inscriptions": d["nb_inscriptions"],
            "nb_formations": d["nb_formations"],
        })
    date_str = date.today().isoformat()
    return generer_csv_response(f"participants_export_{date_str}.csv", en_tetes, lignes)


@participants_bp.route("/export/xlsx", methods=["GET"])
@login_required
def export_participants_xlsx():
    """
    Génère un classeur Excel de l'annuaire des participants selon le périmètre RBAC.
    """
    from app.services.export_service import generer_xlsx_response
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
        d = participant_vers_dict(p, current_user)
        lignes.append({
            "id": d["id"],
            "nom": d["nom"],
            "email": d["email"],
            "entreprise": d["client"]["nom_entreprise"] if d["client"] else "",
            "nb_inscriptions": d["nb_inscriptions"],
            "nb_formations": d["nb_formations"],
        })
    date_str = date.today().isoformat()
    return generer_xlsx_response(f"participants_export_{date_str}.xlsx", en_tetes, lignes, titre_feuille="Participants")


@participants_bp.route("/<int:participant_id>", methods=["GET"])
@login_required
def detail_participant(participant_id):
    """
    Renvoie le profil détaillé d'un participant après contrôle d'habilitation.
    """
    participant = exiger_acces(participants_visibles(current_user), participant_id, current_user)
    return jsonify(participant_vers_dict(participant, current_user)), 200


@participants_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_participant():
    """
    Enregistre un nouveau participant et le lie à son entreprise cliente.
    """
    donnees = request.get_json() or {}
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
    """
    Met à jour les coordonnées ou l'entreprise de rattachement d'un participant.
    """
    participant = db.get_or_404(Participant, participant_id)
    donnees = request.get_json() or {}

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
    """
    Supprime un participant si aucune inscription historique ne lui est rattachée.
    """
    participant = db.get_or_404(Participant, participant_id)

    # Intégrité référentielle : vérification de l'existence d'inscriptions
    inscription_existante = Inscription.query.filter_by(participant_id=participant_id).first()
    if inscription_existante is not None:
        nb_inscriptions = Inscription.query.filter_by(participant_id=participant_id).count()
        return jsonify({
            "erreur": f"Impossible de supprimer ce participant : {nb_inscriptions} inscription(s) y sont associée(s)."
        }), 409

    db.session.delete(participant)
    db.session.commit()

    return "", 204
