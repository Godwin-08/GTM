"""
==============================================================================
Service de Sécurité & Onboarding (Tokens d'Activation & Mots de Passe)
==============================================================================
Ce module gère le cycle de vie cryptographique de l'activation des comptes :
- Génération de tokens d'activation aléatoires cryptographiquement sûrs (CSPRNG).
- Hachage SHA-256 pour le stockage sécurisé en base (le token brut n'est jamais persisté).
- Comparaison en temps constant (hmac.compare_digest) contre les attaques par canal auxiliaire (timing attacks).
- Gestion de la fenêtre de validité temporelle (48h par défaut).
- Validation de la robustesse des mots de passe.
"""

import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Tuple, Optional


def generer_token_activation() -> Tuple[str, str]:
    """
    Génère un token d'activation cryptographiquement sécurisé et son empreinte SHA-256.
    
    :return: Tuple (token_brut, token_hash)
             - token_brut est envoyé à l'utilisateur dans l'URL d'activation.
             - token_hash est persisté en base de données.
    """
    token_brut = secrets.token_urlsafe(32)
    token_hash = hasher_token(token_brut)
    return token_brut, token_hash


def hasher_token(token: str) -> str:
    """Calcule le condensat hexadécimal SHA-256 d'un token textuel."""
    if not token:
        return ""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def comparer_hashes_token(hash_a: str, hash_b: str) -> bool:
    """
    Compare deux chaînes de hachage en temps constant.
    Protège contre les attaques par analyse du temps d'exécution (timing attacks).
    """
    if not hash_a or not hash_b:
        return False
    return hmac.compare_digest(hash_a, hash_b)


def calculer_expiration_activation(heures: int = 48) -> datetime:
    """Calcule la date et l'heure UTC limites de validité du token d'activation."""
    return datetime.utcnow() + timedelta(hours=heures)


def est_token_expire(expiration: Optional[datetime]) -> bool:
    """Vérifie si la date d'expiration spécifiée est antérieure à l'instant présent (UTC)."""
    if expiration is None:
        return True
    return datetime.utcnow() > expiration


def valider_force_mot_de_passe(mot_de_passe: str) -> Tuple[bool, Optional[str]]:
    """
    Vérifie la conformité du mot de passe avec la politique minimale de sécurité (au moins 8 caractères).
    
    :return: Tuple (est_valide, message_erreur_optionnel)
    """
    if not mot_de_passe or len(mot_de_passe) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    return True, None

