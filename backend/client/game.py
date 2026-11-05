"""
game.py - Widget du terrain de jeu : affichage, clavier et tactile.
Emplacement : pinponball/client/game.py

La logique (physique, bot, score) est dans engine.py ; ici on ne fait que
dessiner l'état du moteur et lui transmettre les commandes du joueur.
Les formes graphiques sont créées une seule fois puis seulement déplacées
à chaque image (pas de redessin complet : plus rapide).
"""
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget

import theme
from engine import BALL_R, H, PADDLE_H, PADDLE_MARGIN, PADDLE_W, W, Bot, PongEngine
from levels import get_level

# Codes des touches (Kivy / SDL2).
KEY_W, KEY_S = 119, 115
KEY_UP, KEY_DOWN = 273, 274

DUO_BALL_SPEED = 85.0   # vitesse de balle du mode 2 joueurs
FPS = 60


class PongField(Widget):
    """Terrain : teal, raquettes beiges, balle corail."""

    score_left = NumericProperty(0)
    score_right = NumericProperty(0)

    # Événement envoyé quand un joueur atteint le score gagnant (argument : 0 gauche, 1 droite).
    __events__ = ("on_match_end",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.engine = None
        self.mode = "BOT"          # "BOT" (solo) ou "2P" (duo)
        self.paused = False
        self._keys = set()         # touches actuellement enfoncées
        self._clock = None

        # Formes graphiques créées une seule fois.
        with self.canvas:
            Color(*theme.TEAL)
            self._bg = RoundedRectangle(radius=[dp(16)])
            Color(*theme.BEIGE[:3], 0.35)
            self._net = Line(width=dp(1.5))
            Color(*theme.BEIGE)
            self._left = RoundedRectangle(radius=[dp(4)])
            self._right = RoundedRectangle(radius=[dp(4)])
            Color(*theme.CORAL)
            self._ball = Ellipse()
        self.bind(pos=self._redraw, size=self._redraw)

    # ---------- Cycle de vie d'une manche ----------
    def start(self, mode, level=1):
        """Démarre une nouvelle manche."""
        self.stop()
        self.mode = mode
        if mode == "BOT":
            cfg = get_level(level)
            self.engine = PongEngine(cfg["ball_speed"], Bot(**cfg["bot"]))
        else:
            self.engine = PongEngine(DUO_BALL_SPEED)
        self.score_left = self.score_right = 0
        self.paused = False
        self._keys.clear()
        self._clock = Clock.schedule_interval(self._tick, 1 / FPS)
        self._redraw()

    def stop(self):
        """Arrête la boucle de jeu (appelé en quittant l'écran ou en fin de manche)."""
        if self._clock is not None:
            self._clock.cancel()
            self._clock = None

    @property
    def is_running(self):
        return self._clock is not None and self.engine is not None and self.engine.winner is None

    def _tick(self, dt):
        engine = self.engine
        if engine is None or self.paused:
            return
        left_dir, right_dir = self._inputs()
        engine.update(dt, left_dir, right_dir)
        self.score_left, self.score_right = engine.scores
        self._redraw()
        if engine.winner is not None:
            self.stop()
            self.dispatch("on_match_end", engine.winner)

    def on_match_end(self, winner):
        """Valeur par défaut de l'événement (l'écran de jeu s'y lie dans pong.kv)."""

    # ---------- Clavier ----------
    def key_down(self, key):
        self._keys.add(key)

    def key_up(self, key):
        self._keys.discard(key)

    def _inputs(self):
        """Retourne (direction gauche, direction droite) : -1 bas, 0 immobile, +1 haut."""
        keys = self._keys
        wasd = (KEY_W in keys) - (KEY_S in keys)
        arrows = (KEY_UP in keys) - (KEY_DOWN in keys)
        if self.mode == "BOT":
            # Solo : W/S et flèches commandent tous les deux la raquette de gauche.
            return max(-1, min(1, wasd + arrows)), 0
        return wasd, arrows  # Duo : W/S = joueur 1, flèches = joueur 2

    # ---------- Souris / tactile ----------
    def on_touch_down(self, touch):
        return self._touch(touch)

    def on_touch_move(self, touch):
        return self._touch(touch)

    def _touch(self, touch):
        engine = self.engine
        if (engine is None or self.paused or engine.winner is not None
                or not self.collide_point(*touch.pos)):
            return False
        scale, _, oy = self._geometry()
        # En solo, tout le terrain commande la raquette gauche ; en duo, chaque moitié la sienne.
        side = 0 if self.mode == "BOT" or touch.x < self.center_x else 1
        engine.set_paddle(side, (touch.y - oy) / scale)
        return True

    # ---------- Dessin ----------
    def _geometry(self):
        """Échelle et origine du terrain, centré avec ses proportions conservées."""
        scale = min(self.width / W, self.height / H)
        ox = self.x + (self.width - W * scale) / 2
        oy = self.y + (self.height - H * scale) / 2
        return scale, ox, oy

    def _redraw(self, *_):
        scale, ox, oy = self._geometry()
        engine = self.engine
        left_y = engine.left_y if engine else H / 2
        right_y = engine.right_y if engine else H / 2
        bx = engine.bx if engine else W / 2
        by = engine.by if engine else H / 2

        self._bg.pos, self._bg.size = (ox, oy), (W * scale, H * scale)
        mid = ox + W * scale / 2
        self._net.points = [mid, oy + dp(10), mid, oy + H * scale - dp(10)]

        paddle_size = (PADDLE_W * scale, PADDLE_H * scale)
        self._left.size = self._right.size = paddle_size
        self._left.pos = (ox + PADDLE_MARGIN * scale, oy + (left_y - PADDLE_H / 2) * scale)
        self._right.pos = (ox + (W - PADDLE_MARGIN - PADDLE_W) * scale,
                           oy + (right_y - PADDLE_H / 2) * scale)

        self._ball.size = (2 * BALL_R * scale, 2 * BALL_R * scale)
        self._ball.pos = (ox + (bx - BALL_R) * scale, oy + (by - BALL_R) * scale)