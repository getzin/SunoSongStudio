# backend/services/auth_service.py

import bcrypt
from backend.models.users import create_user, get_user_by_email


def login_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None
    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return None
    return user


def register_user(email: str, username: str, password: str):
    if get_user_by_email(email):
        return False, "Email already registered."

    if len(password) < 4:
        return False, "Password must be at least 4 characters."

    hash_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    create_user(email, username, hash_pw)
    return True, None
