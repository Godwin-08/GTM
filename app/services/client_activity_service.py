"""
Définition unique et centralisée de l'activité d'un client dans GTM.

Règles métier :
- Un client est considéré actif lorsqu'il possède au moins une inscription confirmée
  associée à une session non annulée dont la date de début se situe entre aujourd'hui et les six derniers mois.
- Un client ayant une activité passée, mais aucune activité répondant à cette règle sur les six derniers mois,
  est considéré comme inactif.
- Un client sans aucune inscription confirmée enregistrée est classé 'aucune' (Aucune activité).
"""

from calendar import monthrange
from datetime import date

from sqlalchemy import func

from app.extensions import db
from app.models import Client, Inscription, Participant, Session, Formation


def six_mois_avant(reference_date):
    mois = reference_date.month - 6
    annee = reference_date.year
    if mois <= 0:
        mois += 12
        annee -= 1
    return date(annee, mois, min(reference_date.day, monthrange(annee, mois)[1]))


def filtres_activite(reference_date=None):
    """Filtre SQL : Inscription confirmée à une session non annulée dont la date de début est entre (aujourd'hui - 6 mois) et aujourd'hui."""
    reference_date = reference_date or date.today()
    return (
        Inscription.statut == "confirmee",
        Session.statut != "annulee",
        Session.date_debut >= six_mois_avant(reference_date),
        Session.date_debut <= reference_date,
    )


from app.models import Formation

def nombre_clients_actifs(reference_date=None, annee=None, domaine_id=None, client_id=None, formateur_id=None):
    query = (
        db.session.query(func.count(func.distinct(Participant.client_id)))
        .select_from(Inscription)
        .join(Participant, Inscription.participant_id == Participant.id)
        .join(Session, Inscription.session_id == Session.id)
        .join(Formation, Session.formation_id == Formation.id)
        .filter(Participant.client_id.isnot(None), *filtres_activite(reference_date))
    )
    if annee:
        query = query.filter(func.extract("year", Session.date_debut) == annee)
    if domaine_id:
        query = query.filter(Formation.domaine_id == domaine_id)
    if client_id:
        query = query.filter(Participant.client_id == client_id)
    if formateur_id:
        query = query.filter(Session.formateur_id == formateur_id)
    return query.scalar() or 0


def derniere_session_client(client_id, reference_date=None):
    """Date de début de la dernière session passée ou en cours (non annulée) à laquelle le client a participé."""
    reference_date = reference_date or date.today()
    return (
        db.session.query(func.max(Session.date_debut))
        .select_from(Inscription)
        .join(Participant, Inscription.participant_id == Participant.id)
        .join(Session, Inscription.session_id == Session.id)
        .filter(
            Participant.client_id == client_id,
            Inscription.statut == "confirmee",
            Session.statut != "annulee",
            Session.date_debut <= reference_date,
        )
        .scalar()
    )


derniere_activite_client = derniere_session_client


def statut_activite_client(client_id, reference_date=None):
    reference_date = reference_date or date.today()
    date_derniere = derniere_session_client(client_id, reference_date)
    if date_derniere is None:
        return {
            "statut": "aucune",
            "label": "Aucune activité",
            "derniere_activite": None,
            "mois_inactivite": None,
        }

    mois_inactivite = (
        (reference_date.year - date_derniere.year) * 12
        + (reference_date.month - date_derniere.month)
    )

    if mois_inactivite < 6:
        return {
            "statut": "actif",
            "label": "Actif",
            "derniere_activite": date_derniere,
            "mois_inactivite": mois_inactivite,
        }
    else:
        return {
            "statut": "inactif",
            "label": f"Inactif · {mois_inactivite} mois",
            "derniere_activite": date_derniere,
            "mois_inactivite": mois_inactivite,
        }

