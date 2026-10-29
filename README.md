# 👻 GhostShell

**A haunted terminal companion, with open-source AI at its core.**

> *This is a submission for the Hacktoberfest Open-Source AI Challenge Week 4: Ghost in the Machine*

GhostShell explains shell commands before you run them — in the voice of
a ghost that has haunted Unix since 1971. It tells you what a command
does, where it came from, and whether it is about to delete your life's
work. Then, by default, it runs **nothing**.

## What it does

```bash
python -m ghostshell explain "ls -la"
python -m ghostshell explain "rm -rf /"
python -m ghostshell seance cobol "Who are you?"
python -m ghostshell --interactive
```

Example (offline fallback, no model needed):

```
👻  ghostshell whispers about: rm -rf /
    danger: critical
    lore:   rm (1971, early Unix): removes files. ...
    The ghost shudders. ... DO NOT RUN THIS as written.
    [dry-run: nothing was executed.]
```

Safety rules, by design:

- **Explain by default, never execute.** Execution needs `--execute`
  *and* an explicit `y` confirmation.
- **Critical commands are refused outright**, even with `--execute`:
  `rm -rf /`, `mkfs`, `dd ... of=/dev/...`, and friends.
- **Danger detection is rule-based and testable** (`tests/test_core.py`),
  not left to a model that might miss `rm -rf`.

## Open-source AI at the core

If [Ollama](https://ollama.com) is running locally, GhostShell asks a
local open-weight model to whisper — default `gemma3`:

```bash
ollama pull gemma3
python -m ghostshell explain "grep -r TODO ."
```

Set another model or host with:

```bash
GHOSTSHELL_MODEL=gemma3:4b GHOSTSHELL_OLLAMA_HOST=http://localhost:11434 \
  python -m ghostshell explain "git push --force"
```

If Ollama is not running, GhostShell still gives a complete answer from
its rule engine. No API key, no cloud call, no account. That fallback is
the point, not a limitation: the ghost lives on your machine, or not
at all.

The model prompt is constrained to verified lore handed to it
(`ghostshell/core.py: LORE`), so it cannot invent a fake birth year for
a command it does not know. Unknown commands say so, plainly.

## Why open innovation matters here

A closed terminal assistant would send every command you type — your
file names, your server names, your mistakes — to someone else's
server, and stop working when that service changes its price or shuts
down. GhostShell does the opposite:

- Your commands never leave your machine in offline mode, and in
  Ollama mode they only go to `localhost`.
- You can swap the model (`gemma3` today, another open-weight model
  tomorrow) without rewriting the tool.
- It costs nothing to run, and it keeps working with the internet off.
  A ghost that needs the cloud is not a ghost, it is a subscription.

## Run it

Zero third-party dependencies. Python 3.10+ only.

```bash
python -m ghostshell explain "ls -la"
python -m pytest tests/ -q   # or: python -m unittest discover -s tests -v
```

## Prize categories

- **Best Use of Gemma**: GhostShell's default local model is Gemma 3
  via Ollama. Run `ollama pull gemma3` and the whisper comes from
  Gemma, on your own machine.

## How it is built

- `ghostshell/core.py` — danger patterns, verified command lore,
  Ollama client, offline fallback.
- `ghostshell/cli.py` — `explain`, `seance`, and the interactive REPL.
- `tests/test_core.py` — danger levels, lore honesty, fallback behaviour.

Built during Hacktoberfest Week 4 (Oct 26–31, 2026) as a brand-new
project. No code was copied from other Week 4 submissions.
