"""
main.py - API FastAPI du jeu Pong.
Emplacement : pinponball/backend/main.py
Lancement   : uvicorn main:app --reload   (depuis le dossier backend)
"""
import bcrypt
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db

# Crée les tables au démarrage si elles n'existent pas encore.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Pong API")


# ---------- Outils mot de passe ----------
def hash_password(password: str) -> str:
    """Transforme un mot de passe en hash bcrypt (avec sel intégré)."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Compare un mot de passe saisi au hash stocké."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        # Hash invalide ou corrompu en base : on refuse simplement l'accès.
        return False


# ---------- 1. Inscription ----------
@app.post("/register", response_model=schemas.UserOut)
def register(data: schemas.Credentials, db: Session = Depends(get_db)):
    """Crée un compte avec level_unlocked = 1."""
    user = models.User(
        username=data.username,
        hashed_password=hash_password(data.password),
        level_unlocked=1,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # La contrainte UNIQUE sur username évite aussi les doublons simultanés.
        db.rollback()
        raise HTTPException(status_code=409, detail="Ce nom d'utilisateur existe déjà.")
    db.refresh(user)
    return user


# ---------- 2. Connexion ----------
@app.post("/login", response_model=schemas.UserOut)
def login(data: schemas.Credentials, db: Session = Depends(get_db)):
    """Vérifie les identifiants et renvoie le profil du joueur."""
    user = db.query(models.User).filter(models.User.username == data.username).first()
    # Même message dans les deux cas : on ne révèle pas si le pseudo existe.
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiants incorrects.")
    return user


# ---------- 3. Victoire à un défi ----------
@app.post("/complete-challenge", response_model=schemas.ChallengeResult)
def complete_challenge(data: schemas.ChallengeComplete, db: Session = Depends(get_db)):
    """
    Enregistre la victoire, puis débloque le niveau suivant UNIQUEMENT si
    le niveau gagné est le plus haut débloqué (et qu'il reste un niveau).
    Rejouer un niveau déjà validé ne change donc pas la progression.
    """
    user = db.get(models.User, data.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Joueur introuvable.")

    # On interdit de "gagner" un niveau qu'on n'a pas encore débloqué.
    if data.challenge_level > user.level_unlocked:
        raise HTTPException(status_code=403, detail="Niveau non débloqué.")

    db.add(models.Score(
        user_id=user.id,
        challenge_level=data.challenge_level,
        points=data.points,
    ))

    new_unlocked = False
    if data.challenge_level == user.level_unlocked and user.level_unlocked < schemas.MAX_LEVEL:
        user.level_unlocked += 1
        new_unlocked = True

    db.commit()
    db.refresh(user)
    return schemas.ChallengeResult(
        id=user.id,
        username=user.username,
        level_unlocked=user.level_unlocked,
        new_level_unlocked=new_unlocked,
    )


# 4. Classement
@app.get("/leaderboard", response_model=list[schemas.LeaderboardEntry])
def leaderboard(db: Session = Depends(get_db)):
    """
    Top 10 : niveau débloqué (desc), puis nombre de victoires (desc),
    puis compte le plus ancien (id asc) en cas d'égalité parfaite.
    """
    wins = func.count(models.Score.id)
    rows = (
        db.query(models.User.username, models.User.level_unlocked, wins.label("wins"))
        .outerjoin(models.Score, models.Score.user_id == models.User.id)
        .group_by(models.User.id)
        .order_by(models.User.level_unlocked.desc(), wins.desc(), models.User.id.asc())
        .limit(10)
        .all()
    )
    return [
        schemas.LeaderboardEntry(rank=i, username=r.username,
                                 level_unlocked=r.level_unlocked, wins=r.wins)
        for i, r in enumerate(rows, start=1)
    ]