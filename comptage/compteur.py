"""Module comptage : compteur de répétitions.

Le compteur suit les phases d'un mouvement à partir de l'angle mesuré à chaque
image de la vidéo. Une répétition est comptée quand le mouvement complet a été
réalisé : position haute -> descente -> position basse -> montée -> position haute.

Phases (états) :
    attente  : aucune position haute détectée pour l'instant
    haut     : position tendue (angle >= angle_haut de l'exercice)
    descente : l'angle diminue, la position basse n'est pas encore atteinte
    bas      : position fléchie (angle <= angle_bas de l'exercice)
    montee   : l'angle augmente, la position haute n'est pas encore atteinte
"""

from comptage.exercice import Exercice, obtenir_exercice


class CompteurRepetitions:
    """Compte les répétitions d'un exercice à partir des angles mesurés."""

    ATTENTE = "attente"
    HAUT = "haut"
    DESCENTE = "descente"
    BAS = "bas"
    MONTEE = "montee"

    def __init__(self, exercice):
        """exercice : objet Exercice (voir comptage/exercice.py)."""
        self.exercice = exercice
        self.valeur = 0
        self.phase = self.ATTENTE

    def mettre_a_jour(self, angle):
        """Met à jour le compteur avec l'angle de l'image courante.

        angle : angle en degrés, ou None si les points du corps sont absents.
        Retourne True si une répétition vient d'être comptée, sinon False.
        """
        if angle is None:
            return False

        haute = self.exercice.est_position_haute(angle)
        basse = self.exercice.est_position_basse(angle)
        repetition_comptee = False

        if self.phase == self.ATTENTE:
            if haute:
                self.phase = self.HAUT

        elif self.phase == self.HAUT:
            if not haute:
                self.phase = self.DESCENTE

        elif self.phase == self.DESCENTE:
            if basse:
                self.phase = self.BAS
            elif haute:
                # Descente abandonnée : retour en haut sans avoir atteint le bas
                self.phase = self.HAUT

        elif self.phase == self.BAS:
            if not basse:
                self.phase = self.MONTEE

        elif self.phase == self.MONTEE:
            if haute:
                self.phase = self.HAUT
                self.valeur += 1
                repetition_comptee = True
            elif basse:
                # Remontée abandonnée : retour en bas
                self.phase = self.BAS

        return repetition_comptee

    def changer_exercice(self, exercice):
        """Change d'exercice et remet le compteur à zéro."""
        self.exercice = exercice
        self.reinitialiser()

    def reinitialiser(self):
        """Remet le compteur à zéro et la phase en attente."""
        self.valeur = 0
        self.phase = self.ATTENTE

    def __repr__(self):
        return (f"CompteurRepetitions(exercice={self.exercice.nom!r}, "
                f"valeur={self.valeur}, phase={self.phase!r})")


if __name__ == "__main__":
    # Petit test manuel : python -m comptage.compteur
    compteur = CompteurRepetitions(obtenir_exercice("pompes"))

    # 2 pompes complètes, puis une pompe incomplète (on ne descend pas assez)
    angles = [
        170, 160, 140, 120, 95, 90, 110, 140, 160, 170,   # répétition 1
        168, 150, 120, 98, 92, 120, 155, 168,             # répétition 2
        170, 140, 125, 140, 165,                          # incomplète : non comptée
    ]
    for angle in angles:
        if compteur.mettre_a_jour(angle):
            print(f"Répétition comptée ! Total : {compteur.valeur}")

    print("Résultat final (attendu 2) :", compteur.valeur)
    print("Angle manquant ignoré :", compteur.mettre_a_jour(None))