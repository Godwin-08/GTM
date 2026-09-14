"""
Routes API pour la gestion administrative des utilisateurs et du cycle d'onboarding.

Ce module expose les endpoints RESTful (strictement réservés aux administrateurs) permettant :
- La consultation de la liste des comptes utilisateurs et leurs rôles.
- Le détail individuel d'un compte avec le profil formateur rattaché le cas échéant.
- La création de comptes avec génération de tokens sécurisés d'invitation/activation (Onboarding).
- Le renvoi d'e-mails d'invitation avec régénération de token.
- La modification des données de profil, statut d'activité et rôles (avec garde anti-auto-désactivation).
"""

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

# Déclaration du Blueprint Flask pour l'API d'administration des utilisateurs
utilisateurs_bp = Blueprint("utilisateurs", __name__, url_prefix="/api/utilisateurs")


def utilisateur_vers_dict(utilisateur):
    """
    Convertit un objet Utilisateur en dictionnaire JSON sécurisé.
    NOTE DE SÉCURITÉ : Le condensat de mot de passe (mot_de_passe_hash) n'est JAMAIS renvoyé.

    :param utilisateur: Instance SQLAlchemy d'Utilisateur.
    :return: Dictionnaire JSON représentant le compte utilisateur et son statut d'activation.
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
    """
    Renvoie la liste exhaustive des utilisateurs enregistrés dans la plateforme.
    Réservé au rôle Administrateur.
    """
    utilisateurs = Utilisateur.query.all()
    return jsonify([utilisateur_vers_dict(u) for u in utilisateurs]), 200


@utilisateurs_bp.route("/<int:utilisateur_id>", methods=["GET"])
@admin_required
def detail_utilisateur(utilisateur_id):
    """
    Renvoie les informations détaillées d'un compte utilisateur.
    Réservé au rôle Administrateur.
    """
    utilisateur = db.get_or_404(Utilisateur, utilisateur_id)
    return jsonify(utilisateur_vers_dict(utilisateur)), 200


@utilisateurs_bp.route("", methods=["POST"])
@admin_required
def creer_utilisateur():
    """
    Crée un nouveau compte utilisateur.
    Deux flux sont pris en charge :
    1. Flux direct : mot de passe fourni directement dans le corps de requête (scripts internes).
    2. Flux Onboarding standard : génération d'un token aléatoire sécurisé (48h), compte inactif,
       et envoi d'une invitation par courrier électronique avec lien d'activation.
    """
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
        # Création directe avec mot de passe immédiat
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
        # Flux d'invitation sécurisée par jeton chiffré
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
        base_url = current_app.config.get("APP_BASE_URL") or request.host_url.rstrip("/")
        url_complete = f"{base_url}/activation/{token_activation}"
        reponse["token_activation"] = token_activation
        reponse["url_activation"] = f"/activation/{token_activation}"

        # Expédition de l'e-mail d'invitation (SMTP ou journal Console)
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
    Génère un nouveau jeton d'activation valide 48h pour un utilisateur non encore activé
    et réexpédie l'e-mail d'invitation.
    """
    utilisateur = db.get_or_404(Utilisateur, utilisateur_id)

    if utilisateur.actif:
        return jsonify({"erreur": "Ce compte est déjà activé."}), 400

    token_brut, token_hash = generer_token_activation()
    utilisateur.token_activation_hash = token_hash
    utilisateur.expiration_token = calculer_expiration_activation(48)
    db.session.commit()

    base_url = current_app.config.get("APP_BASE_URL") or request.host_url.rstrip("/")
    url_complete = f"{base_url}/activation/{token_brut}"

    reponse = utilisateur_vers_dict(utilisateur)
    reponse["token_activation"] = token_brut
    reponse["url_activation"] = f"/activation/{token_brut}"
    reponse["message"] = f"Nouvelle invitation générée pour {utilisateur.email}."

    # Renvoi de la notification
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
    """
    Modifie les attributs d'un compte utilisateur (nom, email, rôle, statut actif, mot de passe).
    Intègre une protection contre l'auto-désactivation d'un administrateur connecté.
    """
    utilisateur = db.get_or_404(Utilisateur, utilisateur_id)
    donnees = request.get_json() or {}

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
        # Garde de sécurité : un administrateur ne peut pas désactiver son propre compte
        if utilisateur.id == current_user.id and donnees["actif"] is False:
            return jsonify({"erreur": "vous ne pouvez pas désactiver votre propre compte"}), 400
        utilisateur.actif = donnees["actif"]
    if "mot_de_passe" in donnees and donnees["mot_de_passe"]:
        utilisateur.mot_de_passe_hash = generate_password_hash(
            donnees["mot_de_passe"], method="pbkdf2:sha256"
        )

    db.session.commit()
    return jsonify(utilisateur_vers_dict(utilisateur)), 200
