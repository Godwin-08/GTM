"""Tests unitaires et d'intégration pour le service d'envoi d'e-mails d'onboarding."""

import unittest
from unittest.mock import patch, MagicMock
import smtplib
from werkzeug.security import generate_password_hash

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Utilisateur, Role
from app.services.mail_service import (
    generer_contenu_invitation,
    envoyer_invitation_activation,
)


class MailServiceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_database_uri = Config.SQLALCHEMY_DATABASE_URI
        Config.SQLALCHEMY_DATABASE_URI = "sqlite://"
        cls.app = create_app()
        cls.app.config.update(TESTING=True)

    @classmethod
    def tearDownClass(cls):
        Config.SQLALCHEMY_DATABASE_URI = cls.original_database_uri

    def setUp(self):
        self.context = self.app.app_context()
        self.context.push()
        db.drop_all()
        db.create_all()

        self.admin_role = Role(nom="admin")
        self.gestionnaire_role = Role(nom="gestionnaire")
        db.session.add_all([self.admin_role, self.gestionnaire_role])
        db.session.flush()

        self.admin = Utilisateur(
            nom="Admin User",
            email="admin@test.ma",
            mot_de_passe_hash=generate_password_hash("Secret123"),
            role=self.admin_role,
            actif=True,
        )
        db.session.add(self.admin)
        db.session.commit()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        self.context.pop()

    def connecter_admin(self):
        with self.client.session_transaction() as session:
            session["_user_id"] = str(self.admin.id)
            session["_fresh"] = True

    def test_generation_contenu_invitation(self):
        """Vérifie la présence des éléments textuels et HTML indispensables."""
        url_test = "http://localhost:5000/activation/mon-super-token-123"
        sujet, texte, html = generer_contenu_invitation("Sofia Amrani", url_test)

        self.assertEqual(sujet, "Invitation à rejoindre Galaxy Training Manager")
        self.assertIn("Sofia Amrani", texte)
        self.assertIn(url_test, texte)
        self.assertIn("48 heures", texte)

        self.assertIn("Sofia Amrani", html)
        self.assertIn(url_test, html)
        self.assertIn("#047857", html)  # Couleur Emerald GTM
        self.assertIn("Activer mon compte", html)

    def test_envoi_mode_console_sans_smtp(self):
        """En mode console (par défaut), l'envoi réussit sans aucun serveur SMTP configuré."""
        res = envoyer_invitation_activation(
            destinataire_email="nouveau@test.ma",
            nom_utilisateur="Nouveau Collaborateur",
            url_activation="http://localhost:5000/activation/token-abc",
            config_override={"MAIL_BACKEND": "console"},
        )
        self.assertTrue(res["succes"])
        self.assertEqual(res["mode"], "console")
        self.assertEqual(res["destinataire"], "nouveau@test.ma")

    @patch("smtplib.SMTP")
    def test_envoi_mode_smtp_succes(self, mock_smtp):
        """En mode SMTP, la connexion et l'envoi MIME sont déclenchés correctement."""
        instance_smtp = MagicMock()
        mock_smtp.return_value.__enter__.return_value = instance_smtp

        res = envoyer_invitation_activation(
            destinataire_email="gestionnaire@test.ma",
            nom_utilisateur="Yassine",
            url_activation="http://localhost:5000/activation/token-xyz",
            config_override={
                "MAIL_BACKEND": "smtp",
                "MAIL_SERVER": "smtp.mailtrap.io",
                "MAIL_PORT": 587,
                "MAIL_USE_TLS": True,
                "MAIL_USERNAME": "user123",
                "MAIL_PASSWORD": "pass123",
            },
        )
        self.assertTrue(res["succes"])
        self.assertEqual(res["mode"], "smtp")
        instance_smtp.starttls.assert_called_once()
        instance_smtp.login.assert_called_once_with("user123", "pass123")
        instance_smtp.send_message.assert_called_once()

    @patch("smtplib.SMTP")
    def test_envoi_mode_smtp_echec_isole_et_securise(self, mock_smtp):
        """Une panne SMTP renvoie succes=False sans lever d'exception non gérée."""
        mock_smtp.side_effect = smtplib.SMTPConnectError(421, b"Connection refused")

        res = envoyer_invitation_activation(
            destinataire_email="erreur@test.ma",
            nom_utilisateur="Test Erreur",
            url_activation="http://localhost:5000/activation/token-err",
            config_override={
                "MAIL_BACKEND": "smtp",
                "MAIL_SERVER": "smtp.injoignable.com",
                "MAIL_PORT": 587,
            },
        )
        self.assertFalse(res["succes"])
        self.assertEqual(res["mode"], "smtp")
        self.assertIn("erreur", res)

    @patch("app.routes.utilisateurs.envoyer_invitation_activation")
    def test_creation_compte_avec_panne_smtp_preserve_le_compte(self, mock_envoyer):
        """
        Comportement critique : Si SMTP échoue, le compte DOIT rester créé en base
        en statut 'en_attente', l'API renvoie 201 avec avertissement, et l'Admin peut
        copier le lien d'activation ou renvoyer l'invitation ultérieurement.
        """
        self.connecter_admin()
        mock_envoyer.return_value = {
            "succes": False,
            "mode": "smtp",
            "erreur": "Serveur SMTP temporairement indisponible",
        }

        res = self.client.post(
            "/api/utilisateurs",
            json={
                "nom": "Collaborateur SMTP Fail",
                "email": "smtp.fail@test.ma",
                "role_id": self.gestionnaire_role.id,
            },
        )
        # Statut 201 : le compte a bien été créé
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertEqual(data["statut"], "en_attente")
        self.assertFalse(data["actif"])
        self.assertFalse(data["email_envoye"])
        self.assertIn("avertissement_mail", data)
        self.assertIn("url_activation", data)

        # Vérification en base : l'utilisateur existe bien et est activable
        user_db = Utilisateur.query.filter_by(email="smtp.fail@test.ma").first()
        self.assertIsNotNone(user_db)
        self.assertFalse(user_db.actif)
        self.assertIsNotNone(user_db.token_activation_hash)


if __name__ == "__main__":
    unittest.main()

