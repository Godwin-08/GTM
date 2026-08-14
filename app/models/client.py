from app.extensions import db


class Client(db.Model):
    """
    L'entreprise cliente qui inscrit ses salariés (Participants).
    Séparée de Participant : un Client a plusieurs salariés distincts.
    """

    __tablename__ = "client"

    id = db.Column(db.Integer, primary_key=True)
    nom_entreprise = db.Column(db.String(150), unique=True, nullable=False)
    secteur = db.Column(db.String(100), nullable=True)
    contact_email = db.Column(db.String(150), nullable=True)

    # Un client emploie plusieurs participants
    participants = db.relationship("Participant", back_populates="client")

    def __repr__(self):
        return f"<Client {self.nom_entreprise}>"
