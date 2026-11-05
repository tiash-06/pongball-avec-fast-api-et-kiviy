"""
models.py - Tables de la base de données.
Emplacement : pinponball/backend/models.py
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    """Un joueur : identifiants + niveau maximal débloqué."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)  # jamais le mot de passe en clair
    level_unlocked = Column(Integer, default=1, nullable=False)  # de 1 à 5

    scores = relationship("Score", back_populates="user")


class Score(Base):
    """Une victoire enregistrée à un défi (sert au classement)."""
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_level = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)
    date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="scores")