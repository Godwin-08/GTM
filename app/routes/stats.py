from flask import Blueprint, request, jsonify

from app.services import stats_service, points_attention_service
from app.services.permissions import gestionnaire_ou_admin_required

# Accès réservé à gestionnaire/admin pour l'instant — le point sur l'accès
# des formateurs à leurs propres statistiques reste à trancher avec le tuteur
stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


@stats_bp.route("/remplissage", methods=["GET"])
@gestionnaire_ou_admin_required
def remplissage():
    return jsonify(stats_service.taux_remplissage_global()), 200


@stats_bp.route("/activite-domaine", methods=["GET"])
@gestionnaire_ou_admin_required
def activite_domaine():
    return jsonify(stats_service.activite_par_domaine()), 200


@stats_bp.route("/activite-client", methods=["GET"])
@gestionnaire_ou_admin_required
def activite_client():
    return jsonify(stats_service.activite_par_client()), 200


@stats_bp.route("/activite-formateur", methods=["GET"])
@gestionnaire_ou_admin_required
def activite_formateur():
    return jsonify(stats_service.activite_par_formateur()), 200


@stats_bp.route("/evolution-inscriptions", methods=["GET"])
@gestionnaire_ou_admin_required
def evolution_inscriptions():
    """Filtre optionnel : /api/stats/evolution-inscriptions?annee=2026"""
    annee = request.args.get("annee", type=int)
    return jsonify(stats_service.evolution_inscriptions(annee)), 200


@stats_bp.route("/points-attention", methods=["GET"])
@gestionnaire_ou_admin_required
def points_attention():
    """Renvoie l'ensemble des points d'attention calculés par le backend."""
    return jsonify(points_attention_service.get_points_attention()), 200


@stats_bp.route("/pca", methods=["GET"])
@gestionnaire_ou_admin_required
def pca():
    from app.services.pca_service import get_acp_complete
    return jsonify(get_acp_complete()), 200


