"""
schemas.py - Formats des données échangées avec le client (validation Pydantic).
Emplacement : pinponball/backend/schemas.py
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_LEVEL = 5


class Credentials(BaseModel):
    """Corps des requêtes /register et /login."""
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=4, max_length=64)

    @field_validator("username")
    @classmethod
    def clean_username(cls, v: str) -> str:
        # On retire les espaces autour : "  bob " devient "bob".
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Le nom d'utilisateur doit faire au moins 3 caractères.")
        return v


class UserOut(BaseModel):
    """Ce que l'API renvoie sur un joueur (jamais le mot de passe)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    level_unlocked: int


class ChallengeComplete(BaseModel):
    """Corps de /complete-challenge."""
    user_id: int
    challenge_level: int = Field(ge=1, le=MAX_LEVEL)
    points: int = Field(ge=0)


class ChallengeResult(BaseModel):
    """Réponse de /complete-challenge."""
    id: int
    username: str
    level_unlocked: int
    new_level_unlocked: bool  # True si cette victoire a débloqué le niveau suivant


class LeaderboardEntry(BaseModel):
    """Une ligne du classement."""
    rank: int
    username: str
    level_unlocked: int
    wins: int