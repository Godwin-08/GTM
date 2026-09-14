"""
==============================================================================
Modèle de Données : Participant (Apprenant / Stagiaire)
==============================================================================
Représente un salarié employé par un Client et inscrit à des sessions de formation.
Le participant est une entité métier gérée (il ne dispose pas de compte utilisateur
ni d'accès direct à l'application).
"""

from app.extensions import db


class Participant(db.Model):
    """
    Modèle SQLAlchemy de la table 'participant'.
    
    Attributs :
        id (int) : Identifiant primaire unique.
        nom (str) : Nom et prénom du salarié.
        email (str) : Adresse courriel unique du participant.
        client_id (int) : Clé étrangère vers l'entreprise employeuse (Client).
        client (relationship) : Objet Client associé.
        inscriptions (relationship) : Liste des inscriptions à des sessions.
    """

    __tablename__ = "participant"

    # Clé primaire auto-incrémentée
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)

    # Clé étrangère vers Client
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    client = db.relationship("Client", back_populates="participants")

    # Relation 1-à-N : Inscriptions de ce participant
    inscriptions = db.relationship("Inscription", back_populates="participant")

    def __repr__(self):
        """Représentation textuelle de l'instance pour les logs et le débogage."""
        return f"<Participant {self.nom} ({self.email})>"

