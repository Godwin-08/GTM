"""
Routes API pour la gestion des formateurs (internes et externes).

Ce module expose les endpoints RESTful permettant :
- La consultation et le filtrage des formateurs (par domaine, type interne/externe, nom/email).
- Le calcul dynamique des volumes d'activité (sessions planifiées, en cours, terminées).
- La création et mise à jour des fiches formateurs avec liaison optionnelle à un compte utilisateur.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import Formateur, Domaine, Utilisateur
from app.services.permissions import gestionnaire_ou_admin_required, admin_required
from app.services.access_service import formateurs_visibles, exiger_acces
from app.services.query_validation_service import ErreurFiltre, entier_positif, valeur_parmi

# Déclaration du Blueprint Flask pour l'API des formateurs
formateurs_bp = Blueprint("formateurs", __name__, url_prefix="/api/formateurs")


def formateur_vers_dict(formateur):
    """
    Convertit un objet Formateur en dictionnaire avec calcul des métriques de sessions.

    :param formateur: Instance SQLAlchemy de Formateur.
    :return: Dictionnaire contenant les coordonnées, le domaine, le rattachement utilisateur et les stats de sessions.
    """
    # Exclure les sessions annulées du décompte d'activité opérationnelle
    sessions_valides = [s for s in formateur.sessions if s.statut != "annulee"]
    nb_sessions = len(sessions_valides)
    nb_planifiees = len([s for s in sessions_valides if s.statut in ["planifiee", "en_cours"]])
    nb_terminees = len([s for s in sessions_valides if s.statut == "terminee"])

    return {
        "id": formateur.id,
        "nom": formateur.nom,
        "email": formateur.email,
        "telephone": formateur.telephone,
        "domaine": {
            "id": formateur.domaine.id,
            "nom": formateur.domaine.nom,
        } if formateur.domaine else None,
        "nb_sessions": nb_sessions,
        "nb_planifiees": nb_planifiees,
        "nb_terminees": nb_terminees,
        "a_un_compte": formateur.utilisateur_id is not None,
    }


@formateurs_bp.route("", methods=["GET"])
@gestionnaire_ou_admin_required
def liste_formateurs():
    """
    Renvoie la liste des formateurs avec filtres optionnels combinables (AND) :
    /api/formateurs?domaine_id=1&type=interne&q=youssef
    """
    query = formateurs_visibles(current_user)

    # Validation des filtres typés
    try:
        domaine_id = entier_positif(request.args, "domaine_id")
        type_formateur = valeur_parmi(request.args, "type", {"interne", "externe"})
    except ErreurFiltre as erreur:
        return jsonify({"erreur": str(erreur)}), 400

    if domaine_id is not None:
        query = query.filter(Formateur.domaine_id == domaine_id)

    # Filtrage par statut de compte : interne (associé à un compte utilisateur) vs externe
    if type_formateur == "interne":
        query = query.filter(Formateur.utilisateur_id.isnot(None))
    elif type_formateur == "externe":
        query = query.filter(Formateur.utilisateur_id.is_(None))

    # Recherche textuelle insensible à la casse
    q = request.args.get("q", "").strip()
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Formateur.nom.ilike(pattern),
                Formateur.email.ilike(pattern)
            )
        )

    formateurs = query.all()
    return jsonify([formateur_vers_dict(f) for f in formateurs]), 200


@formateurs_bp.route("/<int:formateur_id>", methods=["GET"])
@login_required
def detail_formateur(formateur_id):
    """
    Renvoie le détail d'un formateur précis sous réserve des habilitations de l'utilisateur connecté.
    """
    formateur = exiger_acces(formateurs_visibles(current_user), formateur_id, current_user)
    return jsonify(formateur_vers_dict(formateur)), 200


@formateurs_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_formateur():
    """
    Enregistre un nouveau formateur dans la base de données.
    Vérifie l'existence du domaine et l'unicité de la liaison utilisateur éventuelle.
    """
    donnees = request.get_json() or {}
    nom = donnees.get("nom")
    domaine_id = donnees.get("domaine_id")

    if not nom or not domaine_id:
        return jsonify({"erreur": "nom et domaine_id sont obligatoires"}), 400

    if not db.session.get(Domaine, domaine_id):
        return jsonify({"erreur": "domaine_id invalide"}), 400

    utilisateur_id = donnees.get("utilisateur_id")
    if utilisateur_id:
        if not db.session.get(Utilisateur, utilisateur_id):
            return jsonify({"erreur": "utilisateur_id invalide"}), 400
        if Formateur.query.filter_by(utilisateur_id=utilisateur_id).first():
            return jsonify({"erreur": "ce compte utilisateur est déjà lié à un autre formateur"}), 409

    formateur = Formateur(
        nom=nom,
        email=donnees.get("email"),
        telephone=donnees.get("telephone"),
        domaine_id=domaine_id,
        utilisateur_id=utilisateur_id,
    )
    db.session.add(formateur)
    db.session.commit()
    return jsonify(formateur_vers_dict(formateur)), 201


@formateurs_bp.route("/<int:formateur_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_formateur(formateur_id):
    """
    Met à jour les informations de contact ou le domaine d'un formateur existant.
    """
    formateur = db.get_or_404(Formateur, formateur_id)
    donnees = request.get_json() or {}

    if "nom" in donnees:
        formateur.nom = donnees["nom"]
    if "email" in donnees:
        formateur.email = donnees["email"]
    if "telephone" in donnees:
        formateur.telephone = donnees["telephone"]
    if "domaine_id" in donnees:
        if not db.session.get(Domaine, donnees["domaine_id"]):
            return jsonify({"erreur": "domaine_id invalide"}), 400
        formateur.domaine_id = donnees["domaine_id"]

    db.session.commit()
    return jsonify(formateur_vers_dict(formateur)), 200


# =============================================================================
# Exports Formateurs (CSV & Excel)
# =============================================================================

@formateurs_bp.route("/export/csv", methods=["GET"])
@gestionnaire_ou_admin_required
def export_formateurs_csv():
    """Génère un export CSV de la liste des formateurs avec leurs statistiques d'activité."""
    from datetime import datetime
    from app.services.export_service import generer_csv_response

    formateurs = Formateur.query.order_by(Formateur.nom.asc()).all()

    en_tetes = {
        "id": "ID",
        "nom": "Nom du formateur",
        "domaine": "Domaine d'expertise",
        "type": "Type (Interne / Externe)",
        "email": "Email de contact",
        "telephone": "Téléphone",
        "compte_utilisateur": "Compte plateforme lié",
        "nb_sessions_total": "Total Sessions",
        "nb_sessions_planifiees": "Sessions Planifiées / En cours",
        "nb_sessions_terminees": "Sessions Terminées",
    }

    lignes = []
    for f in formateurs:
        sessions_valides = [s for s in f.sessions if s.statut != "annulee"]
        nb_planifiees = len([s for s in sessions_valides if s.statut in ["planifiee", "en_cours"]])
        nb_terminees = len([s for s in sessions_valides if s.statut == "terminee"])

        lignes.append({
            "id": f.id,
            "nom": f.nom,
            "domaine": f.domaine.nom if f.domaine else "",
            "type": "Interne" if f.utilisateur_id else "Externe",
            "email": f.email or "",
            "telephone": f.telephone or "",
            "compte_utilisateur": f.utilisateur.email if f.utilisateur else "Aucun",
            "nb_sessions_total": len(sessions_valides),
            "nb_sessions_planifiees": nb_planifiees,
            "nb_sessions_terminees": nb_terminees,
        })

    date_str = datetime.now().strftime("%Y%m%d")
    return generer_csv_response(f"formateurs_export_{date_str}.csv", en_tetes, lignes)


@formateurs_bp.route("/export/xlsx", methods=["GET"])
@gestionnaire_ou_admin_required
def export_formateurs_xlsx():
    """Génère un export Excel (.xlsx) stylisé des formateurs."""
    from datetime import datetime
    from app.services.export_service import generer_xlsx_response

    formateurs = Formateur.query.order_by(Formateur.nom.asc()).all()

    en_tetes = {
        "id": "ID",
        "nom": "Nom du formateur",
        "domaine": "Domaine d'expertise",
        "type": "Type (Interne / Externe)",
        "email": "Email de contact",
        "telephone": "Téléphone",
        "compte_utilisateur": "Compte plateforme lié",
        "nb_sessions_total": "Total Sessions",
        "nb_sessions_planifiees": "Sessions Planifiées / En cours",
        "nb_sessions_terminees": "Sessions Terminées",
    }

    lignes = []
    for f in formateurs:
        sessions_valides = [s for s in f.sessions if s.statut != "annulee"]
        nb_planifiees = len([s for s in sessions_valides if s.statut in ["planifiee", "en_cours"]])
        nb_terminees = len([s for s in sessions_valides if s.statut == "terminee"])

        lignes.append({
            "id": f.id,
            "nom": f.nom,
            "domaine": f.domaine.nom if f.domaine else "",
            "type": "Interne" if f.utilisateur_id else "Externe",
            "email": f.email or "",
            "telephone": f.telephone or "",
            "compte_utilisateur": f.utilisateur.email if f.utilisateur else "Aucun",
            "nb_sessions_total": len(sessions_valides),
            "nb_sessions_planifiees": nb_planifiees,
            "nb_sessions_terminees": nb_terminees,
        })

    date_str = datetime.now().strftime("%Y%m%d")
    return generer_xlsx_response(
        f"formateurs_export_{date_str}.xlsx",
        en_tetes,
        lignes,
        titre_feuille="Formateurs"
    )

