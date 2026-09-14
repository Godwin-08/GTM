"""
==============================================================================
Service d'Analyse en Composantes Principales (ACP) — Galaxy Training Manager
==============================================================================
Ce module implémente de bout en bout l'Analyse en Composantes Principales (ACP)
normée pour explorer les relations entre les Entreprises Clientes (individus)
et les Formations suivies (variables).

Formulation mathématique et étapes algorithmiques :
1. Construction de la matrice brute des effectifs $X$ (taille $n \times p$)
2. Centrage et réduction de la matrice pour obtenir $Z$ ($Z = \frac{X - \mu}{\sigma}$)
3. Calcul de la matrice des corrélations $R = \frac{1}{n} Z^T Z$
4. Décomposition spectrale de $R$ : résolution des couples $(\lambda_k, v_k)$
5. Projection factorielle des individus : $F = Z \cdot V$
6. Calcul des coordonnées et corrélations des variables : $r(x_j, F_k) = v_{jk} \sqrt{\lambda_k}$
7. Calcul des métriques d'aide à l'interprétation :
   - Cosinus carrés ($\cos^2$) : qualité de projection sur les axes
   - Contributions relatives ($CTR$) : part prise dans la construction de l'axe
8. Synthèse métier automatique : détection des clients singuliers (outliers),
   paires similaires et interprétation sémantique des axes factoriels.
"""

import numpy as np
import pandas as pd

from app.models import Client, Formation


def build_matrix():
    """
    Construit le tableau de contingence brut individus × variables.
    - Lignes (Individus) : Entreprises clientes ($n$).
    - Colonnes (Variables) : Formations du catalogue ($p$).
    - Valeurs $X_{ij}$ : Nombre total de salariés inscrits et confirmés du client $i$ à la formation $j$.
    
    :return: DataFrame pandas (index=noms_clients, colonnes=titres_formations)
    """
    clients = Client.query.all()
    formations = Formation.query.all()

    # Initialisation du tableau avec des zéros
    matrice = pd.DataFrame(
        0,
        index=[c.nom_entreprise for c in clients],
        columns=[f.titre for f in formations],
    )

    # Remplissage par agrégation des inscriptions confirmées
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
    Réalise le centrage et la réduction des variables (Z-score standardisation).
    Chaque variable $j$ est transformée selon :
    $$Z_{ij} = \frac{X_{ij} - \bar{X}_j}{\sigma_j}$$
    
    Sécurité : Les colonnes à variance nulle ($\sigma_j = 0$) sont automatiquement
    écartées pour éviter les divisions par zéro.
    
    :param X: DataFrame brute des données
    :return: DataFrame Z des données centrées-réduites
    """
    if X.empty:
        return pd.DataFrame(index=X.index)

    # Calcul de la moyenne et de l'écart-type de population (ddof=0)
    moyennes = X.mean()
    ecarts_types = X.std(ddof=0)

    # Conservation des seules variables présentant une variabilité
    colonnes_valides = ecarts_types[ecarts_types > 0].index
    if len(colonnes_valides) == 0:
        return pd.DataFrame(index=X.index)

    Z = (X[colonnes_valides] - moyennes[colonnes_valides]) / ecarts_types[colonnes_valides]
    return Z.fillna(0.0)


def correlation_matrix(Z):
    """
    Calcule la matrice des corrélations linéaires $R$ (taille $p \times p$).
    $$R = \frac{1}{n} Z^T Z$$
    
    :param Z: DataFrame des données centrées-réduites
    :return: DataFrame R de corrélation
    """
    n = len(Z)
    if n == 0 or Z.empty:
        return pd.DataFrame()
    R = (1 / n) * Z.T.dot(Z)
    return R.fillna(0.0)


def eigendecomposition(R):
    """
    Effectue la décomposition spectrale (valeurs propres et vecteurs propres) de la matrice $R$.
    Les valeurs propres $\lambda_k$ mesurent la quantité de variance (inertie) expliquée par l'axe $k$.
    Les vecteurs propres $v_k$ définissent les directions principales d'inertie.
    
    Les résultats sont triés par ordre décroissant des valeurs propres.
    
    :param R: Matrice de corrélation
    :return: Tuple (valeurs_propres, vecteurs_propres)
    """
    if R.empty or R.shape[0] == 0 or R.shape[1] == 0:
        return np.array([]), np.array([[]])

    try:
        # np.linalg.eigh est optimisé pour les matrices réelles et symétriques
        valeurs_propres, vecteurs_propres = np.linalg.eigh(R.values)
    except Exception:
        return np.array([]), np.array([[]])

    # Tri par ordre décroissant d'inertie
    idx = np.argsort(valeurs_propres)[::-1]
    valeurs_propres = valeurs_propres[idx]
    # Tronquage des petites valeurs résiduelles négatives dues aux imprécisions flottantes
    valeurs_propres = np.maximum(valeurs_propres, 0)
    vecteurs_propres = vecteurs_propres[:, idx]

    return valeurs_propres, vecteurs_propres


def factor_coordinates(Z, vecteurs_propres):
    """
    Calcule les coordonnées factorielles des individus (scores des clients sur les axes) :
    $$F = Z \cdot V$$
    
    :param Z: DataFrame centrée-réduite
    :param vecteurs_propres: Matrice $V$ des vecteurs propres colonnes
    :return: DataFrame $F$ des coordonnées factorielles (colonnes F1, F2, ...)
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
    Calcule le pourcentage d'inertie expliquée par chaque axe et l'inertie cumulée :
    $$\tau_k = \frac{\lambda_k}{\sum \lambda} \times 100$$
    
    :param valeurs_propres: Tableau 1D des valeurs propres
    :return: Tuple (pourcentage_explique_par_axe, pourcentage_cumule)
    """
    total = np.sum(valeurs_propres)
    if total == 0 or len(valeurs_propres) == 0:
        return np.array([]), np.array([])
    pct_expliquee = valeurs_propres / total * 100
    pct_cumulee = np.cumsum(pct_expliquee)
    return pct_expliquee, pct_cumulee


def variable_coordinates(vecteurs_propres, valeurs_propres, noms_variables):
    """
    Calcule les corrélations entre les variables initiales et les axes factoriels :
    $$r(x_j, F_k) = v_{jk} \sqrt{\lambda_k}$$
    Ces coordonnées permettent de tracer le cercle des corrélations.
    
    :param vecteurs_propres: Matrice des vecteurs propres
    :param valeurs_propres: Valeurs propres associées
    :param noms_variables: Liste des libellés de formations
    :return: DataFrame des coordonnées des variables
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
    Calcule la qualité de représentation ($\cos^2$) des variables sur les axes $F_1$ et $F_2$ :
    $$\cos^2(x_j, F_k) = \frac{r(x_j, F_k)^2}{\sum_l r(x_j, F_l)^2}$$
    
    :param corr_df: DataFrame des corrélations variables-axes
    :return: DataFrame contenant cos2_F1 et cos2_F2
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
    Calcule la qualité de représentation ($\cos^2$) des individus sur les axes $F_1$ et $F_2$ :
    $$\cos^2(i, F_k) = \frac{F_{ik}^2}{d^2(i, G)}$$
    Un $\cos^2$ élevé indique que l'individu est fidèlement projeté sans déformation sur le plan factoriel.
    
    :param F_df: DataFrame des coordonnées factorielles des individus
    :return: DataFrame contenant cos2_F1 et cos2_F2
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
    Calcule la contribution relative (%) d'une variable à l'inertie d'un axe :
    $$CTR(x_j, F_k) = \frac{r(x_j, F_k)^2}{\lambda_k} \times 100$$
    
    :param corr_df: DataFrame des corrélations variables-axes
    :param valeurs_propres: Tableau des valeurs propres
    :return: DataFrame contenant ctr_F1 et ctr_F2
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
    Calcule la contribution relative (%) d'un individu à la construction d'un axe :
    $$CTR(i, F_k) = \frac{p_i \cdot F_{ik}^2}{\lambda_k} \times 100 \quad \text{avec } p_i = \frac{1}{n}$$
    
    :param F_df: DataFrame des coordonnées factorielles
    :param valeurs_propres: Tableau des valeurs propres
    :return: DataFrame contenant ctr_F1 et ctr_F2
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
    """
    Filtre les clients dont la qualité de représentation globale sur le plan $(F_1, F_2)$
    est suffisante ($\cos^2(F_1) + \cos^2(F_2) \ge seuil$, par défaut $0.5$).
    """
    return [c for c in clients if (c.get("cos2_f1", 0) + c.get("cos2_f2", 0)) >= seuil]


def find_distinct_client(clients_fiables):
    """
    Détecte automatiquement le client le plus singulier (outlier) sur le plan factoriel
    par rapport au centre de gravité de l'ensemble des clients fiables.
    """
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
    """
    Détecte la paire d'entreprises clientes ayant les profils de formation les plus similaires
    (distance euclidienne minimale sur le plan factoriel $F_1 \times F_2$).
    """
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
    """
    Interprète sémantiquement un axe factoriel en identifiant les formations contributives
    positives et négatives et en détectant un éventuel effet de taille global.
    """
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
    """
    Génère la synthèse décisionnelle métier à destination du tableau de bord.
    """
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
    Point d'entrée principal : Orchestre l'analyse factorielle complète et renvoie
    la structure JSON finale prête pour l'API et Chart.js.
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


# Alias pour compatibilité ascendante
get_acp_clients = get_acp_complete

