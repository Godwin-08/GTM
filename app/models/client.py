"""
==============================================================================
Modèle de Données : Client (Entreprise Cliente)
==============================================================================
Représente une organisation cliente contractant des formations avec Galaxy Solutions.
Un Client finance les formations et emploie plusieurs Participants (salariés).
Il constitue l'unité d'analyse principale pour l'évaluation de l'activité et l'ACP.
"""

from app.extensions import db


class Client(db.Model):
    """
    Modèle SQLAlchemy de la table 'client'.
    
    Attributs :
        id (int) : Identifiant primaire unique.
        nom_entreprise (str) : Raison sociale de l'entreprise (unique et obligatoire).
        secteur (str, optionnel) : Secteur d'activité économique (Banque, Industrie, IT, etc.).
        contact_email (str, optionnel) : Adresse courriel du responsable formation / RH.
        participants (relationship) : Liste des salariés rattachés à cette entreprise.
    """

    __tablename__ = "client"

    # Clé primaire auto-incrémentée
    id = db.Column(db.Integer, primary_key=True)
    # Nom de l'entreprise avec contrainte d'unicité
    nom_entreprise = db.Column(db.String(150), unique=True, nullable=False)
    # Secteur d'activité
    secteur = db.Column(db.String(100), nullable=True)
    # Courriel de contact
    contact_email = db.Column(db.String(150), nullable=True)

    # Relation 1-à-N : Un client emploie plusieurs participants
    participants = db.relationship("Participant", back_populates="client")

    def __repr__(self):
        """Représentation textuelle de l'instance pour les logs et le débogage."""
        return f"<Client {self.nom_entreprise}>"

