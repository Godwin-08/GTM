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


def domaine_vers_dict(domaine):
    """
    Convertit une instance du modèle Domaine en dictionnaire JSON standardisé.

    :param domaine: Instance SQLAlchemy de Domaine.
    :return: Dictionnaire contenant l'identifiant et le nom du domaine.
    """
    return {"id": domaine.id, "nom": domaine.nom}


@domaines_bp.route("", methods=["GET"])
@login_required
def liste_domaines():
    """
    Renvoie la liste complète des domaines d'expertise disponibles dans l'organisme.
    """
    domaines = Domaine.query.all()
    return jsonify([domaine_vers_dict(d) for d in domaines]), 200


@domaines_bp.route("/<int:domaine_id>", methods=["GET"])
@login_required
def detail_domaine(domaine_id):
    """
    Renvoie le détail d'un domaine spécifique par son identifiant unique.
    """
    domaine = db.get_or_404(Domaine, domaine_id)
    return jsonify(domaine_vers_dict(domaine)), 200


@domaines_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required
def creer_domaine():
    """
    Crée un nouveau domaine de formation.
    Permet l'extensibilité du catalogue au-delà des domaines initiaux.
    Réservé aux profils Gestionnaire et Administrateur.
    """
    donnees = request.get_json() or {}
    nom = donnees.get("nom")

    if not nom:
        return jsonify({"erreur": "nom est obligatoire"}), 400

    if Domaine.query.filter_by(nom=nom).first():
        return jsonify({"erreur": "ce domaine existe déjà"}), 409

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

    if "nom" in donnees:
        domaine.nom = donnees["nom"]

    db.session.commit()
    return jsonify(domaine_vers_dict(domaine)), 200
