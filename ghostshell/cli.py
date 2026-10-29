"""GhostShell command line interface.

Safety rule, by design: GhostShell explains by default and never
executes. Execution only happens with --execute AND an explicit
`y` confirmation, and critical commands are refused outright.
"""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys

from .core import danger_level, ghost_commentary, seance


def _print_result(result: dict) -> None:
    print(f"\n👻  ghostshell whispers about: {result['command']}")
    print(f"    danger: {result['danger']}")
    print(f"    lore:   {result['lore']}")
    print(f"    {result['whisper']}")
    print(f"    [source: {result['source']}]")


def _maybe_execute(command: str, execute: bool) -> int:
    if not execute:
        print("    [dry-run: nothing was executed. Add --execute to run it, after confirming.]")
        return 0
    level = danger_level(command)
    if level == "critical":
        print("    [refused: critical command. GhostShell will not run this.]")
        return 2
    answer = input("    The ghost asks: run this for real? [y/N] ").strip().lower()
    if answer != "y":
        print("    [aborted by you. Nothing was executed.]")
        return 0
    try:
        proc = subprocess.run(shlex.split(command))
        return proc.returncode
    except Exception as exc:  # e.g. command not found, bad quoting
        print(f"    [could not run: {exc}]")
        return 1


def _interactive(execute: bool) -> int:
    print("👻  Welcome to GhostShell. Type a shell command and the ghost will explain it.")
    print("    Type `exit` or press Ctrl-C / Ctrl-D to leave. Nothing runs unless you pass --execute and confirm.")
    try:
        while True:
            try:
                line = input("ghostshell> ").strip()
            except EOFError:
                print()
                break
            if not line or line in ("exit", "quit"):
                break
            if line.startswith("seance "):
                parts = line.split(maxsplit=2)
                lang = parts[1] if len(parts) > 1 else "cobol"
                question = parts[2] if len(parts) > 2 else "Tell me who you are."
                result = seance(lang, question)
                print(f"\n👻  {result['whisper']}\n    [lore: {result['lore']}]")
                continue
            result = ghost_commentary(line)
            _print_result(result)
            code = _maybe_execute(line, execute)
            if code not in (0,):
                print(f"    [exit code: {code}]")
    except KeyboardInterrupt:
        print("\n    The ghost fades away. Goodbye.")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="ghostshell", description="A haunted terminal companion. Explains shell commands with a local open-weight model, or offline.")
    sub = parser.add_subparsers(dest="cmd")

    p_explain = sub.add_parser("explain", help="Explain one command (dry-run by default)")
    p_explain.add_argument("command", help='e.g. "ls -la" or "rm -rf build"')
    p_explain.add_argument("--execute", action="store_true", help="Ask to actually run it after explaining")

    p_seance = sub.add_parser("seance", help="Hold a seance with a dead programming language")
    p_seance.add_argument("language", help="e.g. cobol, fortran, pascal, apl, basic")
    p_seance.add_argument("question", nargs="?", default="Tell me who you are.")

    parser.add_argument("--interactive", action="store_true", help="Start the haunted REPL")
    parser.add_argument("--execute", action="store_true", help="With --interactive, allow execution after confirmation")
    args = parser.parse_args(argv)

    if args.cmd == "explain":
        result = ghost_commentary(args.command)
        _print_result(result)
        return _maybe_execute(args.command, args.execute)
    if args.cmd == "seance":
        result = seance(args.language, args.question)
        print(f"\n👻  {result['whisper']}\n    [lore: {result['lore']}]")
        return 0
    if args.interactive or args.cmd is None:
        return _interactive(args.execute)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
