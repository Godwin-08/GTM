from flask import Blueprint, request, jsonify
from flask_login import login_required
from app.extensions import db
from app.models import Formation, Domaine
from app.services.permissions import gestionnaire_ou_admin_required

formations_bp = Blueprint("formations", __name__, url_prefix="/api/formations")

def formation_vers_dict(formation):
    """
    Convertit un objet Formation en dictionnaire simple, prêt à être
    transformé en JSON. On centralise cette conversion dans une fonction
    plutôt que de la répéter dans chaque route, pour éviter d'oublier
    un champ quelque part.
    """
    return {
        "id": formation.id,
        "titre": formation.titre,
        "duree_jours": formation.duree_jours,
        "description": formation.description,
        "domaine": {
            "id": formation.domaine.id,
            "nom": formation.domaine.nom,
        },
    }

@formations_bp.route("", methods=["GET"])
@login_required  # il faut être connecté, peu importe le rôle, pour consulter
def liste_formations():
    """Renvoie toutes les formations du catalogue."""
    formations = Formation.query.all()
    return jsonify([formation_vers_dict(f) for f in formations]), 200

@formations_bp.route("/<int:formation_id>", methods=["GET"])
@login_required
def detail_formation(formation_id):
    """Renvoie une formation précise, ou une erreur 404 si elle n'existe pas."""
    formation = Formation.query.get_or_404(formation_id)
    return jsonify(formation_vers_dict(formation)), 200

@formations_bp.route("", methods=["POST"])
@gestionnaire_ou_admin_required  # seuls admin/gestionnaire peuvent créer
def creer_formation():
    """
    Crée une nouvelle formation à partir d'un JSON du type :
    { "titre": "...", "domaine_id": 1, "duree_jours": 3, "description": "..." }
    """
    donnees = request.get_json()

    # Validation minimale : champs obligatoires présents
    titre = donnees.get("titre")
    domaine_id = donnees.get("domaine_id")
    duree_jours = donnees.get("duree_jours")

    if not titre or not domaine_id or not duree_jours:
        return jsonify({"erreur": "titre, domaine_id et duree_jours sont obligatoires"}), 400

    if not (2 <= duree_jours <= 5):
        return jsonify({"erreur": "duree_jours doit être entre 2 et 5"}), 400

    # Vérifie que le domaine_id fourni existe vraiment,
    # sinon SQLAlchemy lèverait une erreur de clé étrangère moins claire
    domaine = Domaine.query.get(domaine_id)
    if not domaine:
        return jsonify({"erreur": "domaine_id invalide"}), 400

    formation = Formation(
        titre=titre,
        domaine_id=domaine_id,
        duree_jours=duree_jours,
        description=donnees.get("description"),
    )
    db.session.add(formation)
    db.session.commit()

    return jsonify(formation_vers_dict(formation)), 201  # 201 = ressource créée

@formations_bp.route("/<int:formation_id>", methods=["PUT"])
@gestionnaire_ou_admin_required
def modifier_formation(formation_id):
    """Met à jour une formation existante (seuls les champs fournis sont modifiés)."""
    formation = Formation.query.get_or_404(formation_id)
    donnees = request.get_json()

    if "titre" in donnees:
        formation.titre = donnees["titre"]
    if "duree_jours" in donnees:
        if not (2 <= donnees["duree_jours"] <= 5):
            return jsonify({"erreur": "duree_jours doit être entre 2 et 5"}), 400
        formation.duree_jours = donnees["duree_jours"]
    if "description" in donnees:
        formation.description = donnees["description"]
    if "domaine_id" in donnees:
        if not Domaine.query.get(donnees["domaine_id"]):
            return jsonify({"erreur": "domaine_id invalide"}), 400
        formation.domaine_id = donnees["domaine_id"]

    db.session.commit()
    return jsonify(formation_vers_dict(formation)), 200
