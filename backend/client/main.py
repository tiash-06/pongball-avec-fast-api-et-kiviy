"""
main.py - Point d'entrée du client Kivy.
Emplacement : pinponball/client/main.py
Lancement   : python main.py   (depuis le dossier client)

Kivy charge automatiquement pong.kv car la classe s'appelle PongApp.
"""
from kivy.config import Config

# Doit précéder l'import de Window : Échap sert à la pause, pas à quitter l'application.
Config.set("kivy", "exit_on_escape", "0")

from kivy.app import App  # noqa: E402
from kivy.core.window import Window  # noqa: E402
from kivy.uix.screenmanager import FadeTransition, ScreenManager  # noqa: E402

import theme  # noqa: E402
from screens import ChallengesScreen, GameScreen, LoginScreen, ModeMenuScreen  # noqa: E402

# Fond de toutes les fenêtres : beige.
Window.clearcolor = theme.BEIGE
Window.size = (900, 600)


class PongApp(App):
    title = "Pong"

    def build(self):
        sm = ScreenManager(transition=FadeTransition(duration=0.15))
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(ModeMenuScreen(name="mode_menu"))
        sm.add_widget(ChallengesScreen(name="challenges"))
        sm.add_widget(GameScreen(name="game"))
        return sm


if __name__ == "__main__":
    PongApp().run()