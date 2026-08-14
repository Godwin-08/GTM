from app.extensions import db


class Formation(db.Model):
    """
    Le catalogue générique des formations proposées (le "contenu"),
    indépendant des dates précises. Une même formation peut donner
    lieu à plusieurs sessions différentes dans le temps.
    """

    __tablename__ = "formation"

    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(150), nullable=False)
    duree_jours = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=True)

    domaine_id = db.Column(db.Integer, db.ForeignKey("domaine.id"), nullable=False)
    domaine = db.relationship("Domaine", back_populates="formations")

    # Une formation peut donner lieu à plusieurs sessions
    sessions = db.relationship("Session", back_populates="formation")

    def __repr__(self):
        return f"<Formation {self.titre}>"
