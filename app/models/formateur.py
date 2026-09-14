"""
==============================================================================
Modèle de Données : Formateur (Intervenant / Enseignant)
==============================================================================
Représente un animateur de session de formation.
- Possède un domaine de compétence obligatoire (cohérence métier).
- Peut être lié de manière optionnelle (0 ou 1) à un compte Utilisateur
  (pour les formateurs internes disposant d'un accès à la plateforme).
"""

from app.extensions import db


class Formateur(db.Model):
    """
    Modèle SQLAlchemy de la table 'formateur'.
    
    Attributs :
        id (int) : Identifiant primaire unique.
        nom (str) : Nom complet du formateur.
        email (str, optionnel) : Adresse courriel de contact professionnel.
        telephone (str, optionnel) : Numéro de téléphone.
        utilisateur_id (int, optionnel) : Clé étrangère unique vers le compte Utilisateur.
        domaine_id (int) : Clé étrangère vers le Domaine de compétence.
        sessions (relationship) : Liste des sessions animées par ce formateur.
    """

    __tablename__ = "formateur"

    # Clé primaire auto-incrémentée
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    telephone = db.Column(db.String(20), nullable=True)

    # Lien optionnel vers Utilisateur : relation 1-à-1 stricte (unique=True)
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), unique=True, nullable=True
    )
    utilisateur = db.relationship("Utilisateur", back_populates="formateur")

    # Domaine d'expertise obligatoire
    domaine_id = db.Column(db.Integer, db.ForeignKey("domaine.id"), nullable=False)
    domaine = db.relationship("Domaine", back_populates="formateurs")

    # Relation 1-à-N : Sessions animées par ce formateur
    sessions = db.relationship("Session", back_populates="formateur")

    def __repr__(self):
        """Représentation textuelle de l'instance pour les logs et le débogage."""
        return f"<Formateur {self.nom}>"

