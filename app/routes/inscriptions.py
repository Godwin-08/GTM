"""
Routes API pour la gestion des inscriptions de participants aux sessions de formation.

Ce module expose les endpoints RESTful permettant :
- Le filtrage multicritère (session, participant, formation, entreprise cliente, statut, dates).
- L'exportation tabulaire des inscriptions en CSV et Excel (XLSX).
- La création d'inscriptions avec contrôles métier stricts (session non fermée/annulée,
  gestion de la capacité maximale et bascule en liste d'attente, unicité participant-session).
- La mise à jour des statuts (confirmation, annulation, mise en liste d'attente).
"""

from datetime import date
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import Client, Formation, Inscription, Session, Participant
from app.services.permissions import gestionnaire_ou_admin_required
from app.services.access_service import inscriptions_visibles
from app.services.query_validation_service import (
    ErreurFiltre,
    date_iso,
    entier_positif,
    valeur_parmi,
)

# Déclaration du Blueprint Flask pour l'API des inscriptions
inscriptions_bp = Blueprint("inscriptions", __name__, url_prefix="/api/inscriptions")

# Liste énumérative des statuts valides pour une inscription
STATUTS_VALIDES = ["confirmee", "annulee", "liste_attente"]


def inscription_vers_dict(inscription):
    """
    Convertit une instance d'Inscription en dictionnaire JSON avec les détails imbriqués
    de la session (formation, formateur) et du participant (client entreprise).

    :param inscription: Instance SQLAlchemy d'Inscription.
    :return: Dictionnaire structuré complet pour l'affichage front-end.
    """
    return {
        "id": inscription.id,
        "date_inscription": inscription.date_inscription.isoformat(),
        "statut": inscription.statut,
        "session_id": inscription.session_id,
        "session": {
            "id": inscription.session.id,
            "date_debut": inscription.session.date_debut.isoformat(),
            "date_fin": inscription.session.date_fin.isoformat(),
            "type": inscription.session.type,
            "statut": inscription.session.statut,
            "formation": {
                "id": inscription.session.formation.id,
                "titre": inscription.session.formation.titre,
            } if inscription.session and inscription.session.formation else None,
            "formateur": {
                "id": inscription.session.formateur.id,
                "nom": inscription.session.formateur.nom,
            } if inscription.session and inscription.session.formateur else None,
        } if inscription.session else None,
        "participant": {
            "id": inscription.participant.id,
            "nom": inscription.participant.nom,
            "email": inscription.participant.email,
            "client": {
                "id": inscription.participant.client.id,
                "nom_entreprise": inscription.participant.client.nom_entreprise,
            } if inscription.participant.client else None,
        } if inscription.participant else None,
    }


def obtenir_inscriptions_filtrees(user, args):
    """
    Applique les filtres et restrictions RBAC sur la requête SQLAlchemy des inscriptions.

    :param user: Utilisateur connecté.
    :param args: Dictionnaire ou MultiDict des paramètres URL.
    :return: Tuple (liste_inscriptions, tuple_erreur_ou_None).
    """
    # Périmètre initial restreint selon le rôle (ex: formateur ne voit que ses sessions)
    query = inscriptions_visibles(user)

    # Validation des critères de filtrage
    try:
        session_id = entier_positif(args, "session_id")
        participant_id = entier_positif(args, "participant_id")
        formation_id = entier_positif(args, "formation_id")
        client_id = entier_positif(args, "client_id")
        statut = valeur_parmi(args, "statut", set(STATUTS_VALIDES))
        date_debut_min = date_iso(args, "date_debut_min")
        date_debut_max = date_iso(args, "date_debut_max")
        if date_debut_min and date_debut_max and date_debut_min > date_debut_max:
            raise ErreurFiltre("date_debut_min doit être antérieure ou égale à date_debut_max")
    except ErreurFiltre as erreur:
        return None, (jsonify({"erreur": str(erreur)}), 400)

    q = args.get("q", "").strip()

    # Jointures conditionnelles pour optimiser le plan d'exécution SQL
    if formation_id is not None or date_debut_min or date_debut_max or q:
        query = query.join(Inscription.session)
    if client_id is not None or q:
        query = query.join(Inscription.participant)

    # Application des clauses WHERE
    if session_id is not None:
        query = query.filter(Inscription.session_id == session_id)
    if participant_id is not None:
        query = query.filter(Inscription.participant_id == participant_id)
    if formation_id is not None:
        query = query.filter(Session.formation_id == formation_id)
    if client_id is not None:
        query = query.filter(Participant.client_id == client_id)
    if statut is not None:
        query = query.filter(Inscription.statut == statut)
    if date_debut_min:
        query = query.filter(Session.date_debut >= date_debut_min)
    if date_debut_max:
        query = query.filter(Session.date_debut <= date_debut_max)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Participant.nom.ilike(pattern),
                Participant.email.ilike(pattern)
            )
        )

    inscriptions = query.all()
    return inscriptions, None


@inscriptions_bp.route("", methods=["GET"])
@login_required
def liste_inscriptions():
    """
    Renvoie la liste des inscriptions filtrées selon les autorisations de l'utilisateur.
    """
    inscriptions, err = obtenir_inscriptions_filtrees(current_user, request.args)
    if err:
        return err
    return jsonify([inscription_vers_dict(i) for i in inscriptions]), 200


@inscriptions_bp.route("/export/csv", methods=["GET"])
@login_required
def export_inscriptions_csv():
    """
    Exporte la sélection d'inscriptions au format CSV avec encodage UTF-8 BOM pour Excel.
    """
    from app.services.export_service import generer_csv_response
    inscriptions, err = obtenir_inscriptions_filtrees(current_user, request.args)
    if err:
        return err
    en_tetes = {
        "id": "ID Inscription",
        "participant_nom": "Participant",
        "participant_email": "Email Participant",
        "entreprise": "Entreprise Cliente",
        "formation_titre": "Formation",
        "session_id": "ID Session",
        "date_debut_session": "Date Début Session",
        "date_inscription": "Date Inscription",
        "statut": "Statut",
    }
    lignes = []
    for i in inscriptions:
        lignes.append({
            "id": i.id,
            "participant_nom": i.participant.nom if i.participant else "",
            "participant_email": i.participant.email if i.participant else "",
            "entreprise": i.participant.client.nom_entreprise if i.participant and i.participant.client else "",
            "formation_titre": i.session.formation.titre if i.session and i.session.formation else "",
            "session_id": i.session_id,
            "date_debut_session": i.session.date_debut.isoformat() if i.session and i.session.date_debut else "",
            "date_inscription": i.date_inscription.isoformat() if i.date_inscription else "",
            "statut": i.statut,
        })
    date_str = date.today().isoformat()
    return generer_csv_response(f"inscriptions_export_{date_str}.csv", en_tetes, lignes)


@inscriptions_bp.route("/export/xlsx", methods=["GET"])
@login_required
def export_inscriptions_xlsx():
    """
    Exporte la sélection d'inscriptions sous forme de tableau Excel stylisé (.xlsx).
    """
    from app.services.export_service import generer_xlsx_response
    inscriptions, err = obtenir_inscriptions_filtrees(current_user, request.args)
    if err:
        return err
    en_tetes = {
        "id": "ID Inscription",
        "participant_nom": "Participant",
        "participant_email": "Email Participant",
        "entreprise": "Entreprise Cliente",
        "formation_titre": "Formation",
        "session_id": "ID Session",
        "date_debut_session": "Date Début Session",
        "date_inscription": "Date Inscription",
        "statut": "Statut",
    }
    lignes = []
    for i in inscriptions:
        lignes.append({
            "id": i.id,
            "participant_nom": i.participant.nom if i.participant else "",
            "participant_email": i.participant.email if i.participant else "",
            "entreprise": i.participant.client.nom_entreprise if i.participant and i.participant.client else "",
            "formation_titre": i.session.formation.titre if i.session and i.session.formation else "",
            "session_id": i.session_id,
            "date_debut_session": i.session.date_debut.isoformat() if i.session and i.session.date_debut else "",
            "date_inscription": i.date_inscription.isoformat() if i.date_inscription else "",
            "statut": i.statut.replace("_", " ").title() if i.statut else "",
        })
    date_str = date.today().isoformat()
    return generer_xlsx_response(f"inscriptions_export_{date_str}.xlsx", en_tetes, lignes, titre_feuille="Inscriptions")


@inscriptions_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_inscription():
    """
    Enregistre une nouvelle inscription avec validation des règles de capacité et de statut de la session.
    """
    donnees = request.get_json() or {}
    session_id = donnees.get("session_id")
    participant_id = donnees.get("participant_id")

    if not session_id or not participant_id:
        return jsonify({"erreur": "session_id et participant_id sont obligatoires"}), 400

    session = db.session.get(Session, session_id)
    if not session:
        return jsonify({"erreur": "session_id invalide"}), 400

    # Gardes métier : interdire les inscriptions sur des sessions closes ou annulées
    if session.statut == "annulee":
        return jsonify({"erreur": "Impossible d'inscrire un participant à une session annulée."}), 409
    if session.statut == "terminee":
        return jsonify({"erreur": "Impossible d'inscrire un participant à une session terminée."}), 409

    if not db.session.get(Participant, participant_id):
        return jsonify({"erreur": "participant_id invalide"}), 400

    # Vérification d'unicité (un participant ne peut s'inscrire qu'une fois à la même session)
    deja_inscrit = Inscription.query.filter_by(
        session_id=session_id, participant_id=participant_id
    ).first()
    if deja_inscrit:
        return jsonify({"erreur": "ce participant est déjà inscrit à cette session"}), 409

    statut = donnees.get("statut", "confirmee")
    if statut not in STATUTS_VALIDES:
        return jsonify({"erreur": f"statut doit être parmi {STATUTS_VALIDES}"}), 400

    # Contrôle de capacité : seule une inscription confirmée consomme un slot de capacité
    if statut == "confirmee" and session.est_complete():
        return jsonify({
            "erreur": "La session est complète. Utilisez le statut 'liste_attente' si vous souhaitez placer le participant en attente."
        }), 409

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
    Met à jour l'état d'une inscription (confirmee, annulee, liste_attente).
    Vérifie la capacité résiduelle en cas de promotion vers le statut 'confirmee'.
    """
    inscription = db.get_or_404(Inscription, inscription_id)
    donnees = request.get_json() or {}

    if "statut" in donnees:
        nouveau_statut = donnees["statut"]
        if nouveau_statut not in STATUTS_VALIDES:
            return jsonify({"erreur": f"statut doit être parmi {STATUTS_VALIDES}"}), 400

        # Vérifier que la session ne déborde pas si on confirme une inscription en attente/annulée
        if nouveau_statut == "confirmee" and inscription.statut != "confirmee":
            if inscription.session.est_complete():
                return jsonify({
                    "erreur": "La session est complète. Impossible de confirmer cette inscription."
                }), 409

        inscription.statut = nouveau_statut

    db.session.commit()
    return jsonify(inscription_vers_dict(inscription)), 200


@inscriptions_bp.route("", methods=["DELETE"])
@gestionnaire_ou_admin_required
def supprimer_inscriptions_en_lot():
    """Supprime plusieurs inscriptions cochées en une seule action."""
    donnees = request.get_json(silent=True) or {}
    ids = donnees.get("ids")

    if not isinstance(ids, list) or not ids:
        return jsonify({"erreur": "Aucune inscription sélectionnée."}), 400

    ids_valides = []
    for raw_id in ids:
        try:
            ids_valides.append(int(raw_id))
        except (TypeError, ValueError):
            return jsonify({"erreur": "Identifiants d'inscription invalides."}), 400

    inscriptions = Inscription.query.filter(Inscription.id.in_(ids_valides)).all()
    if not inscriptions:
        return jsonify({"erreur": "Aucune inscription correspondante trouvée."}), 404

    for inscription in inscriptions:
        db.session.delete(inscription)
    db.session.commit()

    return jsonify({"supprimees": [inscription.id for inscription in inscriptions]}), 200


@inscriptions_bp.route("/<int:inscription_id>", methods=["DELETE"])
@gestionnaire_ou_admin_required
def supprimer_inscription(inscription_id):
    """Supprime une inscription et la relation participant-session associée."""
    inscription = db.get_or_404(Inscription, inscription_id)
    db.session.delete(inscription)
    db.session.commit()
    return "", 204
