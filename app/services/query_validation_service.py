"""Validation réutilisable des paramètres de filtre HTTP."""

from datetime import date


class ErreurFiltre(ValueError):
    pass


def entier_positif(args, nom):
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
    valeur = args.get(nom)
    if valeur is None or valeur == "":
        return None
    try:
        return date.fromisoformat(valeur)
    except ValueError as erreur:
        raise ErreurFiltre(f"{nom} doit être une date valide au format AAAA-MM-JJ") from erreur


def valeur_parmi(args, nom, valeurs_autorisees):
    valeur = args.get(nom)
    if valeur is None or valeur == "":
        return None
    if valeur not in valeurs_autorisees:
        raise ErreurFiltre(f"{nom} doit être parmi {sorted(valeurs_autorisees)}")
    return valeur
