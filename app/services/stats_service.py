from sqlalchemy import func, extract

from app.extensions import db
from app.models import Session, Inscription, Formation, Domaine, Client, Participant, Formateur


def taux_remplissage_global():
    """
    Calcule le taux de remplissage moyen sur toutes les sessions,
    et identifie les sessions les plus et les moins remplies.
    Ne prend en compte QUE les sessions non annulées : une session
    annulée n'a pas vraiment de "remplissage" au sens utile du terme.
    """
    sessions = Session.query.filter(Session.statut != "annulee").all()

    if not sessions:
        return {
            "taux_moyen": 0,
            "nb_sessions": 0,
            "sessions_les_plus_remplies": [],
            "sessions_les_moins_remplies": [],
        }

    taux_par_session = [
        {
            "session_id": s.id,
            "formation": s.formation.titre,
            "date_debut": s.date_debut.isoformat(),
            "taux_remplissage": s.taux_remplissage(),
        }
        for s in sessions
    ]

    taux_moyen = round(
        sum(t["taux_remplissage"] for t in taux_par_session) / len(taux_par_session),
        2,
    )

    trie = sorted(taux_par_session, key=lambda t: t["taux_remplissage"], reverse=True)

    return {
        "taux_moyen": taux_moyen,
        "nb_sessions": len(sessions),
        "sessions_les_plus_remplies": trie[:5],
        "sessions_les_moins_remplies": trie[-5:],
    }


def activite_par_domaine():
    """
    Pour chaque domaine : nombre de sessions organisées et nombre total
    d'inscriptions confirmées. Se base sur Formation -> Domaine (pas sur
    Formateur -> Domaine), car ce qui compte pour "l'activité" c'est
    ce qui a été enseigné, pas la compétence du formateur assigné.
    """
    resultats = []
    for domaine in Domaine.query.all():
        sessions_du_domaine = (
            Session.query.join(Formation).filter(Formation.domaine_id == domaine.id).all()
        )
        nb_sessions = len(sessions_du_domaine)
        nb_inscriptions_confirmees = sum(
            s.nb_inscrits_confirmes() for s in sessions_du_domaine
        )

        resultats.append(
            {
                "domaine": domaine.nom,
                "nb_sessions": nb_sessions,
                "nb_inscriptions_confirmees": nb_inscriptions_confirmees,
            }
        )

    return sorted(
        resultats,
        key=lambda r: r["nb_inscriptions_confirmees"],
        reverse=True,
    )


def activite_par_client():
    """
    Pour chaque client : nombre de participants distincts qui ont
    suivi au moins une session, nombre total d'inscriptions confirmées,
    date de la dernière inscription et nombre de mois d'inactivité.
    """
    from datetime import date

    aujourd_hui = date.today()
    resultats = []

    for client in Client.query.all():
        inscriptions_confirmees = (
            Inscription.query
            .join(Participant)
            .filter(Participant.client_id == client.id, Inscription.statut == "confirmee")
            .all()
        )

        participants_actifs = {i.participant_id for i in inscriptions_confirmees}

        date_derniere = None
        mois_inactivite = None

        if inscriptions_confirmees:
            dates = [i.date_inscription for i in inscriptions_confirmees if i.date_inscription]
            if dates:
                date_derniere = max(dates)
                mois_inactivite = (aujourd_hui.year - date_derniere.year) * 12 + (aujourd_hui.month - date_derniere.month)

        resultats.append(
            {
                "client": client.nom_entreprise,
                "nb_participants_actifs": len(participants_actifs),
                "nb_inscriptions_confirmees": len(inscriptions_confirmees),
                "date_derniere_inscription": date_derniere.isoformat() if date_derniere else None,
                "mois_inactivite": mois_inactivite,
            }
        )

    return sorted(
        resultats,
        key=lambda r: r["nb_inscriptions_confirmees"],
        reverse=True,
    )



def activite_par_formateur():
    """
    Pour chaque formateur : nombre de sessions animées et taux de
    remplissage moyen de ses sessions. Utile pour identifier qui anime
    le plus, mais aussi qui a tendance à remplir ses sessions ou non.
    """
    resultats = []
    for formateur in Formateur.query.all():
        sessions_non_annulees = [s for s in formateur.sessions if s.statut != "annulee"]
        nb_sessions = len(sessions_non_annulees)

        if nb_sessions > 0:
            taux_moyen = round(
                sum(s.taux_remplissage() for s in sessions_non_annulees) / nb_sessions,
                2,
            )
        else:
            taux_moyen = None

        resultats.append(
            {
                "formateur": formateur.nom,
                "domaine": formateur.domaine.nom,
                "nb_sessions": nb_sessions,
                "taux_remplissage_moyen": taux_moyen,
            }
        )

    return sorted(resultats, key=lambda r: r["nb_sessions"], reverse=True)


def evolution_inscriptions(annee=None):
    """
    Nombre d'inscriptions confirmées par mois, pour repérer une tendance
    dans le temps. Filtrable par année ; sans filtre, prend toutes les
    inscriptions confirmées de la base, quelle que soit l'année.
    """
    query = db.session.query(
        extract("year", Inscription.date_inscription).label("annee"),
        extract("month", Inscription.date_inscription).label("mois"),
        func.count(Inscription.id).label("nb_inscriptions"),
    ).filter(Inscription.statut == "confirmee")

    if annee:
        query = query.filter(extract("year", Inscription.date_inscription) == annee)

    resultats = query.group_by("annee", "mois").order_by("annee", "mois").all()

    return [
        {"annee": int(r.annee), "mois": int(r.mois), "nb_inscriptions": r.nb_inscriptions}
        for r in resultats
    ]
