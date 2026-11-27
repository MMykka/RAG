# Back up the app's database with pg_dump (Supabase Free plan has no backups of its own).
#
# Run from backend/:   .venv\Scripts\python.exe -m scripts.backup_database
#
# - Writes backups/rag-YYYY-MM-DD-HHMM.dump in the project root (gitignored: it holds every chat).
# - Backs up only the app's own tables in the "public" schema (users, conversations, messages,
#   chunks, alembic_version) plus the pgvector extension, not Supabase's internal schemas,
#   so the file can be restored into any PostgreSQL 17 with pgvector.
# - Keeps the newest BACKUP_KEEP files (default 14) and deletes older ones.
# - Uses DATABASE_URL_DIRECT (Session pooler, port 5432): pg_dump does not work through the
#   Transaction pooler (6543). The password goes to pg_dump through the PGPASSWORD environment
#   variable, so it is never on the command line (where other programs could see it) or printed.
#
# Check a backup:   pg_restore --list backups\rag-....dump
# Restore (into an empty PostgreSQL 17 database that has pgvector available):
#   pg_restore --no-owner --no-privileges --dbname <target database> backups\rag-....dump
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy.engine import make_url

from app.config import settings

BACKUP_DIR = Path(__file__).resolve().parents[2] / "backups"
PREFIX = "rag-"
SUFFIX = ".dump"
KEEP = int(os.environ.get("BACKUP_KEEP", "14"))
# where winget installs PostgreSQL 17 on Windows (it does not add it to PATH)
WINDOWS_PG_BIN = Path(r"C:\Program Files\PostgreSQL\17\bin")


def find_pg_dump() -> str:
    # PG_DUMP in .env wins, then PATH, then the default Windows install folder
    for candidate in [os.environ.get("PG_DUMP"), shutil.which("pg_dump"), WINDOWS_PG_BIN / "pg_dump.exe"]:
        if candidate and Path(candidate).is_file():
            return str(candidate)
    sys.exit("pg_dump not found: install PostgreSQL 17 (winget install PostgreSQL.PostgreSQL.17) or set PG_DUMP in .env")


def build_command(database_url: str, outfile: Path, pg_dump: str = "pg_dump") -> tuple[list[str], dict]:
    # Split the URL so the password travels in the environment, not in the arguments.
    url = make_url(database_url)
    args = [
        pg_dump,
        "--host", url.host,
        "--port", str(url.port or 5432),
        "--username", url.username,
        "--dbname", url.database,
        "--format", "custom",      # compressed; restore with pg_restore, can restore single tables
        "--schema", "public",      # only the app's tables, not Supabase's own schemas
        "--extension", "vector",   # pgvector, needed for the chunks.embedding column
        "--no-owner",              # Supabase roles do not exist on another server
        "--no-privileges",
        "--file", str(outfile),
    ]
    env = {**os.environ, "PGPASSWORD": url.password or "", "PGSSLMODE": "require"}
    return args, env


def prune(folder: Path, keep: int) -> list[Path]:
    # Delete all but the newest `keep` backups (the names sort by date). Returns what was deleted.
    backups = sorted(folder.glob(f"{PREFIX}*{SUFFIX}"))
    old = backups[:-keep] if keep > 0 else backups
    for path in old:
        path.unlink()
    return old


def main() -> None:
    BACKUP_DIR.mkdir(exist_ok=True)
    outfile = BACKUP_DIR / f"{PREFIX}{datetime.now():%Y-%m-%d-%H%M}{SUFFIX}"
    args, env = build_command(settings.database_url_direct, outfile, find_pg_dump())

    result = subprocess.run(args, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        outfile.unlink(missing_ok=True)  # never leave a half-written backup behind
        sys.exit(f"Backup failed (pg_dump exit {result.returncode}):\n{result.stderr.strip()}")

    size_kb = outfile.stat().st_size / 1024
    print(f"Backup written: {outfile.name} ({size_kb:.0f} KB)")
    for path in prune(BACKUP_DIR, KEEP):
        print(f"Deleted old backup: {path.name}")


if __name__ == "__main__":
    main()
