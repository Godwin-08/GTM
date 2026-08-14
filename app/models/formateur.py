from app.extensions import db


class Formateur(db.Model):
    """
    La personne qui anime les sessions. Le lien vers Utilisateur est
    optionnel : un formateur externe ou occasionnel peut exister dans
    la base sans avoir besoin de se connecter à l'application.
    """

    __tablename__ = "formateur"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    telephone = db.Column(db.String(20), nullable=True)

    # Lien optionnel vers Utilisateur. unique=True garantit qu'un même
    # compte utilisateur ne peut pas être associé à deux formateurs différents.
    utilisateur_id = db.Column(
        db.Integer, db.ForeignKey("utilisateur.id"), unique=True, nullable=True
    )
    utilisateur = db.relationship("Utilisateur", back_populates="formateur")

    # Domaine de compétence (obligatoire, contrairement au lien utilisateur)
    domaine_id = db.Column(db.Integer, db.ForeignKey("domaine.id"), nullable=False)
    domaine = db.relationship("Domaine", back_populates="formateurs")

    # Un formateur anime plusieurs sessions (relation définie complètement
    # du côté Session, voir plus bas dans ce fichier une fois Session créé)
    sessions = db.relationship("Session", back_populates="formateur")

    def __repr__(self):
        return f"<Formateur {self.nom}>"
