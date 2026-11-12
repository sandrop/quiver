"""Load and filter quiver's commands.toml.

The file holds `[[command]]` tables with `label`, `command` and optional
`tags`. Every problem surfaces as a ConfigError whose message is
"<path>: <problem>", so callers can print it without a traceback.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import tomllib


@dataclass(frozen=True)
class Entry:
    label: str
    command: str
    tags: tuple[str, ...] = ()


class ConfigError(Exception):
    def __init__(self, path: Path, problem: str) -> None:
        super().__init__(f"{path}: {problem}")


def load_commands(path: Path) -> list[Entry]:
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        raise ConfigError(path, "not found") from None
    except (OSError, UnicodeDecodeError) as e:
        raise ConfigError(path, f"cannot read: {e}") from None
    # TOMLDecodeError, the int-digit limit and deep nesting; must stay after
    # the UnicodeDecodeError clause, which is also a ValueError.
    except (ValueError, RecursionError) as e:
        raise ConfigError(path, f"invalid TOML: {e}") from None

    tables = data.get("command")
    if not isinstance(tables, list) or not tables:
        raise ConfigError(path, "no [[command]] entries")
    return [_entry(path, n, t) for n, t in enumerate(tables, 1)]


def _entry(path: Path, n: int, table: object) -> Entry:
    if not isinstance(table, dict):
        raise ConfigError(path, f"entry {n}: must be a [[command]] table")
    for key in ("label", "command"):
        value = table.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(path, f"entry {n}: {key} must be a non-empty string")
    tags = table.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise ConfigError(path, f"entry {n}: tags must be a list of strings")
    return Entry(table["label"], table["command"], tuple(tags))


def filter_entries(entries: list[Entry], term: str) -> list[Entry]:
    """Split term on whitespace; keep entries where every word matches.

    A word matches the label or one tag when its characters appear there in
    order, not necessarily adjacent, ignoring case (`gst` matches `Git
    status`). The command must contain the word as a substring. A word never
    spans two fields.

    Results sort best first: a match at a word start beats a substring
    elsewhere, which beats scattered characters; at the same quality the
    label beats the command or a tag. Each word counts its best field and
    the scores add up over words. Ties keep input order, so a blank term
    returns all entries in input order.
    """
    words = term.casefold().split()
    scored = []
    for e in entries:
        fields = [(e.label.casefold(), 1, True), (e.command.casefold(), 0, False)]
        fields += [(t.casefold(), 0, True) for t in e.tags]
        total = 0
        for w in words:
            best = max(
                (2 * t + b for f, b, z in fields if (t := _score(w, f, z))), default=0
            )
            if not best:
                break
            total += best
        else:
            scored.append((total, e))
    return [e for _, e in sorted(scored, key=lambda s: -s[0])]


def _score(word: str, field: str, fuzzy: bool) -> int:
    # Word start: no letter or digit right before the hit; underscore counts as a separator.
    if re.search(r"(?<![^\W_])" + re.escape(word), field):
        return 3
    if word in field:
        return 2
    return 1 if fuzzy and _subsequence(word, field) else 0


def _subsequence(needle: str, hay: str) -> bool:
    it = iter(hay)
    return all(c in it for c in needle)
