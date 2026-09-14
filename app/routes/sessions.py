"""
Routes API pour la gestion du cycle de vie des sessions de formation.

Ce module expose les endpoints RESTful permettant :
- La recherche avancée et le filtrage multicritère (formateur, formation, domaine,
  type intra/inter, statut temporel, plage de dates, palier de remplissage).
- L'exportation des sessions aux formats CSV, Excel (XLSX) et PDF (fiche session imprimable).
- La création, la modification et la suppression de sessions avec validation stricte
  des contraintes calendaires, de la concordance de domaine formateur/formation et de l'intégrité relationnelle.
"""

from datetime import date
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, func
from app.extensions import db
from app.models import Session, Formation, Formateur, Inscription
from app.services.permissions import gestionnaire_ou_admin_required
from app.services.access_service import sessions_visibles, exiger_acces
from app.services.session_validation_service import (
    ErreurValidationSession,
    valeurs_session_validees,
)

# Déclaration du Blueprint Flask pour l'API des sessions
sessions_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")

# Listes des valeurs énumérées autorisées pour les sessions
STATUTS_VALIDES = ["planifiee", "en_cours", "terminee", "annulee"]
TYPES_VALIDES = ["intra", "inter"]


def session_vers_dict(session):
    """
    Convertit une instance SQLAlchemy de Session en dictionnaire avec calcul des ratios d'occupation.

    :param session: Instance du modèle Session.
    :return: Dictionnaire JSON représentant la session et ses entités associées.
    """
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


def obtenir_sessions_filtrees(user, args):
    """
    Construit la requête SQL SQLAlchemy avec application des filtres dynamiques combinés (AND).

    :param user: Utilisateur connecté (contrôle du périmètre RBAC).
    :param args: Paramètres de requête HTTP (request.args).
    :return: Liste des sessions correspondantes.
    """
    query = sessions_visibles(user)

    # Filtrage par identifiant de formateur
    formateur_id = args.get("formateur_id", type=int)
    if formateur_id:
        query = query.filter(Session.formateur_id == formateur_id)

    # Filtrage par identifiant de formation
    formation_id = args.get("formation_id", type=int)
    if formation_id:
        query = query.filter(Session.formation_id == formation_id)

    # Filtrage par domaine pédagogique
    domaine_id = args.get("domaine_id", type=int)
    if domaine_id:
        query = query.join(Session.formation).filter(Formation.domaine_id == domaine_id)

    # Filtrage par type de session (intra ou inter-entreprise)
    type_session = args.get("type")
    if type_session in TYPES_VALIDES:
        query = query.filter(Session.type == type_session)

    # Filtrage par statut de déroulement
    statut = args.get("statut")
    if statut in STATUTS_VALIDES:
        query = query.filter(Session.statut == statut)

    # Filtrage par bornes de dates de début
    date_debut_min = args.get("date_debut_min")
    if date_debut_min:
        try:
            query = query.filter(Session.date_debut >= date.fromisoformat(date_debut_min))
        except ValueError:
            pass

    date_debut_max = args.get("date_debut_max")
    if date_debut_max:
        try:
            query = query.filter(Session.date_debut <= date.fromisoformat(date_debut_max))
        except ValueError:
            pass

    # Recherche globale sur titre formation, nom formateur ou lieu
    q = args.get("q", "").strip()
    if q:
        pattern = f"%{q}%"
        query = query.join(Session.formation).join(Session.formateur).filter(
            or_(
                Formation.titre.ilike(pattern),
                Formateur.nom.ilike(pattern),
                Session.lieu.ilike(pattern)
            )
        )

    # Filtrage par tranche de taux de remplissage (sous-requête SQL)
    remplissage = args.get("remplissage")
    if remplissage in ["sous_remplie", "nominale", "complete"]:
        subq_confirmes = (
            db.session.query(
                Inscription.session_id,
                func.count(Inscription.id).label("nb_confirmes")
            )
            .filter(Inscription.statut == "confirmee")
            .group_by(Inscription.session_id)
            .subquery()
        )
        query = query.outerjoin(subq_confirmes, Session.id == subq_confirmes.c.session_id)
        taux_expr = (func.coalesce(subq_confirmes.c.nb_confirmes, 0) * 100.0) / Session.capacite_max

        if remplissage == "sous_remplie":
            query = query.filter(taux_expr < 50.0)
        elif remplissage == "nominale":
            query = query.filter(taux_expr >= 50.0, taux_expr < 90.0)
        elif remplissage == "complete":
            query = query.filter(taux_expr >= 90.0)

    return query.distinct().all()


@sessions_bp.route("", methods=["GET"])
@login_required
def liste_sessions():
    """
    Renvoie la liste des sessions avec filtres SQL combinables (AND).
    """
    sessions = obtenir_sessions_filtrees(current_user, request.args)
    return jsonify([session_vers_dict(s) for s in sessions]), 200


@sessions_bp.route("/export/csv", methods=["GET"])
@login_required
def export_sessions_csv():
    """
    Génère un export CSV des sessions selon les filtres actifs et les droits d'accès.
    """
    from app.services.export_service import generer_csv_response
    sessions = obtenir_sessions_filtrees(current_user, request.args)
    en_tetes = {
        "id": "ID Session",
        "formation_titre": "Formation",
        "formateur_nom": "Formateur",
        "type": "Type",
        "date_debut": "Date Début",
        "date_fin": "Date Fin",
        "lieu": "Lieu",
        "statut": "Statut",
        "nb_inscrits_confirmes": "Inscrits Confirmés",
        "capacite_max": "Capacité Max",
        "taux_remplissage": "Taux Remplissage (%)",
    }
    lignes = []
    for s in sessions:
        lignes.append({
            "id": s.id,
            "formation_titre": s.formation.titre if s.formation else "",
            "formateur_nom": s.formateur.nom if s.formateur else "",
            "type": s.type,
            "date_debut": s.date_debut.isoformat() if s.date_debut else "",
            "date_fin": s.date_fin.isoformat() if s.date_fin else "",
            "lieu": s.lieu,
            "statut": s.statut,
            "nb_inscrits_confirmes": s.nb_inscrits_confirmes(),
            "capacite_max": s.capacite_max,
            "taux_remplissage": round(s.taux_remplissage(), 1),
        })
    date_str = date.today().isoformat()
    return generer_csv_response(f"sessions_export_{date_str}.csv", en_tetes, lignes)


@sessions_bp.route("/export/xlsx", methods=["GET"])
@login_required
def export_sessions_xlsx():
    """
    Génère un classeur Excel des sessions selon les filtres actifs et les droits d'accès.
    """
    from app.services.export_service import generer_xlsx_response
    sessions = obtenir_sessions_filtrees(current_user, request.args)
    en_tetes = {
        "id": "ID Session",
        "formation_titre": "Formation",
        "formateur_nom": "Formateur",
        "type": "Type",
        "date_debut": "Date Début",
        "date_fin": "Date Fin",
        "lieu": "Lieu",
        "statut": "Statut",
        "nb_inscrits_confirmes": "Inscrits Confirmés",
        "capacite_max": "Capacité Max",
        "taux_remplissage": "Taux Remplissage (%)",
    }
    lignes = []
    for s in sessions:
        lignes.append({
            "id": s.id,
            "formation_titre": s.formation.titre if s.formation else "",
            "formateur_nom": s.formateur.nom if s.formateur else "",
            "type": s.type.upper() if s.type else "",
            "date_debut": s.date_debut.isoformat() if s.date_debut else "",
            "date_fin": s.date_fin.isoformat() if s.date_fin else "",
            "lieu": s.lieu,
            "statut": s.statut.replace("_", " ").title() if s.statut else "",
            "nb_inscrits_confirmes": s.nb_inscrits_confirmes(),
            "capacite_max": s.capacite_max,
            "taux_remplissage": round(s.taux_remplissage(), 1),
        })
    date_str = date.today().isoformat()
    return generer_xlsx_response(f"sessions_export_{date_str}.xlsx", en_tetes, lignes, titre_feuille="Sessions")


@sessions_bp.route("/<int:session_id>/export/pdf", methods=["GET"])
@login_required
def export_session_pdf(session_id):
    """
    Génère la fiche récapitulative PDF complète d'une session avec la liste d'émargement des stagiaires.
    """
    from app.services.export_service import generer_fiche_session_pdf
    from app.routes.inscriptions import inscription_vers_dict
    session_obj = exiger_acces(sessions_visibles(current_user), session_id, current_user)
    inscriptions = [inscription_vers_dict(i) for i in session_obj.inscriptions]
    return generer_fiche_session_pdf(session_vers_dict(session_obj), inscriptions)


@sessions_bp.route("/<int:session_id>", methods=["GET"])
@login_required
def detail_session(session_id):
    """
    Renvoie le détail complet d'une session après vérification des droits d'accès.
    """
    session = exiger_acces(sessions_visibles(current_user), session_id, current_user)
    return jsonify(session_vers_dict(session)), 200


@sessions_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_session():
    """
    Crée une nouvelle session de formation après validation métier :
    - Présence de tous les champs obligatoires.
    - Cohérence temporelle des dates.
    - Concordance de domaine entre le formateur assigné et la formation.
    """
    donnees = request.get_json(silent=True) or {}

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

    try:
        date_debut, date_fin, statut = valeurs_session_validees(donnees)
    except ErreurValidationSession as erreur:
        return jsonify({"erreur": str(erreur)}), 400

    formation = db.session.get(Formation, formation_id)
    if not formation:
        return jsonify({"erreur": "formation_id invalide"}), 400

    formateur = db.session.get(Formateur, formateur_id)
    if not formateur:
        return jsonify({"erreur": "formateur_id invalide"}), 400

    # Règle métier : le formateur doit obligatoirement appartenir au même domaine d'expertise que la formation
    if formateur.domaine_id != formation.domaine_id:
        return jsonify({"erreur": "Le formateur sélectionné n'appartient pas au domaine de cette formation"}), 400

    session = Session(
        formation_id=formation_id,
        formateur_id=formateur_id,
        date_debut=date_debut,
        date_fin=date_fin,
        type=type_session,
        capacite_max=capacite_max,
        lieu=donnees.get("lieu"),
        statut=statut,
    )
    db.session.add(session)
    db.session.commit()
    return jsonify(session_vers_dict(session)), 201


@sessions_bp.route("/<int:session_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_session(session_id):
    """
    Met à jour les informations logistiques ou le statut d'une session.
    """
    session = db.get_or_404(Session, session_id)
    donnees = request.get_json(silent=True) or {}

    try:
        date_debut, date_fin, statut = valeurs_session_validees(donnees, session)
    except ErreurValidationSession as erreur:
        return jsonify({"erreur": str(erreur)}), 400

    session.date_debut = date_debut
    session.date_fin = date_fin
    session.statut = statut
    if "lieu" in donnees:
        session.lieu = donnees["lieu"]
    if "capacite_max" in donnees:
        if donnees["capacite_max"] <= 0:
            return jsonify({"erreur": "capacite_max doit être positif"}), 400
        session.capacite_max = donnees["capacite_max"]

    db.session.commit()
    return jsonify(session_vers_dict(session)), 200


@sessions_bp.route("/<int:session_id>", methods=["DELETE"])
@gestionnaire_ou_admin_required
def supprimer_session(session_id):
    """
    Supprime une session si aucun stagiaire n'y est inscrit (intégrité relationnelle).
    """
    session_obj = db.get_or_404(Session, session_id)

    inscription_existante = Inscription.query.filter_by(session_id=session_id).first()
    if inscription_existante is not None:
        nb_inscriptions = Inscription.query.filter_by(session_id=session_id).count()
        return jsonify({
            "erreur": f"Impossible de supprimer cette session : {nb_inscriptions} inscription(s) y sont associée(s)."
        }), 409

    db.session.delete(session_obj)
    db.session.commit()

    return "", 204
