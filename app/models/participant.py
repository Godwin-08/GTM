from app.extensions import db


class Participant(db.Model):
    """
    Le salarié d'un Client qui suit réellement une formation.
    Ne se connecte jamais à l'application (pas de compte Utilisateur) :
    c'est une donnée gérée par les gestionnaires, pas un acteur du système.
    """

    __tablename__ = "participant"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)

    client_id = db.Column(db.Integer, db.ForeignKey("client.id"), nullable=False)
    client = db.relationship("Client", back_populates="participants")

    # Un participant peut avoir plusieurs inscriptions (sessions suivies)
    inscriptions = db.relationship("Inscription", back_populates="participant")

    def __repr__(self):
        return f"<Participant {self.nom}>"
