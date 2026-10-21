"""Module comptage : définition des exercices et calcul des angles.

Conventions
-----------
- Un angle est exprimé en degrés, entre 0 et 180, et mesuré à l'articulation
  centrale (ex. le coude pour les pompes : épaule - coude - poignet).
- angle_haut : seuil de la position « tendue » (grand angle).
  La position est considérée haute quand l'angle est >= angle_haut.
- angle_bas : seuil de la position « fléchie » (petit angle).
  La position est considérée basse quand l'angle est <= angle_bas.
- Les points du corps sont fournis sous la forme d'un dictionnaire
  {"nom_articulation": (x, y)}, où le nom est suivi du côté : "_d" (droit)
  ou "_g" (gauche). Exemple : {"coude_d": (0.52, 0.40)}.
  Ce format sera adapté à la classe Pose du module vision si besoin.
"""

import math


class Exercice:
    """Décrit un exercice de fitness et sait mesurer son angle clé."""

    def __init__(self, nom, articulations, angle_haut, angle_bas):
        """
        nom           : nom de l'exercice (ex. "pompes")
        articulations : trio (extrémité 1, articulation centrale, extrémité 2)
                        ex. ("epaule", "coude", "poignet")
        angle_haut    : seuil de la position tendue (degrés)
        angle_bas     : seuil de la position fléchie (degrés)
        """
        if len(articulations) != 3:
            raise ValueError("Il faut exactement 3 articulations.")
        if angle_bas >= angle_haut:
            raise ValueError("angle_bas doit être inférieur à angle_haut.")
        self.nom = nom
        self.articulations = tuple(articulations)
        self.angle_haut = angle_haut
        self.angle_bas = angle_bas

    def obtenir_angles(self):
        """Retourne les seuils (angle_haut, angle_bas)."""
        return self.angle_haut, self.angle_bas

    @staticmethod
    def calculer_angle(a, b, c):
        """Angle en degrés (0 à 180) au point b, entre les segments b-a et b-c.

        a, b, c sont des points (x, y). Retourne None si deux points
        sont confondus (angle impossible à calculer).
        """
        bax, bay = a[0] - b[0], a[1] - b[1]
        bcx, bcy = c[0] - b[0], c[1] - b[1]
        if (bax == 0 and bay == 0) or (bcx == 0 and bcy == 0):
            return None
        produit_scalaire = bax * bcx + bay * bcy
        produit_vectoriel = bax * bcy - bay * bcx
        return abs(math.degrees(math.atan2(produit_vectoriel, produit_scalaire)))

    def angle_depuis_points(self, points, cote="d"):
        """Calcule l'angle clé de l'exercice à partir des points du corps.

        points : dictionnaire {"coude_d": (x, y), ...}
        cote   : "d" (droit) ou "g" (gauche)
        Retourne None si une articulation nécessaire est absente.
        """
        cles = [f"{partie}_{cote}" for partie in self.articulations]
        if any(cle not in points for cle in cles):
            return None
        a, b, c = (points[cle] for cle in cles)
        return self.calculer_angle(a, b, c)

    def est_position_haute(self, angle):
        """Vrai si l'angle correspond à la position tendue."""
        return angle is not None and angle >= self.angle_haut

    def est_position_basse(self, angle):
        """Vrai si l'angle correspond à la position fléchie."""
        return angle is not None and angle <= self.angle_bas

    def __repr__(self):
        return (f"Exercice({self.nom!r}, haut={self.angle_haut}, "
                f"bas={self.angle_bas})")


# Catalogue des exercices disponibles
EXERCICES = {
    "pompes": Exercice("pompes", ("epaule", "coude", "poignet"), 150, 100),
    "squats": Exercice("squats", ("hanche", "genou", "cheville"), 160, 100),
    "curl biceps": Exercice("curl biceps", ("epaule", "coude", "poignet"), 150, 60),
}


def lister_exercices():
    """Retourne la liste des noms d'exercices disponibles."""
    return list(EXERCICES.keys())


def obtenir_exercice(nom):
    """Retourne l'objet Exercice correspondant au nom (sans tenir compte de la casse)."""
    cle = nom.strip().lower()
    if cle not in EXERCICES:
        raise KeyError(f"Exercice inconnu : {nom!r}. Disponibles : {lister_exercices()}")
    return EXERCICES[cle]


if __name__ == "__main__":
    # Petit test manuel : python -m comptage.exercice
    print("Exercices disponibles :", lister_exercices())
    print("Angle droit (attendu 90) :", Exercice.calculer_angle((1, 0), (0, 0), (0, 1)))
    print("Bras tendu (attendu 180) :", Exercice.calculer_angle((-1, 0), (0, 0), (1, 0)))

    pompes = obtenir_exercice("pompes")
    points = {"epaule_d": (0, 0), "coude_d": (1, 0), "poignet_d": (1, 1)}
    angle = pompes.angle_depuis_points(points)
    print("Angle du coude (attendu 90) :", angle)
    print("Position basse ?", pompes.est_position_basse(angle))
    print("Position haute ?", pompes.est_position_haute(angle))
    print("Point manquant (attendu None) :", pompes.angle_depuis_points({}))