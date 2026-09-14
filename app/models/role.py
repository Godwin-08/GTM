"""
==============================================================================
Modèle de Données : Role (Habilitations RBAC)
==============================================================================
Référentiel des rôles utilisateurs de la plateforme Galaxy Training Manager :
- 'admin'        : Accès complet (utilisateurs, exports, suppressions, paramétrages).
- 'gestionnaire' : Gestion des formations, sessions, clients, participants et inscriptions.
- 'formateur'    : Accès restreint à ses propres sessions et émargements.
"""

from app.extensions import db


class Role(db.Model):
    """
    Modèle SQLAlchemy de la table 'role'.
    
    Attributs :
        id (int) : Identifiant primaire unique.
        nom (str) : Nom unique du rôle ('admin', 'gestionnaire', 'formateur').
        utilisateurs (relationship) : Liste des comptes utilisateurs rattachés à ce rôle.
    """

    __tablename__ = "role"

    # Clé primaire auto-incrémentée
    id = db.Column(db.Integer, primary_key=True)
    # Intitulé unique du rôle
    nom = db.Column(db.String(30), unique=True, nullable=False)

    # Relation 1-à-N : Utilisateurs disposant de ce rôle
    utilisateurs = db.relationship("Utilisateur", back_populates="role")

    def __repr__(self):
        """Représentation textuelle de l'instance pour les logs et le débogage."""
        return f"<Role {self.nom}>"

