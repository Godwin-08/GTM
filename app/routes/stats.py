"""
==============================================================================
Contrôleur API Statistiques & Pilotage Décisionnel (/api/stats)
==============================================================================
Expose les points de terminaison d'analyse de données, KPI et exports de gestion :
- GET /api/stats/kpi-globaux          : 6 indicateurs clés de synthèse
- GET /api/stats/remplissage           : Remplissage global et sessions extrêmes
- GET /api/stats/activite-domaine     : Volumes d'activité par domaine
- GET /api/stats/activite-client      : Engagement et inactivité des clients
- GET /api/stats/activite-formateur   : Charge et taux de remplissage formateurs
- GET /api/stats/evolution-inscriptions : Chronologie mensuelle des inscriptions
- GET /api/stats/points-attention     : Alertes de gestion et sessions à risque
- GET /api/stats/pca                  : Résultats factoriels de l'ACP
- GET /api/stats/export/pdf           : Téléchargement du rapport de décision PDF
- GET /api/stats/kpi-formateur        : Espace personnel du formateur connecté
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required

from app.services import stats_service, points_attention_service
from app.services.permissions import gestionnaire_ou_admin_required, tous_roles_required
from app.services.query_validation_service import ErreurFiltre, entier_positif

stats_bp = Blueprint("stats", __name__, url_prefix="/api/stats")


def extraire_filtres_stats():
    """
    Extrait et valide les filtres universels de la requête HTTP (année, domaine, client, formateur).
    Applique le cloisonnement automatique si l'utilisateur est un formateur.
    """
    annee = entier_positif(request.args, "annee")
    domaine_id = entier_positif(request.args, "domaine_id")
    client_id = entier_positif(request.args, "client_id")
    formateur_id = entier_positif(request.args, "formateur_id")

    # Cloisonnement de sécurité : un formateur ne peut consulter que ses propres métriques
    if current_user.is_authenticated and current_user.a_role("formateur"):
        if current_user.formateur:
            formateur_id = current_user.formateur.id

    return annee, domaine_id, client_id, formateur_id


@stats_bp.route("/kpi-globaux", methods=["GET"])
@gestionnaire_ou_admin_required
def kpi_globaux():
    """Renvoie les 6 indicateurs globaux du tableau de bord sous les filtres actifs."""
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
    """Renvoie les métriques de taux de remplissage et les sessions les plus/moins remplies."""
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
    """Renvoie la répartition du nombre de sessions et d'inscriptions par domaine."""
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
    """Renvoie les métriques d'activité et d'inactivité par entreprise cliente."""
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
    """Renvoie les volumes d'activité et taux de remplissage par formateur."""
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
    """Renvoie l'évolution mensuelle des inscriptions confirmées (pour affichage graphique)."""
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
    """Renvoie l'ensemble des points d'attention et alertes calculés par le backend."""
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
    """Exécute l'Analyse en Composantes Principales (ACP) et retourne les projections factorielles."""
    from app.services.acp_service import get_acp_complete
    return jsonify(get_acp_complete()), 200


@stats_bp.route("/export/pdf", methods=["GET"])
@gestionnaire_ou_admin_required
def export_dashboard_pdf():
    """Génère le rapport de décision PDF du tableau de bord selon les filtres actifs."""
    from app.services.export_service import generer_rapport_dashboard_pdf
    from app.models import Domaine, Client, Formateur
    from app.extensions import db

    try:
        annee, domaine_id, client_id, formateur_id = extraire_filtres_stats()
    except ErreurFiltre as err:
        return jsonify({"erreur": str(err)}), 400

    kpis = stats_service.kpi_globaux(
        annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id
    )
    points_att = points_attention_service.get_points_attention(
        annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id
    )

    # Construction du libellé de périmètre
    labels = []
    if annee:
        labels.append(f"Année {annee}")
    if domaine_id:
        d = db.session.get(Domaine, domaine_id)
        if d:
            labels.append(f"Domaine: {d.nom}")
    if client_id:
        c = db.session.get(Client, client_id)
        if c:
            labels.append(f"Client: {c.nom_entreprise}")
    if formateur_id:
        f = db.session.get(Formateur, formateur_id)
        if f:
            labels.append(f"Formateur: {f.nom}")

    filtres_str = " • ".join(labels) if labels else "Global Entreprise"
    return generer_rapport_dashboard_pdf(kpis, points_att, filtres_str)


@stats_bp.route("/kpi-formateur", methods=["GET"])
@tous_roles_required
def kpi_formateur():
    """KPIs personnels du formateur connecté (accès réservé au formateur lui-même)."""
    if not current_user.a_role("formateur"):
        from flask import abort
        abort(403, description="Réservé aux formateurs.")
    if not current_user.formateur:
        return jsonify({"erreur": "Aucun profil formateur associé à ce compte."}), 404
    return jsonify(stats_service.kpi_formateur(current_user.formateur.id)), 200




