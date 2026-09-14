"""
==============================================================================
Modèle de Données : Domaine (Domaine d'expertise)
==============================================================================
Référentiel des grands axes thématiques de formation de Galaxy Solutions :
- Web & Data
- Management Agile
- Cybersécurité

Garantit la cohérence stricte entre les formations proposées et les compétences
des formateurs assignés.
"""

from app.extensions import db


class Domaine(db.Model):
    """
    Modèle SQLAlchemy de la table 'domaine'.
    
    Attributs :
        id (int) : Identifiant primaire unique.
        nom (str) : Intitulé unique du domaine (ex: 'Web & Data').
        formations (relationship) : Liste des formations appartenant à ce domaine.
        formateurs (relationship) : Liste des formateurs qualifiés dans ce domaine.
    """

    __tablename__ = "domaine"

    # Clé primaire auto-incrémentée
    id = db.Column(db.Integer, primary_key=True)
    # Intitulé unique du domaine
    nom = db.Column(db.String(50), unique=True, nullable=False)

    # Relations inverses : domaine.formations et domaine.formateurs
    formations = db.relationship("Formation", back_populates="domaine")
    formateurs = db.relationship("Formateur", back_populates="domaine")

    def __repr__(self):
        """Représentation textuelle de l'instance pour les logs et le débogage."""
        return f"<Domaine {self.nom}>"

