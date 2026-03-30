import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_database_url():
    url = os.getenv("DATABASE_URL", "")

    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    if not url:
        # Fallback SQLite local (développement uniquement)
        # Sur Render, DATABASE_URL doit toujours être défini
        url = "sqlite:///" + os.path.join(BASE_DIR, "portfolio.db")
        print("[WARNING] DATABASE_URL non défini — utilisation de SQLite (données non persistantes !)")
    else:
        print(f"[DB] Connexion PostgreSQL détectée ✓")

    return url


class Config:
    SECRET_KEY          = os.getenv("SECRET_KEY", "change-this-in-production")
    SQLALCHEMY_DATABASE_URI     = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,       # vérifie la connexion avant chaque requête
        "pool_recycle": 300,         # recycle les connexions toutes les 5 min
        "pool_timeout": 30,
        "connect_args": {} if "postgresql" in get_database_url() else {},
    }
    UPLOAD_FOLDER   = os.path.join(BASE_DIR, "static", "uploads")
    PROFILE_FOLDER  = os.path.join(BASE_DIR, "static", "uploads", "profile")
    PHOTOS_FOLDER   = os.path.join(BASE_DIR, "static", "uploads", "photos")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ADMIN_USERNAME  = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD  = os.getenv("ADMIN_PASSWORD", "admin123")
