"""
==============================================================================
Modèle de Données : Inscription (Liaison Participant — Session)
==============================================================================
Représente la participation d'un salarié à une session de formation donnée.
Gère le cycle de vie de l'inscription via ses 3 statuts métier :
- 'confirmee'     : Place réservée comptabilisée dans le taux de remplissage.
- 'liste_attente' : En attente de désistement si la capacité maximale est atteinte.
- 'annulee'       : Inscription annulée (ne consomme pas de place).

Une contrainte d'unicité (uq_session_participant) empêche tout doublon en base.
"""

from datetime import date
from app.extensions import db


class Inscription(db.Model):
    """
    Modèle SQLAlchemy de la table 'inscription'.
    
    Attributs :
        id (int) : Identifiant primaire unique.
        date_inscription (date) : Date d'enregistrement (par défaut : aujourd'hui).
        statut (str) : 'confirmee', 'annulee' ou 'liste_attente'.
        session_id (int) : Clé étrangère vers la Session.
        participant_id (int) : Clé étrangère vers le Participant.
        session (relationship) : Objet Session rattaché.
        participant (relationship) : Objet Participant rattaché.
    """

    __tablename__ = "inscription"

    id = db.Column(db.Integer, primary_key=True)
    date_inscription = db.Column(db.Date, nullable=False, default=date.today)
    statut = db.Column(db.String(20), nullable=False, default="confirmee")

    # Clés étrangères
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    session = db.relationship("Session", back_populates="inscriptions")

    participant_id = db.Column(db.Integer, db.ForeignKey("participant.id"), nullable=False)
    participant = db.relationship("Participant", back_populates="inscriptions")

    # Contrainte d'unicité composite au niveau de la base MySQL
    __table_args__ = (
        db.UniqueConstraint("session_id", "participant_id", name="uq_session_participant"),
    )

    def confirmer(self):
        """Passe l'inscription au statut 'confirmee'."""
        self.statut = "confirmee"

    def annuler(self):
        """Passe l'inscription au statut 'annulee'."""
        self.statut = "annulee"

    def mettre_en_liste_attente(self):
        """Passe l'inscription en 'liste_attente'."""
        self.statut = "liste_attente"

    def __repr__(self):
        """Représentation textuelle de l'instance pour les logs et le débogage."""
        return f"<Inscription session={self.session_id} participant={self.participant_id} [{self.statut}]>"

