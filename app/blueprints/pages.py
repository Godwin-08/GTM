"""
==============================================================================
Blueprint des Pages Web HTML — Architecture SPA / API REST
==============================================================================
Ce blueprint gère exclusivement le routage et le rendu des templates Jinja2 HTML.
Il applique une séparation stricte des responsabilités (SOC) :
- Aucune logique métier ni requête SQL lourde n'est exécutée ici.
- Les pages chargent les données de façon dynamique via fetch() vers l'API REST (/api/...).
- Il effectue l'aiguillage selon l'authentification et le rôle (ex: vue formateur vs vue admin/gestionnaire).
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

pages_bp = Blueprint('pages', __name__)


@pages_bp.route('/')
def index():
    """Point d'entrée racine : redirige l'utilisateur vers son tableau de bord approprié ou vers le login."""
    if current_user.is_authenticated:
        if current_user.a_role("formateur"):
            return redirect(url_for('pages.dashboard_formateur'))
        return redirect(url_for('pages.dashboard'))
    return redirect(url_for('pages.login_page'))


@pages_bp.route('/login')
def login_page():
    """Affiche la page de connexion de la plateforme."""
    return render_template('login.html')


@pages_bp.route('/activation/<token>')
def activation_page(token):
    """Affiche la page d'activation de compte et de définition du mot de passe initial."""
    return render_template('auth/activation.html', token=token)


@pages_bp.route('/logo-showcase')
def logo_showcase():
    """Page de présentation de l'identité visuelle et de la charte graphique de Galaxy Solutions."""
    return render_template('logo_showcase.html')


# =============================================================================
# Tableaux de bord
# =============================================================================

@pages_bp.route('/dashboard')
@login_required
def dashboard():
    """Tableau de bord de pilotage global (Direction, Administrateurs, Gestionnaires)."""
    if current_user.a_role("formateur"):
        return redirect(url_for('pages.dashboard_formateur'))
    return render_template('dashboard.html')


@pages_bp.route('/dashboard-formateur')
@login_required
def dashboard_formateur():
    """Tableau de bord personnel dédié au formateur connecté (ses sessions, ses indicateurs)."""
    if not current_user.a_role("formateur"):
        return redirect(url_for('pages.dashboard'))
    return render_template('dashboard_formateur.html')


# =============================================================================
# Catalogue & Sessions de Formation
# =============================================================================

@pages_bp.route('/formations')
@login_required
def formations():
    """Page de consultation et gestion du catalogue de formations."""
    return render_template('formations/liste.html')


@pages_bp.route('/formations/<int:formation_id>')
@login_required
def formation_detail(formation_id):
    """Page de détail d'une formation et historique de ses sessions."""
    return render_template('formations/detail.html', formation_id=formation_id)


@pages_bp.route('/sessions')
@login_required
def sessions():
    """Page de planification et suivi des sessions de formation."""
    return render_template('sessions/liste.html')


@pages_bp.route('/sessions/<int:session_id>')
@login_required
def session_detail(session_id):
    """Page de détail d'une session, gestion des inscriptions et feuille d'émargement."""
    return render_template('sessions/detail.html', session_id=session_id)


# =============================================================================
# Clients, Participants et Intervenants
# =============================================================================

@pages_bp.route('/clients')
@login_required
def clients():
    """Page de gestion du portefeuille d'entreprises clientes."""
    return render_template('clients/liste.html')


@pages_bp.route('/clients/<int:client_id>')
@login_required
def client_detail(client_id):
    """Page de fiche client, salariés rattachés et historique de participation."""
    return render_template('clients/detail.html', client_id=client_id)


@pages_bp.route('/formateurs')
@login_required
def formateurs():
    """Page de l'annuaire des formateurs et intervenants par domaine."""
    return render_template('formateurs/liste.html')


@pages_bp.route('/participants')
@login_required
def participants():
    """Page de la liste des apprenants et salariés inscrits."""
    return render_template('participants/liste.html')


@pages_bp.route('/participants/<int:participant_id>')
@login_required
def participant_detail(participant_id):
    """Page de parcours individuel d'un participant."""
    return render_template('participants/detail.html', participant_id=participant_id)


@pages_bp.route('/inscriptions')
@login_required
def inscriptions():
    """Page de suivi global des inscriptions et listes d'attente."""
    return render_template('inscriptions/liste.html')


# =============================================================================
# Administration, Notifications & Data Analytics (ACP)
# =============================================================================

@pages_bp.route('/notifications')
@login_required
def notifications():
    """Page du centre d'alertes et points d'attention."""
    if current_user.a_role("formateur"):
        return redirect(url_for('pages.dashboard_formateur'))
    return render_template('notifications.html')


@pages_bp.route('/utilisateurs')
@login_required
def utilisateurs():
    """Page d'administration des comptes utilisateurs et habilitations RBAC."""
    return render_template('utilisateurs/liste.html')


@pages_bp.route('/utilisateurs/<int:utilisateur_id>')
@login_required
def utilisateur_detail(utilisateur_id):
    """Page de profil et modification d'un compte utilisateur."""
    return render_template('utilisateurs/detail.html', utilisateur_id=utilisateur_id)


@pages_bp.route('/domaines')
@login_required
def domaines():
    """Page de gestion et d'administration des domaines d'expertise métier."""
    if current_user.a_role("formateur"):
        return redirect(url_for('pages.dashboard_formateur'))
    return render_template('domaines/liste.html')


@pages_bp.route('/analytics/acp')
@login_required
def analytics_acp():
    """Page d'Analyse en Composantes Principales (Plan factoriel interactif, cos², corrélations)."""
    if current_user.a_role("formateur"):
        return redirect(url_for('pages.dashboard_formateur'))
    return render_template('analytics/acp.html')






