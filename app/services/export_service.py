import csv
import io
from flask import Response

def generer_csv_response(nom_fichier, en_tetes, lignes):
    """
    Génère une Flask Response au format CSV avec encodage UTF-8 + BOM (utf-8-sig).
    
    :param nom_fichier: Nom du fichier CSV téléchargé
    :param en_tetes: Dict {cle_dict: 'Nom de la colonne'} ou liste de clés
    :param lignes: Liste de dictionnaires de données
    """
    output_bytes = io.BytesIO()
    text_stream = io.TextIOWrapper(output_bytes, encoding="utf-8-sig", newline="")

    if isinstance(en_tetes, dict):
        fieldnames = list(en_tetes.keys())
        header_map = en_tetes
    else:
        fieldnames = list(en_tetes)
        header_map = {f: f for f in fieldnames}

    writer = csv.DictWriter(text_stream, fieldnames=fieldnames, extrasaction="ignore")
    writer.writerow(header_map)

    for ligne in lignes:
        writer.writerow(ligne)

    text_stream.flush()
    csv_data = output_bytes.getvalue()

    response = Response(csv_data, mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{nom_fichier}"'
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

