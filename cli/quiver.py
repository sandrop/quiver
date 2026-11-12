#!/usr/bin/env python3
"""quiver selector: print saved commands from commands.toml as JSON.

Usage: quiver.py list [--config PATH] [--filter TERM]
       quiver.py init [--config PATH]

`list` prints {"path": ..., "entries": [{"label", "command", "tags"}]} on stdout.
`init` copies the starter pack in defaults/commands.toml to the config path and
never overwrites an existing file.
Python-version, config, starter and write errors print one `error [<code>]: ...` line on stderr
and exit 2. Invalid arguments use argparse's usage and error output.

This file must parse on Python 3.9 so the version guard below can run there.
"""

from __future__ import annotations

import sys

MIN_PYTHON = (3, 11)


def python_error(version: tuple[int, ...]) -> str | None:
    if tuple(version[:2]) < MIN_PYTHON:
        return (
            f"error [python]: quiver needs Python 3.11+, got {version[0]}.{version[1]}"
        )
    return None


# The guard runs before the lib/ import, which pulls in tomllib (3.11+).
_msg = python_error(sys.version_info)
if _msg:
    print(_msg, file=sys.stderr)
    sys.exit(2)

import argparse
import json
import shlex
from dataclasses import asdict
from pathlib import Path

# Direct-execution bootstrap: put the sibling lib/ on sys.path so `import
# commands` resolves when this file is run as a script (tests get the path
# from conftest.py instead).
_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from commands import ConfigError, filter_entries, load_commands

STARTER = Path(__file__).resolve().parent.parent / "defaults" / "commands.toml"


def default_config_path() -> Path:
    return Path.home() / ".config/sct/quiver/commands.toml"


def init(path: Path) -> int:
    # Read and validate the starter before touching the target, so a broken
    # install never leaves a config that a later init would refuse to replace.
    try:
        count = len(load_commands(STARTER))
        text = STARTER.read_text(encoding="utf-8")
    except ConfigError as e:
        print(f"error [starter]: {e}", file=sys.stderr)
        return 2
    except (OSError, UnicodeDecodeError) as e:
        print(f"error [starter]: {STARTER}: cannot read: {e}", file=sys.stderr)
        return 2
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"error [write]: {path}: {e}", file=sys.stderr)
        return 2
    try:
        f = open(path, "x", encoding="utf-8")  # noqa: SIM115 - `with f:` below; split so only a created file is removed
    except FileExistsError:
        print(f"error [exists]: {path} already exists", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error [write]: {path}: {e}", file=sys.stderr)
        return 2
    try:
        with f:
            f.write(text)
    except OSError as e:
        print(f"error [write]: {path}: {e}", file=sys.stderr)
        # Exclusive creation succeeded, so remove our incomplete target.
        try:
            path.unlink(missing_ok=True)
        except OSError as cleanup_error:
            print(
                f"error [write]: {path}: could not remove incomplete target: {cleanup_error}",
                file=sys.stderr,
            )
        return 2
    print(f"wrote {count} entries to {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="quiver")
    sub = parser.add_subparsers(dest="cmd", required=True)
    ls = sub.add_parser("list", help="print entries as JSON")
    ls.add_argument("--config", type=Path, default=None, help="commands.toml path")
    ls.add_argument("--filter", default="", help="match label, tags or command")
    it = sub.add_parser("init", help="write the starter commands.toml")
    it.add_argument("--config", type=Path, default=None, help="commands.toml path")
    args = parser.parse_args(argv)

    path = args.config or default_config_path()
    if args.cmd == "init":
        return init(path)
    try:
        entries = filter_entries(load_commands(path), args.filter)
    except ConfigError as e:
        hint = ""
        try:
            missing = not path.exists()
        except OSError:
            # Existence is unknown (e.g. an unsearchable parent), so no hint.
            missing = False
        if missing:
            cmd = ["python3", str(Path(__file__).resolve()), "init"]
            if args.config:
                cmd += ["--config", str(path)]
            hint = f"; run {shlex.join(cmd)} for a starter pack"
        print(f"error [config]: {e}{hint}", file=sys.stderr)
        return 2
    entries_json = [asdict(e) for e in entries]
    print(json.dumps({"path": str(path), "entries": entries_json}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
