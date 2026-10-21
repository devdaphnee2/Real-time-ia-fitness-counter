"""Tests automatiques du module comptage.

Lancer depuis la racine du projet :
    python -m unittest discover -v
"""

import unittest

from comptage.compteur import CompteurRepetitions
from comptage.exercice import Exercice, lister_exercices, obtenir_exercice


class TestExercice(unittest.TestCase):

    def test_angle_droit(self):
        angle = Exercice.calculer_angle((1, 0), (0, 0), (0, 1))
        self.assertAlmostEqual(angle, 90.0)

    def test_angle_bras_tendu(self):
        angle = Exercice.calculer_angle((-1, 0), (0, 0), (1, 0))
        self.assertAlmostEqual(angle, 180.0)

    def test_points_confondus_retourne_none(self):
        self.assertIsNone(Exercice.calculer_angle((0, 0), (0, 0), (1, 1)))

    def test_angle_depuis_points(self):
        pompes = obtenir_exercice("pompes")
        points = {"epaule_d": (0, 0), "coude_d": (1, 0), "poignet_d": (1, 1)}
        self.assertAlmostEqual(pompes.angle_depuis_points(points), 90.0)

    def test_angle_depuis_points_cote_gauche(self):
        pompes = obtenir_exercice("pompes")
        points = {"epaule_g": (0, 0), "coude_g": (1, 0), "poignet_g": (1, 1)}
        self.assertAlmostEqual(pompes.angle_depuis_points(points, cote="g"), 90.0)

    def test_point_manquant_retourne_none(self):
        pompes = obtenir_exercice("pompes")
        self.assertIsNone(pompes.angle_depuis_points({"coude_d": (1, 0)}))

    def test_positions_haute_et_basse(self):
        pompes = obtenir_exercice("pompes")
        self.assertTrue(pompes.est_position_haute(170))
        self.assertFalse(pompes.est_position_haute(120))
        self.assertTrue(pompes.est_position_basse(90))
        self.assertFalse(pompes.est_position_basse(120))
        self.assertFalse(pompes.est_position_haute(None))

    def test_exercice_inconnu(self):
        with self.assertRaises(KeyError):
            obtenir_exercice("danse")

    def test_angles_invalides(self):
        with self.assertRaises(ValueError):
            Exercice("test", ("a", "b", "c"), angle_haut=90, angle_bas=150)

    def test_catalogue(self):
        self.assertEqual(lister_exercices(), ["pompes", "squats", "curl biceps"])
        self.assertEqual(obtenir_exercice(" Pompes ").nom, "pompes")


class TestCompteurRepetitions(unittest.TestCase):

    def setUp(self):
        self.compteur = CompteurRepetitions(obtenir_exercice("pompes"))

    def envoyer(self, angles):
        for angle in angles:
            self.compteur.mettre_a_jour(angle)

    def test_depart(self):
        self.assertEqual(self.compteur.valeur, 0)
        self.assertEqual(self.compteur.phase, CompteurRepetitions.ATTENTE)

    def test_une_repetition_complete(self):
        self.envoyer([170, 140, 120, 95, 90, 110, 140, 160, 170])
        self.assertEqual(self.compteur.valeur, 1)
        self.assertEqual(self.compteur.phase, CompteurRepetitions.HAUT)

    def test_trois_repetitions(self):
        une_repetition = [170, 140, 95, 90, 120, 160, 170]
        self.envoyer(une_repetition * 3)
        self.assertEqual(self.compteur.valeur, 3)

    def test_repetition_incomplete_non_comptee(self):
        self.envoyer([170, 140, 125, 140, 165])
        self.assertEqual(self.compteur.valeur, 0)

    def test_phases_successives(self):
        phases = []
        for angle in [170, 140, 90, 120, 160]:
            self.compteur.mettre_a_jour(angle)
            phases.append(self.compteur.phase)
        self.assertEqual(phases, ["haut", "descente", "bas", "montee", "haut"])

    def test_retour_true_quand_repetition_comptee(self):
        resultats = [self.compteur.mettre_a_jour(a)
                     for a in [170, 140, 90, 120, 160]]
        self.assertEqual(resultats, [False, False, False, False, True])

    def test_angle_none_ignore(self):
        self.envoyer([170, 140])
        phase_avant = self.compteur.phase
        self.assertFalse(self.compteur.mettre_a_jour(None))
        self.assertEqual(self.compteur.phase, phase_avant)

    def test_pas_de_comptage_sans_position_haute(self):
        # Le mouvement commence en bas : rien ne se passe avant d'avoir été en haut
        self.envoyer([90, 95, 90])
        self.assertEqual(self.compteur.valeur, 0)
        self.assertEqual(self.compteur.phase, CompteurRepetitions.ATTENTE)

    def test_reinitialiser(self):
        self.envoyer([170, 140, 90, 120, 160])
        self.compteur.reinitialiser()
        self.assertEqual(self.compteur.valeur, 0)
        self.assertEqual(self.compteur.phase, CompteurRepetitions.ATTENTE)

    def test_changer_exercice(self):
        self.envoyer([170, 140, 90, 120, 160])
        self.compteur.changer_exercice(obtenir_exercice("squats"))
        self.assertEqual(self.compteur.exercice.nom, "squats")
        self.assertEqual(self.compteur.valeur, 0)

    def test_squats(self):
        compteur = CompteurRepetitions(obtenir_exercice("squats"))
        for angle in [170, 150, 120, 95, 120, 150, 165, 170]:
            compteur.mettre_a_jour(angle)
        self.assertEqual(compteur.valeur, 1)

    def test_curl_biceps(self):
        compteur = CompteurRepetitions(obtenir_exercice("curl biceps"))
        for angle in [165, 120, 70, 50, 80, 130, 155]:
            compteur.mettre_a_jour(angle)
        self.assertEqual(compteur.valeur, 1)


if __name__ == "__main__":
    unittest.main()