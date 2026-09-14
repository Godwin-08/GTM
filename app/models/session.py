"""
==============================================================================
Modèle de Données : Session (Session de Formation Planifiée)
==============================================================================
Représente une occurrence précise et datée d'une Formation.
- Associe une Formation à un Formateur qualifié.
- Types supportés : 'inter' (inter-entreprises) ou 'intra' (dédiée à un client).
- Statuts de cycle de vie : 'planifiee', 'en_cours', 'terminee', 'annulee'.
- Calcule dynamiquement le nombre d'inscrits confirmés et le taux de remplissage.
"""

from app.extensions import db


class Session(db.Model):
    """
    Modèle SQLAlchemy de la table 'session'.
    
    Attributs :
        id (int) : Identifiant primaire unique.
        date_debut (date) : Date de début de la session.
        date_fin (date) : Date de fin de la session.
        type (str) : 'intra' ou 'inter'.
        capacite_max (int) : Nombre maximal de places disponibles.
        lieu (str, optionnel) : Salle ou adresse de la formation.
        statut (str) : 'planifiee', 'en_cours', 'terminee' ou 'annulee'.
        formation_id (int) : Clé étrangère vers Formation.
        formateur_id (int) : Clé étrangère vers Formateur.
        formation (relationship) : Objet Formation rattaché.
        formateur (relationship) : Objet Formateur rattaché.
        inscriptions (relationship) : Liste des inscriptions associées.
    """

    __tablename__ = "session"

    # Clé primaire auto-incrémentée
    id = db.Column(db.Integer, primary_key=True)
    date_debut = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'intra' ou 'inter'
    capacite_max = db.Column(db.Integer, nullable=False)
    lieu = db.Column(db.String(150), nullable=True)
    statut = db.Column(db.String(20), nullable=False, default="planifiee")

    # Clés étrangères
    formation_id = db.Column(db.Integer, db.ForeignKey("formation.id"), nullable=False)
    formation = db.relationship("Formation", back_populates="sessions")

    formateur_id = db.Column(db.Integer, db.ForeignKey("formateur.id"), nullable=False)
    formateur = db.relationship("Formateur", back_populates="sessions")

    # Relation 1-à-N : Inscriptions à cette session
    inscriptions = db.relationship("Inscription", back_populates="session")

    def nb_inscrits_confirmes(self):
        """Compte uniquement les inscriptions au statut 'confirmee'."""
        return sum(1 for i in self.inscriptions if i.statut == "confirmee")

    def taux_remplissage(self):
        """
        Calcule le taux de remplissage réel de la session (entre 0.0 et 1.0+).
        Se base exclusivement sur les inscriptions confirmées (exclut 'annulee' et 'liste_attente').
        """
        if self.capacite_max == 0:
            return 0
        return round(self.nb_inscrits_confirmes() / self.capacite_max, 2)

    def est_complete(self):
        """Indique si la capacité maximale de la session est atteinte ou dépassée."""
        return self.nb_inscrits_confirmes() >= self.capacite_max

    def __repr__(self):
        """Représentation textuelle de l'instance pour les logs et le débogage."""
        return f"<Session {self.id} - {self.formation.titre if self.formation else ''} ({self.date_debut}) [{self.statut}]>"

