"""
==============================================================================
Service de Contrôle d'Accès aux Données (RBAC Data Filtering)
==============================================================================
Ce module garantit l'étanchéité et la confidentialité des données entre utilisateurs :
- Administrateurs et Gestionnaires ont une visibilité globale sur l'ensemble des données.
- Les Formateurs ont un périmètre restreint strict : ils n'accèdent qu'aux sessions
  qu'ils animent personnellement, aux inscriptions et salariés associés, ainsi qu'aux
  entreprises clientes concernées.
"""

from flask import abort

from app.extensions import db
from app.models import Client, Formation, Formateur, Inscription, Participant, Session


def est_formateur(utilisateur):
    """Vérifie si l'utilisateur connecté possède le rôle 'formateur'."""
    return utilisateur.is_authenticated and utilisateur.a_role("formateur")


def _formateur_id(utilisateur):
    """Récupère l'ID du profil formateur associé au compte connecté ou déclenche une erreur 403."""
    if not utilisateur.formateur:
        abort(403, description="Aucun formateur n'est associé à ce compte.")
    return utilisateur.formateur.id


def sessions_visibles(utilisateur):
    """Retourne la requête de base pour les sessions autorisées pour cet utilisateur."""
    query = Session.query
    if est_formateur(utilisateur):
        query = query.filter(Session.formateur_id == _formateur_id(utilisateur))
    return query


def inscriptions_visibles(utilisateur):
    """Retourne la requête filtrée des inscriptions visibles (restreinte aux sessions du formateur)."""
    query = Inscription.query
    if est_formateur(utilisateur):
        sessions_autorisees = db.session.query(Session.id).filter(
            Session.formateur_id == _formateur_id(utilisateur)
        )
        query = query.filter(Inscription.session_id.in_(sessions_autorisees))
    return query


def participants_visibles(utilisateur):
    """Retourne la requête filtrée des participants (uniquement ceux inscrits aux sessions du formateur)."""
    query = Participant.query
    if est_formateur(utilisateur):
        query = (
            query.join(Inscription)
            .join(Session)
            .filter(Session.formateur_id == _formateur_id(utilisateur))
            .distinct()
        )
    return query


def clients_visibles(utilisateur):
    """Retourne la requête filtrée des clients (uniquement les entreprises ayant des stagiaires dans les sessions du formateur)."""
    query = Client.query
    if est_formateur(utilisateur):
        query = (
            query.join(Participant)
            .join(Inscription)
            .join(Session)
            .filter(Session.formateur_id == _formateur_id(utilisateur))
            .distinct()
        )
    return query


def formations_visibles(utilisateur):
    """Retourne les formations dispensées par le formateur ou l'ensemble du catalogue pour les gestionnaires."""
    query = Formation.query
    if est_formateur(utilisateur):
        query = (
            query.join(Session)
            .filter(Session.formateur_id == _formateur_id(utilisateur))
            .distinct()
        )
    return query


def formateurs_visibles(utilisateur):
    """Retourne le profil du formateur connecté ou l'annuaire complet pour les gestionnaires."""
    query = Formateur.query
    if est_formateur(utilisateur):
        query = query.filter(Formateur.id == _formateur_id(utilisateur))
    return query


def exiger_acces(query, identifiant, utilisateur, message="Accès interdit."):
    """
    Récupère une ressource spécifique en validant les habilitations de l'utilisateur.
    Renvoie 403 Forbidden sans divulguer l'existence de la donnée si l'accès est refusé,
    ou 404 Not Found si l'entité n'existe pas en base.
    """
    entite = query.column_descriptions[0]["type"]
    objet = query.filter(entite.id == identifiant).first()
    if objet is None:
        if est_formateur(utilisateur):
            abort(403, description=message)
        abort(404)
    return objet


