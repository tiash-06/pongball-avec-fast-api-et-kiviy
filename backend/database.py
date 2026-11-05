"""
database.py - Connexion à la base SQLite via SQLAlchemy.
Emplacement : pinponball/backend/database.py
"""
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Le fichier .db est toujours créé à côté de ce script,
# quel que soit le dossier depuis lequel on lance uvicorn.
DB_PATH = Path(__file__).resolve().parent / "pong_game.db"

# check_same_thread=False : nécessaire car FastAPI utilise plusieurs threads.
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

# Classe de base dont héritent tous les modèles (User, Score).
Base = declarative_base()


def get_db():
    """Fournit une session par requête et la ferme toujours à la fin."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()