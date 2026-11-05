"""
api.py - Communication avec le backend FastAPI.
Emplacement : pinponball/client/api.py

Chaque appel s'exécute dans un thread séparé : l'interface Kivy ne se fige
jamais pendant la requête. Les callbacks (on_success / on_error) sont
ensuite rappelés sur le thread principal de Kivy, donc sûrs pour modifier l'UI.
"""
import threading

import requests
from kivy.clock import Clock

API_URL = "http://127.0.0.1:8000"
TIMEOUT = 5  # secondes avant d'abandonner une requête

# Messages lisibles pour les erreurs de validation (code 422) du backend.
_FIELD_MESSAGES = {
    "username": "Nom d'utilisateur : 3 à 20 caractères.",
    "password": "Mot de passe : 4 à 64 caractères.",
}


def _extract_error(response):
    """Transforme une réponse d'erreur de l'API en message pour le joueur."""
    try:
        detail = response.json().get("detail")
    except ValueError:
        return "Erreur du serveur."

    if isinstance(detail, str):          # 401, 403, 404, 409 : message direct
        return detail
    if isinstance(detail, list) and detail:  # 422 : liste d'erreurs de champs
        field = detail[0].get("loc", [""])[-1]
        return _FIELD_MESSAGES.get(field, "Données invalides.")
    return "Requête invalide."


def _request(method, path, on_success, on_error, json=None):
    """Lance la requête en arrière-plan et rappelle le bon callback."""

    def worker():
        try:
            response = requests.request(method, f"{API_URL}{path}", json=json, timeout=TIMEOUT)
        except (requests.ConnectionError, requests.Timeout):
            result = (False, "Serveur injoignable. Le backend est-il lancé ?")
        except requests.RequestException:
            result = (False, "Erreur réseau.")
        else:
            if response.ok:
                result = (True, response.json())
            else:
                result = (False, _extract_error(response))

        ok, payload = result
        # Retour sur le thread principal de Kivy.
        Clock.schedule_once(lambda dt: (on_success if ok else on_error)(payload))

    threading.Thread(target=worker, daemon=True).start()


# ---------- Fonctions publiques ----------
def login(username, password, on_success, on_error):
    _request("POST", "/login", on_success, on_error,
             json={"username": username, "password": password})


def register(username, password, on_success, on_error):
    _request("POST", "/register", on_success, on_error,
             json={"username": username, "password": password})


    def complete_challenge(user_id, level, points, on_success, on_error):
    """Enregistre une victoire. Réponse : {id, username, level_unlocked, new_level_unlocked}."""
    _request("POST", "/complete-challenge", on_success, on_error,
             json={"user_id": user_id, "challenge_level": level, "points": points})