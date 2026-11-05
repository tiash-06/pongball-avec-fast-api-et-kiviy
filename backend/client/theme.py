"""
theme.py - Palette de couleurs unique du jeu (source de vérité).
Emplacement : pinponball/client/theme.py

Format Kivy : listes RGBA avec valeurs de 0 à 1.
Utilisé par pong.kv (#:import theme theme) et par le code Python.
"""


def hex_to_rgba(hex_code, alpha=1.0):
    """Convertit '#RRGGBB' en [r, g, b, a] (valeurs 0-1)."""
    h = hex_code.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return [r, g, b, alpha]


TEAL = hex_to_rgba("#008080")    # principal : boutons, titres, terrain de jeu
CORAL = hex_to_rgba("#E2725B")   # accent : actions fortes, erreurs, balle
BEIGE = hex_to_rgba("#F5F5DC")   # fond des pages, raquettes
WHITE = [1, 1, 1, 1]             # cartes, formulaires, champs de saisie

TEAL_SOFT = hex_to_rgba("#008080", 0.45)  # indications (hint) et éléments verrouillés
TEAL_PALE = hex_to_rgba("#D0E8E8")  # bouton secondaire discret (ex. "Menu des défis")