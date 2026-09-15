"""
Routes API pour la consultation du référentiel des rôles applicatifs (RBAC).

Ce module expose les endpoints RESTful permettant :
- La consultation de la liste des rôles système disponibles (admin, gestionnaire, formateur).
- La consultation d'un rôle précis.
"""

from flask import Blueprint, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import Role

# Déclaration du Blueprint Flask pour l'API des rôles
roles_bp = Blueprint("roles", __name__, url_prefix="/api/roles")


def role_vers_dict(role):
    """
    Convertit un objet Role en dictionnaire JSON standardisé.

    :param role: Instance SQLAlchemy de Role.
    :return: Dictionnaire contenant l'identifiant et le nom du rôle.
    """
    return {
        "id": role.id,
        "nom": role.nom,
    }


@roles_bp.route("", methods=["GET"])
@login_required
def liste_roles():
    """
    Renvoie la liste exhaustive des rôles définis dans le référentiel système.
    """
    roles = Role.query.order_by(Role.id).all()
    return jsonify([role_vers_dict(r) for r in roles]), 200


@roles_bp.route("/<int:role_id>", methods=["GET"])
@login_required
def detail_role(role_id):
    """
    Renvoie le détail d'un rôle spécifique par son identifiant unique.
    """
    role = db.get_or_404(Role, role_id)
    return jsonify(role_vers_dict(role)), 200

