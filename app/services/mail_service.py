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

    # 2. Version HTML Transactionnelle Haute Fidélité (Design Moderne Galaxy Solutions)
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{sujet}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #0b0f19; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased; color: #334155;">
    <!-- Container Global -->
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #0b0f19; padding: 40px 16px;">
        <tr>
            <td align="center">
                <!-- Carte Principale -->
                <table role="presentation" width="100%" style="max-width: 580px; background-color: #ffffff; border-radius: 16px; overflow: hidden; border: 1px solid #1e293b; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.4);">
                    
                    <!-- En-tête élégant Dark & Orange -->
                    <tr>
                        <td style="background-color: #0f172a; padding: 28px 36px; text-align: left; border-bottom: 3px solid #F26B1F;">
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                <tr>
                                    <td style="vertical-align: middle;">
                                        <table role="presentation" cellspacing="0" cellpadding="0">
                                            <tr>
                                                <td style="width: 40px; height: 40px; background-color: #0b0f19; border: 1px solid #334155; border-radius: 10px; text-align: center; vertical-align: middle; padding: 4px;">
                                                    <svg width="32" height="32" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" style="display: block; margin: 0 auto;">
                                                        <path d="M72 34C67 25 58 20 48 20C32.5 20 20 32.5 20 48C20 63.5 32.5 76 48 76C62 76 74 65 75.8 51H50V41H86C86 68 68 86 48 86C27 86 10 69 10 48C10 27 27 10 48 10C61 10 73 17 80 28L72 34Z" fill="#F26B1F"/>
                                                        <rect x="36" y="52" width="6" height="14" rx="3" fill="#F26B1F" opacity="0.6"/>
                                                        <rect x="46" y="44" width="6" height="22" rx="3" fill="#F26B1F" opacity="0.8"/>
                                                        <rect x="56" y="34" width="6" height="32" rx="3" fill="#F26B1F"/>
                                                    </svg>
                                                </td>
                                                <td style="padding-left: 14px; vertical-align: middle;">
                                                    <div style="color: #ffffff; font-size: 18px; font-weight: 700; letter-spacing: -0.02em; line-height: 1.2;">Galaxy Training Manager</div>
                                                    <div style="color: #94a3b8; font-size: 12px; font-weight: 500;">Plateforme de Pilotage des Formations</div>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Corps du message -->
                    <tr>
                        <td style="padding: 36px 36px 28px 36px;">
                            <h1 style="margin: 0 0 16px 0; font-size: 20px; font-weight: 700; color: #0f172a; line-height: 1.3;">
                                Bienvenue sur votre nouvel espace GTM
                            </h1>
                            
                            <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.6; color: #334155;">
                                Bonjour <strong>{nom_affiche}</strong>,
                            </p>
                            
                            <p style="margin: 0 0 24px 0; font-size: 14px; line-height: 1.6; color: #475569;">
                                Un compte utilisateur a été créé pour vous par l'administrateur de <strong>Galaxy Solutions</strong>. Pour commencer à piloter vos formations et sessions, veuillez activer votre accès en définissant votre mot de passe personnel.
                            </p>

                            <!-- Bouton Call to Action Principal -->
                            <table role="presentation" cellspacing="0" cellpadding="0" width="100%" style="margin: 28px 0;">
                                <tr>
                                    <td align="center">
                                        <table role="presentation" cellspacing="0" cellpadding="0">
                                            <tr>
                                                <td align="center" style="border-radius: 10px; background-color: #F26B1F; box-shadow: 0 4px 12px rgba(242, 107, 31, 0.35);">
                                                    <a href="{url_activation}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 14px; font-weight: 600; color: #ffffff; text-decoration: none; border-radius: 10px; background-color: #F26B1F; letter-spacing: 0.02em;">
                                                        Activer mon compte &rarr;
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>

                            <!-- Encadré Durée de validité -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; margin: 20px 0;">
                                <tr>
                                    <td style="padding: 14px 18px;">
                                        <div style="font-size: 13px; font-weight: 600; color: #0f172a; margin-bottom: 4px;">
                                            &#9201; Durée de validité : 48 heures
                                        </div>
                                        <div style="font-size: 12px; line-height: 1.5; color: #64748b;">
                                            Ce lien sécurisé à usage unique expirera automatiquement au-delà de ce délai.
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <!-- Sécurité & Rôles -->
                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-top: 16px;">
                                <tr>
                                    <td style="font-size: 12px; color: #047857; font-weight: 600; padding: 4px 0;">
                                        &#128274; Environnement sécurisé SSL &bull; Contrôle d'accès RBAC
                                    </td>
                                </tr>
                            </table>

                            <!-- Lien de secours textuel -->
                            <p style="margin: 24px 0 0 0; padding-top: 18px; border-top: 1px solid #f1f5f9; font-size: 12px; line-height: 1.6; color: #94a3b8;">
                                Si le bouton ne fonctionne pas, copiez et collez cette URL dans votre navigateur :<br>
                                <a href="{url_activation}" style="color: #F26B1F; text-decoration: underline; word-break: break-all;">{url_activation}</a>
                            </p>
                        </td>
                    </tr>

                    <!-- Pied de page -->
                    <tr>
                        <td style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 20px 36px; text-align: center;">
                            <p style="margin: 0; font-size: 12px; color: #94a3b8; line-height: 1.5;">
                                &copy; Galaxy Solutions &bull; Plateforme GTM<br>
                                Ce message est automatique, merci de ne pas y répondre.
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

