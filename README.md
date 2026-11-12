# quiver

Quiver keeps a curated pool of saved commands in a TOML file and inserts the
one you pick into the Claude Code prompt. It works like
[Pet](https://github.com/knqyf263/pet) does in the shell: each entry has a
label, the command and optional tags, and you filter the pool as you type.

The plugin has the selector that reads and filters the file, the path that
puts a command in the prompt, and `/quiver`, which opens a pane to pick from.

## Install

Quiver ships its own marketplace in this repo:

```bash
claude plugin marketplace add sandrop/quiver
claude plugin install quiver@quiver
```

The repo stays private until first-release testing ends.

Quiver needs Python 3.11 or newer, for `tomllib`. On an older interpreter the
selector prints `error [python]: quiver needs Python 3.11+, got 3.9` and exits 2.

## Config

Quiver reads `~/.config/sct/quiver/commands.toml`. Each entry is a
`[[command]]` table:

| Key       | Type            | Required |
| --------- | --------------- | -------- |
| `label`   | string          | yes      |
| `command` | string          | yes      |
| `tags`    | list of strings | no       |

Entries keep their file order. Example:

```toml
[[command]]
label = "Git status"
command = "git status -sb"
tags = ["git"]

[[command]]
label = "Run tests"
command = "~/.venv/bin/python3 -m pytest tests -q"
tags = ["py", "test"]

[[command]]
label = "Validate plugin"
command = "claude plugin validate ."
tags = ["claude"]

[[command]]
label = "List files"
command = "ls -la"
```

### Starter pack

`defaults/commands.toml` holds 34 entries in six groups: sct tooling, prose
replies, Claude Code, git, files and search, and network. Copy it to the
config path with:

```bash
python3 cli/quiver.py init [--config PATH]
```

`init` never overwrites: an existing target, even an empty one, prints
`error [exists]` and exits 2.

Entries come in three kinds, since quiver inserts the text as typed:

- Shell entries start with `! `, so Claude Code runs them in the shell. Each is
  read-only and uses git, `claude` or tools on stock macOS and Debian/Ubuntu,
  with no GNU-only or BSD-only flags.
- Slash commands such as `/rename ` and `/model ...`. The sct tooling group
  calls `/cobtask-workflow:*`, `/cobtask-review:*` and
  `/context-window-manager:*`, which need those plugins installed.
- Prose replies such as `what do you recommend?`.

### Import from Pet

A Pet `snippet.toml` uses `[[Snippets]]` tables, so quiver rejects it with
`no [[command]] entries`. Convert it once:

```bash
~/.venv/bin/python3 scripts/pet_import.py [SNIPPET_TOML] [--out PATH]
```

`SNIPPET_TOML` defaults to `~/.config/pet/snippet.toml` and `--out` to
`~/.config/sct/quiver/commands.toml`.

| Pet key       | quiver key |
| ------------- | ---------- |
| `Description` | `label`    |
| `command`     | `command`  |
| `Tag`         | `tags`     |

Pet's `Output` is dropped. The script never overwrites: an existing target
prints `error [exists]` and exits 2. An entry with a blank `Description` or
`command` fails the whole run; every bad entry is reported by index as
`error [pet]` and nothing is written. If `init` already wrote the starter
pack, move it aside first.

## Selector

```bash
python3 cli/quiver.py list [--config PATH] [--filter TERM]
```

`--filter` splits the term on whitespace, and an entry matches when every
word matches, ignoring case. In the label or one tag, a word's characters
must appear in order, though not necessarily side by side: `gst` matches `Git
status`. The command must contain the word as a substring. Results sort best first: a match at a word
start beats a substring elsewhere, which beats scattered characters, and at the
same quality the label beats the command or a tag. Scores add up over words,
and ties keep file order. A blank term returns every entry in file order. The
output is JSON:

```json
{
  "path": "/Users/you/.config/sct/quiver/commands.toml",
  "entries": [
    {"label": "Git status", "command": "git status -sb", "tags": ["git"]}
  ]
}
```

## Inserting a command

```text
/quiver-insert git status -sb
```

Quiver puts the command into the prompt. Nothing is ever submitted or run: you
read the command, edit it if you like, and press Enter yourself.

When the prompt cannot take the text (a dialog holds the keys, or the session
has no prompt box), quiver copies the command to the clipboard and a toast
says so:

```text
quiver: prompt unavailable (dialog); copied to clipboard
```

When the copy fails too, the toast reads `quiver: could not insert or copy
(<reasons>)`.

## Picking a command

```text
/quiver
```

`/quiver` is the one way to pick; nothing is listed in the transcript. A pane
opens listing every command with its tags, and any text after `/quiver` is
ignored. Type to filter; the pane matches exactly as `list --filter` does.
Press Down to reach the rows, move with the arrows and press Enter to insert
one. Enter in the filter takes the first match. Esc closes the pane. As with
`/quiver-insert`, nothing is submitted.

The pane runs the selector with the `python3` on the session's PATH, which
must be 3.11 or newer. When the config is missing, empty or malformed, the
pane shows the selector's `error [...]` line instead of a list.

## Errors

A missing, unreadable, empty or malformed file, or an entry with a missing or
wrong-typed key, prints one line on stderr and exits 2:

```text
error [config]: /Users/you/.config/sct/quiver/commands.toml: entry 2: command must be a non-empty string
```

When the file is missing, the line ends with
`; run python3 <path to quiver.py> init for a starter pack`.

## Acknowledgements

quiver is modeled on [Pet](https://github.com/knqyf263/pet), the command-line
snippet manager by knqyf263.
