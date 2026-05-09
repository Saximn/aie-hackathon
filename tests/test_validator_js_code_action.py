"""Tests for Validator.validate_action (JS code).

Public interface under test:
    Validator.validate_action(action: JsCodeAction) -> ValidationResult
    ValidationResult.ok: bool
    ValidationResult.reason: str
"""

from __future__ import annotations

import sys
from pathlib import Path

BRAIN_ROOT = Path(__file__).resolve().parents[1] / "brain"
sys.path.insert(0, str(BRAIN_ROOT))

import unittest

from models import JsCodeAction
from validator import ValidationResult, Validator


def _make_action(code: str) -> JsCodeAction:
    return JsCodeAction(id="test-1", code=code)


class TestValidatorJsCodeAction(unittest.TestCase):
    def setUp(self):
        self.v = Validator()

    # ------------------------------------------------------------------
    # test_validate_rejects_empty_code
    # ------------------------------------------------------------------
    def test_validate_rejects_empty_code(self):
        for code in ("", "   ", "\t\n"):
            with self.subTest(code=repr(code)):
                result = self.v.validate_action(_make_action(code))
                self.assertFalse(result.ok)

    # ------------------------------------------------------------------
    # test_validate_accepts_simple_safe_code
    # ------------------------------------------------------------------
    def test_validate_accepts_simple_safe_code(self):
        result = self.v.validate_action(_make_action("await bot.chat('hi');"))
        self.assertTrue(result.ok)

    # ------------------------------------------------------------------
    # test_validate_rejects_require
    # ------------------------------------------------------------------
    def test_validate_rejects_require(self):
        result = self.v.validate_action(_make_action("const fs = require('fs');"))
        self.assertFalse(result.ok)
        self.assertIn("require", result.reason)

    # ------------------------------------------------------------------
    # test_validate_rejects_eval
    # ------------------------------------------------------------------
    def test_validate_rejects_eval(self):
        result = self.v.validate_action(_make_action("eval('malicious()');"))
        self.assertFalse(result.ok)
        self.assertIn("eval", result.reason)

    # ------------------------------------------------------------------
    # test_validate_rejects_dynamic_import
    # ------------------------------------------------------------------
    def test_validate_rejects_dynamic_import(self):
        result = self.v.validate_action(_make_action("const m = import('module');"))
        self.assertFalse(result.ok)

    # ------------------------------------------------------------------
    # test_validate_rejects_code_over_limit
    # ------------------------------------------------------------------
    def test_validate_rejects_code_over_limit(self):
        big = "x" * 32_001
        result = self.v.validate_action(_make_action(big))
        self.assertFalse(result.ok)
        self.assertIn("too long", result.reason)


if __name__ == "__main__":
    unittest.main()
