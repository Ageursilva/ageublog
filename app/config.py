import os
from datetime import timedelta


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, "blog.db")
DEFAULT_DATABASE_URL = f"sqlite:///{SQLITE_PATH}"
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


class Config:
    # Sem fallback: chave ausente deve falhar o boot (ver create_app).
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Só ativa em produção via .env (SESSION_COOKIE_SECURE=true);
    # em desenvolvimento (http://localhost) deve permanecer falso.
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "false").lower()
        in ("1", "true", "yes")
    )
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    POSTS_PER_PAGE = 6
    TRUSTED_HOSTS = [
        h.strip()
        for h in os.environ.get(
            "TRUSTED_HOSTS",
            "ageu.blog,www.ageu.blog,localhost,127.0.0.1",
        ).split(",")
        if h.strip()
    ]
