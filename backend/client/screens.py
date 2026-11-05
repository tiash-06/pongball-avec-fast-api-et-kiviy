"""
screens.py - Les écrans de l'application (leur apparence est dans pong.kv).
Emplacement : pinponball/client/screens.py
"""
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen

import api
import theme
from engine import WIN_SCORE
from game import PongField  # noqa: F401  (enregistre le widget pour pong.kv)
from levels import LEVELS, MAX_LEVEL, get_level
from session import session
from widgets import LevelButton, ResultOverlay



# 1. Connexion / inscription

class LoginScreen(Screen):
    """Écran de connexion / inscription."""

    def on_enter(self):
        # Écran propre à chaque arrivée (ex. après une déconnexion).
        self.ids.password_input.text = ""
        self.set_message("")
        Clock.schedule_once(lambda dt: setattr(self.ids.username_input, "focus", True), 0.1)

    def set_message(self, text, error=True):
        """Affiche un message : corail pour une erreur, teal pour une info."""
        label = self.ids.message_label
        label.text = text
        label.color = theme.CORAL if error else theme.TEAL

    def set_busy(self, busy):
        """Désactive les boutons pendant une requête (évite le double clic)."""
        self.ids.btn_login.disabled = busy
        self.ids.btn_register.disabled = busy

    def submit(self, action):
        """action = 'login' ou 'register'."""
        if self.ids.btn_login.disabled:  # requête déjà en cours
            return

        username = self.ids.username_input.text.strip()
        password = self.ids.password_input.text  # on ne modifie jamais le mot de passe

        # Validation côté client : évite un aller-retour inutile vers le serveur.
        if len(username) < 3:
            return self.set_message("Nom d'utilisateur : 3 caractères minimum.")
        if len(password) < 4:
            return self.set_message("Mot de passe : 4 caractères minimum.")

        self.set_busy(True)
        self.set_message("Connexion en cours...", error=False)
        call = api.login if action == "login" else api.register
        call(username, password, on_success=self._on_success, on_error=self._on_error)

    def _on_success(self, user):
        session.login(user)
        self.set_busy(False)
        self.manager.current = "mode_menu"

    def _on_error(self, message):
        self.set_busy(False)
        self.set_message(message)


# 2. Menu principal : choix du mode de jeu

class ModeMenuScreen(Screen):
    """Choix entre le mode Solo (défis contre le bot) et le mode 2 joueurs."""

    def on_pre_enter(self):
        user = session.user
        self.ids.welcome_label.text = f"Bienvenue, {user['username']} !"
        self.ids.level_label.text = f"Niveau débloqué : {user['level_unlocked']} / {MAX_LEVEL}"

    def start_two_players(self):
        """Mode duo local : deux joueurs sur le même clavier, sans sauvegarde."""
        game = self.manager.get_screen("game")
        game.setup(mode="2P", level=1)
        self.manager.current = "game"

    def logout(self):
        session.logout()
        self.manager.current = "login"


# 3. Menu des 5 défis

class ChallengesScreen(Screen):
    """
    Affiche les 5 défis selon la progression du joueur :
      - niveau déjà réussi      -> bouton teal
      - niveau à battre (actuel) -> bouton corail
      - niveau verrouillé        -> teal pâle + cadenas, non cliquable
    """

    def on_pre_enter(self):
        # On reconstruit la liste à chaque entrée : la progression a pu changer.
        unlocked = session.user["level_unlocked"]
        self.ids.progress_label.text = f"Niveau débloqué : {unlocked} / {MAX_LEVEL}"

        box = self.ids.levels_box
        box.clear_widgets()
        for level in LEVELS:
            number = level["number"]
            button = LevelButton(level=number, text=f"Défi {number}  -  {level['name']}")

            if number > unlocked:
                button.disabled = True            # verrouillé
            elif number < unlocked:
                button.bg_color = theme.TEAL      # déjà réussi
            else:
                button.bg_color = theme.CORAL     # prochain défi à battre

            button.bind(on_release=self.on_level_pressed)
            box.add_widget(button)

    def on_level_pressed(self, button):
        # Sécurité en plus du bouton désactivé : jamais de niveau verrouillé.
        if button.level > session.user["level_unlocked"]:
            return
        game = self.manager.get_screen("game")
        game.setup(mode="BOT", level=button.level)
        self.manager.current = "game"



# 4. Écran de jeu (PROVISOIRE : remplacé à l'étape 4)

class GameScreen(Screen):
    mode = "BOT"   # "BOT" (solo) ou "2P" (duo local)
    level = 1

    def setup(self, mode, level):
        """Appelé par les menus avant d'afficher l'écran."""
        self.mode = mode
        self.level = level

    def on_pre_enter(self):
        if self.mode == "BOT":
            self.ids.info_label.text = f"Défi {self.level} : le jeu arrive à l'étape 4"
        else:
            self.ids.info_label.text = "Mode 2 joueurs : le jeu arrive à l'étape 4"

    def leave(self):
        self.manager.current = "challenges" if self.mode == "BOT" else "mode_menu"