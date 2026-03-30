import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def get_database_url():
    url = os.getenv("DATABASE_URL", "")

    # Render fournit postgres://, SQLAlchemy veut postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    # psycopg3 utilise postgresql+psycopg:// au lieu de postgresql://
    if url.startswith("postgresql://") and "+psycopg" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    if not url:
        url = "sqlite:///" + os.path.join(BASE_DIR, "portfolio.db")
        print("[WARNING] DATABASE_URL non défini — SQLite utilisé (non persistant)")
    else:
        print(f"[DB] Connexion PostgreSQL (psycopg3) ✓")

    return url


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    SQLALCHEMY_DATABASE_URI = get_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_timeout": 30,
    }
    UPLOAD_FOLDER  = os.path.join(BASE_DIR, "static", "uploads")
    PROFILE_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "profile")
    PHOTOS_FOLDER  = os.path.join(BASE_DIR, "static", "uploads", "photos")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
