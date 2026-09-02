"""Tests unitaires pour la Sous-étape 2.1 — Générateur de Seed et données déterministes."""

import unittest
from pathlib import Path

from scripts.generate_seed_data import generer_donnees_seed, OUTPUT_FILE


class SeedGeneratorTestCase(unittest.TestCase):
    def test_generation_seed_fichier_et_invariants(self):
        resultats = generer_donnees_seed()

        # 1. Vérification de l'existence du fichier SQL produit
        self.assertTrue(OUTPUT_FILE.exists(), f"Le fichier {OUTPUT_FILE} doit exister")

        # 2. Vérification des volumes de données demandés
        self.assertEqual(resultats["roles"], 3)
        self.assertEqual(resultats["domaines"], 3)
        self.assertEqual(resultats["utilisateurs"], 6)
        self.assertEqual(resultats["formateurs"], 10)
        self.assertEqual(resultats["formations"], 12)
        self.assertEqual(resultats["clients"], 30)
        self.assertEqual(resultats["participants"], 150)
        self.assertEqual(resultats["sessions"], 60)
        self.assertGreaterEqual(resultats["inscriptions"], 400)

        # 3. Vérification du contenu du fichier SQL
        contenu = OUTPUT_FILE.read_text(encoding="utf-8")
        self.assertIn("USE galaxy_solutions;", contenu)
        self.assertIn("INSERT INTO Client", contenu)
        self.assertIn("INSERT INTO Participant", contenu)
        self.assertIn("INSERT INTO Session", contenu)
        self.assertIn("INSERT INTO Inscription", contenu)

        # 4. Vérification d'unicité (aucun participant inscrit deux fois à la même session)
        section_inscription = contenu.split("-- Inscription")[1].split("-- Total inscriptions")[0]
        lignes_inscriptions = [
            l.strip() for l in section_inscription.splitlines()
            if l.strip().startswith("(")
        ]
        inscriptions_tuples = set()
        for ligne in lignes_inscriptions:
            parts = ligne.strip(" (;,)\n").split(",")
            sid, pid = int(parts[0].strip()), int(parts[1].strip())
            key = (sid, pid)
            self.assertNotIn(key, inscriptions_tuples, f"Doublon trouvé pour session {sid} et participant {pid}")
            inscriptions_tuples.add(key)


if __name__ == "__main__":
    unittest.main()
