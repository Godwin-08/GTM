from datetime import date
from app.extensions import db


class Inscription(db.Model):
    """
    Le lien entre un Participant et une Session — répond à la question
    "qui est inscrit où". Le champ statut est CRITIQUE : sans lui,
    le taux de remplissage des sessions serait faux (une inscription
    annulée ou en liste d'attente ne doit pas compter comme confirmée).
    """

    __tablename__ = "inscription"

    id = db.Column(db.Integer, primary_key=True)
    date_inscription = db.Column(db.Date, nullable=False, default=date.today)
    statut = db.Column(db.String(20), nullable=False, default="confirmee")
    # 'confirmee' / 'annulee' / 'liste_attente'

    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    session = db.relationship("Session", back_populates="inscriptions")

    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"), nullable=False)
    participant = db.relationship("Participant", back_populates="inscriptions")

    # Empêche qu'un même participant soit inscrit deux fois à la même session
    # (contrainte au niveau de la base, en plus de toute vérification côté code)
    __table_args__ = (
        db.UniqueConstraint("session_id", "participant_id", name="uq_session_participant"),
    )

    def confirmer(self):
        self.statut = "confirmee"

    def annuler(self):
        self.statut = "annulee"

    def mettre_en_liste_attente(self):
        self.statut = "liste_attente"

    def __repr__(self):
        return f"<Inscription session={self.session_id} participant={self.participant_id}>"
