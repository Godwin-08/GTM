from app.extensions import db


class Session(db.Model):
    """
    Une occurrence précise et planifiée d'une Formation (dates, lieu,
    formateur assigné). Volontairement PAS de client_id direct ici :
    une session peut être inter-entreprises (plusieurs clients, via
    leurs participants inscrits) — voir Inscription/Participant.
    """

    __tablename__ = "session"

    id = db.Column(db.Integer, primary_key=True)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'intra' ou 'inter'
    capacite_max = db.Column(db.Integer, nullable=False)
    lieu = db.Column(db.String(150), nullable=True)
    statut = db.Column(db.String(20), nullable=False, default="planifiee")
    # 'planifiee' / 'en_cours' / 'terminee' / 'annulee'

    formation_id = db.Column(db.Integer, db.ForeignKey("formation.id"), nullable=False)
    formation = db.relationship("Formation", back_populates="sessions")

    formateur_id = db.Column(db.Integer, db.ForeignKey("formateur.id"), nullable=False)
    formateur = db.relationship("Formateur", back_populates="sessions")

    # Une session reçoit plusieurs inscriptions
    inscriptions = db.relationship("Inscription", back_populates="session")

    def nb_inscrits_confirmes(self):
        """Compte uniquement les inscriptions au statut 'confirmee'."""
        return sum(1 for i in self.inscriptions if i.statut == "confirmee")

    def taux_remplissage(self):
        """
        Calcule le taux de remplissage réel de la session.
        Se base uniquement sur les inscriptions confirmées : une
        inscription annulée ou en liste d'attente ne doit jamais
        gonfler artificiellement ce taux.
        """
        if self.capacite_max == 0:
            return 0
        return round(self.nb_inscrits_confirmes() / self.capacite_max, 2)

    def est_complete(self):
        return self.nb_inscrits_confirmes() >= self.capacite_max

    def __repr__(self):
        return f"<Session {self.id} - {self.date_debut}>"
