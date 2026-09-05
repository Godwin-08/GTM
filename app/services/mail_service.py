"""
Service d'envoi de courriels transactionnels pour Galaxy Training Manager (GTM).
Supporte deux modes d'exécution :
- 'console' (mode local / démo / soutenance) : formatage complet et affichage dans les logs sans dépendance SMTP
- 'smtp' (mode production) : envoi réel via smtplib (SSL / TLS) avec configuration sécurisée par variables d'environnement
"""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger("gtm.mail")


def generer_contenu_invitation(nom_utilisateur: str, url_activation: str) -> Tuple[str, str, str]:
    """
    Génère le sujet, la version texte brut et la version HTML responsive de l'invitation.
    Charte visuelle : Emerald Graphite (Galaxy Solutions).
    """
    sujet = "Invitation à rejoindre Galaxy Training Manager"

    nom_affiche = nom_utilisateur.strip() if nom_utilisateur else "Collaborateur"

    # 1. Version Texte Brut
    texte_brut = f"""Bonjour {nom_affiche},

Un compte utilisateur a été créé pour vous sur la plateforme Galaxy Training Manager (GTM).

Pour finaliser votre inscription et accéder à votre espace de formation, veuillez définir votre mot de passe personnel en vous rendant sur l'adresse suivante :

{url_activation}

Ce lien sécurisé à usage unique est valable pendant 48 heures.

Si vous n'êtes pas à l'origine de cette demande, veuillez ignorer ce message.

Cordialement,
L'équipe Galaxy Solutions
Plateforme GTM — https://galaxysolutions.ma
"""

    # 2. Version HTML Transactionnelle Haute Fidélité
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{sujet}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #334155;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #0f172a; padding: 40px 16px;">
        <tr>
            <td align="center">
                <table role="presentation" width="100%" style="max-width: 580px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);">
                    
                    <!-- En-tête de marque Emerald Graphite -->
                    <tr>
                        <td style="background-color: #047857; padding: 32px 40px; text-align: left;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td>
                                        <div style="display: inline-block; width: 36px; height: 36px; line-height: 36px; background-color: #F26B1F; border-radius: 8px; text-align: center; color: #ffffff; font-weight: bold; font-size: 18px; vertical-align: middle;">G</div>
                                        <span style="color: #ffffff; font-size: 20px; font-weight: 700; margin-left: 12px; vertical-align: middle; letter-spacing: -0.025em;">Galaxy Training Manager</span>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Corps du message -->
                    <tr>
                        <td style="padding: 40px 40px 32px 40px;">
                            <h1 style="margin: 0 0 16px 0; font-size: 22px; font-weight: 700; color: #0f172a; line-height: 1.3;">
                                Bienvenue sur votre nouvel espace GTM
                            </h1>
                            
                            <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 1.6; color: #475569;">
                                Bonjour <strong>{nom_affiche}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 24px 0; font-size: 14px; line-height: 1.6; color: #475569;">
                                Un compte a été configuré pour vous par l'administrateur de <strong>Galaxy Solutions</strong>. Pour commencer à piloter vos formations et sessions, veuillez activer votre accès en définissant votre mot de passe personnel.
                            </p>

                            <!-- Bouton Call to Action -->
                            <table role="presentation" cellspacing="0" cellpadding="0" style="margin: 32px 0;">
                                <tr>
                                    <td align="center" style="border-radius: 10px; background-color: #047857;">
                                        <a href="{url_activation}" target="_blank" style="display: inline-block; padding: 14px 28px; font-size: 14px; font-weight: 600; color: #ffffff; text-decoration: none; border-radius: 10px; background-color: #047857; letter-spacing: 0.01em;">
                                            Activer mon compte &rarr;
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- Encadré durée de validité -->
                            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; margin: 24px 0 0 0;">
                                <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 600; color: #0f172a;">
                                    &#9201; Durée de validité :
                                </p>
                                <p style="margin: 0; font-size: 12px; line-height: 1.5; color: #64748b;">
                                    Ce lien d'activation sécurisé à usage unique expire automatiquement dans <strong>48 heures</strong>.
                                </p>
                            </div>

                            <!-- Lien de secours textuel -->
                            <p style="margin: 24px 0 0 0; font-size: 12px; line-height: 1.5; color: #94a3b8;">
                                Si le bouton ne fonctionne pas, copiez et collez cette URL dans votre navigateur :<br>
                                <a href="{url_activation}" style="color: #047857; text-decoration: underline; word-break: break-all;">{url_activation}</a>
                            </p>
                        </td>
                    </tr>

                    <!-- Pied de page -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 24px 40px; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                                &copy; Galaxy Solutions — Plateforme GTM. Ce courriel a été envoyé automatiquement, merci de ne pas y répondre.
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return sujet, texte_brut, html


def envoyer_invitation_activation(
    destinataire_email: str,
    nom_utilisateur: str,
    url_activation: str,
    config_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Point d'entrée universel pour l'envoi de l'invitation d'activation.
    Gère le fallback console et l'envoi réel SMTP avec gestion d'erreurs étanche.
    """
    from flask import current_app

    config = {}
    if current_app:
        config.update(current_app.config)
    if config_override:
        config.update(config_override)

    backend = config.get("MAIL_BACKEND", "console").lower()
    expediteur = config.get("MAIL_FROM", "Galaxy Training Manager <no-reply@galaxysolutions.ma>")

    sujet, texte_brut, html = generer_contenu_invitation(nom_utilisateur, url_activation)

    # -------------------------------------------------------------
    # 1. MODE CONSOLE / DÉMO / LOCAL (Zéro dépendance externe)
    # -------------------------------------------------------------
    if backend != "smtp":
        logger.info(
            "\n" + "=" * 70 + "\n"
            "[GTM MAIL SERVICE — MODE CONSOLE / DÉMO]\n"
            f"Destinataire : {destinataire_email}\n"
            f"Nom          : {nom_utilisateur}\n"
            f"Sujet        : {sujet}\n"
            f"Lien Direct  : {url_activation}\n"
            "=" * 70
        )
        return {
            "succes": True,
            "mode": "console",
            "destinataire": destinataire_email,
            "sujet": sujet,
            "url_activation": url_activation,
        }

    # -------------------------------------------------------------
    # 2. MODE SMTP RÉEL (Production)
    # -------------------------------------------------------------
    serveur_smtp = config.get("MAIL_SERVER", "localhost")
    port = int(config.get("MAIL_PORT", 587))
    use_tls = bool(config.get("MAIL_USE_TLS", True))
    use_ssl = bool(config.get("MAIL_USE_SSL", False))
    utilisateur_smtp = config.get("MAIL_USERNAME")
    mot_de_passe_smtp = config.get("MAIL_PASSWORD")

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = sujet
        message["From"] = expediteur
        message["To"] = destinataire_email

        # Attache les 2 versions MIME
        part1 = MIMEText(texte_brut, "plain", "utf-8")
        part2 = MIMEText(html, "html", "utf-8")
        message.attach(part1)
        message.attach(part2)

        if use_ssl:
            with smtplib.SMTP_SSL(serveur_smtp, port, timeout=10) as serveur:
                if utilisateur_smtp and mot_de_passe_smtp:
                    serveur.login(utilisateur_smtp, mot_de_passe_smtp)
                serveur.send_message(message)
        else:
            with smtplib.SMTP(serveur_smtp, port, timeout=10) as serveur:
                if use_tls:
                    serveur.starttls()
                if utilisateur_smtp and mot_de_passe_smtp:
                    serveur.login(utilisateur_smtp, mot_de_passe_smtp)
                serveur.send_message(message)

        logger.info("E-mail d'invitation envoyé avec succès via SMTP à %s", destinataire_email)
        return {
            "succes": True,
            "mode": "smtp",
            "destinataire": destinataire_email,
            "sujet": sujet,
            "url_activation": url_activation,
        }

    except Exception as exc:
        # Journalisation sécurisée sans exposer les identifiants
        logger.error(
            "Échec de l'envoi du courriel d'activation à %s via SMTP (%s:%d) : %s",
            destinataire_email,
            serveur_smtp,
            port,
            exc,
        )
        return {
            "succes": False,
            "mode": "smtp",
            "erreur": "Échec de l'acheminement de l'e-mail d'invitation via le serveur SMTP.",
            "url_activation": url_activation,
        }

