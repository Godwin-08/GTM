from flask import Blueprint, render_template
from flask_login import login_required

# Ce blueprint gère uniquement l'affichage des pages HTML.
# Il ne contient aucune logique métier, aucune requête SQLAlchemy.
# Toutes les données réelles sont récupérées côté navigateur via fetch()
# vers les routes API existantes (/api/...).
pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/login')
def login_page():
    return render_template('login.html')

@pages_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@pages_bp.route('/formations')
@login_required
def formations():
    return render_template('formations/liste.html')

@pages_bp.route('/formations/<int:formation_id>')
@login_required
def formation_detail(formation_id):
    return render_template('formations/detail.html', formation_id=formation_id)

@pages_bp.route('/sessions')
@login_required
def sessions():
    return render_template('sessions/liste.html')

@pages_bp.route('/sessions/<int:session_id>')
@login_required
def session_detail(session_id):
    return render_template('sessions/detail.html', session_id=session_id)

@pages_bp.route('/clients')
@login_required
def clients():
    return render_template('clients/liste.html')

@pages_bp.route('/clients/<int:client_id>')
@login_required
def client_detail(client_id):
    return render_template('clients/detail.html', client_id=client_id)

@pages_bp.route('/formateurs')
@login_required
def formateurs():
    return render_template('formateurs/liste.html')

@pages_bp.route('/participants')
@login_required
def participants():
    return render_template('participants/liste.html')

@pages_bp.route('/participants/<int:participant_id>')
@login_required
def participant_detail(participant_id):
    return render_template('participants/detail.html', participant_id=participant_id)

@pages_bp.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html')

@pages_bp.route('/utilisateurs')
@login_required
def utilisateurs():
    return render_template('utilisateurs/liste.html')

@pages_bp.route('/utilisateurs/<int:utilisateur_id>')
@login_required
def utilisateur_detail(utilisateur_id):
    return render_template('utilisateurs/detail.html', utilisateur_id=utilisateur_id)
