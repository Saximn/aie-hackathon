"""Viewer dependency smoke test.

Behaviour: the bot's viewer dependencies (canvas + prismarine-viewer) must
load without throwing when required from the bot/ directory. This guards
against accidental removal of 'canvas' from bot/package.json.
"""
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOT_DIR = REPO / "bot"


def _node(*code_lines: str) -> tuple[int, str]:
    script = "; ".join(code_lines)
    result = subprocess.run(
        ["node", "--input-type=commonjs"],
        input=script,
        capture_output=True,
        text=True,
        cwd=str(BOT_DIR),
        timeout=15,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def test_canvas_module_loads():
    """canvas native module must be resolvable from bot/node_modules."""
    code, out = _node("require('canvas'); console.log('ok')")
    assert code == 0, f"canvas failed to load: {out}"
    assert "ok" in out


def test_prismarine_viewer_loads_with_canvas():
    """prismarine-viewer must load without 'Cannot find module canvas' error."""
    code, out = _node("require('prismarine-viewer'); console.log('ok')")
    assert code == 0, f"prismarine-viewer failed to load: {out}"
    assert "Cannot find module" not in out
    assert "ok" in out
