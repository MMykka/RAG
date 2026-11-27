# Tests for scripts/backup_database.py that need neither pg_dump nor the database.
from pathlib import Path

from scripts.backup_database import build_command, prune

URL = "postgresql+psycopg2://postgres.abc:s3cr%40t-pw@aws-0-eu-west-3.pooler.supabase.com:5432/postgres"


def test_password_is_not_on_the_command_line(tmp_path):
    args, env = build_command(URL, tmp_path / "x.dump")
    assert not any("s3cr" in a for a in args)  # never in the arguments (other programs can see those)
    assert env["PGPASSWORD"] == "s3cr@t-pw"    # %40 in the URL is decoded to @
    assert env["PGSSLMODE"] == "require"


def test_command_targets_the_app_tables_on_the_session_pooler(tmp_path):
    args, _ = build_command(URL, tmp_path / "x.dump")
    pairs = dict(zip(args[1::2], args[2::2]))
    assert pairs["--host"] == "aws-0-eu-west-3.pooler.supabase.com"
    assert pairs["--port"] == "5432"
    assert pairs["--username"] == "postgres.abc"
    assert pairs["--dbname"] == "postgres"
    assert pairs["--format"] == "custom"
    assert pairs["--schema"] == "public"
    assert pairs["--extension"] == "vector"
    assert "--no-owner" in args and "--no-privileges" in args


def test_prune_keeps_the_newest(tmp_path):
    names = [f"rag-2026-11-{day:02d}-0300.dump" for day in range(1, 21)]  # 20 daily backups
    for name in names:
        (tmp_path / name).write_text("x")
    (tmp_path / "notes.txt").write_text("not a backup")

    deleted = prune(tmp_path, keep=14)
    left = sorted(p.name for p in tmp_path.glob("rag-*.dump"))
    assert left == names[-14:]                       # the 14 newest stay
    assert [p.name for p in deleted] == names[:6]    # the 6 oldest are gone
    assert (tmp_path / "notes.txt").exists()         # other files are never touched


def test_prune_with_fewer_backups_than_keep(tmp_path):
    (tmp_path / "rag-2026-11-27-0300.dump").write_text("x")
    assert prune(tmp_path, keep=14) == []
    assert len(list(tmp_path.glob("*.dump"))) == 1
