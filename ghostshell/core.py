"""GhostShell core: danger detection, command lore, and ghost commentary.

Zero third-party dependencies. The open-weight model path is optional:
if Ollama is running locally, GhostShell asks it (default: gemma3) to
whisper. If it is not, a rule-based fallback still gives a complete,
accurate answer, so the tool works offline, on a laptop, with no key
and no data leaving the machine.
"""
from __future__ import annotations

import json
import os
import re
import urllib.request

# Real, checkable lore only. No invented history: if a command is not
# in this table, the ghost says so instead of hallucinating a birth year.
LORE = {
    "ls": ("1971, early Unix", "lists files. It has watched directories fill and empty for fifty years."),
    "cd": ("1971, early Unix", "changes directory. Every ghost has a favourite room it keeps returning to."),
    "pwd": ("1971, early Unix", "prints where you are. Useful when you no longer recognise the hallway."),
    "cp": ("1971, early Unix", "copies a file. A copy is not a resurrection, only an echo."),
    "mv": ("1971, early Unix", "moves or renames a file. Things moved in the dark are rarely found again."),
    "rm": ("1971, early Unix", "removes files. The deadliest ordinary command: deletion here has no afterlife by default."),
    "grep": ("1973, Unix", "searches text for a pattern. It listens for a name whispered in a file."),
    "find": ("1970s, Unix", "walks a directory tree looking for something lost."),
    "cat": ("1971, early Unix", "concatenates and prints files. It reads aloud what was left behind."),
    "echo": ("1971, early Unix", "repeats words back. In an empty shell, that is the closest thing to a reply."),
    "chmod": ("1971, early Unix", "changes permissions. Opening every door at once is how hauntings start."),
    "chown": ("1971, early Unix", "changes file ownership. Someone else's name on the door changes who may enter."),
    "ps": ("1970s, Unix", "lists running processes. A census of everything still alive in this machine."),
    "kill": ("1971, early Unix", "sends a signal to a process, often to end it. Say the name carefully."),
    "ssh": ("1995, OpenSSH lineage", "opens an encrypted shell on another machine. A knock on a distant door."),
    "git": ("2005, Linus Torvalds", "tracks changes. A commit is a message left for whoever comes next."),
    "curl": ("1998, Daniel Stenberg", "transfers data over a URL. It knocks and asks a server to speak."),
    "wget": ("1996, GNU Wget", "downloads files. It carries things home from the internet."),
    "tar": ("1979, Unix", "archives files. A bundle tied up and stored in the attic."),
    "docker": ("2013, Docker", "runs containers. Small sealed rooms, each with its own ghost."),
    "python": ("1991, Guido van Rossum", "runs Python code. The snake in the machine."),
    "node": ("2009, Ryan Dahl", "runs JavaScript outside a browser. A spirit that escaped its original house."),
}

DEAD_LANGUAGES = {
    "cobol": ("1959", "business data processing. It still runs banks and payrolls, quietly, in the basement."),
    "fortran": ("1957", "scientific computing. It calculated orbits before most of us were born."),
    "pascal": ("1970", "teaching and structured programming. A strict schoolteacher, now retired."),
    "apl": ("1966", "array programming. It spoke in symbols most mortals could not read."),
    "basic": ("1964", "beginners' programming. Many programmers met their first ghost here."),
}

# Ordered: first match wins, so critical patterns are checked first.
_DANGER_PATTERNS = [
    ("critical", re.compile(r"\brm\s+-[^\s]*r[^\s]*f\b.*\s/(\s|$)")),
    ("critical", re.compile(r"\brm\s+-[^\s]*r[^\s]*f\b.*\s/\*")),
    ("critical", re.compile(r"\bmkfs\b")),
    ("critical", re.compile(r"\bdd\b.*\bof=/dev/")),
    ("critical", re.compile(r">\s*/dev/sd[a-z]")),
    ("critical", re.compile(r"\bchmod\s+-R\s+777\s+/")),
    ("high", re.compile(r"\brm\s+-[^\s]*r[^\s]*f\b")),
    ("high", re.compile(r"\brm\s+-[^\s]*f\b")),
    ("high", re.compile(r"\|\s*(sh|bash)\s*$")),
    ("high", re.compile(r"\bcurl\b.*\|\s*(sh|bash)")),
    ("high", re.compile(r"\bwget\b.*\|\s*(sh|bash)")),
    ("high", re.compile(r"\bchmod\s+777\b")),
    ("high", re.compile(r"\bkill\s+-9\b")),
    ("high", re.compile(r"\bgit\s+push\s+--force\b")),
    ("medium", re.compile(r"\brm\b")),
    ("medium", re.compile(r"\bmv\b")),
    ("medium", re.compile(r"\bgit\s+push\b")),
    ("medium", re.compile(r"\bdocker\s+(rm|system\s+prune)\b")),
    ("medium", re.compile(r"\bsudo\b")),
]

_DANGER_ADVICE = {
    "critical": "DO NOT RUN THIS as written. It can destroy a system or a disk. Stop, back up, and rewrite it with an explicit, narrow target.",
    "high": "High risk. Double-check the target, add a backup or a dry run first, and never pipe a remote script straight into a shell.",
    "medium": "Reversible only if you have a copy. Confirm the target before you press enter.",
    "low": "Ordinary risk. Still read it once before running.",
}


def parse_command(text: str) -> str:
    """Return the first word of a command line, lower-cased."""
    text = (text or "").strip()
    if not text:
        return ""
    # Strip a leading sudo so `sudo rm` is still recognised as rm.
    if text.startswith("sudo "):
        text = text[5:].lstrip()
    return text.split()[0].lower() if text.split() else ""


def danger_level(command: str) -> str:
    """Return critical / high / medium / low for a command line."""
    text = (command or "").strip()
    for level, pattern in _DANGER_PATTERNS:
        if pattern.search(text):
            return level
    return "low"


def _ollama_whisper(command: str, lore: str, level: str) -> str | None:
    """Ask a local Ollama model. Returns None if Ollama is unavailable.

    No API key, no cloud call. The prompt constrains the model to the
    facts we hand it, so it cannot invent a fake history for a command.
    """
    host = os.environ.get("GHOSTSHELL_OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("GHOSTSHELL_MODEL", "gemma3")
    prompt = (
        "You are a friendly ghost haunting a terminal. In at most 3 short "
        "sentences, in a spooky but clear tone, explain what this shell "
        "command does and warn about its danger level. Use ONLY these facts "
        f"about the command, do not invent history: {lore}. "
        f"Command: {command}. Danger level: {level}."
    )
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        host.rstrip("/") + "/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return None
    text = (data.get("response") or "").strip()
    return text or None


def ghost_commentary(command: str) -> dict:
    """Explain a command. Always returns a complete answer, with or
    without a local model. Keys: command, base, danger, lore, whisper, source."""
    command = (command or "").strip()
    base = parse_command(command)
    level = danger_level(command)
    if base in LORE:
        year, note = LORE[base]
        lore = f"{base} ({year}): {note}"
    else:
        lore = f"{base or 'this command'}: no verified lore in GhostShell's table, so the ghost will not invent a history for it."
    whisper = _ollama_whisper(command, lore, level)
    if whisper:
        return {
            "command": command, "base": base, "danger": level,
            "lore": lore, "whisper": whisper, "source": "ollama:" + os.environ.get("GHOSTSHELL_MODEL", "gemma3"),
        }
    if level == "critical":
        whisper = f"The ghost shudders. {lore} {_DANGER_ADVICE[level]}"
    elif level in ("high", "medium"):
        whisper = f"The ghost leans close and whispers: {lore} {_DANGER_ADVICE[level]}"
    else:
        whisper = f"The ghost drifts by and murmurs: {lore} {_DANGER_ADVICE[level]}"
    return {
        "command": command, "base": base, "danger": level,
        "lore": lore, "whisper": whisper, "source": "offline-fallback",
    }


def seance(language: str, question: str) -> dict:
    """A seance with a dead programming language. Fallback answers are
    templates, never fake model output; a local model may rewrite them."""
    key = (language or "").strip().lower()
    year, note = DEAD_LANGUAGES.get(key, ("unknown year", "a language whose story GhostShell has not yet recorded."))
    lore = f"{key} ({year}): {note}"
    prompt_q = (question or "").strip() or "Tell me who you are."
    whisper = _ollama_whisper(f"seance {key}: {prompt_q}", lore, "low")
    if not whisper:
        whisper = (
            f"The spirit of {key} stirs. {note} "
            f"You asked: '{prompt_q}'. In its own era it would have answered in {key.upper()} "
            "style, line by line, with no cloud, no account, and no one else listening. "
            "That is the point: it runs here, on your machine, or not at all."
        )
    return {"language": key, "lore": lore, "whisper": whisper}
