import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ReferenceListProperty, ObjectProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse

# URL de votre API FastAPI locale
API_URL = "http://127.0.0.1:8000"

current_user = None

# --- 1. ÉCRAN DE CONNEXION ---
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=50, spacing=20)
        
        self.title_label = Label(text="PONG GAME - CONNEXION", font_size=24, size_hint_y=None, height=50)
        self.username_input = TextInput(hint_text='Nom d\'utilisateur', multiline=False, size_hint_y=None, height=40)
        self.password_input = TextInput(hint_text='Mot de passe', password=True, multiline=False, size_hint_y=None, height=40)
        self.info_label = Label(text="", color=(1, 0, 0, 1), size_hint_y=None, height=30)
        
        btn_login = Button(text="Se connecter", size_hint_y=None, height=50)
        btn_login.bind(on_press=self.do_login)
        
        btn_register = Button(text="S'inscrire", size_hint_y=None, height=50)
        btn_register.bind(on_press=self.do_register)
        
        layout.add_widget(self.title_label)
        layout.add_widget(self.username_input)
        layout.add_widget(self.password_input)
        layout.add_widget(self.info_label)
        layout.add_widget(btn_login)
        layout.add_widget(btn_register)
        self.add_widget(layout)

    def do_login(self, instance):
        global current_user
        try:
            response = requests.post(f"{API_URL}/login", json={
                "username": self.username_input.text.strip(),
                "password": self.password_input.text.strip()
            })
            if response.status_code == 200:
                current_user = response.json()
                self.manager.current = 'mode_menu'
            else:
                self.info_label.text = "Identifiants incorrects."
        except:
            self.info_label.text = "Erreur de connexion au serveur."

    def do_register(self, instance):
        global current_user
        try:
            response = requests.post(f"{API_URL}/register", json={
                "username": self.username_input.text.strip(),
                "password": self.password_input.text.strip()
            })
            if response.status_code == 200:
                current_user = response.json()
                self.manager.current = 'mode_menu'
            else:
                self.info_label.text = response.json().get("detail", "Erreur d'inscription.")
        except:
            self.info_label.text = "Erreur de connexion au serveur."


# --- 2. MENU DE SÉLECTION DU MODE ---
class ModeMenuScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=60, spacing=20)
        layout.add_widget(Label(text=f"Bienvenue, {current_user['username']} !", font_size=22, size_hint_y=None, height=40))
        
        btn_challenges = Button(text="Mode Solo : Les 5 Défis (vs Bot)", size_hint_y=None, height=60)
        btn_challenges.bind(on_press=lambda x: setattr(self.manager, 'current', 'challenges_menu'))
        
        btn_local_2p = Button(text="Mode 2 Joueurs Local", size_hint_y=None, height=60)
        btn_local_2p.bind(on_press=self.start_2p_game)
        
        layout.add_widget(btn_challenges)
        layout.add_widget(btn_local_2p)
        self.add_widget(layout)

    def start_2p_game(self, instance):
        game_screen = self.manager.get_screen('game')
        game_screen.game_mode = "2P"
        game_screen.challenge_level = 1
        self.manager.current = 'game'


# --- 3. MENU DES DÉFIS ---
class ChallengesMenuScreen(Screen):
    def on_enter(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical', padding=40, spacing=12)
        layout.add_widget(Label(text=f"CHOISISSEZ UN DÉFI (Max débloqué : {current_user['level_unlocked']}/5)", font_size=18, size_hint_y=None, height=40))
        
        for i in range(1, 6):
            unlocked = i <= current_user['level_unlocked']
            btn = Button(text=f"Défi {i}" if unlocked else f"Défi {i} (🔒 Verrouillé)", size_hint_y=None, height=45, disabled=not unlocked)
            if unlocked:
                btn.bind(on_press=lambda inst, lvl=i: self.start_challenge(lvl))
            layout.add_widget(btn)
            
        btn_back = Button(text="Retour au menu principal", size_hint_y=None, height=45)
        btn_back.bind(on_press=lambda x: setattr(self.manager, 'current', 'mode_menu'))
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def start_challenge(self, level):
        game_screen = self.manager.get_screen('game')
        game_screen.game_mode = "BOT"
        game_screen.challenge_level = level
        self.manager.current = 'game'


# --- 4. ÉLÉMENTS DU JEU PONG ---
class PongPaddle(Widget):
    score = NumericProperty(0)
    def bounce_ball(self, ball):
        if self.collide_widget(ball):
            vx, vy = ball.velocity
            offset = (ball.center_y - self.center_y) / (self.height / 2)
            ball.velocity = (-vx * 1.1, vy + offset * 15)

class PongBall(Widget):
    velocity_x = NumericProperty(0)
    velocity_y = NumericProperty(0)
    velocity = ReferenceListProperty(velocity_x, velocity_y)
    def move(self):
        self.pos = Vector(*self.velocity) + self.pos

class PongGame(Widget):
    ball = ObjectProperty(None)
    player1 = ObjectProperty(None)
    player2 = ObjectProperty(None)
    challenge_level = 1
    game_mode = "BOT"

    def __init__(self, **kwargs):
        super(PongGame, self).__init__(**kwargs)
        
        # Fond noir et graphismes du terrain
        with self.canvas:
            Color(0, 0, 0, 1)
            self.bg = Rectangle(pos=self.pos, size=self.size)
            
        self.bind(pos=self.update_canvas, size=self.update_canvas)

        # Création des composants du jeu
        self.ball = PongBall(size=(30, 30))
        self.player1 = PongPaddle(size=(20, 100))
        self.player2 = PongPaddle(size=(20, 100))
        
        self.add_widget(self.ball)
        self.add_widget(self.player1)
        self.add_widget(self.player2)

        # Labels pour les scores
        self.score1_label = Label(text="0", font_size=50, pos=(200, 500))
        self.score2_label = Label(text="0", font_size=50, pos=(600, 500))
        self.add_widget(self.score1_label)
        self.add_widget(self.score2_label)

    def update_canvas(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.player1.x = 20
        self.player1.center_y = self.center_y
        self.player2.x = self.width - 40
        self.player2.center_y = self.center_y
        self.ball.center = self.center

    def start_game(self):
        self.player1.score = 0
        self.player2.score = 0
        self.ball.center = self.center
        self.ball.velocity = (4 * self.challenge_level, 4 * self.challenge_level)
        Clock.schedule_interval(self.update, 1.0 / 60.0)

    def on_touch_move(self, touch):
        if touch.x < self.width / 2:
            self.player1.center_y = touch.y
        elif self.game_mode == "2P" and touch.x >= self.width / 2:
            self.player2.center_y = touch.y

    def update(self, dt):
        self.ball.move()
        
        self.score1_label.text = str(self.player1.score)
        self.score2_label.text = str(self.player2.score)
        self.score1_label.center_x = self.width / 4
        self.score1_label.top = self.height - 50
        self.score2_label.center_x = self.width * 3 / 4
        self.score2_label.top = self.height - 50

        if self.game_mode == "BOT":
            ai_speed = 2 + (self.challenge_level * 1.5)
            if self.player2.center_y < self.ball.center_y:
                self.player2.center_y += ai_speed
            elif self.player2.center_y > self.ball.center_y:
                self.player2.center_y -= ai_speed

        if self.ball.y < self.y or self.ball.top > self.top:
            self.ball.velocity_y *= -1

        self.player1.bounce_ball(self.ball)
        self.player2.bounce_ball(self.ball)

        if self.ball.x > self.width:
            self.player1.score += 1
            self.reset_ball()
            self.check_win_condition()

        if self.ball.x < self.x:
            self.player2.score += 1
            self.reset_ball()
            if self.game_mode == "2P":
                self.check_win_condition_2p()

    def reset_ball(self):
        self.ball.center = self.center
        self.ball.velocity = (-self.ball.velocity_x, 4)

    def check_win_condition(self):
        if self.game_mode == "BOT" and self.player1.score >= 3:
            Clock.unschedule(self.update)
            self.save_victory_to_backend()

    def check_win_condition_2p(self):
        if self.player2.score >= 3:
            Clock.unschedule(self.update)
            App.get_running_app().root.current = 'mode_menu'

    def save_victory_to_backend(self):
        global current_user
        try:
            res = requests.post(f"{API_URL}/complete-challenge", json={
                "user_id": current_user["id"],
                "challenge_level": self.challenge_level,
                "points": self.player1.score
            })
            if res.status_code == 200:
                current_user["level_unlocked"] = res.json()["level_unlocked"]
        except Exception as e:
            print("Erreur sauvegarde :", e)
        App.get_running_app().root.current = 'challenges_menu'


class GameScreen(Screen):
    def on_enter(self):
        game_widget = self.children[0]
        if hasattr(game_widget, 'start_game'):
            game_widget.start_game()


# --- 5. APPLICATION PRINCIPALE ---
class PongApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(ModeMenuScreen(name='mode_menu'))
        sm.add_widget(ChallengesMenuScreen(name='challenges_menu'))
        
        game_screen = GameScreen(name='game')
        game_screen.add_widget(PongGame())
        sm.add_widget(game_screen)
        
        return sm

if __name__ == '__main__':
    PongApp().run()