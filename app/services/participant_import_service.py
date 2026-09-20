"""
==============================================================================
Service d'Import de Participants (CSV & Excel XLSX)
==============================================================================
Ce module assure l'importation par lot de listes de participants / apprenants :
1. Détection automatique du format (CSV ou Excel .xlsx).
2. Tolérance d'encodage (UTF-8, UTF-8 avec BOM, Latin-1).
3. Détection automatique des délimiteurs CSV (virgule ou point-virgule).
4. Normalisation intelligente des noms de colonnes (ex: 'Entreprise' -> 'client').
5. Validation granulaire par ligne :
   - Présence du nom et de l'email.
   - Format d'adresse email valide.
   - Unicité de l'email (en base et au sein du même fichier).
   - Résolution automatique de l'entreprise cliente (par raison sociale ou ID).
6. Compte-rendu d'exécution détaillé (nombre importé, nombre ignoré, détails des erreurs).
"""

import csv
import io
import re
from typing import Dict, Any, List, Tuple
import openpyxl
from flask import Response
from app.extensions import db
from app.models import Participant, Client

EMAIL_REGEX = re.compile(r"^[\w\.\+\-]+@[\w\-]+(\.[\w\-]+)+$")


def normaliser_cle(cle: str) -> str:
    """Nettoie et normalise une chaîne d'en-tête pour la correspondance insensible à la casse et aux accents."""
    if not cle:
        return ""
    c = str(cle).strip().lower()
    c = c.replace("é", "e").replace("è", "e").replace("ê", "e").replace("à", "a").replace("ç", "c")
    c = re.sub(r"[\s\-_]+", "_", c)
    return c


def mapper_colonnes(en_tetes_bruts: List[str]) -> Dict[str, str]:
    """
    Associe les colonnes du fichier source aux champs cibles du modèle Participant.
    Retourne un dictionnaire {nom_champ_cible: nom_colonne_source}.
    """
    mapping = {}
    for col in en_tetes_bruts:
        cle_norm = normaliser_cle(col)
        if cle_norm in ["nom", "nom_complet", "nom_et_prenom", "nom_participant", "stagiaire", "apprenant", "participant"]:
            mapping["nom"] = col
        elif cle_norm in ["email", "courriel", "mail", "adresse_email", "e_mail", "contact_email"]:
            mapping["email"] = col
        elif cle_norm in ["entreprise", "client", "nom_entreprise", "societe", "client_id", "organisation", "employeur"]:
            mapping["entreprise"] = col
    return mapping


def extraire_lignes_csv(flux_binaire: bytes) -> Tuple[List[str], List[Dict[str, str]]]:
    """Extrait les en-têtes et les lignes d'un contenu binaire CSV."""
    # Détection de l'encodage
    texte = None
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            texte = flux_binaire.decode(enc)
            break
        except UnicodeDecodeError:
            continue

    if texte is None:
        raise ValueError("Impossible de décoder le fichier CSV (encodage non supporté).")

    # Détection du délimiteur (virgule, point-virgule ou tabulation)
    premiere_ligne = texte.splitlines()[0] if texte.splitlines() else ""
    delimiter = ";" if premiere_ligne.count(";") > premiere_ligne.count(",") else ","

    flux_texte = io.StringIO(texte)
    reader = csv.DictReader(flux_texte, delimiter=delimiter)
    en_tetes = reader.fieldnames or []
    lignes = [dict(ligne) for ligne in reader if any(v.strip() for v in ligne.values() if v)]
    return list(en_tetes), lignes


def extraire_lignes_xlsx(flux_binaire: bytes) -> Tuple[List[str], List[Dict[str, str]]]:
    """Extrait les en-têtes et les lignes d'un classeur Excel XLSX."""
    wb = openpyxl.load_workbook(io.BytesIO(flux_binaire), data_only=True)
    ws = wb.active
    lignes_brutes = list(ws.iter_rows(values_only=True))

    if not lignes_brutes:
        return [], []

    en_tetes_bruts = [str(cell).strip() for cell in lignes_brutes[0] if cell is not None]
    lignes = []

    for row_idx, row in enumerate(lignes_brutes[1:], start=2):
        if not any(cell is not None and str(cell).strip() for cell in row):
            continue
        ligne_dict = {}
        for col_idx, col_nom in enumerate(en_tetes_bruts):
            if col_idx < len(row):
                val = row[col_idx]
                ligne_dict[col_nom] = str(val).strip() if val is not None else ""
            else:
                ligne_dict[col_nom] = ""
        lignes.append(ligne_dict)

    return en_tetes_bruts, lignes


def importer_participants_depuis_flux(nom_fichier: str, contenu_binaire: bytes) -> Dict[str, Any]:
    """
    Point d'entrée principal pour l'import de participants depuis un fichier CSV ou Excel.
    
    :param nom_fichier: Nom du fichier uploadé (ex: 'participants.csv')
    :param contenu_binaire: Octets bruts du fichier
    :return: Dictionnaire récapitulatif du traitement
    """
    nom_lower = nom_fichier.lower()
    if nom_lower.endswith(".csv"):
        en_tetes, lignes_sources = extraire_lignes_csv(contenu_binaire)
    elif nom_lower.endswith(".xlsx"):
        en_tetes, lignes_sources = extraire_lignes_xlsx(contenu_binaire)
    else:
        return {
            "succes": False,
            "erreur": "Format de fichier non pris en charge. Veuillez fournir un fichier .csv ou .xlsx.",
        }

    if not en_tetes or not lignes_sources:
        return {
            "succes": False,
            "erreur": "Le fichier importé est vide ou ne contient aucune ligne de données.",
        }

    mapping = mapper_colonnes(en_tetes)
    colonnes_manquantes = []
    if "nom" not in mapping:
        colonnes_manquantes.append("Nom (ou Nom complet)")
    if "email" not in mapping:
        colonnes_manquantes.append("Email (ou Courriel)")
    if "entreprise" not in mapping:
        colonnes_manquantes.append("Entreprise (ou Client)")

    if colonnes_manquantes:
        return {
            "succes": False,
            "erreur": f"Colonnes obligatoires manquantes dans le fichier : {', '.join(colonnes_manquantes)}. Colonnes détectées : {', '.join(en_tetes)}.",
        }

    # Pré-chargement des clients existants pour résolution rapide O(1)
    clients = Client.query.all()
    client_par_nom = {c.nom_entreprise.strip().lower(): c for c in clients}
    client_par_id = {c.id: c for c in clients}

    # Pré-chargement des emails existants
    emails_existants = {p.email.strip().lower() for p in Participant.query.with_entities(Participant.email).all()}
    emails_vus_dans_fichier = set()

    participants_a_inserer = []
    erreurs = []

    for num_ligne, ligne in enumerate(lignes_sources, start=2):
        nom = str(ligne.get(mapping["nom"], "")).strip()
        email = str(ligne.get(mapping["email"], "")).strip().lower()
        val_entreprise = str(ligne.get(mapping["entreprise"], "")).strip()

        # 1. Validation de présence du nom
        if not nom:
            erreurs.append({
                "ligne": num_ligne,
                "email": email or "-",
                "motif": "Le nom du participant est obligatoire.",
            })
            continue

        # 2. Validation de l'email
        if not email or not EMAIL_REGEX.match(email):
            erreurs.append({
                "ligne": num_ligne,
                "email": email or "-",
                "motif": "Adresse courriel invalide ou manquante.",
            })
            continue

        # 3. Vérification de doublon
        if email in emails_existants or email in emails_vus_dans_fichier:
            erreurs.append({
                "ligne": num_ligne,
                "email": email,
                "motif": "Cette adresse email est déjà utilisée.",
            })
            continue

        # 4. Résolution de l'entreprise cliente
        client_cible = None
        if val_entreprise.isdigit() and int(val_entreprise) in client_par_id:
            client_cible = client_par_id[int(val_entreprise)]
        elif val_entreprise.lower() in client_par_nom:
            client_cible = client_par_nom[val_entreprise.lower()]

        if not client_cible:
            erreurs.append({
                "ligne": num_ligne,
                "email": email,
                "motif": f"Entreprise cliente '{val_entreprise}' introuvable dans la base.",
            })
            continue

        # Ligne valide
        emails_vus_dans_fichier.add(email)
        participant = Participant(
            nom=nom,
            email=email,
            client_id=client_cible.id,
        )
        participants_a_inserer.append(participant)

    # Insertion en base
    if participants_a_inserer:
        db.session.add_all(participants_a_inserer)
        db.session.commit()

    return {
        "succes": True,
        "total_lignes": len(lignes_sources),
        "nb_importes": len(participants_a_inserer),
        "nb_erreurs": len(erreurs),
        "erreurs": erreurs,
    }


def generer_template_import_csv() -> Response:
    """Génère un fichier CSV modèle prêt à remplir avec encodage UTF-8 BOM."""
    output_bytes = io.BytesIO()
    text_stream = io.TextIOWrapper(output_bytes, encoding="utf-8-sig", newline="")
    writer = csv.writer(text_stream, delimiter=";")

    # En-têtes officiels
    writer.writerow(["Nom", "Email", "Entreprise"])
    # Lignes d'exemple
    writer.writerow(["Karim Bennani", "karim.bennani@entreprise.ma", "Attijariwafa Bank"])
    writer.writerow(["Fatima Zahra El Amrani", "fz.elamrani@entreprise.ma", "Maroc Telecom"])

    text_stream.flush()
    csv_data = output_bytes.getvalue()

    response = Response(csv_data, mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = 'attachment; filename="template_import_participants.csv"'
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

