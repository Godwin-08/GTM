from flask import Blueprint, request, jsonify
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models import Utilisateur, Role, Formateur
from app.services.permissions import admin_required

from app.services.activation_service import (
    generer_token_activation,
    calculer_expiration_activation,
)
from app.services.mail_service import envoyer_invitation_activation

utilisateurs_bp = Blueprint("utilisateurs", __name__, url_prefix="/api/utilisateurs")

def utilisateur_vers_dict(utilisateur):
    """
    Ne renvoie JAMAIS mot_de_passe_hash, même haché : ce champ n'a aucune
    raison de sortir de la base de données vers l'extérieur, même vers
    un admin. Personne n'a besoin de le voir, ni de le vérifier à l'œil.
    """
    formateur = Formateur.query.filter_by(utilisateur_id=utilisateur.id).first()
    return {
        "id": utilisateur.id,
        "nom": utilisateur.nom,
        "email": utilisateur.email,
        "actif": utilisateur.actif,
        "statut": utilisateur.statut,
        "est_en_attente": utilisateur.est_en_attente,
        "expiration_token": utilisateur.expiration_token.isoformat() if utilisateur.expiration_token else None,
        "date_creation": utilisateur.date_creation.isoformat(),
        "role": {
            "id": utilisateur.role.id,
            "nom": utilisateur.role.nom,
        },
        "formateur": {
            "id": formateur.id,
            "nom": formateur.nom,
            "telephone": formateur.telephone,
            "domaine": {
                "id": formateur.domaine.id,
                "nom": formateur.domaine.nom,
            } if formateur.domaine else None,
        } if formateur else None,
    }

@utilisateurs_bp.route("", methods=["GET"])
@admin_required
def liste_utilisateurs():
    utilisateurs = Utilisateur.query.all()
    return jsonify([utilisateur_vers_dict(u) for u in utilisateurs]), 200

@utilisateurs_bp.route("/<int:utilisateur_id>", methods=["GET"])
@admin_required
def detail_utilisateur(utilisateur_id):
    utilisateur = db.get_or_404(Utilisateur, utilisateur_id)
    return jsonify(utilisateur_vers_dict(utilisateur)), 200

@utilisateurs_bp.route("", methods=["POST"])
@admin_required
def creer_utilisateur():
    donnees = request.get_json() or {}
    nom = donnees.get("nom")
    email = donnees.get("email")
    role_id = donnees.get("role_id")
    mot_de_passe = donnees.get("mot_de_passe")

    if not all([nom, email, role_id]):
        return jsonify({"erreur": "nom, email et role_id sont obligatoires"}), 400

    if not db.session.get(Role, role_id):
        return jsonify({"erreur": "role_id invalide"}), 400

    if Utilisateur.query.filter_by(email=email).first():
        return jsonify({"erreur": "un compte avec cet email existe déjà"}), 409

    token_activation = None
    if mot_de_passe:
        # Création directe avec mot de passe (rétrocompatibilité / scripts internes)
        utilisateur = Utilisateur(
            nom=nom,
            email=email,
            mot_de_passe_hash=generate_password_hash(mot_de_passe, method="pbkdf2:sha256"),
            role_id=role_id,
            actif=True,
            token_activation_hash=None,
            expiration_token=None,
        )
    else:
        # Nouveau flux standard Onboarding : compte créé en attente d'activation
        token_brut, token_hash = generer_token_activation()
        token_activation = token_brut
        expiration = calculer_expiration_activation(48)

        utilisateur = Utilisateur(
            nom=nom,
            email=email,
            mot_de_passe_hash=None,
            role_id=role_id,
            actif=False,
            token_activation_hash=token_hash,
            expiration_token=expiration,
        )

    db.session.add(utilisateur)
    db.session.commit()

    reponse = utilisateur_vers_dict(utilisateur)
    if token_activation:
        base_url = request.host_url.rstrip("/")
        base_url = current_app.config.get("APP_BASE_URL") or request.host_url.rstrip("/")
        url_complete = f"{base_url}/activation/{token_activation}"
        reponse["token_activation"] = token_activation
        reponse["url_activation"] = f"/activation/{token_activation}"

        # Envoi de l'invitation par mail (Mode Console ou SMTP)
        resultat_mail = envoyer_invitation_activation(
            destinataire_email=utilisateur.email,
            nom_utilisateur=utilisateur.nom,
            url_activation=url_complete,
        )
        reponse["email_envoye"] = resultat_mail.get("succes", True)
        if not resultat_mail.get("succes"):
            reponse["avertissement_mail"] = resultat_mail.get("erreur")

    return jsonify(reponse), 201


@utilisateurs_bp.route("/<int:utilisateur_id>/renvoyer-invitation", methods=["POST"])
@admin_required
def renvoyer_invitation(utilisateur_id):
    """
    Régénère un token d'activation pour un compte toujours en attente d'activation
    et réexpédie l'e-mail d'invitation.
    """
    utilisateur = db.get_or_404(Utilisateur, utilisateur_id)

    if utilisateur.actif:
        return jsonify({"erreur": "Ce compte est déjà activé."}), 400

    token_brut, token_hash = generer_token_activation()
    utilisateur.token_activation_hash = token_hash
    utilisateur.expiration_token = calculer_expiration_activation(48)
    db.session.commit()

    base_url = request.host_url.rstrip("/")
    base_url = current_app.config.get("APP_BASE_URL") or request.host_url.rstrip("/")
    url_complete = f"{base_url}/activation/{token_brut}"

    reponse = utilisateur_vers_dict(utilisateur)
    reponse["token_activation"] = token_brut
    reponse["url_activation"] = f"/activation/{token_brut}"
    reponse["message"] = f"Nouvelle invitation générée pour {utilisateur.email}."

    # Renvoi du courriel d'activation
    resultat_mail = envoyer_invitation_activation(
        destinataire_email=utilisateur.email,
        nom_utilisateur=utilisateur.nom,
        url_activation=url_complete,
    )
    reponse["email_envoye"] = resultat_mail.get("succes", True)
    if not resultat_mail.get("succes"):
        reponse["avertissement_mail"] = resultat_mail.get("erreur")

    return jsonify(reponse), 200

@utilisateurs_bp.route("/<int:utilisateur_id>", methods=["PUT"])
@admin_required
def modifier_utilisateur(utilisateur_id):
    utilisateur = db.get_or_404(Utilisateur, utilisateur_id)
    donnees = request.get_json()

    if "nom" in donnees:
        utilisateur.nom = donnees["nom"]
    if "email" in donnees:
        if Utilisateur.query.filter(
            Utilisateur.email == donnees["email"], Utilisateur.id != utilisateur_id
        ).first():
            return jsonify({"erreur": "cet email est déjà utilisé par un autre compte"}), 409
        utilisateur.email = donnees["email"]
    if "role_id" in donnees:
        if not db.session.get(Role, donnees["role_id"]):
            return jsonify({"erreur": "role_id invalide"}), 400
        utilisateur.role_id = donnees["role_id"]
    if "actif" in donnees:
        if utilisateur.id == current_user.id and donnees["actif"] is False:
            return jsonify({"erreur": "vous ne pouvez pas désactiver votre propre compte"}), 400
        utilisateur.actif = donnees["actif"]
    if "mot_de_passe" in donnees and donnees["mot_de_passe"]:
        utilisateur.mot_de_passe_hash = generate_password_hash(
            donnees["mot_de_passe"], method="pbkdf2:sha256"
        )

    db.session.commit()
    return jsonify(utilisateur_vers_dict(utilisateur)), 200
