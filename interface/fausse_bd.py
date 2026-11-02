"""Fausse base de données pour développer l'interface sans attendre le membre 4.

Même interface que la vraie GestionBD (donnees/gestion_bd.py) :
enregistrer(seance) et lireHistorique(). Les données sont gardées en mémoire.
"""
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Seance:
    dateSeance: datetime
    nomExercice: str
    duree: int            # en secondes
    nbRepetitions: int
    cheminVideo: str


class GestionBD:
    def __init__(self):
        self._seances = [
            Seance(datetime(2026, 10, 18, 10, 30), "Chest Fly", 95, 12, "chest_fly.mp4"),
            Seance(datetime(2026, 10, 19, 16, 5), "Dumbbell", 70, 10, "dumbbell.mp4"),
        ]

    def enregistrer(self, seance):
        self._seances.append(seance)

    def lireHistorique(self):
        return list(self._seances)