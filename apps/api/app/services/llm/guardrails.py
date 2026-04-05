from __future__ import annotations

import re

def sanitize_user_message(content: str, *, max_chars: int) -> str:
    """Strip null bytes and bound length before persisting or sending upstream."""
    s = content.replace("\x00", "")
    if len(s) > max_chars:
        s = s[:max_chars]
    return s


def _strip_controls(s: str) -> str:
    out: list[str] = []
    for ch in s:
        o = ord(ch)
        if ch in "\n\r\t" or o >= 32:
            out.append(ch)
    return "".join(out)


# Light output hygiene — not a full HTML sanitizer (frontend should still escape).
_UNSAFE_SUBS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"<\s*script\b", re.IGNORECASE), "[removed]"),
    (re.compile(r"<\s*/\s*script\s*>", re.IGNORECASE), "[removed]"),
    (re.compile(r"javascript\s*:", re.IGNORECASE), "[removed]"),
    (re.compile(r"on\w+\s*=", re.IGNORECASE), "[removed]"),
)


def sanitize_assistant_output(content: str, *, max_chars: int) -> str:
    s = _strip_controls(content.replace("\x00", ""))
    for pat, repl in _UNSAFE_SUBS:
        s = pat.sub(repl, s)
    if len(s) > max_chars:
        suffix = "\n\n[Assistant reply truncated for length.]"
        s = s[: max(0, max_chars - len(suffix))] + suffix
    return s
