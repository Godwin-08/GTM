"""
Service centralisé de calcul de l'Analyse en Composantes Principales (ACP) pour GTM.
Calcule la décomposition factorielle (individus clients × variables formations),
les corrélations, la qualité de représentation (cos²), la contribution aux axes
et produit une synthèse d'interprétation métier descriptive.

Méthodologie :
1. Construction de la matrice de comptage (Clients × Formations)
2. Centrage-réduction (Z-Score) avec sécurité sur variance nulle
3. Matrice de corrélation R et recherche des valeurs/vecteurs propres (Eigendecomposition)
4. Calcul des coordonnées factorielles, cos² et contributions (ctr)
5. Analyse descriptive métier (effets de taille, clients atypiques, paires proches)
"""

import numpy as np
import pandas as pd

from app.models import Client, Formation


def build_matrix():
    """
    Construit la matrice X : lignes = clients, colonnes = formations,
    valeurs = nombre d'inscriptions confirmées de ce client à cette formation.
    """
    clients = Client.query.all()
    formations = Formation.query.all()

    matrice = pd.DataFrame(
        0,
        index=[c.nom_entreprise for c in clients],
        columns=[f.titre for f in formations],
    )

    for client in clients:
        for participant in client.participants:
            for inscription in participant.inscriptions:
                if (
                    inscription.statut == "confirmee"
                    and inscription.session
                    and inscription.session.formation
                ):
                    formation_titre = inscription.session.formation.titre
                    if formation_titre in matrice.columns:
                        matrice.loc[client.nom_entreprise, formation_titre] += 1

    return matrice


def standardize(X):
    """
    Centrage-réduction (z-score).
    Exclut les colonnes sans variance (écart-type = 0).
    """
    if X.empty:
        return pd.DataFrame(index=X.index)

    moyennes = X.mean()
    ecarts_types = X.std(ddof=0)

    colonnes_valides = ecarts_types[ecarts_types > 0].index
    if len(colonnes_valides) == 0:
        return pd.DataFrame(index=X.index)

    Z = (X[colonnes_valides] - moyennes[colonnes_valides]) / ecarts_types[colonnes_valides]
    return Z.fillna(0.0)


def correlation_matrix(Z):
    """
    Matrice de corrélation R = (1/n) * Z^T * Z.
    """
    n = len(Z)
    if n == 0 or Z.empty:
        return pd.DataFrame()
    R = (1 / n) * Z.T.dot(Z)
    return R.fillna(0.0)


def eigendecomposition(R):
    """
    Valeurs propres et vecteurs propres de R.
    """
    if R.empty or R.shape[0] == 0 or R.shape[1] == 0:
        return np.array([]), np.array([[]])

    try:
        valeurs_propres, vecteurs_propres = np.linalg.eigh(R.values)
    except Exception:
        return np.array([]), np.array([[]])

    idx = np.argsort(valeurs_propres)[::-1]
    valeurs_propres = valeurs_propres[idx]
    valeurs_propres = np.maximum(valeurs_propres, 0)
    vecteurs_propres = vecteurs_propres[:, idx]

    return valeurs_propres, vecteurs_propres


def factor_coordinates(Z, vecteurs_propres):
    """
    Coordonnées factorielles des individus F = Z . v.
    """
    if Z.empty or vecteurs_propres.size == 0 or vecteurs_propres.shape[0] == 0:
        return pd.DataFrame(index=Z.index)

    composantes = Z.values @ vecteurs_propres
    F = pd.DataFrame(
        composantes,
        index=Z.index,
        columns=[f"F{i+1}" for i in range(composantes.shape[1])],
    )
    return F.fillna(0.0)


def explained_variance(valeurs_propres):
    """
    % de variance expliquée et cumulée.
    """
    total = np.sum(valeurs_propres)
    if total == 0 or len(valeurs_propres) == 0:
        return np.array([]), np.array([])
    pct_expliquee = valeurs_propres / total * 100
    pct_cumulee = np.cumsum(pct_expliquee)
    return pct_expliquee, pct_cumulee


def variable_coordinates(vecteurs_propres, valeurs_propres, noms_variables):
    """
    Corrélations variables-axes r(x_j, F_k) = v_jk * sqrt(lambda_k).
    """
    if vecteurs_propres.size == 0 or len(valeurs_propres) == 0:
        return pd.DataFrame(index=noms_variables)

    correlations = vecteurs_propres * np.sqrt(valeurs_propres)
    corr_df = pd.DataFrame(
        correlations,
        index=noms_variables,
        columns=[f"F{i+1}" for i in range(len(valeurs_propres))],
    )
    return corr_df.fillna(0.0)


def compute_cos2_variables(corr_df):
    """
    Qualité de représentation des variables (cos²).
    """
    if corr_df.empty:
        return pd.DataFrame(index=corr_df.index)

    F = corr_df.values
    norme2 = np.sum(F**2, axis=1)
    norme2 = np.where(norme2 == 0, 1e-10, norme2)

    cos2_f1 = (F[:, 0]**2) / norme2 if F.shape[1] >= 1 else np.zeros(len(corr_df))
    cos2_f2 = (F[:, 1]**2) / norme2 if F.shape[1] >= 2 else np.zeros(len(corr_df))

    return pd.DataFrame({
        "cos2_F1": np.nan_to_num(cos2_f1),
        "cos2_F2": np.nan_to_num(cos2_f2),
    }, index=corr_df.index)


def compute_cos2_individus(F_df):
    """
    Qualité de représentation des individus (cos²).
    """
    if F_df.empty:
        return pd.DataFrame(index=F_df.index)

    coords = F_df.values
    norme2 = np.sum(coords**2, axis=1)
    norme2 = np.where(norme2 == 0, 1e-10, norme2)

    cos2_f1 = (coords[:, 0]**2) / norme2 if coords.shape[1] >= 1 else np.zeros(len(F_df))
    cos2_f2 = (coords[:, 1]**2) / norme2 if coords.shape[1] >= 2 else np.zeros(len(F_df))

    return pd.DataFrame({
        "cos2_F1": np.nan_to_num(cos2_f1),
        "cos2_F2": np.nan_to_num(cos2_f2),
    }, index=F_df.index)


def compute_contributions_variables(corr_df, valeurs_propres):
    """
    Contribution des variables aux axes.
    """
    if corr_df.empty or len(valeurs_propres) == 0:
        return pd.DataFrame(index=corr_df.index)

    lambda_1 = valeurs_propres[0] if len(valeurs_propres) >= 1 and valeurs_propres[0] > 1e-10 else 1e-10
    lambda_2 = valeurs_propres[1] if len(valeurs_propres) >= 2 and valeurs_propres[1] > 1e-10 else 1e-10

    ctr_f1 = (corr_df["F1"]**2 / lambda_1) * 100 if "F1" in corr_df.columns else np.zeros(len(corr_df))
    ctr_f2 = (corr_df["F2"]**2 / lambda_2) * 100 if "F2" in corr_df.columns else np.zeros(len(corr_df))

    return pd.DataFrame({
        "ctr_F1": np.nan_to_num(ctr_f1),
        "ctr_F2": np.nan_to_num(ctr_f2),
    }, index=corr_df.index)


def compute_contributions_individus(F_df, valeurs_propres):
    """
    Contribution des individus aux axes.
    """
    if F_df.empty or len(valeurs_propres) == 0:
        return pd.DataFrame(index=F_df.index)

    n = len(F_df)
    poids = 1 / n if n > 0 else 0

    lambda_1 = valeurs_propres[0] if len(valeurs_propres) >= 1 and valeurs_propres[0] > 1e-10 else 1e-10
    lambda_2 = valeurs_propres[1] if len(valeurs_propres) >= 2 and valeurs_propres[1] > 1e-10 else 1e-10

    ctr_f1 = poids * (F_df["F1"]**2) / lambda_1 * 100 if "F1" in F_df.columns else np.zeros(len(F_df))
    ctr_f2 = poids * (F_df["F2"]**2) / lambda_2 * 100 if "F2" in F_df.columns else np.zeros(len(F_df))

    return pd.DataFrame({
        "ctr_F1": np.nan_to_num(ctr_f1),
        "ctr_F2": np.nan_to_num(ctr_f2),
    }, index=F_df.index)


def filter_reliable_clients(clients, seuil=0.5):
    return [c for c in clients if (c.get("cos2_f1", 0) + c.get("cos2_f2", 0)) >= seuil]


def find_distinct_client(clients_fiables):
    if len(clients_fiables) < 3:
        return None

    centroide_f1 = sum(c["f1"] for c in clients_fiables) / len(clients_fiables)
    centroide_f2 = sum(c["f2"] for c in clients_fiables) / len(clients_fiables)

    distances = [
        (c, ((c["f1"] - centroide_f1) ** 2 + (c["f2"] - centroide_f2) ** 2) ** 0.5)
        for c in clients_fiables
    ]
    distances.sort(key=lambda x: x[1], reverse=True)

    client_le_plus_eloigne, distance_max = distances[0]
    autres_distances = [d for _, d in distances[1:]]

    moyenne_autres = sum(autres_distances) / len(autres_distances)
    ecart_type_autres = (
        sum((d - moyenne_autres) ** 2 for d in autres_distances) / len(autres_distances)
    ) ** 0.5

    if ecart_type_autres > 0:
        z_score = (distance_max - moyenne_autres) / ecart_type_autres
    else:
        z_score = 0

    if z_score >= 1.5:
        niveau = "fort"
    elif z_score >= 0.5:
        niveau = "modere"
    else:
        return None

    return {"nom": client_le_plus_eloigne["nom"], "niveau": niveau}


def find_closest_pair(clients_fiables):
    if len(clients_fiables) < 4:
        return None

    distances = []
    for i in range(len(clients_fiables)):
        for j in range(i + 1, len(clients_fiables)):
            a, b = clients_fiables[i], clients_fiables[j]
            d = ((a["f1"] - b["f1"]) ** 2 + (a["f2"] - b["f2"]) ** 2) ** 0.5
            distances.append((d, a, b))

    if not distances:
        return None

    distances.sort(key=lambda x: x[0])
    distance_min, client_a, client_b = distances[0]

    autres_distances = [d for d, _, _ in distances[1:]]
    moyenne_autres = sum(autres_distances) / len(autres_distances)
    ecart_type_autres = (
        sum((d - moyenne_autres) ** 2 for d in autres_distances) / len(autres_distances)
    ) ** 0.5

    if ecart_type_autres > 0:
        z_score = (moyenne_autres - distance_min) / ecart_type_autres
    else:
        z_score = 0

    if z_score >= 1.5:
        niveau = "fort"
    elif z_score >= 0.5:
        niveau = "modere"
    else:
        return None

    return {"client_a": client_a["nom"], "client_b": client_b["nom"], "niveau": niveau}


def interpret_axis(formations, axe="f1"):
    if not formations:
        return {"positif": [], "negatif": [], "effet_taille": False}

    nb_formations = len(formations)
    seuil = (100 / nb_formations) * 1.5

    cle_ctr = f"ctr_{axe}"
    cle_coord = axe

    formations_significatives = [f for f in formations if f.get(cle_ctr, 0) >= seuil]
    formations_significatives.sort(key=lambda f: f.get(cle_ctr, 0), reverse=True)

    positives = [f["titre"] for f in formations_significatives if f.get(cle_coord, 0) > 0]
    negatives = [f["titre"] for f in formations_significatives if f.get(cle_coord, 0) < 0]

    toutes_coords = [f.get(cle_coord, 0) for f in formations]
    effet_taille_global = (all(c >= 0 for c in toutes_coords) or all(c <= 0 for c in toutes_coords)) if toutes_coords else False
    effet_taille = effet_taille_global or (bool(positives) != bool(negatives))

    return {
        "positif": positives[:3],
        "negatif": negatives[:3],
        "effet_taille": effet_taille,
    }


def build_business_summary(resultats_acp):
    clients = resultats_acp.get("clients", [])
    formations = resultats_acp.get("formations", [])
    clients_fiables = filter_reliable_clients(clients)

    return {
        "nb_clients_analyses": len(clients),
        "nb_clients_fiables": len(clients_fiables),
        "client_distinct": find_distinct_client(clients_fiables),
        "paire_proche": find_closest_pair(clients_fiables),
        "axe_1": interpret_axis(formations, axe="f1"),
        "axe_2": interpret_axis(formations, axe="f2"),
        "peut_conclure": len(clients_fiables) >= 3,
        "avertissement_methode": (
            "Ces résultats sont issus d'une analyse factorielle descriptive ("
            "Analyse en Composantes Principales). Elle constitue un outil "
            "d'exploration visuelle et de synthèse, et non un modèle prédictif."
        ) if len(clients_fiables) < 15 else None,
    }


def get_acp_complete():
    """
    Exécute l'analyse ACP complète descriptive et renvoie une structure JSON sécurisée.
    """
    X = build_matrix()
    if X.empty:
        return {
            "nb_clients": 0,
            "nb_formations": 0,
            "valeurs_propres": [],
            "variance_expliquee": {"par_axe": [], "cumulee": []},
            "clients": [],
            "formations": [],
            "interpretation": {
                "nb_clients_analyses": 0,
                "nb_clients_fiables": 0,
                "client_distinct": None,
                "paire_proche": None,
                "axe_1": {"positif": [], "negatif": [], "effet_taille": False},
                "axe_2": {"positif": [], "negatif": [], "effet_taille": False},
                "peut_conclure": False,
                "avertissement_methode": "Données insuffisantes pour l'analyse ACP.",
            },
        }

    Z = standardize(X)
    if Z.empty:
        return {
            "nb_clients": X.shape[0],
            "nb_formations": X.shape[1],
            "valeurs_propres": [],
            "variance_expliquee": {"par_axe": [], "cumulee": []},
            "clients": [],
            "formations": [],
            "interpretation": {
                "nb_clients_analyses": X.shape[0],
                "nb_clients_fiables": 0,
                "client_distinct": None,
                "paire_proche": None,
                "axe_1": {"positif": [], "negatif": [], "effet_taille": False},
                "axe_2": {"positif": [], "negatif": [], "effet_taille": False},
                "peut_conclure": False,
                "avertissement_methode": "Variance nulle sur l'ensemble des formations.",
            },
        }

    R = correlation_matrix(Z)
    valeurs_propres, vecteurs_propres = eigendecomposition(R)
    F = factor_coordinates(Z, vecteurs_propres)
    pct_expliquee, pct_cumulee = explained_variance(valeurs_propres)
    corr_df = variable_coordinates(vecteurs_propres, valeurs_propres, Z.columns)

    cos2_variables = compute_cos2_variables(corr_df)
    cos2_individus = compute_cos2_individus(F)
    ctr_variables = compute_contributions_variables(corr_df, valeurs_propres)
    ctr_individus = compute_contributions_individus(F, valeurs_propres)

    resultats = {
        "nb_clients": X.shape[0],
        "nb_formations": Z.shape[1],
        "valeurs_propres": [round(float(v), 4) for v in valeurs_propres if not np.isnan(v)],
        "variance_expliquee": {
            "par_axe": [round(float(v), 2) for v in pct_expliquee if not np.isnan(v)],
            "cumulee": [round(float(v), 2) for v in pct_cumulee if not np.isnan(v)],
        },
        "clients": [
            {
                "nom": nom,
                "f1": round(float(F.loc[nom, "F1"]), 3) if "F1" in F.columns and not np.isnan(F.loc[nom, "F1"]) else 0.0,
                "f2": round(float(F.loc[nom, "F2"]), 3) if "F2" in F.columns and not np.isnan(F.loc[nom, "F2"]) else 0.0,
                "cos2_f1": round(float(cos2_individus.loc[nom, "cos2_F1"]), 3) if "cos2_F1" in cos2_individus.columns and not np.isnan(cos2_individus.loc[nom, "cos2_F1"]) else 0.0,
                "cos2_f2": round(float(cos2_individus.loc[nom, "cos2_F2"]), 3) if "cos2_F2" in cos2_individus.columns and not np.isnan(cos2_individus.loc[nom, "cos2_F2"]) else 0.0,
                "ctr_f1": round(float(ctr_individus.loc[nom, "ctr_F1"]), 2) if "ctr_F1" in ctr_individus.columns and not np.isnan(ctr_individus.loc[nom, "ctr_F1"]) else 0.0,
                "ctr_f2": round(float(ctr_individus.loc[nom, "ctr_F2"]), 2) if "ctr_F2" in ctr_individus.columns and not np.isnan(ctr_individus.loc[nom, "ctr_F2"]) else 0.0,
            }
            for nom in F.index
        ],
        "formations": [
            {
                "titre": titre,
                "f1": round(float(corr_df.loc[titre, "F1"]), 3) if "F1" in corr_df.columns and not np.isnan(corr_df.loc[titre, "F1"]) else 0.0,
                "f2": round(float(corr_df.loc[titre, "F2"]), 3) if "F2" in corr_df.columns and not np.isnan(corr_df.loc[titre, "F2"]) else 0.0,
                "cos2_f1": round(float(cos2_variables.loc[titre, "cos2_F1"]), 3) if "cos2_F1" in cos2_variables.columns and not np.isnan(cos2_variables.loc[titre, "cos2_F1"]) else 0.0,
                "cos2_f2": round(float(cos2_variables.loc[titre, "cos2_F2"]), 3) if "cos2_F2" in cos2_variables.columns and not np.isnan(cos2_variables.loc[titre, "cos2_F2"]) else 0.0,
                "ctr_f1": round(float(ctr_variables.loc[titre, "ctr_F1"]), 2) if "ctr_F1" in ctr_variables.columns and not np.isnan(ctr_variables.loc[titre, "ctr_F1"]) else 0.0,
                "ctr_f2": round(float(ctr_variables.loc[titre, "ctr_F2"]), 2) if "ctr_F2" in ctr_variables.columns and not np.isnan(ctr_variables.loc[titre, "ctr_F2"]) else 0.0,
            }
            for titre in corr_df.index
        ],
    }

    resultats["interpretation"] = build_business_summary(resultats)
    return resultats


# Alias pour compatibilité
get_acp_clients = get_acp_complete
