"""Gestion de la base de données SQLite (module données).

Deux tables, en 3ᵉ forme normale :
    exercice (idExercice, nom)                      -- un exercice n'est stocké qu'une fois
    seance   (idSeance, dateSeance, duree, nbRepetitions, cheminVideo, idExercice)

Un exercice a plusieurs séances (clé étrangère seance.idExercice).
Les seuils d'angle restent dans comptage/exercice.py, pas en base.

Même interface que interface/fausse_bd.py :
    enregistrer(seance)  et  lireHistorique() -> liste de Seance
"""
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from donnees.seance import Seance

# fitness.db est créé à la racine du projet (ignoré par Git grâce à *.db)
CHEMIN_PAR_DEFAUT = str(Path(__file__).resolve().parent.parent / "fitness.db")


class GestionBD:
    def __init__(self, cheminBD=CHEMIN_PAR_DEFAUT):
        self.cheminBD = cheminBD
        self._creerTables()

    def _connexion(self):
        connexion = sqlite3.connect(self.cheminBD)
        connexion.execute("PRAGMA foreign_keys = ON")
        return connexion

    def _creerTables(self):
        with closing(self._connexion()) as connexion, connexion:
            connexion.execute("""
                CREATE TABLE IF NOT EXISTS exercice (
                    idExercice INTEGER PRIMARY KEY AUTOINCREMENT,
                    nom        TEXT NOT NULL UNIQUE
                )""")
            connexion.execute("""
                CREATE TABLE IF NOT EXISTS seance (
                    idSeance      INTEGER PRIMARY KEY AUTOINCREMENT,
                    dateSeance    TEXT    NOT NULL,
                    duree         INTEGER NOT NULL CHECK (duree >= 0),
                    nbRepetitions INTEGER NOT NULL CHECK (nbRepetitions >= 0),
                    cheminVideo   TEXT    NOT NULL,
                    idExercice    INTEGER NOT NULL
                                  REFERENCES exercice (idExercice)
                )""")

    def enregistrer(self, seance):
        """Enregistre une séance et renseigne seance.idSeance."""
        with closing(self._connexion()) as connexion, connexion:
            connexion.execute("INSERT OR IGNORE INTO exercice (nom) VALUES (?)",
                              (seance.nomExercice,))
            idExercice = connexion.execute(
                "SELECT idExercice FROM exercice WHERE nom = ?",
                (seance.nomExercice,)).fetchone()[0]
            curseur = connexion.execute(
                "INSERT INTO seance (dateSeance, duree, nbRepetitions, cheminVideo, idExercice) "
                "VALUES (?, ?, ?, ?, ?)",
                (seance.dateSeance.isoformat(timespec="seconds"), seance.duree,
                 seance.nbRepetitions, seance.cheminVideo, idExercice))
            seance.idSeance = curseur.lastrowid
        return seance.idSeance

    def lireHistorique(self):
        """Renvoie la liste des séances, la plus récente en premier."""
        with closing(self._connexion()) as connexion:
            lignes = connexion.execute("""
                SELECT s.idSeance, s.dateSeance, e.nom, s.duree,
                       s.nbRepetitions, s.cheminVideo
                FROM seance s JOIN exercice e ON e.idExercice = s.idExercice
                ORDER BY s.dateSeance DESC, s.idSeance DESC""").fetchall()
        return [Seance(datetime.fromisoformat(date), nom, duree, nb, chemin, idSeance)
                for idSeance, date, nom, duree, nb, chemin in lignes]