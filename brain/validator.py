"""JS-code validator for OmniPlay-MC.

We block obvious escape hatches before handing code to the bridge. The bridge
itself runs the body inside an `(async (...) => { ... })()` wrapper with only
named arguments in scope, but a static check catches outright dangerous calls
earlier (and produces a clearer dashboard message).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from models import JsCodeAction, RecoveryTransition

LUA_DENY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("os.execute", re.compile(r"\bos\.execute\s*\(")),
    ("io.popen", re.compile(r"\bio\.popen\s*\(")),
    ("load", re.compile(r"\bload\s*\(")),
    ("loadstring", re.compile(r"\bloadstring\s*\(")),
    ("dofile", re.compile(r"\bdofile\s*\(")),
    ("require", re.compile(r"\brequire\s*\(")),
]

DENY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("require()", re.compile(r"\brequire\s*\(")),
    ("dynamic import", re.compile(r"\bimport\s*\(")),
    ("process.*", re.compile(r"\bprocess\s*\.")),
    ("fs/path", re.compile(r"\b(?:fs|path|os|child_process)\s*\.")),
    ("http", re.compile(r"\b(?:fetch|XMLHttpRequest|http\s*\.|https\s*\.)")),
    ("eval", re.compile(r"\beval\s*\(")),
    ("Function ctor", re.compile(r"\bnew\s+Function\s*\(")),
    ("global", re.compile(r"\b(?:globalThis|global)\s*\.")),
]


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    status: RecoveryTransition
    reason: str = ""


class Validator:
    def validate_action(self, action: JsCodeAction) -> ValidationResult:
        code = action.code
        if not code or not code.strip():
            return ValidationResult(False, RecoveryTransition.REPLAN, "empty code")
        for label, pattern in DENY_PATTERNS:
            if pattern.search(code):
                return ValidationResult(False, RecoveryTransition.REPLAN, f"forbidden token: {label}")
        if len(code) > 32_000:
            return ValidationResult(False, RecoveryTransition.REPLAN, "code too long (>32KB)")
        return ValidationResult(True, RecoveryTransition.CONTINUE, "")

    def validate_lua(self, code: str) -> ValidationResult:
        if not code or not code.strip():
            return ValidationResult(False, RecoveryTransition.REPLAN, "empty code")
        for label, pattern in LUA_DENY_PATTERNS:
            if pattern.search(code):
                return ValidationResult(False, RecoveryTransition.REPLAN, f"forbidden token: {label}")
        return ValidationResult(True, RecoveryTransition.CONTINUE, "")


__all__ = ["ValidationResult", "Validator"]
