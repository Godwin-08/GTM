from datetime import datetime
from app.extensions import db
from flask_login import UserMixin


class Utilisateur(db.Model, UserMixin):
    """
    Comptes des employés Galaxy Solutions (admin, gestionnaire, formateur).
    UserMixin vient de Flask-Login : il ajoute automatiquement les méthodes
    dont Flask-Login a besoin (is_authenticated, is_active, get_id, etc.)
    pour gérer les sessions de connexion sans qu'on ait à les réécrire.
    """

    __tablename__ = "utilisateur"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe_hash = db.Column(db.String(255), nullable=True)
    actif = db.Column(db.Boolean, default=True, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    # Sécurité Onboarding : hash SHA-256 du token d'activation (jamais stocké en clair)
    # et date limite de validité (UTC naïf)
    token_activation_hash = db.Column(db.String(64), nullable=True, index=True)
    expiration_token = db.Column(db.DateTime, nullable=True)

    # Clé étrangère vers Role
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    role = db.relationship("Role", back_populates="utilisateurs")

    # Relation vers Formateur : un utilisateur peut être lié à AU PLUS un
    # formateur (uselist=False transforme la relation en objet unique,
    # pas en liste, puisque la contrainte UNIQUE garantit 0 ou 1 formateur)
    formateur = db.relationship("Formateur", back_populates="utilisateur", uselist=False)

    @property
    def statut(self):
        """
        Détermine l'état du compte parmi les 3 états métier :
        - 'actif' : compte activé et autorisé à se connecter
        - 'en_attente' : compte créé, en attente de définition du mot de passe
        - 'desactive' : compte inactif (désactivé par un admin)
        """
        if self.actif:
            return "actif"
        if self.token_activation_hash is not None:
            return "en_attente"
        return "desactive"

    @property
    def est_en_attente(self):
        return not self.actif and self.token_activation_hash is not None

    def a_role(self, nom_role):
        """
        Vérifie si l'utilisateur a un rôle précis, ex: utilisateur.a_role("admin").
        Évite d'avoir à écrire "utilisateur.role.nom == 'admin'" partout
        dans les routes, ce qui serait plus sujet aux fautes de frappe.
        """
        return self.role.nom == nom_role

    def __repr__(self):
        return f"<Utilisateur {self.email} [{self.statut}]>"
