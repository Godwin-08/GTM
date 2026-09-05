import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Tuple, Optional


def generer_token_activation() -> Tuple[str, str]:
    """
    Génère un token d'activation cryptographiquement sécurisé et son hash SHA-256.
    Le token brut est transmis à l'utilisateur (via lien),
    seul le condensat SHA-256 est conservé en base de données.
    """
    token_brut = secrets.token_urlsafe(32)
    token_hash = hasher_token(token_brut)
    return token_brut, token_hash


def hasher_token(token: str) -> str:
    """Calcule le hash SHA-256 d'un token textuel."""
    if not token:
        return ""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def comparer_hashes_token(hash_a: str, hash_b: str) -> bool:
    """Compare deux hashes en temps constant pour prévenir les attaques par timing."""
    if not hash_a or not hash_b:
        return False
    return hmac.compare_digest(hash_a, hash_b)


def calculer_expiration_activation(heures: int = 48) -> datetime:
    """Retourne la date limite de validité du token (horodatage UTC naïf cohérent)."""
    return datetime.utcnow() + timedelta(hours=heures)


def est_token_expire(expiration: Optional[datetime]) -> bool:
    """Vérifie si la date limite d'un token est dépassée."""
    if expiration is None:
        return True
    return datetime.utcnow() > expiration


def valider_force_mot_de_passe(mot_de_passe: str) -> Tuple[bool, Optional[str]]:
    """
    Vérifie les critères minimaux de sécurité du mot de passe défini par l'utilisateur.
    """
    if not mot_de_passe or len(mot_de_passe) < 8:
        return False, "Le mot de passe doit contenir au moins 8 caractères."
    return True, None
