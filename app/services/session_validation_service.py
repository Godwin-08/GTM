"""
==============================================================================
Service de Validation des Sessions (Cohérence des Dates et Statuts)
==============================================================================
Ce module garantit la cohérence chronologique et temporelle des sessions de formation :
- date_fin >= date_debut
- Statuts autorisés : 'planifiee', 'en_cours', 'terminee', 'annulee'
- Cohérence temporelle avec la date du jour :
  * 'planifiee' : doit débuter strictement après aujourd'hui
  * 'en_cours'  : doit englober aujourd'hui (date_debut <= aujourd'hui <= date_fin)
  * 'terminee'  : doit avoir pris fin avant aujourd'hui (date_fin < aujourd'hui)
"""

from datetime import date

STATUTS_VALIDES = {"planifiee", "en_cours", "terminee", "annulee"}


class ErreurValidationSession(ValueError):
    """Exception levée en cas de violation des règles chronologiques d'une session."""
    pass


def convertir_date(valeur, nom_champ):
    """
    Convertit une chaîne en objet date Python (format AAAA-MM-JJ).
    
    :raises ErreurValidationSession: Si le format ou le type est invalide
    """
    if not isinstance(valeur, str):
        raise ErreurValidationSession(f"{nom_champ} doit être une date au format AAAA-MM-JJ")
    try:
        return date.fromisoformat(valeur)
    except ValueError as erreur:
        raise ErreurValidationSession(
            f"{nom_champ} doit être une date valide au format AAAA-MM-JJ"
        ) from erreur


def valider_dates_et_statut(date_debut, date_fin, statut, reference_date=None):
    """
    Vérifie la conformité logique entre les dates de début/fin et le statut de la session.
    """
    if date_fin < date_debut:
        raise ErreurValidationSession("date_fin doit être postérieure ou égale à date_debut")
    if statut not in STATUTS_VALIDES:
        raise ErreurValidationSession(f"statut doit être parmi {sorted(STATUTS_VALIDES)}")

    reference_date = reference_date or date.today()
    if statut == "planifiee" and date_debut <= reference_date:
        raise ErreurValidationSession("une session planifiée doit commencer après aujourd'hui")
    if statut == "en_cours" and not date_debut <= reference_date <= date_fin:
        raise ErreurValidationSession("une session en cours doit inclure la date d'aujourd'hui")
    if statut == "terminee" and date_fin >= reference_date:
        raise ErreurValidationSession("une session terminée doit être finie avant aujourd'hui")


def valeurs_session_validees(donnees, session=None):
    """
    Parse et valide les données de session soumises en création (session=None)
    ou en mise à jour partielle (session existante fournie).
    
    :return: Tuple (date_debut, date_fin, statut)
    """
    if session is None:
        champs_manquants = [cle for cle in ("date_debut", "date_fin") if not donnees.get(cle)]
        if champs_manquants:
            raise ErreurValidationSession(
                ", ".join(champs_manquants) + " est/sont obligatoire(s)"
            )
        date_debut = convertir_date(donnees["date_debut"], "date_debut")
        date_fin = convertir_date(donnees["date_fin"], "date_fin")
        statut = donnees.get("statut", "planifiee")
    else:
        date_debut = convertir_date(donnees["date_debut"], "date_debut") if "date_debut" in donnees else session.date_debut
        date_fin = convertir_date(donnees["date_fin"], "date_fin") if "date_fin" in donnees else session.date_fin
        statut = donnees.get("statut", session.statut)

    valider_dates_et_statut(date_debut, date_fin, statut)
    return date_debut, date_fin, statut

