"""
Routes API pour la gestion des domaines d'expertise métier.

Ce module expose les endpoints RESTful permettant :
- La consultation de la liste des domaines de formation (Web & Data, Management Agile, Cybersécurité).
- La consultation unitaire d'un domaine.
- La création et mise à jour de domaines (accès restreint aux gestionnaires et administrateurs).
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import Domaine
from app.services.permissions import gestionnaire_ou_admin_required

# Déclaration du Blueprint Flask pour l'API des domaines
domaines_bp = Blueprint("domaines", __name__, url_prefix="/api/domaines")


def domaine_vers_dict(domaine, inclure_details=False):
    """
    Convertit une instance du modèle Domaine en dictionnaire JSON standardisé.
    - inclure_details=False : payload léger pour la liste (compteurs seuls).
    - inclure_details=True : payload complet pour le détail unitaire (formations et formateurs imbriqués).

    :param domaine: Instance SQLAlchemy de Domaine.
    :param inclure_details: Booléen indiquant si les listes détaillées doivent être jointes.
    :return: Dictionnaire JSON représentant le domaine.
    """
    data = {
        "id": domaine.id,
        "nom": domaine.nom,
        "nb_formations": len(domaine.formations) if domaine.formations else 0,
        "nb_formateurs": len(domaine.formateurs) if domaine.formateurs else 0,
    }

    if inclure_details:
        data["formations"] = [
            {
                "id": f.id,
                "titre": f.titre,
                "duree_jours": f.duree_jours,
                "description": f.description,
                "nb_sessions": len(f.sessions) if f.sessions else 0,
            }
            for f in (domaine.formations or [])
        ]
        data["formateurs"] = [
            {
                "id": formateur.id,
                "nom": formateur.nom,
                "email": formateur.email,
                "telephone": formateur.telephone,
            }
            for formateur in (domaine.formateurs or [])
        ]

    return data


@domaines_bp.route("", methods=["GET"])
@login_required
def liste_domaines():
    """
    Renvoie la liste complète des domaines (payload léger optimisé avec compteurs).
    """
    domaines = Domaine.query.order_by(Domaine.nom).all()
    return jsonify([domaine_vers_dict(d, inclure_details=False) for d in domaines]), 200


@domaines_bp.route("/<int:domaine_id>", methods=["GET"])
@login_required
def detail_domaine(domaine_id):
    """
    Renvoie le détail complet d'un domaine spécifique avec ses formations et formateurs rattachés.
    """
    domaine = db.get_or_404(Domaine, domaine_id)
    return jsonify(domaine_vers_dict(domaine, inclure_details=True)), 200


@domaines_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_domaine():
    """
    Crée un nouveau domaine de formation.
    Permet l'extensibilité du catalogue au-delà des domaines initiaux.
    Réservé aux profils Gestionnaire et Administrateur.
    """
    donnees = request.get_json() or {}
    nom = (donnees.get("nom") or "").strip()

    if not nom:
        return jsonify({"erreur": "Le nom du domaine est obligatoire."}), 400

    if Domaine.query.filter_by(nom=nom).first():
        return jsonify({"erreur": "Ce domaine existe déjà."}), 409

    domaine = Domaine(nom=nom)
    db.session.add(domaine)
    db.session.commit()
    return jsonify(domaine_vers_dict(domaine)), 201


@domaines_bp.route("/<int:domaine_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_domaine(domaine_id):
    """
    Met à jour la désignation d'un domaine existant.
    Réservé aux profils Gestionnaire et Administrateur.
    """
    domaine = db.get_or_404(Domaine, domaine_id)
    donnees = request.get_json() or {}
    nom = (donnees.get("nom") or "").strip()

    if not nom:
        return jsonify({"erreur": "Le nom du domaine est obligatoire."}), 400

    doublon = Domaine.query.filter(Domaine.nom == nom, Domaine.id != domaine_id).first()
    if doublon:
        return jsonify({"erreur": "Un autre domaine porte déjà ce nom."}), 409

    domaine.nom = nom
    db.session.commit()
    return jsonify(domaine_vers_dict(domaine)), 200


@domaines_bp.route("/<int:domaine_id>", methods=["DELETE"])
@gestionnaire_ou_admin_required
def supprimer_domaine(domaine_id):
    """
    Supprime un domaine de formation si aucune formation ni formateur n'y est rattaché.
    Réservé aux profils Gestionnaire et Administrateur.
    """
    domaine = db.get_or_404(Domaine, domaine_id)

    if (domaine.formations and len(domaine.formations) > 0) or (domaine.formateurs and len(domaine.formateurs) > 0):
        return jsonify({
            "erreur": "Impossible de supprimer ce domaine car des formations ou des formateurs y sont associés."
        }), 409

    db.session.delete(domaine)
    db.session.commit()
    return jsonify({"message": f"Le domaine '{domaine.nom}' a été supprimé avec succès."}), 200
