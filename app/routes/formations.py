"""
Routes API pour la gestion des formations pédagogiques.

Ce module expose les points d'entrée (endpoints) RESTful permettant :
- La consultation et le filtrage multicritère (domaine, mot-clé textuel) des formations.
- L'exportation des listes de formations aux formats CSV et Excel (XLSX).
- La consultation détaillée d'une formation selon les habilitations RBAC de l'utilisateur.
- La création, la mise à jour et la suppression de formations avec vérification des
  contraintes d'intégrité relationnelle (présence de sessions associées).
"""

from datetime import date
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_
from app.extensions import db
from app.models import Formation, Domaine, Session
from app.services.permissions import gestionnaire_ou_admin_required
from app.services.access_service import formations_visibles, exiger_acces
from app.services.query_validation_service import ErreurFiltre, entier_positif

# Déclaration du Blueprint Flask pour l'API des formations
formations_bp = Blueprint("formations", __name__, url_prefix="/api/formations")


def formation_vers_dict(formation):
    """
    Convertit une instance du modèle SQLAlchemy Formation en dictionnaire sérialisable en JSON.

    :param formation: Instance du modèle Formation.
    :return: Dictionnaire contenant les attributs de la formation et les informations imbriquées de son domaine.
    """
    return {
        "id": formation.id,
        "titre": formation.titre,
        "duree_jours": formation.duree_jours,
        "description": formation.description,
        "domaine": {
            "id": formation.domaine.id,
            "nom": formation.domaine.nom,
        } if formation.domaine else None,
    }


def obtenir_formations_filtrees(user, args):
    """
    Applique les filtres de recherche et de restriction d'accès sur la requête des formations.

    :param user: Utilisateur actuellement connecté (Flask-Login current_user).
    :param args: Paramètres de requête URL (request.args).
    :return: Tuple (liste_formations, erreur_reponse_ou_None).
    """
    # Récupération de la requête de base restreinte selon le rôle de l'utilisateur
    query = formations_visibles(user)

    # Validation et application du filtre par identifiant de domaine
    try:
        domaine_id = entier_positif(args, "domaine_id")
    except ErreurFiltre as erreur:
        return None, (jsonify({"erreur": str(erreur)}), 400)
    if domaine_id is not None:
        query = query.filter(Formation.domaine_id == domaine_id)

    # Filtrage textuel insensible à la casse sur le titre et la description
    q = args.get("q", "").strip()
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            or_(
                Formation.titre.ilike(pattern),
                Formation.description.ilike(pattern)
            )
        )

    return query.all(), None


@formations_bp.route("", methods=["GET"])
@login_required
def liste_formations():
    """
    Renvoie la liste des formations visibles par l'utilisateur connecté avec filtres optionnels.
    Exemple : /api/formations?domaine_id=1&q=python
    """
    formations, err = obtenir_formations_filtrees(current_user, request.args)
    if err:
        return err
    return jsonify([formation_vers_dict(f) for f in formations]), 200


@formations_bp.route("/export/csv", methods=["GET"])
@login_required
def export_formations_csv():
    """
    Génère et télécharge un fichier d'export CSV des formations filtrées selon les droits de l'utilisateur.
    """
    from app.services.export_service import generer_csv_response
    formations, err = obtenir_formations_filtrees(current_user, request.args)
    if err:
        return err
    en_tetes = {
        "id": "ID Formation",
        "titre": "Titre",
        "domaine": "Domaine",
        "duree_jours": "Durée (jours)",
        "description": "Description",
    }
    lignes = []
    for f in formations:
        lignes.append({
            "id": f.id,
            "titre": f.titre,
            "domaine": f.domaine.nom if f.domaine else "",
            "duree_jours": f.duree_jours,
            "description": f.description or "",
        })
    date_str = date.today().isoformat()
    return generer_csv_response(f"formations_export_{date_str}.csv", en_tetes, lignes)


@formations_bp.route("/export/xlsx", methods=["GET"])
@login_required
def export_formations_xlsx():
    """
    Génère et télécharge un classeur Excel (XLSX) des formations filtrées selon les droits de l'utilisateur.
    """
    from app.services.export_service import generer_xlsx_response
    formations, err = obtenir_formations_filtrees(current_user, request.args)
    if err:
        return err
    en_tetes = {
        "id": "ID Formation",
        "titre": "Titre",
        "domaine": "Domaine",
        "duree_jours": "Durée (jours)",
        "description": "Description",
    }
    lignes = []
    for f in formations:
        lignes.append({
            "id": f.id,
            "titre": f.titre,
            "domaine": f.domaine.nom if f.domaine else "",
            "duree_jours": f.duree_jours,
            "description": f.description or "",
        })
    date_str = date.today().isoformat()
    return generer_xlsx_response(f"formations_export_{date_str}.xlsx", en_tetes, lignes, titre_feuille="Formations")


@formations_bp.route("/<int:formation_id>", methods=["GET"])
@login_required
def detail_formation(formation_id):
    """
    Renvoie le détail complet d'une formation précise, ou 404/403 si inaccessible.
    """
    formation = exiger_acces(formations_visibles(current_user), formation_id, current_user)
    return jsonify(formation_vers_dict(formation)), 200


@formations_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_formation():
    """
    Crée une nouvelle formation au catalogue après validation des règles métier (durée, unicité du titre, domaine).
    Réservé aux profils Gestionnaire et Administrateur.
    """
    donnees = request.get_json() or {}

    titre = donnees.get("titre")
    domaine_id = donnees.get("domaine_id")
    duree_jours = donnees.get("duree_jours")

    # Contrôle des champs obligatoires
    if not titre or not domaine_id or not duree_jours:
        return jsonify({"erreur": "titre, domaine_id et duree_jours sont obligatoires"}), 400

    # Règle métier : la durée d'une session pédagogique standard est comprise entre 2 et 5 jours
    if not (2 <= duree_jours <= 5):
        return jsonify({"erreur": "duree_jours doit être entre 2 et 5"}), 400

    # Vérification de l'existence du domaine parent
    if not db.session.get(Domaine, domaine_id):
        return jsonify({"erreur": "domaine_id invalide"}), 400

    # Contrôle d'unicité sur le titre
    if Formation.query.filter_by(titre=titre).first():
        return jsonify({"erreur": "une formation avec ce titre existe déjà"}), 409

    formation = Formation(
        titre=titre,
        domaine_id=domaine_id,
        duree_jours=duree_jours,
        description=donnees.get("description"),
    )
    db.session.add(formation)
    db.session.commit()

    return jsonify(formation_vers_dict(formation)), 201


@formations_bp.route("/<int:formation_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_formation(formation_id):
    """
    Met à jour les attributs d'une formation existante.
    Réservé aux profils Gestionnaire et Administrateur.
    """
    formation = db.get_or_404(Formation, formation_id)
    donnees = request.get_json() or {}

    # Modification du titre avec vérification d'unicité
    if "titre" in donnees:
        existe = Formation.query.filter_by(titre=donnees["titre"]).first()
        if existe and existe.id != formation_id:
            return jsonify({"erreur": "une formation avec ce titre existe déjà"}), 409
        formation.titre = donnees["titre"]

    # Modification du domaine de rattachement
    if "domaine_id" in donnees:
        if not db.session.get(Domaine, donnees["domaine_id"]):
            return jsonify({"erreur": "domaine_id invalide"}), 400
        formation.domaine_id = donnees["domaine_id"]

    # Modification de la durée en jours
    if "duree_jours" in donnees:
        if not (2 <= donnees["duree_jours"] <= 5):
            return jsonify({"erreur": "duree_jours doit être entre 2 et 5"}), 400
        formation.duree_jours = donnees["duree_jours"]

    # Modification de la description pédagogique
    if "description" in donnees:
        formation.description = donnees["description"]

    db.session.commit()
    return jsonify(formation_vers_dict(formation)), 200


@formations_bp.route("/<int:formation_id>", methods=["DELETE"])
@gestionnaire_ou_admin_required
def supprimer_formation(formation_id):
    """
    Supprime une formation du catalogue si aucune session ne lui est rattachée.
    Réservé aux profils Gestionnaire et Administrateur.
    """
    formation = db.get_or_404(Formation, formation_id)

    # Blocage préventif en cas de sessions existantes (intégrité référentielle)
    session_associee = Session.query.filter_by(formation_id=formation_id).first()
    if session_associee is not None:
        nb_sessions = Session.query.filter_by(formation_id=formation_id).count()
        return jsonify({
            "erreur": f"Impossible de supprimer cette formation : {nb_sessions} session(s) y sont associée(s)."
        }), 409

    db.session.delete(formation)
    db.session.commit()
    return "", 204
