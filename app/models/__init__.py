"""
==============================================================================
Package des Modèles de Données SQLAlchemy — Galaxy Training Manager (GTM)
==============================================================================
Ce module centralise l'export de l'ensemble des entités relationnelles.
Il simplifie les imports dans l'application :
`from app.models import Client, Formation, Session, ...`

Les relations de clés étrangères et back_populates sont résolues dynamiquement
par SQLAlchemy au moment de l'initialisation de l'application.
"""

from app.models.role import Role
from app.models.domaine import Domaine
from app.models.utilisateur import Utilisateur
from app.models.formateur import Formateur
from app.models.formation import Formation
from app.models.client import Client
from app.models.participant import Participant
from app.models.session import Session
from app.models.inscription import Inscription

