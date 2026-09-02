from flask import Blueprint, request, jsonify
from flask_login import current_user

from app.services import stats_service, points_attention_service
from app.services.permissions import gestionnaire_ou_admin_required
from app.services.query_validation_service import ErreurFiltre, entier_positif

stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


def extraire_filtres_stats():
    annee = entier_positif(request.args, "annee")
    domaine_id = entier_positif(request.args, "domaine_id")
    client_id = entier_positif(request.args, "client_id")
    formateur_id = entier_positif(request.args, "formateur_id")

    if current_user.is_authenticated and current_user.a_role("formateur"):
        if current_user.formateur:
            formateur_id = current_user.formateur.id

    return annee, domaine_id, client_id, formateur_id


@stats_bp.route("/kpi-globaux", methods=["GET"])
@gestionnaire_ou_admin_required
def kpi_globaux():
    """Source unique des indicateurs globaux du tableau de bord avec filtres optionnels."""
    try:
        annee, domaine_id, client_id, formateur_id = extraire_filtres_stats()
    except ErreurFiltre as err:
        return jsonify({"erreur": str(err)}), 400

    return jsonify(stats_service.kpi_globaux(
        annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id
    )), 200


@stats_bp.route("/remplissage", methods=["GET"])
@gestionnaire_ou_admin_required
def remplissage():
    try:
        annee, domaine_id, client_id, formateur_id = extraire_filtres_stats()
    except ErreurFiltre as err:
        return jsonify({"erreur": str(err)}), 400

    return jsonify(stats_service.taux_remplissage_global(
        annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id
    )), 200


@stats_bp.route("/activite-domaine", methods=["GET"])
@gestionnaire_ou_admin_required
def activite_domaine():
    try:
        annee, domaine_id, client_id, formateur_id = extraire_filtres_stats()
    except ErreurFiltre as err:
        return jsonify({"erreur": str(err)}), 400

    return jsonify(stats_service.activite_par_domaine(
        annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id
    )), 200


@stats_bp.route("/activite-client", methods=["GET"])
@gestionnaire_ou_admin_required
def activite_client():
    try:
        annee, domaine_id, client_id, formateur_id = extraire_filtres_stats()
    except ErreurFiltre as err:
        return jsonify({"erreur": str(err)}), 400

    return jsonify(stats_service.activite_par_client(
        annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id
    )), 200


@stats_bp.route("/activite-formateur", methods=["GET"])
@gestionnaire_ou_admin_required
def activite_formateur():
    try:
        annee, domaine_id, client_id, formateur_id = extraire_filtres_stats()
    except ErreurFiltre as err:
        return jsonify({"erreur": str(err)}), 400

    return jsonify(stats_service.activite_par_formateur(
        annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id
    )), 200


@stats_bp.route("/evolution-inscriptions", methods=["GET"])
@gestionnaire_ou_admin_required
def evolution_inscriptions():
    try:
        annee, domaine_id, client_id, formateur_id = extraire_filtres_stats()
    except ErreurFiltre as err:
        return jsonify({"erreur": str(err)}), 400

    return jsonify(stats_service.evolution_inscriptions(
        annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id
    )), 200


@stats_bp.route("/points-attention", methods=["GET"])
@gestionnaire_ou_admin_required
def points_attention():
    """Renvoie l'ensemble des points d'attention calculés par le backend sous filtres."""
    try:
        annee, domaine_id, client_id, formateur_id = extraire_filtres_stats()
    except ErreurFiltre as err:
        return jsonify({"erreur": str(err)}), 400

    return jsonify(points_attention_service.get_points_attention(
        annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id
    )), 200


@stats_bp.route("/pca", methods=["GET"])
@gestionnaire_ou_admin_required
def pca():
    from app.services.acp_service import get_acp_complete
    return jsonify(get_acp_complete()), 200


