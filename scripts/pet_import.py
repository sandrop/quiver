#!/usr/bin/env python3
"""Convert a Pet snippet.toml into a quiver commands.toml.

Usage: pet_import.py [SNIPPET_TOML] [--out PATH]

Maps Pet's Description, command and Tag to label, command and tags in file
order; Output is dropped. Any bad entry, an unreadable Pet file or an existing
target prints one `error [<code>]: ...` line per problem on stderr, exits 2
and writes nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import tomllib


class PetError(Exception):
    def __init__(self, problems: list[str]) -> None:
        super().__init__("\n".join(problems))
        self.problems = problems


def toml_string(s: str) -> str:
    # JSON's escapes are a subset of TOML basic-string escapes; DEL is the one
    # character TOML forbids raw that json.dumps leaves alone.
    return json.dumps(s, ensure_ascii=False).replace("\x7f", "\\u007f")


def _problems(n: int, s: object) -> list[str]:
    if not isinstance(s, dict):
        return [f"entry {n}: must be a [[Snippets]] table"]
    out = []
    for key in ("Description", "command"):
        value = s.get(key)
        if not isinstance(value, str) or not value.strip():
            out.append(f"entry {n}: {key} must be a non-empty string")
    tags = s.get("Tag", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        out.append(f"entry {n}: Tag must be a list of strings")
    return out


def convert(snippets: list, path: Path) -> str:
    problems = [
        f"{path}: {p}" for n, s in enumerate(snippets, 1) for p in _problems(n, s)
    ]
    if problems:
        raise PetError(problems)
    blocks = []
    for s in snippets:
        lines = [
            "[[command]]",
            f"label = {toml_string(s['Description'])}",
            f"command = {toml_string(s['command'])}",
        ]
        if s.get("Tag"):
            lines.append(f"tags = [{', '.join(toml_string(t) for t in s['Tag'])}]")
        blocks.append("\n".join(lines) + "\n")
    return "\n".join(blocks)


def read_snippets(path: Path) -> list:
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise PetError([f"{path}: not found"]) from None
    except (OSError, UnicodeDecodeError) as e:
        raise PetError([f"{path}: cannot read: {e}"]) from None
    # Must stay after the UnicodeDecodeError clause, which is also a ValueError.
    except (ValueError, RecursionError) as e:
        raise PetError([f"{path}: invalid TOML: {e}"]) from None

    snippets = data.get("Snippets")
    if not isinstance(snippets, list) or not snippets:
        raise PetError([f"{path}: no [[Snippets]] entries"])
    return snippets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pet_import")
    parser.add_argument(
        "pet",
        nargs="?",
        type=Path,
        default=Path.home() / ".config/pet/snippet.toml",
        help="Pet snippet.toml path",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path.home() / ".config/sct/quiver/commands.toml",
        help="commands.toml to create",
    )
    args = parser.parse_args(argv)

    try:
        snippets = read_snippets(args.pet)
        text = convert(snippets, args.pet)
    except PetError as e:
        for problem in e.problems:
            print(f"error [pet]: {problem}", file=sys.stderr)
        return 2
    try:
        args.out.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"error [write]: {args.out}: {e}", file=sys.stderr)
        return 2
    try:
        f = open(args.out, "x", encoding="utf-8")  # noqa: SIM115 - `with f:` below; split so only a created file is removed
    except FileExistsError:
        print(f"error [exists]: {args.out} already exists", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error [write]: {args.out}: {e}", file=sys.stderr)
        return 2
    try:
        with f:
            f.write(text)
    except OSError as e:
        print(f"error [write]: {args.out}: {e}", file=sys.stderr)
        # Exclusive creation succeeded, so remove our incomplete target.
        try:
            args.out.unlink(missing_ok=True)
        except OSError as cleanup_error:
            print(
                f"error [write]: {args.out}: could not remove incomplete target: {cleanup_error}",
                file=sys.stderr,
            )
        return 2
    print(f"wrote {len(snippets)} entries to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
