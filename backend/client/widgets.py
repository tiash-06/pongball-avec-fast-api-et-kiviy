"""
widgets.py - Widgets personnalisés réutilisables (leur apparence est dans pong.kv).
Emplacement : pinponball/client/widgets.py
"""
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout

import theme


class ThemedButton(Button):
    """Bouton arrondi dont la couleur de fond se règle avec bg_color."""
    bg_color = ListProperty(theme.TEAL)


class LevelButton(ThemedButton):
    """Bouton d'un défi. Verrouillé = disabled (teal pâle + cadenas dessiné)."""
    level = NumericProperty(1)


class ResultOverlay(FloatLayout):
    """
    Carte affichée par-dessus le jeu (victoire, Game Over, pause).
    Jusqu'à 3 boutons : a (teal), b (corail), c (discret, caché si text_c est vide).
    Chaque bouton déclenche un événement on_a / on_b / on_c auquel l'écran se lie.
    """
    title = StringProperty("")
    message = StringProperty("")
    accent = ListProperty(theme.TEAL)   # couleur du titre
    text_a = StringProperty("")
    text_b = StringProperty("")
    text_c = StringProperty("")
    disabled_b = BooleanProperty(False)
    kind = StringProperty("")           # "win", "lose", "pause"... pour que l'écran s'y retrouve

    __events__ = ("on_a", "on_b", "on_c")

    def on_a(self):
        pass

    def on_b(self):
        pass

    def on_c(self):
        pass