"""
==============================================================================
Service d'Évaluation de l'Activité Client (Règle Métier des 6 Mois)
==============================================================================
Définit la règle métier unique et centralisée pour classifier l'état d'un Client :
- 'actif'   : Possède au moins une inscription confirmée à une session non annulée
              dont la date de début se situe dans les 6 derniers mois (aujourd'hui - 6 mois).
- 'inactif' : A déjà suivi des formations par le passé, mais aucune dans les 6 derniers mois.
- 'aucune'  : Nouveau client n'ayant jamais participé à la moindre formation.
"""

from calendar import monthrange
from datetime import date
from sqlalchemy import func

from app.extensions import db
from app.models import Client, Inscription, Participant, Session, Formation


def six_mois_avant(reference_date):
    """
    Calcule la date exacte située 6 mois avant la date de référence en gérant
    les passages d'années et les fins de mois (ex: 31 mars -> 30 septembre).
    """
    mois = reference_date.month - 6
    annee = reference_date.year
    if mois <= 0:
        mois += 12
        annee -= 1
    return date(annee, mois, min(reference_date.day, monthrange(annee, mois)[1]))


def filtres_activite(reference_date=None):
    """
    Construit les clauses de filtrage SQLAlchemy traduisant la règle des 6 mois :
    - Inscription confirmée
    - Session non annulée
    - Date de début comprise entre [reference_date - 6 mois] et reference_date
    """
    reference_date = reference_date or date.today()
    return (
        Inscription.statut == "confirmee",
        Session.statut != "annulee",
        Session.date_debut >= six_mois_avant(reference_date),
        Session.date_debut <= reference_date,
    )


def nombre_clients_actifs(reference_date=None, annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """
    Compte le nombre d'entreprises clientes actives selon les filtres appliqués.
    """
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
    """
    Identifie la date de début de la session la plus récente à laquelle les salariés
    du client ont participé (inscriptions confirmées uniquement).
    """
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


# Alias pour la lisibilité
derniere_activite_client = derniere_session_client


def statut_activite_client(client_id, reference_date=None):
    """
    Détermine l'état d'activité détaillé d'un client et calcule le nombre de mois d'inactivité.
    
    :return: Dictionnaire avec les clés :
             - statut : 'actif', 'inactif', 'aucune'
             - label : Libellé affichable dans l'interface
             - derniere_activite : date ou None
             - mois_inactivite : int ou None
    """
    reference_date = reference_date or date.today()
    date_derniere = derniere_session_client(client_id, reference_date)
    if date_derniere is None:
        return {
            "statut": "aucune",
            "label": "Aucune activité",
            "derniere_activite": None,
            "mois_inactivite": None,
        }

    # Calcul de l'écart en mois
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


