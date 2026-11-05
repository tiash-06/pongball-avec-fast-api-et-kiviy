"""
session.py - État global du joueur connecté pendant la partie.
Emplacement : pinponball/client/session.py

Usage :  from session import session
         session.user["username"]
"""


class Session:
    """Garde en mémoire le profil renvoyé par l'API (id, username, level_unlocked)."""

    def __init__(self):
        self.user = None

    @property
    def is_logged_in(self):
        return self.user is not None

    def login(self, user):
        self.user = dict(user)

    def logout(self):
        self.user = None

    def update_level(self, level_unlocked):
        """Met à jour le niveau débloqué après une victoire."""
        if self.user is not None:
            self.user["level_unlocked"] = level_unlocked


# Instance unique partagée par tout le client.
session = Session()