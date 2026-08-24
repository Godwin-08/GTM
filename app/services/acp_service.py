"""
Service qui calcule l'Analyse en Composantes Principales (ACP)
des clients selon leur profil de consommation de formations.

Méthodologie :
- Matrice Clients × Formations (comptage des inscriptions confirmées)
- Filtrage des colonnes avec au moins une inscription pour la robustesse
- Standardisation (centrage-réduction) via StandardScaler
- ACP sur 2 composantes principales (PC1, PC2) via Scikit-Learn
"""

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from app.models import Client, Formation, Inscription, Session


def get_acp_clients():
    """
    Calcule la projection ACP des clients sur 2 axes (PC1, PC2),
    à partir de leur nombre d'inscriptions confirmées par formation.

    Retourne un dict avec :
    - variance_expliquee : {pc1: float, pc2: float, cumulee: float}
    - clients : liste de {nom, pc1, pc2}
    - matrice_utilisee : dimensions de la matrice (nb_clients, nb_formations)
    """
    clients = Client.query.all()
    formations = Formation.query.all()

    if not clients or not formations:
        return {
            "variance_expliquee": {"pc1": 0.0, "pc2": 0.0, "cumulee": 0.0},
            "clients": [],
            "matrice_utilisee": {"nb_clients": 0, "nb_formations": 0},
        }

    # --- 1. Construction de la matrice Clients x Formations ---
    matrice = pd.DataFrame(
        0,
        index=[c.nom_entreprise for c in clients],
        columns=[f.titre for f in formations],
    )

    for client in clients:
        for participant in client.participants:
            for inscription in participant.inscriptions:
                if inscription.statut == "confirmee" and inscription.session and inscription.session.formation:
                    formation_titre = inscription.session.formation.titre
                    if formation_titre in matrice.columns:
                        matrice.loc[client.nom_entreprise, formation_titre] += 1

    # --- Robustesse : ne conserver que les formations ayant au moins 1 inscription confirmée ---
    formations_actives = [col for col in matrice.columns if matrice[col].sum() > 0]
    if len(formations_actives) >= 2:
        matrice_acp = matrice[formations_actives]
    else:
        matrice_acp = matrice

    # --- 2. Standardisation (centrage-réduction) ---
    scaler = StandardScaler()
    matrice_standardisee = scaler.fit_transform(matrice_acp)

    # --- 3. ACP sur 2 composantes ---
    n_components = min(2, matrice_standardisee.shape[1], matrice_standardisee.shape[0])
    acp = PCA(n_components=n_components)
    coordonnees = acp.fit_transform(matrice_standardisee)

    variance_pc1 = round(float(acp.explained_variance_ratio_[0] * 100), 1) if n_components >= 1 else 0.0
    variance_pc2 = round(float(acp.explained_variance_ratio_[1] * 100), 1) if n_components >= 2 else 0.0
    variance_cumulee = round(variance_pc1 + variance_pc2, 1)

    # --- 4. Formatage du résultat pour le frontend ---
    clients_projetes = [
        {
            "nom": nom_client,
            "pc1": round(float(coordonnees[i, 0]), 2) if n_components >= 1 else 0.0,
            "pc2": round(float(coordonnees[i, 1]), 2) if n_components >= 2 else 0.0,
        }
        for i, nom_client in enumerate(matrice_acp.index)
    ]

    return {
        "variance_expliquee": {
            "pc1": variance_pc1,
            "pc2": variance_pc2,
            "cumulee": variance_cumulee,
        },
        "clients": clients_projetes,
        "matrice_utilisee": {
            "nb_clients": matrice_acp.shape[0],
            "nb_formations": matrice_acp.shape[1],
        },
    }
