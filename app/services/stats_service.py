from datetime import date

from sqlalchemy import func, extract

from app.extensions import db
from app.models import Session, Inscription, Formation, Domaine, Client, Participant, Formateur
from app.services.client_activity_service import (
    derniere_activite_client,
    nombre_clients_actifs,
)


def kpi_globaux(reference_date=None, annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """Retourne les six indicateurs globaux du tableau de bord avec filtres optionnels."""
    reference_date = reference_date or date.today()

    query_sessions = Session.query.join(Formation, Session.formation_id == Formation.id).filter(Session.statut != "annulee")
    if annee:
        query_sessions = query_sessions.filter(extract("year", Session.date_debut) == annee)
    if domaine_id:
        query_sessions = query_sessions.filter(Formation.domaine_id == domaine_id)
    if formateur_id:
        query_sessions = query_sessions.filter(Session.formateur_id == formateur_id)
    if client_id:
        query_sessions = query_sessions.join(Session.inscriptions).join(Inscription.participant).filter(Participant.client_id == client_id)

    sessions_actives_count = query_sessions.distinct().count()
    clients_actifs = nombre_clients_actifs(reference_date, annee=annee, domaine_id=domaine_id, client_id=client_id, formateur_id=formateur_id)

    query_participants = (
        db.session.query(func.count(func.distinct(Inscription.participant_id)))
        .select_from(Inscription)
        .join(Session, Inscription.session_id == Session.id)
        .join(Formation, Session.formation_id == Formation.id)
        .join(Participant, Inscription.participant_id == Participant.id)
        .filter(
            Inscription.statut == "confirmee",
            Inscription.participant_id.isnot(None),
            Session.statut != "annulee",
        )
    )
    if annee:
        query_participants = query_participants.filter(extract("year", Session.date_debut) == annee)
    if domaine_id:
        query_participants = query_participants.filter(Formation.domaine_id == domaine_id)
    if formateur_id:
        query_participants = query_participants.filter(Session.formateur_id == formateur_id)
    if client_id:
        query_participants = query_participants.filter(Participant.client_id == client_id)

    participants_distincts = query_participants.scalar() or 0

    query_taux = (
        db.session.query(
            Session.id,
            Session.capacite_max,
            func.count(Inscription.id).label("nb_inscrits"),
        )
        .join(Formation, Session.formation_id == Formation.id)
        .outerjoin(
            Inscription,
            (Inscription.session_id == Session.id)
            & (Inscription.statut == "confirmee"),
        )
        .filter(Session.statut != "annulee", Session.capacite_max > 0)
    )
    if annee:
        query_taux = query_taux.filter(extract("year", Session.date_debut) == annee)
    if domaine_id:
        query_taux = query_taux.filter(Formation.domaine_id == domaine_id)
    if formateur_id:
        query_taux = query_taux.filter(Session.formateur_id == formateur_id)
    if client_id:
        query_taux = query_taux.join(Inscription.participant).filter(Participant.client_id == client_id)

    taux_par_session = query_taux.group_by(Session.id, Session.capacite_max).all()
    taux_moyen_remplissage = (
        round(
            sum(session.nb_inscrits / session.capacite_max for session in taux_par_session)
            / len(taux_par_session)
            * 100,
            1,
        )
        if taux_par_session
        else 0
    )

    query_formateurs = query_sessions.filter(Session.formateur_id.isnot(None))
    formateurs_mobilises = (
        query_formateurs.with_entities(func.count(func.distinct(Session.formateur_id)))
        .scalar()
        or 0
    )

    if client_id or formateur_id or annee:
        formations_catalogue = query_sessions.with_entities(func.count(func.distinct(Session.formation_id))).scalar() or 0
    elif domaine_id:
        formations_catalogue = Formation.query.filter(Formation.domaine_id == domaine_id).count()
    else:
        formations_catalogue = Formation.query.count()

    return {
        "sessions_actives": sessions_actives_count,
        "clients_actifs": clients_actifs,
        "participants_distincts": participants_distincts,
        "formations_catalogue": formations_catalogue,
        "taux_moyen_remplissage": taux_moyen_remplissage,
        "formateurs_mobilises": formateurs_mobilises,
    }


def taux_remplissage_global(annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """
    Calcule le taux de remplissage moyen sur toutes les sessions avec filtres.
    """
    query = Session.query.join(Formation, Session.formation_id == Formation.id).filter(Session.statut != "annulee")
    if annee:
        query = query.filter(extract("year", Session.date_debut) == annee)
    if domaine_id:
        query = query.filter(Formation.domaine_id == domaine_id)
    if formateur_id:
        query = query.filter(Session.formateur_id == formateur_id)
    if client_id:
        query = query.join(Session.inscriptions).join(Inscription.participant).filter(Participant.client_id == client_id)

    sessions = query.distinct().all()
    sessions_avec_capacite_valide = [s for s in sessions if s.capacite_max > 0]

    if not sessions_avec_capacite_valide:
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
        for s in sessions_avec_capacite_valide
    ]

    taux_moyen = (
        round(
            sum(t["taux_remplissage"] for t in taux_par_session) / len(taux_par_session),
            2,
        )
        if taux_par_session
        else 0
    )

    trie = sorted(taux_par_session, key=lambda t: t["taux_remplissage"], reverse=True)

    return {
        "taux_moyen": taux_moyen,
        "nb_sessions": len(sessions_avec_capacite_valide),
        "sessions_les_plus_remplies": trie[:5],
        "sessions_les_moins_remplies": trie[-5:],
    }


def activite_par_domaine(annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """
    Pour chaque domaine : nombre de sessions organisées et nombre total d'inscriptions confirmées.
    Applique le contexte de filtrage.
    """
    domaines = Domaine.query.all()
    if domaine_id:
        domaines = [d for d in domaines if d.id == domaine_id]

    resultats = []
    for d in domaines:
        q_sessions = Session.query.join(Formation).filter(Formation.domaine_id == d.id, Session.statut != "annulee")
        if annee:
            q_sessions = q_sessions.filter(extract("year", Session.date_debut) == annee)
        if formateur_id:
            q_sessions = q_sessions.filter(Session.formateur_id == formateur_id)
        if client_id:
            q_sessions = q_sessions.join(Session.inscriptions).join(Inscription.participant).filter(Participant.client_id == client_id)

        sessions_du_domaine = q_sessions.distinct().all()
        nb_sessions = len(sessions_du_domaine)

        # Inscriptions confirmées dans ces sessions
        q_inscriptions = Inscription.query.join(Session).join(Formation).filter(
            Formation.domaine_id == d.id,
            Inscription.statut == "confirmee",
            Session.statut != "annulee"
        )
        if annee:
            q_inscriptions = q_inscriptions.filter(extract("year", Session.date_debut) == annee)
        if formateur_id:
            q_inscriptions = q_inscriptions.filter(Session.formateur_id == formateur_id)
        if client_id:
            q_inscriptions = q_inscriptions.join(Inscription.participant).filter(Participant.client_id == client_id)

        nb_inscriptions_confirmees = q_inscriptions.count()

        if nb_sessions > 0 or nb_inscriptions_confirmees > 0 or not (annee or domaine_id or client_id or formateur_id):
            resultats.append(
                {
                    "domaine": d.nom,
                    "nb_sessions": nb_sessions,
                    "nb_inscriptions_confirmees": nb_inscriptions_confirmees,
                }
            )

    return sorted(
        resultats,
        key=lambda r: r["nb_inscriptions_confirmees"],
        reverse=True,
    )


def activite_par_client(annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """
    Pour chaque client : métriques d'inscriptions et d'inactivité sous filtres.
    """
    aujourd_hui = date.today()
    clients = Client.query.all()
    if client_id:
        clients = [c for c in clients if c.id == client_id]

    resultats = []
    for client in clients:
        q_inscriptions = (
            Inscription.query
            .join(Participant)
            .join(Session)
            .join(Formation)
            .filter(
                Participant.client_id == client.id,
                Inscription.statut == "confirmee",
                Session.statut != "annulee"
            )
        )
        if annee:
            q_inscriptions = q_inscriptions.filter(extract("year", Session.date_debut) == annee)
        if domaine_id:
            q_inscriptions = q_inscriptions.filter(Formation.domaine_id == domaine_id)
        if formateur_id:
            q_inscriptions = q_inscriptions.filter(Session.formateur_id == formateur_id)

        inscriptions_confirmees = q_inscriptions.all()
        participants_actifs = {i.participant_id for i in inscriptions_confirmees}

        date_derniere = derniere_activite_client(client.id, aujourd_hui)
        mois_inactivite = None
        if date_derniere:
            mois_inactivite = (
                (aujourd_hui.year - date_derniere.year) * 12
                + (aujourd_hui.month - date_derniere.month)
            )

        if len(inscriptions_confirmees) > 0 or not (annee or domaine_id or client_id or formateur_id):
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


def activite_par_formateur(annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """
    Pour chaque formateur : nombre de sessions animées et remplissage sous filtres.
    """
    formateurs = Formateur.query.all()
    if formateur_id:
        formateurs = [f for f in formateurs if f.id == formateur_id]

    resultats = []
    for formateur in formateurs:
        q_sessions = Session.query.join(Formation).filter(Session.formateur_id == formateur.id, Session.statut != "annulee")
        if annee:
            q_sessions = q_sessions.filter(extract("year", Session.date_debut) == annee)
        if domaine_id:
            q_sessions = q_sessions.filter(Formation.domaine_id == domaine_id)
        if client_id:
            q_sessions = q_sessions.join(Session.inscriptions).join(Inscription.participant).filter(Participant.client_id == client_id)

        sessions = q_sessions.distinct().all()
        nb_sessions = len(sessions)

        if nb_sessions > 0:
            taux_moyen = round(
                sum(s.taux_remplissage() for s in sessions) / nb_sessions,
                2,
            )
        else:
            taux_moyen = None

        if nb_sessions > 0 or not (annee or domaine_id or client_id or formateur_id):
            resultats.append(
                {
                    "formateur": formateur.nom,
                    "domaine": formateur.domaine.nom if formateur.domaine else "—",
                    "nb_sessions": nb_sessions,
                    "taux_remplissage_moyen": taux_moyen,
                }
            )

    return sorted(resultats, key=lambda r: r["nb_sessions"], reverse=True)


def evolution_inscriptions(annee=None, domaine_id=None, client_id=None, formateur_id=None):
    """
    Nombre d'inscriptions confirmées par mois avec filtres.
    Si annee est fourni, retourne impérativement les 12 mois (avec 0 si absent).
    """
    query = (
        db.session.query(
            extract("year", Session.date_debut).label("annee"),
            extract("month", Session.date_debut).label("mois"),
            func.count(Inscription.id).label("nb_inscriptions"),
        )
        .join(Session, Inscription.session_id == Session.id)
        .join(Formation, Session.formation_id == Formation.id)
        .filter(Inscription.statut == "confirmee", Session.statut != "annulee")
    )

    if annee:
        query = query.filter(extract("year", Session.date_debut) == annee)
    if domaine_id:
        query = query.filter(Formation.domaine_id == domaine_id)
    if formateur_id:
        query = query.filter(Session.formateur_id == formateur_id)
    if client_id:
        query = query.join(Participant, Inscription.participant_id == Participant.id).filter(Participant.client_id == client_id)

    resultats = query.group_by("annee", "mois").order_by("annee", "mois").all()
    dict_res = {(int(r.annee), int(r.mois)): r.nb_inscriptions for r in resultats}

    if annee:
        final_list = []
        for m in range(1, 13):
            val = dict_res.get((annee, m), 0)
            final_list.append({"annee": annee, "mois": m, "nb_inscriptions": val})
        return final_list

    return [
        {"annee": int(r.annee), "mois": int(r.mois), "nb_inscriptions": r.nb_inscriptions}
        for r in resultats
    ]
