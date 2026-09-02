"""Règles de visibilité des données selon le rôle connecté."""

from flask import abort

from app.extensions import db
from app.models import Client, Formation, Formateur, Inscription, Participant, Session


def est_formateur(utilisateur):
    return utilisateur.is_authenticated and utilisateur.a_role("formateur")


def _formateur_id(utilisateur):
    if not utilisateur.formateur:
        abort(403, description="Aucun formateur n'est associé à ce compte.")
    return utilisateur.formateur.id


def sessions_visibles(utilisateur):
    query = Session.query
    if est_formateur(utilisateur):
        query = query.filter(Session.formateur_id == _formateur_id(utilisateur))
    return query


def inscriptions_visibles(utilisateur):
    query = Inscription.query
    if est_formateur(utilisateur):
        sessions_autorisees = db.session.query(Session.id).filter(
            Session.formateur_id == _formateur_id(utilisateur)
        )
        query = query.filter(Inscription.session_id.in_(sessions_autorisees))
    return query


def participants_visibles(utilisateur):
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
    query = Formation.query
    if est_formateur(utilisateur):
        query = (
            query.join(Session)
            .filter(Session.formateur_id == _formateur_id(utilisateur))
            .distinct()
        )
    return query


def formateurs_visibles(utilisateur):
    query = Formateur.query
    if est_formateur(utilisateur):
        query = query.filter(Formateur.id == _formateur_id(utilisateur))
    return query


def exiger_acces(query, identifiant, utilisateur, message="Accès interdit."):
    """Retourne la ressource visible ou renvoie 403 sans révéler d'autres données."""
    entite = query.column_descriptions[0]["type"]
    objet = query.filter(entite.id == identifiant).first()
    if objet is None:
        if est_formateur(utilisateur):
            abort(403, description=message)
        abort(404)
    return objet

