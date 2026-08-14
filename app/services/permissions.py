from functools import wraps
from flask import abort
from flask_login import current_user

def role_required(*roles_autorises):
    """
    Décorateur qui restreint une route à un ou plusieurs rôles précis.
    Usage : @role_required("admin") ou @role_required("admin", "gestionnaire")

    *roles_autorises capture un nombre variable d'arguments (ici des
    chaînes de rôles), ce qui permet d'autoriser plusieurs rôles à la fois
    sans avoir à écrire un décorateur différent pour chaque combinaison.
    """
    def decorateur(fonction_route):
        @wraps(fonction_route)
        def fonction_protegee(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401, description="Connexion requise.")

            if not any(current_user.a_role(r) for r in roles_autorises):
                abort(403, description="Accès refusé : rôle insuffisant.")

            return fonction_route(*args, **kwargs)
        return fonction_protegee
    return decorateur

def admin_required(fonction_route):
    return role_required("admin")(fonction_route)

def gestionnaire_ou_admin_required(fonction_route):
    return role_required("admin", "gestionnaire")(fonction_route)
