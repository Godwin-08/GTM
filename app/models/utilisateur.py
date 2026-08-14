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
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    actif = db.Column(db.Boolean, default=True, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    # Clé étrangère vers Role
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    role = db.relationship("Role", back_populates="utilisateurs")

    # Relation vers Formateur : un utilisateur peut être lié à AU PLUS un
    # formateur (uselist=False transforme la relation en objet unique,
    # pas en liste, puisque la contrainte UNIQUE garantit 0 ou 1 formateur)
    formateur = db.relationship("Formateur", back_populates="utilisateur", uselist=False)

    def a_role(self, nom_role):
        """
        Vérifie si l'utilisateur a un rôle précis, ex: utilisateur.a_role("admin").
        Évite d'avoir à écrire "utilisateur.role.nom == 'admin'" partout
        dans les routes, ce qui serait plus sujet aux fautes de frappe.
        """
        return self.role.nom == nom_role

    def __repr__(self):
        return f"<Utilisateur {self.email}>"
