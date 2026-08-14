# Ce fichier centralise l'import de tous les modèles.
# Il permet d'écrire "from app.models import Role, Formation, ..."
# ailleurs dans le code, au lieu de connaître le nom exact de chaque
# fichier (app.models.role, app.models.formation, etc.)
#
# L'ORDRE des imports n'a pas d'importance ici : SQLAlchemy résout les
# relations entre modèles (via les chaînes "Session", "Formation"...)
# seulement au moment où l'application démarre, pas à la lecture de ce fichier.

from app.models.role import Role
from app.models.domaine import Domaine
from app.models.utilisateur import Utilisateur
from app.models.formateur import Formateur
from app.models.formation import Formation
from app.models.client import Client
from app.models.participant import Participant
from app.models.session import Session
from app.models.inscription import Inscription
