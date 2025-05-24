from manim import *

class MateMeScene(Scene):
    def construct(self):
        # Création du texte
        text = Text("MateMe", font="Arial", font_size=96)
        
        # Centrer le texte (par défaut, c’est déjà le cas)
        text.move_to(ORIGIN)
        
        # Animation d'apparition du texte
        self.play(Write(text))
        
        # Pause pour garder le texte à l'écran un moment
        self.wait(2)

"""
Pour lancer la video : manim -pql video.py MateMeScene

"""
