"""Talking to the private source database.

Shared by the B4 export scripts. The two B2 scripts still carry their own copies
of this and predate it. Merging them is a change to a working export path with no
reader-visible gain, so it waits for a reason rather than riding along here.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

CONTAINER = "meu-feed-catolico-api-mysql-1"


def git(source: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(source), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def read_credentials(source: Path) -> dict[str, str]:
    env = {}
    for line in (source / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith(("DB_USERNAME=", "DB_PASSWORD=", "DB_DATABASE=")):
            key, _, value = line.partition("=")
            env[key] = value
    return {
        "user": env["DB_USERNAME"],
        "password": env["DB_PASSWORD"],
        "database": env["DB_DATABASE"],
    }


def query(container: str, credentials: dict[str, str], sql: str) -> str:
    """Runs SQL in the source container and returns the single value it selects.

    Credentials go in on stdin as a defaults file rather than on the command
    line. On the command line they reach `ps`, and they reach the traceback of
    any failure, because CalledProcessError prints the whole argument list.

    utf8mb4 is not optional either. The client defaults to latin1 here, which
    brings every accented character back as a raw byte and would corrupt the
    entire Portuguese and Latin corpus silently.
    """
    defaults = "[client]\nuser={user}\npassword={password}\n".format(**credentials)
    result = subprocess.run(
        [
            "docker",
            "exec",
            "-i",
            container,
            "mysql",
            "--defaults-extra-file=/dev/stdin",
            "--default-character-set=utf8mb4",
            credentials["database"],
            "-N",
            "-B",
            "--raw",
            "-e",
            sql,
        ],
        input=defaults.encode("utf-8"),
        capture_output=True,
    )
    if result.returncode != 0:
        reason = result.stderr.decode("utf-8").strip()
        raise RuntimeError(f"the source database refused the query: {reason}")
    return result.stdout.decode("utf-8").strip()


def refuse_a_dirty_tree(source: Path) -> str | None:
    """The whole tree, not only the fixtures.

    Provenance names a commit and the tables are a function of the import code as
    much as of the input files, so an uncommitted change to the importer makes
    that record wrong too.
    """
    dirty = git(source, "status", "--porcelain")
    return f"the source repository has uncommitted changes:\n{dirty}" if dirty else None
