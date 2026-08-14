from app.extensions import db


class Role(db.Model):
    """
    Référentiel des 3 rôles possibles : admin, gestionnaire, formateur.
    Une table séparée plutôt qu'un simple champ texte, pour garantir
    que la valeur est toujours cohérente (pas de faute de frappe possible
    comme "Admin" vs "admin" à un endroit et pas un autre).
    """

    __tablename__ = "role"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(30), unique=True, nullable=False)

    # Relation inverse : permet de faire role.utilisateurs pour récupérer
    # tous les utilisateurs qui ont ce rôle. back_populates crée le lien
    # dans les deux sens avec Utilisateur.role (défini plus tard).
    utilisateurs = db.relationship("Utilisateur", back_populates="role")

    def __repr__(self):
        # Représentation lisible utile pour le débogage (ex: dans un print())
        return f"<Role {self.nom}>"
