import os
from pathlib import Path


# find the ENV file

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

# Load the ENV file into the environment variables, goes through each line and skips the stuff it can't use mainly blank lines, comments and lines with no =
def _load_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        #stores the value as an environment variable, but only if one with that name doesn’t already exist. So a variable set by Docker or the server wins over the .env file.
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env(ENV_FILE)


def _psycopg2(url: str) -> str:
    # SQLAlchemy 2.1 defaults plain postgresql:// to psycopg (v3); the stack uses psycopg2. mainly to use psycopg2 to speak with supabase instead of psycopg3, which is the default in SQLAlchemy 2.1. This is because psycopg3 is not compatible with some existing code and libraries that expect psycopg2.
    return url.replace("postgresql://", "postgresql+psycopg2://", 1)

# settings is the one place where your app’s configuration lives, so the rest of the code never has to read .env or environment variables itself. without it, every file that needs the database URL would do its own thing
class Settings:
    # Direct/session connection: used by Alembic migrations.
    database_url_direct: str = _psycopg2(os.environ.get("DATABASE_URL_DIRECT", ""))
    # Pooler connection (port 6543): used by the running app. Falls back to the direct URL until it is added.
    database_url: str = _psycopg2(os.environ.get("DATABASE_URL", "")) or database_url_direct
    
    secret_key: str = os.environ.get("SECRET_KEY", "")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    # Secure cookie = sent only over HTTPS. Off on this PC (plain http://localhost), set COOKIE_SECURE=true on the server at go-live.
    cookie_secure: bool = os.environ.get("COOKIE_SECURE", "false").lower() == "true"



settings = Settings()
if not settings.secret_key:
    raise RuntimeError("SECRET_KEY is missing from .env")

