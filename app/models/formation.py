"""
==============================================================================
Modèle de Données : Formation (Catalogue des Cours)
==============================================================================
Représente une offre pédagogique générique (programme de formation).
Elle est définie indépendamment des dates de planification (sessions).
Chaque formation est rattachée à un domaine d'expertise et possède une durée en jours (2 à 5 jours).
"""

from app.extensions import db


class Formation(db.Model):
    """
    Modèle SQLAlchemy de la table 'formation'.
    
    Attributs :
        id (int) : Identifiant primaire unique.
        titre (str) : Nom de la formation (ex: 'Python pour la Data Science').
        duree_jours (int) : Durée pédagogique en jours (entre 2 et 5).
        description (str, optionnel) : Programme détaillé et objectifs de la formation.
        domaine_id (int) : Clé étrangère vers le Domaine thématique.
        domaine (relationship) : Objet Domaine associé.
        sessions (relationship) : Liste des sessions planifiées de cette formation.
    """

    __tablename__ = "formation"

    # Clé primaire auto-incrémentée
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    duree_jours = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)

    # Clé étrangère vers le domaine d'expertise
    domaine_id = db.Column(db.Integer, db.ForeignKey("domaine.id"), nullable=False)
    domaine = db.relationship("Domaine", back_populates="formations")

    # Relation 1-à-N : Une formation donne lieu à plusieurs sessions
    sessions = db.relationship("Session", back_populates="formation")

    def __repr__(self):
        """Représentation textuelle de l'instance pour les logs et le débogage."""
        return f"<Formation {self.titre}>"

