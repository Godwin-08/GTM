"""
==============================================================================
Service de Validation des Paramètres de Requêtes HTTP (Query Params)
==============================================================================
Fournit des fonctions de parsing et de validation robuste pour les paramètres
passés dans request.args (entiers strictement positifs, dates au format ISO AAAA-MM-JJ,
valeurs limitées à un ensemble autorisé).
"""

from datetime import date


class ErreurFiltre(ValueError):
    """Exception levée lorsqu'un paramètre de filtre HTTP est syntaxiquement ou sémantiquement invalide."""
    pass


def entier_positif(args, nom):
    """
    Extrait et valide un entier strictement positif (> 0) depuis les arguments de requête.
    
    :param args: Dictionnaire ou MultiDict (request.args)
    :param nom: Nom du paramètre HTTP
    :return: int ou None si absent/vide
    :raises ErreurFiltre: Si la valeur n'est pas un entier strictement supérieur à 0
    """
    valeur = args.get(nom)
    if valeur is None or valeur == "":
        return None
    try:
        resultat = int(valeur)
    except ValueError as erreur:
        raise ErreurFiltre(f"{nom} doit être un entier positif") from erreur
    if resultat <= 0:
        raise ErreurFiltre(f"{nom} doit être un entier positif")
    return resultat


def date_iso(args, nom):
    """
    Extrait et valide une date au format ISO 8601 (AAAA-MM-JJ).
    
    :param args: MultiDict de requêtes
    :param nom: Nom du paramètre
    :return: date ou None
    :raises ErreurFiltre: Si le format de la date est incorrect
    """
    valeur = args.get(nom)
    if valeur is None or valeur == "":
        return None
    try:
        return date.fromisoformat(valeur)
    except ValueError as erreur:
        raise ErreurFiltre(f"{nom} doit être une date valide au format AAAA-MM-JJ") from erreur


def valeur_parmi(args, nom, valeurs_autorisees):
    """
    Extrait et vérifie qu'une chaîne appartient à une liste fermée de valeurs admises.
    
    :param args: MultiDict de requêtes
    :param nom: Nom du paramètre
    :param valeurs_autorisees: Collection (set/list) de valeurs valides
    :return: str ou None
    :raises ErreurFiltre: Si la valeur n'est pas autorisée
    """
    valeur = args.get(nom)
    if valeur is None or valeur == "":
        return None
    if valeur not in valeurs_autorisees:
        raise ErreurFiltre(f"{nom} doit être parmi {sorted(valeurs_autorisees)}")
    return valeur

