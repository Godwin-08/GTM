"""
Service centralisant le calcul des "Points d'attention" de GTM.
Toute la logique métier (seuils, règles) vit ici, dans le backend.
Le frontend (dashboard, cloche) ne fait qu'afficher ce que ce service renvoie.
"""

from datetime import date, timedelta
from app.models import Session
from app.services.stats_service import activite_par_client, evolution_inscriptions


def get_points_attention():
    """
    Calcule l'ensemble des points d'attention actuels de GTM.
    Retourne un dict {"total": int, "items": [...]}.
    Chaque item a la forme : {type, niveau, titre, message, url}.
    """
    items = []

    items += _sessions_a_risque()
    items += _clients_inactifs()
    items += _tendance_globale()

    return {
        "total": len(items),
        "items": items,
    }


def _sessions_a_risque():
    """
    Règle : une session est à risque si elle démarre dans les 7 prochains jours
    ET que son taux de remplissage est inférieur à 40%.
    On exclut les sessions complètes ou annulées.
    """
    aujourdhui = date.today()
    dans_sept_jours = aujourdhui + timedelta(days=7)

    sessions = Session.query.filter(
        Session.date_debut >= aujourdhui,
        Session.date_debut <= dans_sept_jours,
        Session.statut != 'annulee',
    ).order_by(Session.date_debut.asc()).all()

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


def _clients_inactifs():
    """
    Règle : un client est inactif si sa dernière inscription confirmée
    date de 6 mois ou plus. Les clients sans historique (mois_inactivite=None)
    ne sont volontairement pas inclus, pour éviter les faux positifs
    sur des clients récemment créés.
    """
    clients = activite_par_client()

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


def _tendance_globale():
    """
    Règle : compare la somme des inscriptions des 3 derniers mois disponibles
    à celle des 3 mois précédents. N'affiche rien si la variation est
    dans la fourchette de ±5% (considérée comme du bruit statistique),
    ou s'il n'y a pas assez d'historique (moins de 6 mois de données).
    """
    evolution = evolution_inscriptions()

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
        return []  # tendance stable, pas de point d'attention

    direction = "progressent" if variation > 0 else "reculent"

    return [{
        "type": "tendance_globale",
        "niveau": "info",  # niveau neutre, ni danger ni warning
        "titre": "Tendance",
        "message": f"Les inscriptions {direction} de {abs(variation)}% sur les 3 derniers mois.",
        "url": "/dashboard",
    }]

