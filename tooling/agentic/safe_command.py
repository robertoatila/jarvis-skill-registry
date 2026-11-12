"""Run one command line as an argument vector, never through a shell.

Several runtime paths receive a command as text (a verification requirement,
a patch test command, an infrastructure task).  Passing that text to
``subprocess`` with ``shell=True`` lets the text chain commands, redirect
output and substitute subcommands.  This module is the single place that turns
such text into an argument vector and starts exactly one process.

Scope and limits (stated so the guarantee is not overread):

- What it guarantees: no shell interprets the text.  Operators (``;``, ``&&``,
  ``|``, redirections, subshells, command substitution) are refused with
  :class:`CommandRejected` instead of being passed to the program as literal
  arguments, so a command that depended on them fails loudly.
- What it does not do: it is not a sandbox and not an allowlist.  The named
  program still runs with the caller's privileges; callers keep their own
  authorization gates.  Variable expansion (``$HOME``, ``%PATH%``), tilde
  expansion and globbing (``*.py``) are not performed, because there is no
  shell to do it: such text reaches the program literally.
- The Windows splitting rules are the inverse of ``subprocess.list2cmdline``
  and are exercised by tests through the ``windows`` parameter; they have not
  been run on a Windows host from this repository's test battery.

Pure Python standard library.
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Mapping, Optional, Sequence, Union

__all__ = [
    "CommandRejected",
    "split_command",
    "resolve_executable",
    "run_command_line",
    "display_command",
]

Command = Union[str, Sequence[str]]

# Characters cmd.exe re-interprets when Windows starts a batch file.
_BATCH_UNSAFE_CHARS = frozenset('&|<>^%!()"\r\n')
_BATCH_SUFFIXES = (".bat", ".cmd")


class CommandRejected(ValueError):
    """The command text cannot be run as a single process without a shell."""


def _is_windows(windows: Optional[bool]) -> bool:
    return (os.name == "nt") if windows is None else bool(windows)


def _reject_shell_syntax_posix(command: str) -> None:
    quote = ""
    index = 0
    length = len(command)
    while index < length:
        char = command[index]
        if quote == "'":
            if char == "'":
                quote = ""
        elif quote == '"':
            if char == "\\" and index + 1 < length:
                if command[index + 1] in "`$\r\n":
                    # A shell and shlex disagree on these escapes; refuse instead of guessing.
                    raise CommandRejected("ambiguous escape inside double quotes: use single quotes")
                index += 1
            elif char == '"':
                quote = ""
            elif char == "`" or command.startswith("$(", index):
                raise CommandRejected("command substitution is not supported: there is no shell")
        else:
            if char == "\\" and index + 1 < length:
                if command[index + 1] in "\r\n":
                    raise CommandRejected("a command must be a single line")
                index += 1
            elif char in "'\"":
                quote = char
            elif char in "\r\n":
                raise CommandRejected("a command must be a single line")
            elif char == "`" or command.startswith("$(", index):
                raise CommandRejected("command substitution is not supported: there is no shell")
            elif char == "#" and (index == 0 or command[index - 1] in " \t"):
                raise CommandRejected("shell comments are not supported: quote the '#' if it is an argument")
            elif char in ";&|<>()":
                raise CommandRejected(
                    f"shell operator {char!r} is not supported: pass one command, without chaining or redirection"
                )
        index += 1


def _split_windows(command: str) -> list[str]:
    """Split with the Microsoft C runtime rules (inverse of ``list2cmdline``)."""
    argv: list[str] = []
    current: list[str] = []
    in_quotes = False
    started = False
    index = 0
    length = len(command)
    while index < length:
        char = command[index]
        if char == "\\":
            run = 0
            while index < length and command[index] == "\\":
                run += 1
                index += 1
            if index < length and command[index] == '"':
                current.append("\\" * (run // 2))
                if run % 2:
                    current.append('"')
                    index += 1
            else:
                current.append("\\" * run)
            started = True
            continue
        if char == '"':
            if in_quotes and index + 1 < length and command[index + 1] == '"':
                current.append('"')
                index += 2
                continue
            in_quotes = not in_quotes
            started = True
        elif char in " \t" and not in_quotes:
            if started:
                argv.append("".join(current))
                current = []
                started = False
        elif char in "\r\n":
            raise CommandRejected("a command must be a single line")
        elif char in "&|<>" and not in_quotes:
            raise CommandRejected(
                f"shell operator {char!r} is not supported: pass one command, without chaining or redirection"
            )
        else:
            current.append(char)
            started = True
        index += 1
    if in_quotes:
        raise CommandRejected("unbalanced quotation in command")
    if started:
        argv.append("".join(current))
    return argv


def split_command(command: Command, *, windows: Optional[bool] = None) -> list[str]:
    """Return the argument vector for ``command`` or raise :class:`CommandRejected`.

    A sequence is taken as an already split argument vector.  Text is split
    with the quoting rules of the host platform (``windows`` overrides the
    detection, which is what the tests use).
    """
    if isinstance(command, (bytes, bytearray)):
        raise CommandRejected("command must be text or a sequence of text arguments")
    if not isinstance(command, str):
        try:
            argv = list(command)
        except TypeError as exc:
            raise CommandRejected("command must be text or a sequence of text arguments") from exc
        if not all(isinstance(part, str) for part in argv):
            raise CommandRejected("every command argument must be text")
    else:
        if "\x00" in command:
            raise CommandRejected("command contains a NUL character")
        if _is_windows(windows):
            argv = _split_windows(command)
        else:
            _reject_shell_syntax_posix(command)
            try:
                argv = shlex.split(command, posix=True)
            except ValueError as exc:
                raise CommandRejected(f"command cannot be parsed: {exc}") from exc
    if not argv or not argv[0].strip():
        raise CommandRejected("command is empty")
    if any("\x00" in part for part in argv):
        raise CommandRejected("command contains a NUL character")
    return argv


def resolve_executable(
    argv: Sequence[str],
    *,
    env: Optional[Mapping[str, str]] = None,
    windows: Optional[bool] = None,
) -> list[str]:
    """Resolve a bare program name through ``PATH`` (and ``PATHEXT`` on Windows).

    A program given with a directory component is left untouched so that it
    keeps resolving against the child's working directory.  An unknown name is
    also left untouched: starting it raises ``FileNotFoundError`` at the call
    site, which is reported as a failed command rather than hidden here.
    """
    resolved = list(argv)
    program = resolved[0]
    if not (os.sep in program or (os.altsep and os.altsep in program) or "/" in program):
        search_path = None if env is None else env.get("PATH")
        found = shutil.which(program, path=search_path)
        if found:
            resolved[0] = found
    if _is_windows(windows) and resolved[0].lower().endswith(_BATCH_SUFFIXES):
        for argument in resolved[1:]:
            if _BATCH_UNSAFE_CHARS.intersection(argument):
                raise CommandRejected(
                    "arguments with cmd.exe metacharacters cannot be passed to a batch file safely"
                )
    return resolved


def display_command(command: Command) -> str:
    """Return a single-line rendering of ``command`` for logs and evidence."""
    if isinstance(command, str):
        return command
    return " ".join(shlex.quote(str(part)) for part in command)


def run_command_line(
    command: Command,
    *,
    cwd: Optional[Union[str, Path]] = None,
    timeout: Optional[float] = None,
    env: Optional[Mapping[str, str]] = None,
) -> "subprocess.CompletedProcess[str]":
    """Start exactly one process for ``command`` and capture its text output.

    Raises :class:`CommandRejected` before anything is started when the text
    needs a shell, ``FileNotFoundError`` when the program does not exist, and
    ``subprocess.TimeoutExpired`` after the child has been killed.
    """
    argv = resolve_executable(split_command(command), env=env)
    return subprocess.run(  # noqa: S603 - argument vector, shell is never used
        argv,
        shell=False,
        cwd=str(cwd) if cwd is not None else None,
        env=dict(env) if env is not None else None,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )
