"""
engine.py - Moteur du jeu : physique de la balle, raquettes, score et bot.
Emplacement : pinponball/client/engine.py

Aucune dépendance à Kivy : toute la logique est ici, l'affichage est dans game.py.
Le terrain est en unités abstraites (W x H) ; game.py les convertit en pixels,
donc le jeu garde les mêmes proportions quelle que soit la taille de la fenêtre.
Axe Y vers le HAUT (comme Kivy) : y = 0 en bas du terrain.
"""
import math
import random

# Dimensions du terrain (unités abstraites) 
W, H = 180.0, 100.0
PADDLE_W, PADDLE_H = 2.6, 20.0
PADDLE_MARGIN = 5.0          # distance entre une raquette et le bord du terrain
BALL_R = 1.9                 # rayon de la balle

# ---------- Règles ----------
WIN_SCORE = 3                # points pour gagner une manche
PLAYER_SPEED = 95.0          # vitesse des raquettes au clavier (unités / s)
MAX_ANGLE = math.radians(55) # angle maximal de renvoi (bord de raquette)
SPEEDUP = 1.06               # la balle accélère de 6 % à chaque raquette touchée
MAX_SPEED_FACTOR = 1.7       # plafond : 1,7 x la vitesse de départ
SERVE_DELAY = 0.9            # pause (s) avant chaque service
START_DELAY = 1.3            # pause (s) au début de la manche
MAX_DT = 1 / 30              # un gros lag ne doit jamais "téléporter" la balle


def clamp(value, low, high):
    return max(low, min(high, value))


class Bot:
    """
    Intelligence artificielle de la raquette de droite.
    Trois réglages définissent la difficulté :
      speed    : vitesse max de la raquette (unités/s)
      reaction : délai (s) entre deux "décisions" -> plus c'est long, plus il est lent à réagir
      error    : erreur de visée aléatoire (unités) ajoutée à chaque décision
      aim      : 0 à 1, le bot frappe volontairement la balle avec le bord de sa raquette
                 pour la renvoyer en angle (sinon les échanges ne finiraient jamais)
    """

    def __init__(self, speed, reaction, error, aim=0.0):
        self.speed = speed
        self.reaction = reaction
        self.error = error
        self.aim = aim
        self.target = H / 2
        self._timer = 0.0

    def _choose_target(self, engine):
        """Décide où se placer. Retourne le centre quand la balle s'éloigne."""
        if engine.vx <= 0:
            return H / 2
        # Le bot suit la position ACTUELLE de la balle (il n'anticipe pas les rebonds) :
        # c'est sa vitesse limitée qui le fait rater les tirs rapides et en angle.
        y = engine.by
        # Décalage voulu : toucher la balle avec le haut ou le bas de la raquette.
        offset = random.uniform(-self.aim, self.aim) * (PADDLE_H / 2)
        return y - offset + random.uniform(-self.error, self.error)

    def update(self, dt, engine, paddle_y):
        """Retourne la nouvelle position de la raquette."""
        self._timer -= dt
        if self._timer <= 0:
            self._timer = self.reaction
            self.target = self._choose_target(engine)

        diff = self.target - paddle_y
        step = self.speed * dt
        if abs(diff) <= step:
            return self.target
        return paddle_y + math.copysign(step, diff)


class PongEngine:
    """
    État complet d'une manche. Le joueur 1 est à gauche (côté 0),
    le joueur 2 ou le bot à droite (côté 1).
    """

    def __init__(self, ball_speed, bot=None):
        self.base_speed = ball_speed
        self.max_speed = ball_speed * MAX_SPEED_FACTOR
        self.bot = bot
        self.left_y = H / 2
        self.right_y = H / 2
        self.scores = [0, 0]
        self.winner = None            # None, 0 (gauche) ou 1 (droite)
        self.bx = self.by = self.vx = self.vy = 0.0
        self.serve_timer = 0.0
        self._serve(random.choice((-1, 1)), START_DELAY)

    #  Service
    def _serve(self, direction, delay=SERVE_DELAY):
        """Replace la balle au centre, à vitesse de base, direction = -1 (gauche) ou +1 (droite)."""
        angle = random.uniform(-0.35, 0.35)
        self.bx, self.by = W / 2, H / 2
        self.vx = direction * self.base_speed * math.cos(angle)
        self.vy = self.base_speed * math.sin(angle)
        self.serve_timer = delay

    # Raquettes 
    def set_paddle(self, side, y):
        """Place directement une raquette (souris / tactile)."""
        y = clamp(y, PADDLE_H / 2, H - PADDLE_H / 2)
        if side == 0:
            self.left_y = y
        else:
            self.right_y = y

    def _move_paddles(self, dt, left_dir, right_dir):
        lo, hi = PADDLE_H / 2, H - PADDLE_H / 2
        self.left_y = clamp(self.left_y + left_dir * PLAYER_SPEED * dt, lo, hi)
        if self.bot:
            self.right_y = clamp(self.bot.update(dt, self, self.right_y), lo, hi)
        else:
            self.right_y = clamp(self.right_y + right_dir * PLAYER_SPEED * dt, lo, hi)

    # Boucle principale 
    def update(self, dt, left_dir=0, right_dir=0):
        """Avance le jeu de dt secondes. left_dir / right_dir valent -1, 0 ou +1."""
        if self.winner is not None:
            return
        dt = min(dt, MAX_DT)
        self._move_paddles(dt, left_dir, right_dir)

        if self.serve_timer > 0:
            self.serve_timer -= dt
            return

        # Sous-pas : la balle n'avance jamais de plus de ~75 % de son rayon d'un coup,
        # ce qui empêche de traverser une raquette (effet "tunnel") même à grande vitesse.
        speed = math.hypot(self.vx, self.vy)
        steps = max(1, math.ceil(speed * dt / (BALL_R * 0.75)))
        for _ in range(steps):
            self._step(dt / steps)
            if self.serve_timer > 0 or self.winner is not None:
                break

    def _step(self, dt):
        self.bx += self.vx * dt
        self.by += self.vy * dt

        # Rebond sur les murs haut et bas.
        if self.by < BALL_R:
            self.by, self.vy = BALL_R, abs(self.vy)
        elif self.by > H - BALL_R:
            self.by, self.vy = H - BALL_R, -abs(self.vy)

        # Raquette gauche : face avant à x = marge + largeur.
        left_face = PADDLE_MARGIN + PADDLE_W
        if (self.vx < 0 and self.bx - BALL_R <= left_face
                and self.bx + BALL_R >= PADDLE_MARGIN
                and abs(self.by - self.left_y) <= PADDLE_H / 2 + BALL_R * 0.6):
            self._bounce(side=0, face_x=left_face + BALL_R)

        # Raquette droite.
        right_face = W - PADDLE_MARGIN - PADDLE_W
        if (self.vx > 0 and self.bx + BALL_R >= right_face
                and self.bx - BALL_R <= W - PADDLE_MARGIN
                and abs(self.by - self.right_y) <= PADDLE_H / 2 + BALL_R * 0.6):
            self._bounce(side=1, face_x=right_face - BALL_R)

        # Balle sortie du terrain : point pour l'autre joueur.
        if self.bx + BALL_R < 0:
            self._point(scorer=1)
        elif self.bx - BALL_R > W:
            self._point(scorer=0)

    def _bounce(self, side, face_x):
        """Renvoie la balle : l'angle dépend de l'endroit touché sur la raquette."""
        paddle_y = self.left_y if side == 0 else self.right_y
        offset = clamp((self.by - paddle_y) / (PADDLE_H / 2), -1, 1)  # -1 bas ... +1 haut
        speed = min(math.hypot(self.vx, self.vy) * SPEEDUP, self.max_speed)
        angle = offset * MAX_ANGLE
        direction = 1 if side == 0 else -1
        self.vx = direction * speed * math.cos(angle)
        self.vy = speed * math.sin(angle)
        self.bx = face_x  # on sort la balle de la raquette

    def _point(self, scorer):
        self.scores[scorer] += 1
        if self.scores[scorer] >= WIN_SCORE:
            self.winner = scorer
            return
        # Celui qui a encaissé le point reçoit le service (balle vers lui).
        self._serve(direction=1 if scorer == 0 else -1)