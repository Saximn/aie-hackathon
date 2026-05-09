"""Tests for Validator.validate_lua (Lua code).

Public interface under test:
    Validator.validate_lua(code: str) -> ValidationResult
    ValidationResult.ok: bool
    ValidationResult.reason: str
"""

from __future__ import annotations

import sys
from pathlib import Path

BRAIN_ROOT = Path(__file__).resolve().parents[1] / "brain"
sys.path.insert(0, str(BRAIN_ROOT))

import unittest

from validator import Validator


class TestValidatorLua(unittest.TestCase):
    def setUp(self):
        self.v = Validator()

    # ------------------------------------------------------------------
    # test_lua_validate_accepts_safe_code
    # ------------------------------------------------------------------
    def test_lua_validate_accepts_safe_code(self):
        result = self.v.validate_lua('game.player.print("hi")')
        self.assertTrue(result.ok)

    # ------------------------------------------------------------------
    # test_lua_validate_rejects_os_execute
    # ------------------------------------------------------------------
    def test_lua_validate_rejects_os_execute(self):
        result = self.v.validate_lua("os.execute('rm -rf /')")
        self.assertFalse(result.ok)
        self.assertIn("os.execute", result.reason)

    # ------------------------------------------------------------------
    # test_lua_validate_rejects_io_popen
    # ------------------------------------------------------------------
    def test_lua_validate_rejects_io_popen(self):
        result = self.v.validate_lua("local f = io.popen('ls')")
        self.assertFalse(result.ok)
        self.assertIn("io.popen", result.reason)

    # ------------------------------------------------------------------
    # test_lua_validate_rejects_load
    # ------------------------------------------------------------------
    def test_lua_validate_rejects_load(self):
        for snippet in ("load('evil')", "loadstring('evil')"):
            with self.subTest(snippet=snippet):
                result = self.v.validate_lua(snippet)
                self.assertFalse(result.ok)

    # ------------------------------------------------------------------
    # test_lua_validate_rejects_empty_code
    # ------------------------------------------------------------------
    def test_lua_validate_rejects_empty_code(self):
        for code in ("", "   ", "\t\n"):
            with self.subTest(code=repr(code)):
                result = self.v.validate_lua(code)
                self.assertFalse(result.ok)


if __name__ == "__main__":
    unittest.main()
