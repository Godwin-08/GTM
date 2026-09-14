"""
==============================================================================
Décorateurs de Contrôle d'Accès par Rôle (RBAC Decorators)
==============================================================================
Fournit des décorateurs Python pour sécuriser l'accès aux routes de l'API REST
et aux pages web en fonction du rôle de l'utilisateur connecté :
- @admin_required                : Réservé aux administrateurs.
- @gestionnaire_ou_admin_required : Autorisé aux admins et gestionnaires.
- @tous_roles_required           : Accessible à tous les utilisateurs authentifiés.
"""

from functools import wraps
from flask import abort
from flask_login import current_user


def role_required(*roles_autorises):
    """
    Décorateur d'autorisation paramétrable restreignant l'accès à une liste de rôles.
    
    Exemple d'utilisation :
    @role_required("admin", "gestionnaire")
    def ma_route():
        ...
    """
    def decorateur(fonction_route):
        """Décorateur intermédiaire recevant la fonction de vue Flask à envelopper."""
        @wraps(fonction_route)
        def fonction_protegee(*args, **kwargs):
            """Enveloppe exécutée avant l'appel de la route pour contrôler l'authentification et le rôle."""
            # 1. Vérification que l'utilisateur est bien authentifié
            if not current_user.is_authenticated:
                abort(401, description="Connexion requise.")

            # 2. Vérification que le rôle de l'utilisateur fait partie des rôles autorisés
            if not any(current_user.a_role(r) for r in roles_autorises):
                abort(403, description="Accès refusé : rôle insuffisant.")

            return fonction_route(*args, **kwargs)
        return fonction_protegee
    return decorateur


def admin_required(fonction_route):
    """Restreint la route aux seuls utilisateurs ayant le rôle 'admin'."""
    return role_required("admin")(fonction_route)


def gestionnaire_ou_admin_required(fonction_route):
    """Restreint la route aux utilisateurs ayant le rôle 'admin' ou 'gestionnaire'."""
    return role_required("admin", "gestionnaire")(fonction_route)


def tous_roles_required(fonction_route):
    """Autorise l'accès à tous les rôles authentifiés ('admin', 'gestionnaire', 'formateur')."""
    return role_required("admin", "gestionnaire", "formateur")(fonction_route)

