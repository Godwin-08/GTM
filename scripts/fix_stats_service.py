"""Script pour réécrire proprement la fonction kpi_formateur dans stats_service.py"""

new_func = """

def kpi_formateur(formateur_id):
    \"\"\"
    Retourne les indicateurs personnels d'un formateur :
    - Nombre total de sessions animées (non annulées)
    - Nombre de sessions à venir
    - Nombre de sessions terminées
    - Taux de remplissage moyen de ses sessions
    - Nombre total de participants distincts formés
    - Répartition de ses sessions par domaine
    - Ses prochaines sessions planifiées
    \"\"\"
    from datetime import date as date_cls

    aujourd_hui = date_cls.today()

    sessions = (
        Session.query
        .join(Formation, Session.formation_id == Formation.id)
        .filter(Session.formateur_id == formateur_id, Session.statut != "annulee")
        .all()
    )

    sessions_a_venir = [s for s in sessions if s.date_debut >= aujourd_hui]
    sessions_terminees = [s for s in sessions if s.date_debut < aujourd_hui]

    taux_moyen = (
        round(
            sum(s.taux_remplissage() for s in sessions) / len(sessions) * 100, 1
        )
        if sessions else 0
    )

    participants_distincts = (
        db.session.query(func.count(func.distinct(Inscription.participant_id)))
        .join(Session, Inscription.session_id == Session.id)
        .filter(
            Session.formateur_id == formateur_id,
            Session.statut != "annulee",
            Inscription.statut == "confirmee",
        )
        .scalar() or 0
    )

    # Répartition par domaine
    domaines_count = {}
    for s in sessions:
        nom_domaine = s.formation.domaine.nom if s.formation.domaine else "Autre"
        domaines_count[nom_domaine] = domaines_count.get(nom_domaine, 0) + 1
    repartition_domaines = [
        {"domaine": k, "nb_sessions": v}
        for k, v in sorted(domaines_count.items(), key=lambda x: x[1], reverse=True)
    ]

    # Prochaines sessions (5 max)
    prochaines = sorted(sessions_a_venir, key=lambda s: s.date_debut)[:5]
    prochaines_data = [
        {
            "id": s.id,
            "formation": s.formation.titre,
            "date_debut": s.date_debut.isoformat(),
            "lieu": s.lieu or "—",
            "nb_inscrits_confirmes": sum(1 for i in s.inscriptions if i.statut == "confirmee"),
            "capacite_max": s.capacite_max,
            "taux_remplissage": round(s.taux_remplissage(), 2),
            "est_complete": s.est_complete(),
        }
        for s in prochaines
    ]

    return {
        "nb_sessions_total": len(sessions),
        "nb_sessions_a_venir": len(sessions_a_venir),
        "nb_sessions_terminees": len(sessions_terminees),
        "taux_moyen_remplissage": taux_moyen,
        "participants_distincts": participants_distincts,
        "repartition_domaines": repartition_domaines,
        "prochaines_sessions": prochaines_data,
    }
"""

with open('app/services/stats_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Trouver la ligne start_marker et tronquer à partir de là
start_marker = '\ndef kpi_formateur(formateur_id):'
idx = content.find(start_marker)
if idx == -1:
    # Pas encore présente, juste ajouter à la fin
    content = content.rstrip() + '\n' + new_func
    print("Ajout en fin de fichier")
else:
    content = content[:idx] + new_func
    print(f"Remplacement à l'index {idx}")

with open('app/services/stats_service.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)

print("OK - stats_service.py mis à jour proprement")

