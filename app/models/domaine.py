from app.extensions import db


class Domaine(db.Model):
    """
    Référentiel des 3 domaines de formation (Web & Data, Management Agile,
    Cybersécurité). Partagé entre Formation et Formateur pour garantir
    que les deux utilisent toujours les mêmes valeurs (cohérence).
    """

    __tablename__ = "domaine"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), unique=True, nullable=False)

    # Relations inverses : domaine.formations et domaine.formateurs
    formations = db.relationship("Formation", back_populates="domaine")
    formateurs = db.relationship("Formateur", back_populates="domaine")

    def __repr__(self):
        return f"<Domaine {self.nom}>"
