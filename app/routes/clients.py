"""
==============================================================================
Contrôleur API Entreprises Clientes (/api/clients)
==============================================================================
Gère le cycle de vie du portefeuille clients de Galaxy Solutions :
- GET    /api/clients             : Liste paginée/filtrée avec statut d'activité
- GET    /api/clients/export/csv  : Export CSV UTF-8 BOM
- GET    /api/clients/export/xlsx : Export Excel stylisé
- GET    /api/clients/<id>        : Fiche client détaillée et historique des sessions
- POST   /api/clients             : Création d'un nouveau client
- PUT    /api/clients/<id>        : Mise à jour des coordonnées
- DELETE /api/clients/<id>        : Suppression sécurisée (bloquée si participants liés)
"""

from datetime import date
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import Client, Participant, Inscription, Session
from app.services.permissions import gestionnaire_ou_admin_required
from app.services.access_service import clients_visibles, exiger_acces, est_formateur, _formateur_id
from app.services.client_activity_service import statut_activite_client
from app.services.export_service import generer_csv_response, generer_xlsx_response

clients_bp = Blueprint("clients", __name__, url_prefix="/api/clients")


def client_vers_dict(client, user=None):
    """
    Transforme une entité Client en dictionnaire JSON structuré.
    - Intègre le statut d'activité calculé (règle des 6 mois).
    - Agrège l'historique complet des sessions suivies par les collaborateurs.
    - Cloisonne les données si l'utilisateur est un formateur.
    """
    query_inscriptions = (
        Inscription.query
        .join(Participant)
        .filter(Participant.client_id == client.id, Inscription.statut == "confirmee")
    )
    if user and est_formateur(user):
        fid = _formateur_id(user)
        query_inscriptions = query_inscriptions.join(Session).filter(Session.formateur_id == fid)

    inscriptions_confirmees = query_inscriptions.all()

    info_activite = statut_activite_client(client.id)
    statut_activite = info_activite["statut"]
    label_activite = info_activite["label"]
    mois_inactivite = info_activite["mois_inactivite"]
    date_derniere = info_activite["derniere_activite"]
    derniere_activite_fmt = date_derniere.strftime("%d/%m/%Y") if date_derniere else "—"

    # Agrégation des sessions de formation suivies par les salariés du client
    sessions_map = {}
    formations_ids = set()
    participants_ids = set()
    for i in inscriptions_confirmees:
        if i.participant_id:
            participants_ids.add(i.participant_id)
        if i.session:
            if i.session.formation_id:
                formations_ids.add(i.session.formation_id)
            sid = i.session.id
            if sid not in sessions_map:
                sessions_map[sid] = {
                    "id": i.session.id,
                    "formation_titre": i.session.formation.titre if i.session.formation else "Formation sans titre",
                    "formation_id": i.session.formation_id,
                    "date_debut": i.session.date_debut.strftime("%d/%m/%Y") if i.session.date_debut else "—",
                    "date_fin": i.session.date_fin.strftime("%d/%m/%Y") if i.session.date_fin else "—",
                    "raw_date": i.session.date_debut or date.min,
                    "statut": i.session.statut,
                    "nb_participants": 0,
                }
            sessions_map[sid]["nb_participants"] += 1

    sessions_historique = sorted(
        sessions_map.values(),
        key=lambda s: s["raw_date"],
        reverse=True
    )
    for s in sessions_historique:
        s.pop("raw_date", None)

    nb_participants = len(participants_ids) if (user and est_formateur(user)) else len(client.participants)

    return {
        "id": client.id,
        "nom_entreprise": client.nom_entreprise,
        "secteur": client.secteur,
        "contact_email": client.contact_email,
        "nb_participants": nb_participants,
        "nb_sessions": len(sessions_map),
        "nb_formations": len(formations_ids),
        "derniere_activite": derniere_activite_fmt,
        "statut_activite": statut_activite,
        "label_activite": label_activite,
        "mois_inactivite": mois_inactivite,
        "sessions_historique": sessions_historique,
    }


def obtenir_clients_filtres(user, args):
    """Applique les filtres de recherche textuelle, de secteur et de statut d'activité."""
    query = clients_visibles(user)

    q = args.get("q", "").strip()
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Client.nom_entreprise.ilike(pattern),
                Client.contact_email.ilike(pattern)
            )
        )

    secteur = args.get("secteur", "").strip()
    if secteur:
        query = query.filter(Client.secteur.ilike(f"%{secteur}%"))

    clients = query.all()
    dicts = [client_vers_dict(c, user) for c in clients]

    statut_activite = args.get("statut_activite")
    if statut_activite:
        if statut_activite not in ["actif", "inactif", "aucune"]:
            return None, (jsonify({"erreur": "statut_activite doit être parmi ['actif', 'inactif', 'aucune']"}), 400)
        dicts = [d for d in dicts if d["statut_activite"] == statut_activite]

    return dicts, None


@clients_bp.route("", methods=["GET"])
@login_required
def liste_clients():
    """Renvoie la liste des clients filtrés selon les critères de la requête."""
    dicts, err = obtenir_clients_filtres(current_user, request.args)
    if err:
        return err
    return jsonify(dicts), 200


@clients_bp.route("/export/csv", methods=["GET"])
@login_required
def export_clients_csv():
    """Génère un export CSV de la liste courante des clients."""
    dicts, err = obtenir_clients_filtres(current_user, request.args)
    if err:
        return err
    en_tetes = {
        "id": "ID Client",
        "nom_entreprise": "Entreprise",
        "secteur": "Secteur",
        "contact_email": "Contact Email",
        "nb_participants": "Nb Participants",
        "nb_sessions": "Nb Sessions",
        "nb_formations": "Nb Formations",
        "statut_activite": "Statut Activité",
        "label_activite": "Label Activité",
        "derniere_activite": "Dernière Activité",
    }
    lignes = []
    for d in dicts:
        lignes.append({
            "id": d["id"],
            "nom_entreprise": d["nom_entreprise"],
            "secteur": d["secteur"] or "",
            "contact_email": d["contact_email"] or "",
            "nb_participants": d["nb_participants"],
            "nb_sessions": d["nb_sessions"],
            "nb_formations": d["nb_formations"],
            "statut_activite": d["statut_activite"],
            "label_activite": d["label_activite"],
            "derniere_activite": d["derniere_activite"],
        })
    date_str = date.today().isoformat()
    return generer_csv_response(f"clients_export_{date_str}.csv", en_tetes, lignes)


@clients_bp.route("/export/xlsx", methods=["GET"])
@login_required
def export_clients_xlsx():
    """Génère un export Excel (.xlsx) stylisé des clients."""
    dicts, err = obtenir_clients_filtres(current_user, request.args)
    if err:
        return err
    en_tetes = {
        "id": "ID Client",
        "nom_entreprise": "Entreprise",
        "secteur": "Secteur",
        "contact_email": "Contact Email",
        "nb_participants": "Nb Participants",
        "nb_sessions": "Nb Sessions",
        "nb_formations": "Nb Formations",
        "label_activite": "Statut Activité",
        "derniere_activite": "Dernière Activité",
    }
    lignes = []
    for d in dicts:
        lignes.append({
            "id": d["id"],
            "nom_entreprise": d["nom_entreprise"],
            "secteur": d["secteur"] or "",
            "contact_email": d["contact_email"] or "",
            "nb_participants": d["nb_participants"],
            "nb_sessions": d["nb_sessions"],
            "nb_formations": d["nb_formations"],
            "label_activite": d["label_activite"],
            "derniere_activite": d["derniere_activite"] or "Aucune",
        })
    date_str = date.today().isoformat()
    return generer_xlsx_response(f"clients_export_{date_str}.xlsx", en_tetes, lignes, titre_feuille="Clients")


@clients_bp.route("/<int:client_id>", methods=["GET"])
@login_required
def detail_client(client_id):
    """Renvoie la fiche détaillée d'un client."""
    client = exiger_acces(clients_visibles(current_user), client_id, current_user)
    return jsonify(client_vers_dict(client, current_user)), 200


@clients_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_client():
    """Crée une nouvelle entreprise cliente."""
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
    """Met à jour les informations d'une entreprise cliente."""
    client = db.get_or_404(Client, client_id)
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
    """Supprime un client si aucun participant n'y est rattaché (garantie d'intégrité)."""
    client = db.get_or_404(Client, client_id)

    participant_existant = Participant.query.filter_by(client_id=client_id).first()
    if participant_existant is not None:
        nb_participants = Participant.query.filter_by(client_id=client_id).count()
        return jsonify({
            "erreur": f"Impossible de supprimer ce client : {nb_participants} participant(s) y sont associé(s)."
        }), 409

    db.session.delete(client)
    db.session.commit()
    return "", 204

