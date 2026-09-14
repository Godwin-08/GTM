"""
==============================================================================
Service de Détection des Points d'Attention & Alertes de Gestion
==============================================================================
Ce module centralise la logique algorithmique de surveillance proactive de GTM :
1. Sessions à risque : Sessions débutant dans les 7 prochains jours avec un taux
   de remplissage strictement inférieur à 40% (hors sessions complètes ou annulées).
2. Clients inactifs : Entreprises clientes dont la dernière participation remonte
   à 6 mois ou plus.
3. Tendances d'inscriptions : Évolution comparative entre les 3 derniers mois
   et les 3 mois précédents (hausse/baisse significative > 5%).
"""

from datetime import date, timedelta
from sqlalchemy import extract
from app.models import Session, Formation, Inscription, Participant
from app.services.stats_service import activite_par_client, evolution_inscriptions


def get_points_attention(annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """
    Calcule et agrège l'ensemble des points d'attention sous le contexte de filtres actif.
    
    :return: Dictionnaire avec le nombre total et la liste des alertes
    """
    items = []

    # 1. Détection des sessions critiques à court terme
    items += _sessions_a_risque(annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id)
    # 2. Détection des comptes clients en sommeil
    items += _clients_inactifs(annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id)
    # 3. Évaluation de la tendance globale d'activité
    items += _tendance_globale(annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id)

    return {
        "total": len(items),
        "items": items,
    }


def _sessions_a_risque(annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """
    Règle : Une session est à risque (danger) si date_debut ∈ [aujourd'hui, aujourd'hui + 7 jours]
    ET taux_remplissage < 0.40.
    """
    aujourdhui = date.today()
    dans_sept_jours = aujourdhui + timedelta(days=7)

    query = Session.query.join(Formation, Session.formation_id == Formation.id).filter(
        Session.date_debut >= aujourdhui,
        Session.date_debut <= dans_sept_jours,
        Session.statut != 'annulee',
    )

    if annee:
        query = query.filter(extract("year", Session.date_debut) == annee)
    if domaine_id:
        query = query.filter(Formation.domaine_id == domaine_id)
    if formateur_id:
        query = query.filter(Session.formateur_id == formateur_id)
    if client_id:
        query = query.join(Session.inscriptions).join(Inscription.participant).filter(Participant.client_id == client_id)

    sessions = query.distinct().order_by(Session.date_debut.asc()).all()

    items = []
    for s in sessions:
        taux = s.taux_remplissage()
        if taux < 0.4 and not s.est_complete():
            diff_jours = (s.date_debut - aujourdhui).days
            delai = "Aujourd'hui" if diff_jours == 0 else "Demain" if diff_jours == 1 else f"Dans {diff_jours} jours"

            items.append({
                "type": "session_risque",
                "niveau": "danger",
                "titre": "Session à risque",
                "message": f"{s.formation.titre} · {round(taux * 100)}% rempli · {delai}",
                "url": "/sessions",
            })

    return items


def _clients_inactifs(annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """
    Règle : Un client est qualifié d'inactif (warning) si son délai de carence
    dépasse le seuil des 6 mois.
    """
    clients = activite_par_client(annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id)

    items = []
    inactifs = [c for c in clients if c["mois_inactivite"] is not None and c["mois_inactivite"] >= 6]
    inactifs.sort(key=lambda c: c["mois_inactivite"], reverse=True)

    for c in inactifs:
        items.append({
            "type": "client_inactif",
            "niveau": "warning",
            "titre": "Client inactif",
            "message": f"{c['client']} · Inactif depuis {c['mois_inactivite']} mois",
            "url": "/clients",
        })

    return items


def _tendance_globale(annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """
    Règle : Compare la somme des inscriptions des 3 derniers mois disponibles à celle
    des 3 mois antérieurs pour dégager la dynamique commerciale (info).
    """
    evolution = evolution_inscriptions(annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id)

    if len(evolution) < 6:
        return []

    trois_derniers = evolution[-3:]
    trois_precedents = evolution[-6:-3]

    somme_derniers = sum(m["nb_inscriptions"] for m in trois_derniers)
    somme_precedents = sum(m["nb_inscriptions"] for m in trois_precedents)

    if somme_precedents == 0:
        return []

    variation = round(((somme_derniers - somme_precedents) / somme_precedents) * 100)

    if abs(variation) <= 5:
        return []

    direction = "progressent" if variation > 0 else "reculent"

    return [{
        "type": "tendance_globale",
        "niveau": "info",
        "titre": "Tendance",
        "message": f"Les inscriptions {direction} de {abs(variation)}% sur les 3 derniers mois.",
        "url": "/dashboard",
    }]


