from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
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

inscriptions_bp = Blueprint("inscriptions", __name__, url_prefix="/api/inscriptions")

STATUTS_VALIDES = ["confirmee", "annulee", "liste_attente"]

def inscription_vers_dict(inscription):
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
    query = inscriptions_visibles(user)

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

    if formation_id is not None or date_debut_min or date_debut_max or q:
        query = query.join(Inscription.session)
    if client_id is not None or q:
        query = query.join(Inscription.participant)

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
        from sqlalchemy import or_
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
    """Filtres SQL combinables (AND), toujours dans le périmètre autorisé."""
    inscriptions, err = obtenir_inscriptions_filtrees(current_user, request.args)
    if err:
        return err
    return jsonify([inscription_vers_dict(i) for i in inscriptions]), 200

from datetime import date

@inscriptions_bp.route("/export/csv", methods=["GET"])
@login_required
def export_inscriptions_csv():
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

@inscriptions_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_inscription():
    donnees = request.get_json()
    session_id = donnees.get("session_id")
    participant_id = donnees.get("participant_id")

    if not session_id or not participant_id:
        return jsonify({"erreur": "session_id et participant_id sont obligatoires"}), 400

    session = db.session.get(Session, session_id)
    if not session:
        return jsonify({"erreur": "session_id invalide"}), 400

    # Gardes métier : interdire les inscriptions sur sessions fermées
    if session.statut == "annulee":
        return jsonify({"erreur": "Impossible d'inscrire un participant à une session annulée."}), 409
    if session.statut == "terminee":
        return jsonify({"erreur": "Impossible d'inscrire un participant à une session terminée."}), 409

    if not db.session.get(Participant, participant_id):
        return jsonify({"erreur": "participant_id invalide"}), 400

    deja_inscrit = Inscription.query.filter_by(
        session_id=session_id, participant_id=participant_id
    ).first()
    if deja_inscrit:
        return jsonify({"erreur": "ce participant est déjà inscrit à cette session"}), 409

    statut = donnees.get("statut", "confirmee")
    if statut not in STATUTS_VALIDES:
        return jsonify({"erreur": f"statut doit être parmi {STATUTS_VALIDES}"}), 400

    # Vérification capacité : uniquement si on tente une inscription confirmée
    # Une inscription en liste_attente ou annulée ne consomme pas de place
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
    Sert surtout à changer le statut : confirmer, annuler,
    ou mettre en liste d'attente une inscription existante.
    Si le passage à 'confirmee' dépasse la capacité, on bloque.
    """
    inscription = db.get_or_404(Inscription, inscription_id)
    donnees = request.get_json()

    if "statut" in donnees:
        nouveau_statut = donnees["statut"]
        if nouveau_statut not in STATUTS_VALIDES:
            return jsonify({"erreur": f"statut doit être parmi {STATUTS_VALIDES}"}), 400

        # Si on confirme une inscription qui n'était pas confirmée,
        # vérifier que la session n'est pas déjà complète
        if nouveau_statut == "confirmee" and inscription.statut != "confirmee":
            if inscription.session.est_complete():
                return jsonify({
                    "erreur": "La session est complète. Impossible de confirmer cette inscription."
                }), 409

        inscription.statut = nouveau_statut

    db.session.commit()
    return jsonify(inscription_vers_dict(inscription)), 200
