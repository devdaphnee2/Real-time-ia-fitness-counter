"""Classe Seance : une séance d'entraînement analysée sur une vidéo."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Seance:
    dateSeance: datetime
    nomExercice: str
    duree: int            # en secondes
    nbRepetitions: int
    cheminVideo: str
    idSeance: Optional[int] = None   # rempli par GestionBD.enregistrer()