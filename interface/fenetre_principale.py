"""Interface Tkinter du compteur de fitness (membre 3).

Lancer depuis la racine du projet :
    python -m interface.fenetre_principale

Le compteur est le vrai (comptage/compteur.py et comptage/exercice.py).
La lecture de la vidéo et la détection du corps (MediaPipe) sont faites ici
de façon PROVISOIRE, en attendant les classes du module vision (FichierVideo,
DetecteurPose). Les endroits à remplacer sont marqués « A BRANCHER ».
"""
import os
import time
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

import cv2
import mediapipe as mp
from PIL import Image, ImageTk

from comptage.compteur import CompteurRepetitions
from comptage.exercice import lister_exercices, obtenir_exercice

from donnees.gestion_bd import GestionBD
from donnees.seance import Seance

EXERCICES = lister_exercices()
LARGEUR_VIDEO = 640
HAUTEUR_VIDEO = 360
FOND = "#e9f5f3"

# --- PROVISOIRE : conversion des points MediaPipe au format de comptage/exercice.py
# A BRANCHER : sera fait par DetecteurPose / Pose (module vision, membre 1).
_PL = mp.solutions.pose.PoseLandmark
_PARTIES = {
    "epaule": (_PL.LEFT_SHOULDER, _PL.RIGHT_SHOULDER),
    "coude": (_PL.LEFT_ELBOW, _PL.RIGHT_ELBOW),
    "poignet": (_PL.LEFT_WRIST, _PL.RIGHT_WRIST),
    "hanche": (_PL.LEFT_HIP, _PL.RIGHT_HIP),
    "genou": (_PL.LEFT_KNEE, _PL.RIGHT_KNEE),
    "cheville": (_PL.LEFT_ANKLE, _PL.RIGHT_ANKLE),
}


def _extraire_points(resultat, largeur, hauteur):
    """Renvoie {"coude_d": (x, y), ...} en PIXELS (pas en coordonnées normalisées).

    Les angles sont calculés en pixels : avec des coordonnées normalisées
    (0 à 1), l'angle serait déformé sur une image qui n'est pas carrée.
    Les points peu visibles (visibilité < 0.5) sont ignorés.
    """
    points = {}
    if not resultat.pose_landmarks:
        return points
    repere = resultat.pose_landmarks.landmark
    for nom, (gauche, droite) in _PARTIES.items():
        for suffixe, point in (("g", gauche), ("d", droite)):
            p = repere[point.value]
            if p.visibility >= 0.5:
                points[f"{nom}_{suffixe}"] = (p.x * largeur, p.y * hauteur)
    return points


class FenetrePrincipale:
    def __init__(self, racine):
        self.racine = racine
        self.bd = GestionBD()

        self.exerciceChoisi = EXERCICES[0]
        self.cheminVideo = ""

        self._capture = None
        self._tache = None
        self._enCours = False
        self._pose = None
        self._exercice = None
        self._compteurRep = None
        self._compteur = 0
        self._nbImages = 0
        self._debut = 0.0
        self._delai = 33  # millisecondes entre deux images

        self._construire()
        self._majBoutons()

    # ------------------------------------------------------------------
    # Construction de la fenêtre
    # ------------------------------------------------------------------
    def _construire(self):
        r = self.racine
        r.title("Compteur de fitness en temps réel")
        r.configure(bg=FOND)
        r.resizable(False, False)
        r.protocol("WM_DELETE_WINDOW", self.quitter)

        tk.Label(r, text="Human Fitness Tracking and Counting System",
                 font=("Arial", 16, "bold"), bg="white", padx=10, pady=4
                 ).pack(pady=(12, 8))

        # Zone vidéo de taille fixe
        cadre = tk.Frame(r, width=LARGEUR_VIDEO, height=HAUTEUR_VIDEO, bg="#d9d9d9")
        cadre.pack_propagate(False)
        cadre.pack(padx=20)
        self.labelVideo = tk.Label(cadre, text="Aucune vidéo choisie",
                                   bg="#d9d9d9", fg="#555555", font=("Arial", 12))
        self.labelVideo.pack(expand=True, fill="both")

        # Compteur et informations
        self.labelCompteur = tk.Label(r, text="Répétitions : 0",
                                      font=("Arial", 20, "bold"), fg="#c0392b", bg=FOND)
        self.labelCompteur.pack(pady=(10, 0))
        self.labelInfo = tk.Label(r, text="Choisissez une vidéo pour commencer.",
                                  font=("Arial", 10), bg=FOND)
        self.labelInfo.pack(pady=(0, 6))

        # Choix de l'exercice
        ligne = tk.Frame(r, bg=FOND)
        ligne.pack(pady=4)
        tk.Label(ligne, text="Select Fitness Option :", bg=FOND,
                 font=("Arial", 10)).pack(side="left", padx=(0, 6))
        self.listeExercices = ttk.Combobox(ligne, values=EXERCICES,
                                           state="readonly", width=18)
        self.listeExercices.set(self.exerciceChoisi)
        self.listeExercices.pack(side="left")
        self.listeExercices.bind("<<ComboboxSelected>>",
                                 lambda _e: self.choisirExercice())

        # Boutons
        barre = tk.Frame(r, bg=FOND)
        barre.pack(pady=(8, 14))
        self.boutons = {}
        for nom, texte, action in [
            ("video", "Choose Video File", self.choisirVideo),
            ("start", "Start Tracking", self.demarrerSuivi),
            ("stop", "Stop Tracking", self.arreterSuivi),
            ("logs", "View Logs", self.voirHistorique),
            ("exit", "Exit", self.quitter),
        ]:
            b = tk.Button(barre, text=texte, command=action,
                          font=("Arial", 10, "bold"), width=16, pady=4)
            b.pack(side="left", padx=4)
            self.boutons[nom] = b

    def _majBoutons(self):
        etat = lambda actif: "normal" if actif else "disabled"
        self.boutons["video"].config(state=etat(not self._enCours))
        self.boutons["start"].config(state=etat(bool(self.cheminVideo) and not self._enCours))
        self.boutons["stop"].config(state=etat(self._enCours))
        self.listeExercices.config(state="disabled" if self._enCours else "readonly")

    # ------------------------------------------------------------------
    # Actions des boutons (méthodes du diagramme de classes)
    # ------------------------------------------------------------------
    def choisirVideo(self):
        chemin = filedialog.askopenfilename(
            title="Choisir une vidéo",
            filetypes=[("Video Files", "*.mp4 *.avi")])
        if not chemin:
            return
        self.cheminVideo = chemin
        self.labelInfo.config(text=f"Vidéo : {os.path.basename(chemin)}")
        self._majBoutons()

    def choisirExercice(self):
        self.exerciceChoisi = self.listeExercices.get()

    def demarrerSuivi(self):
        if self._enCours:
            return
        if not self.cheminVideo:
            messagebox.showwarning("Vidéo manquante", "Choisissez d'abord une vidéo.")
            return

        # A BRANCHER : ouvrir la vidéo avec FichierVideo(self.cheminVideo).ouvrir()
        self._capture = cv2.VideoCapture(self.cheminVideo)
        if not self._capture.isOpened():
            messagebox.showerror("Erreur", "Impossible d'ouvrir cette vidéo.")
            self._capture = None
            return

        try:
            self._exercice = obtenir_exercice(self.exerciceChoisi)
        except KeyError as erreur:
            messagebox.showerror("Exercice inconnu", str(erreur))
            self._capture.release()
            self._capture = None
            return
        self._compteurRep = CompteurRepetitions(self._exercice)
        # PROVISOIRE : A BRANCHER avec DetecteurPose (membre 1)
        self._pose = mp.solutions.pose.Pose(min_detection_confidence=0.5,
                                            min_tracking_confidence=0.5)

        fps = self._capture.get(cv2.CAP_PROP_FPS) or 30
        self._delai = max(10, int(1000 / fps))
        self._compteur = 0
        self._nbImages = 0
        self._debut = time.time()
        self._enCours = True
        self.afficherCompteur(0)
        self.labelInfo.config(text=f"Suivi en cours : {self.exerciceChoisi}")
        self._majBoutons()
        self._boucle()

    def arreterSuivi(self):
        self._terminer(videoTerminee=False)

    def voirHistorique(self):
        fenetre = tk.Toplevel(self.racine)
        fenetre.title("Historique des séances")
        fenetre.resizable(False, False)

        colonnes = ("date", "exercice", "duree", "repetitions")
        tableau = ttk.Treeview(fenetre, columns=colonnes, show="headings", height=10)
        for col, titre, largeur in [("date", "Date", 140), ("exercice", "Exercice", 120),
                                    ("duree", "Durée", 80), ("repetitions", "Répétitions", 100)]:
            tableau.heading(col, text=titre)
            tableau.column(col, width=largeur, anchor="center")
        tableau.pack(padx=10, pady=10)

        seances = self.bd.lireHistorique()
        for s in sorted(seances, key=lambda x: x.dateSeance, reverse=True):
            tableau.insert("", "end", values=(
                s.dateSeance.strftime("%d/%m/%Y %H:%M"),
                s.nomExercice, f"{s.duree} s", s.nbRepetitions))
        if not seances:
            tk.Label(fenetre, text="Aucune séance enregistrée.").pack(pady=(0, 10))

    def quitter(self):
        self._terminer(videoTerminee=False)
        self.racine.destroy()

    # ------------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------------
    def afficherImage(self, image):
        """Affiche une image OpenCV (BGR) dans la zone vidéo."""
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil = Image.fromarray(rgb)
        pil.thumbnail((LARGEUR_VIDEO, HAUTEUR_VIDEO))
        photo = ImageTk.PhotoImage(pil)
        self.labelVideo.config(image=photo, text="")
        self.labelVideo.image = photo  # garder une référence, sinon l'image disparaît

    def afficherCompteur(self, n):
        self.labelCompteur.config(text=f"Répétitions : {n}")

    # ------------------------------------------------------------------
    # Boucle de lecture
    # ------------------------------------------------------------------
    def _boucle(self):
        if not self._enCours:
            return

        # A BRANCHER : image = self.fichierVideo.lireImage()
        ok, image = self._capture.read()
        if not ok:
            self._terminer(videoTerminee=True)
            return
        self._nbImages += 1

        # PROVISOIRE : détection faite ici avec MediaPipe.
        # A BRANCHER : remplacer par DetecteurPose (membre 1)
        hauteur, largeur = image.shape[:2]
        resultat = self._pose.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if resultat.pose_landmarks:
            mp.solutions.drawing_utils.draw_landmarks(
                image, resultat.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)

        points = _extraire_points(resultat, largeur, hauteur)
        angle = self._exercice.angle_depuis_points(points, cote="d")
        if self._compteurRep.mettre_a_jour(angle):
            self._compteur = self._compteurRep.valeur
            self.afficherCompteur(self._compteur)
        texteAngle = "angle : --" if angle is None else f"angle : {angle:.0f}°"
        self.labelInfo.config(
            text=f"Suivi en cours : {self.exerciceChoisi} - phase : "
                 f"{self._compteurRep.phase} - {texteAngle}")

        self.afficherImage(image)
        self._tache = self.racine.after(self._delai, self._boucle)

    def _terminer(self, videoTerminee):
        if not self._enCours:
            return
        self._enCours = False
        if self._tache is not None:
            self.racine.after_cancel(self._tache)
            self._tache = None
        if self._capture is not None:
            self._capture.release()
            self._capture = None
        if self._pose is not None:
            self._pose.close()
            self._pose = None

        duree = int(time.time() - self._debut)
        self.bd.enregistrer(Seance(datetime.now(), self.exerciceChoisi,
                                   duree, self._compteur, self.cheminVideo))
        message = "Vidéo terminée" if videoTerminee else "Suivi arrêté"
        self.labelInfo.config(
            text=f"{message} : {self._compteur} répétitions, séance enregistrée.")
        self._majBoutons()


def lancer():
    racine = tk.Tk()
    FenetrePrincipale(racine)
    racine.mainloop()


if __name__ == "__main__":
    lancer()