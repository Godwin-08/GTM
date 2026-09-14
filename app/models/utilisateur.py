"""
==============================================================================
Modèle de Données : Utilisateur (Comptes Applicatifs & Sécurité)
==============================================================================
Gère les comptes utilisateurs des collaborateurs Galaxy Solutions (Admin, Gestionnaire, Formateur).
- Intègre Flask-Login (UserMixin) pour l'authentification et les sessions.
- Sécurise le stockage des mots de passe par hachage PBKDF2:SHA256.
- Implémente le workflow d'Onboarding sécurisé : création en attente d'activation
  avec token à usage unique condensé en SHA-256 et expiration automatique à 48h.
- Fournit des helpers pour la vérification des rôles (RBAC).
"""

from datetime import datetime
from app.extensions import db
from flask_login import UserMixin


class Utilisateur(db.Model, UserMixin):
    """
    Modèle SQLAlchemy de la table 'utilisateur'.
    
    Attributs :
        id (int) : Identifiant primaire unique.
        nom (str) : Nom complet du collaborateur.
        email (str) : Adresse courriel professionnelle unique.
        mot_de_passe_hash (str, optionnel) : Condensat PBKDF2:SHA256 du mot de passe (None si en attente).
        actif (bool) : État d'activation du compte.
        date_creation (datetime) : Horodatage UTC de création.
        token_activation_hash (str, optionnel) : Empreinte SHA-256 du token d'activation à usage unique.
        expiration_token (datetime, optionnel) : Date/heure UTC limite de validité du token.
        role_id (int) : Clé étrangère vers le Role.
        role (relationship) : Objet Role associé.
        formateur (relationship) : Profil Formateur lié (si rôle formateur).
    """

    __tablename__ = "utilisateur"

    # Clé primaire auto-incrémentée
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(255), nullable=True)
    actif = db.Column(db.Boolean, default=True, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    # Sécurité Onboarding : hash SHA-256 du token d'activation (jamais stocké en clair)
    token_activation_hash = db.Column(db.String(64), nullable=True, index=True)
    expiration_token = db.Column(db.DateTime, nullable=True)

    # Clé étrangère vers Role
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    role = db.relationship("Role", back_populates="utilisateurs")

    # Relation 1-à-1 optionnelle vers Formateur
    formateur = db.relationship("Formateur", back_populates="utilisateur", uselist=False)

    @property
    def statut(self):
        """
        Détermine l'état du compte parmi les 3 statuts métier :
        - 'actif'      : Compte activé et autorisé à se connecter.
        - 'en_attente' : Compte créé, en attente d'activation par l'utilisateur.
        - 'desactive'  : Compte désactivé par un administrateur.
        """
        if self.actif:
            return "actif"
        if self.token_activation_hash is not None:
            return "en_attente"
        return "desactive"

    @property
    def est_en_attente(self):
        """Indique si le compte est actuellement en attente d'activation."""
        return not self.actif and self.token_activation_hash is not None

    def a_role(self, nom_role):
        """
        Vérifie si l'utilisateur possède un rôle spécifique.
        Exemple : user.a_role("admin") -> True/False
        """
        return self.role.nom == nom_role

    def __repr__(self):
        """Représentation textuelle de l'instance pour les logs et le débogage."""
        return f"<Utilisateur {self.email} [{self.statut}] role={self.role.nom if self.role else 'None'}>"

