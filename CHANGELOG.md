# Changelog

## 0.10.1 - 2026-11-12

- The README drops its private-repo note now that `sandrop/quiver` is public (QVR-0015).

## 0.10.0 - 2026-11-12

- First public release, from `sandrop/quiver`. The README install section now names that repo and its `quiver` marketplace; the dev install routes are gone (QVR-0006).
- Adds the MIT `LICENSE` that plugin.json already named (QVR-0006).

## 0.9.0 - 2026-11-11

- Breaking: the starter pack is rebuilt around what quiver inserts into a prompt, from 29 to 34 entries. Shell entries now start with `! ` so Claude Code runs them; in 0.8.0 `git status -sb` landed as plain prompt text. New groups: sct tooling (`/cobtask-workflow:*`, `/cobtask-review:*` and `/context-window-manager:handoff`, which need those plugins), prose replies, and Claude Code (`/rename `, `/model ...` and `! claude ...` checks). The processes and disk groups and most files entries are gone. `init` never overwrites, so an existing config keeps its old entries: copy what you want from `defaults/commands.toml` by hand, or run `init --config` on a fresh path (QVR-0014).
- `tests/test_defaults.py` checks each entry by kind (ADR-0007): the portable-binary, flag and `sh`-parse guards run on the text after `! `, slash commands must match `/name` plus an optional space, and the read-only deny list still covers every entry (QVR-0014).
- README credits [Pet](https://github.com/knqyf263/pet) by knqyf263, which quiver is modeled on (QVR-0014).

## 0.8.0 - 2026-11-11

- Breaking: a word now matches the command only as a substring. A term that found an entry only through letters scattered across its command text no longer finds it, so short terms return shorter lists (`dust` drops from 47 hits to 3 on a 107-entry pool). The label and tags still accept scattered characters: `gst` matches `Git status`. To find such an entry again, type a contiguous part of its command, or add the abbreviation you use to its label or tags (QVR-0013).

## 0.7.0 - 2026-11-10

- Breaking: filtered results no longer keep file order. They sort best first: word-start matches, then substrings, then scattered characters, with the label above the command or a tag at the same quality; ties keep file order (QVR-0011). Enter in the pane's filter takes the first result, so a term may now insert a different command than in 0.6.0. To pick in file order, clear the filter: a blank term still lists every entry in file order.
- Fuzzy filter for the selector and the pane: each whitespace-separated word must appear, characters in order, in the label, the command or one tag (`gst` matches `Git status`). Every word must match (QVR-0008).

## 0.6.0 - 2026-11-09

- Starter pack in `defaults/commands.toml`: 29 read-only, portable entries for git, files and search, processes, network and disk (QVR-0009).
- `quiver.py init [--config PATH]` copies the starter pack to the config path. It never overwrites an existing file.
- The missing-config error now names `init`.
- ADR-0004: the starter pack ships through an explicit `init` subcommand.

## 0.5.0 - 2026-11-09

- `/quiver` opens the pane; `/quiver-panel` is removed, with no alias (QVR-0010).
- ADR-0003: no list mode in the transcript, and no picker reads a choice by dropping a prompt in `prompt.submit`.

## 0.4.0 - 2026-11-08

- `/quiver-panel` pane mode: a pane listing every entry with its tags (QVR-0005).
- Typing in the pane filters through the selector (`list --filter`), so the pane matches exactly as list mode does.
- Enter on a row, or in the filter for the first match, inserts the command through `insertCommand` and closes the pane. Nothing is submitted.
- The pane is never blank: it shows the selector's `error [...]` line, `error [selector]: ...` when `python3` cannot run or prints unreadable output, or `No command matches "<term>".`

## 0.3.0 - 2026-11-08

- `scripts/pet_import.py`: one-shot import of a Pet `snippet.toml` into `commands.toml` (QVR-0007).

## 0.2.0 - 2026-11-08

- Insertion entry point `insertCommand` in `hooks/insert.ts`, the one path list mode and pane mode call. It puts the command in the prompt at the cursor and never submits it.
- Clipboard fallback: when the prompt cannot take the text, quiver copies the command and shows a toast saying why. When the copy fails too, the toast says neither worked.
- `/quiver-insert <command>` slash command.

## 0.1.0 - 2026-11-07

- Plugin skeleton: `.claude-plugin/plugin.json` and a marketplace whose source is the repo root.
- `commands.toml` loader: `[[command]]` entries with `label`, `command` and optional `tags`, kept in file order; every problem is a one-line `error [config]` naming the path.
- Filter over label, tags and command, case-insensitive.
- `list` selector printing JSON.
- Python version guard: on Python older than 3.11 the selector prints `error [python]` and exits 2 instead of a traceback.
