from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import Session, Formation, Formateur
from app.services.permissions import gestionnaire_ou_admin_required

sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")

STATUTS_VALIDES = ["planifiee", "en_cours", "terminee", "annulee"]
TYPES_VALIDES = ["intra", "inter"]

def session_vers_dict(session):
    return {
        "id": session.id,
        "date_debut": session.date_debut.isoformat(),
        "date_fin": session.date_fin.isoformat(),
        "type": session.type,
        "capacite_max": session.capacite_max,
        "lieu": session.lieu,
        "statut": session.statut,
        "formation": {
            "id": session.formation.id,
            "titre": session.formation.titre,
        },
        "formateur": {
            "id": session.formateur.id,
            "nom": session.formateur.nom,
        },
        "nb_inscrits_confirmes": session.nb_inscrits_confirmes(),
        "taux_remplissage": session.taux_remplissage(),
        "est_complete": session.est_complete(),
    }

@sessions_bp.route("", methods=["GET"])
@login_required
def liste_sessions():
    """
    Liste les sessions, avec filtres optionnels :
    /api/sessions?statut=planifiee
    /api/sessions?formateur_id=3
    """
    query = Session.query

    statut = request.args.get("statut")
    if statut:
        query = query.filter_by(statut=statut)

    formateur_id = request.args.get("formateur_id", type=int)
    if formateur_id:
        query = query.filter_by(formateur_id=formateur_id)

    sessions = query.all()
    return jsonify([session_vers_dict(s) for s in sessions]), 200

@sessions_bp.route("/<int:session_id>", methods=["GET"])
@login_required
def detail_session(session_id):
    session = Session.query.get_or_404(session_id)
    return jsonify(session_vers_dict(session)), 200

@sessions_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_session():
    donnees = request.get_json()

    formation_id = donnees.get("formation_id")
    formateur_id = donnees.get("formateur_id")
    date_debut = donnees.get("date_debut")
    date_fin = donnees.get("date_fin")
    type_session = donnees.get("type")
    capacite_max = donnees.get("capacite_max")

    if not all([formation_id, formateur_id, date_debut, date_fin, type_session, capacite_max]):
        return jsonify({
            "erreur": "formation_id, formateur_id, date_debut, date_fin, type et capacite_max sont obligatoires"
        }), 400

    if type_session not in TYPES_VALIDES:
        return jsonify({"erreur": f"type doit être parmi {TYPES_VALIDES}"}), 400

    if capacite_max <= 0:
        return jsonify({"erreur": "capacite_max doit être positif"}), 400

    if date_fin < date_debut:
        return jsonify({"erreur": "date_fin doit être postérieure ou égale à date_debut"}), 400

    formation = Formation.query.get(formation_id)
    if not formation:
        return jsonify({"erreur": "formation_id invalide"}), 400

    if not Formateur.query.get(formateur_id):
        return jsonify({"erreur": "formateur_id invalide"}), 400

    session = Session(
        formation_id=formation_id,
        formateur_id=formateur_id,
        date_debut=date_debut,
        date_fin=date_fin,
        type=type_session,
        capacite_max=capacite_max,
        lieu=donnees.get("lieu"),
        statut=donnees.get("statut", "planifiee"),
    )
    db.session.add(session)
    db.session.commit()
    return jsonify(session_vers_dict(session)), 201

@sessions_bp.route("/<int:session_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_session(session_id):
    session = Session.query.get_or_404(session_id)
    donnees = request.get_json()

    if "statut" in donnees:
        if donnees["statut"] not in STATUTS_VALIDES:
            return jsonify({"erreur": f"statut doit être parmi {STATUTS_VALIDES}"}), 400
        session.statut = donnees["statut"]

    if "date_debut" in donnees:
        session.date_debut = donnees["date_debut"]
    if "date_fin" in donnees:
        session.date_fin = donnees["date_fin"]
    if "lieu" in donnees:
        session.lieu = donnees["lieu"]
    if "capacite_max" in donnees:
        if donnees["capacite_max"] <= 0:
            return jsonify({"erreur": "capacite_max doit être positif"}), 400
        session.capacite_max = donnees["capacite_max"]

    db.session.commit()
    return jsonify(session_vers_dict(session)), 200
