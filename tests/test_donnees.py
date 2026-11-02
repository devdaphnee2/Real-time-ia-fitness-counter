"""Tests du module données. Lancer : python -m unittest tests.test_donnees"""
import os
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import datetime

from donnees.gestion_bd import GestionBD
from donnees.seance import Seance


class TestGestionBD(unittest.TestCase):
    def setUp(self):
        self.dossier = tempfile.TemporaryDirectory()
        self.chemin = os.path.join(self.dossier.name, "test.db")
        self.bd = GestionBD(self.chemin)

    def tearDown(self):
        self.dossier.cleanup()

    def test_historique_vide(self):
        self.assertEqual(self.bd.lireHistorique(), [])

    def test_enregistrer_puis_lire(self):
        s = Seance(datetime(2026, 10, 20, 14, 30), "pompes", 60, 8, "videos_test/a.mp4")
        idSeance = self.bd.enregistrer(s)
        self.assertEqual(s.idSeance, idSeance)
        lue = self.bd.lireHistorique()[0]
        self.assertEqual((lue.nomExercice, lue.duree, lue.nbRepetitions, lue.cheminVideo),
                         ("pompes", 60, 8, "videos_test/a.mp4"))
        self.assertEqual(lue.dateSeance, datetime(2026, 10, 20, 14, 30))

    def test_donnees_conservees_apres_reouverture(self):
        self.bd.enregistrer(Seance(datetime(2026, 10, 20, 9, 0), "squats", 45, 5, "b.mp4"))
        autre = GestionBD(self.chemin)
        self.assertEqual(len(autre.lireHistorique()), 1)

    def test_exercice_stocke_une_seule_fois(self):
        for h in (9, 10):
            self.bd.enregistrer(Seance(datetime(2026, 10, 20, h, 0), "squats", 45, 5, "b.mp4"))
        with closing(sqlite3.connect(self.chemin)) as c:
            self.assertEqual(c.execute("SELECT COUNT(*) FROM exercice").fetchone()[0], 1)

    def test_plus_recente_en_premier(self):
        self.bd.enregistrer(Seance(datetime(2026, 10, 18, 9, 0), "squats", 45, 5, "b.mp4"))
        self.bd.enregistrer(Seance(datetime(2026, 10, 20, 9, 0), "pompes", 45, 5, "c.mp4"))
        self.assertEqual(self.bd.lireHistorique()[0].nomExercice, "pompes")

    def test_valeur_negative_refusee(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.bd.enregistrer(Seance(datetime(2026, 10, 20, 9, 0), "pompes", 10, -1, "d.mp4"))


if __name__ == "__main__":
    unittest.main()