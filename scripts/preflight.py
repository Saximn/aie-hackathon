"""OmniPlay-MC preflight checker — stdlib only, no extra deps.

Usage:
    python scripts/preflight.py

Exit codes:
    0  All checks passed (OK or WARN)
    1  At least one FAIL
"""
from __future__ import annotations

import os
import pathlib
import shutil
import socket
import subprocess
import sys
from typing import Callable, NamedTuple

# ---------------------------------------------------------------------------
# Terminal colours (disabled on Windows without ANSICON/WT unless supported)
# ---------------------------------------------------------------------------
_ANSI = sys.platform != "win32" or os.environ.get("WT_SESSION") or os.environ.get("ANSICON")


def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _ANSI else text


OK   = _c("32", "[OK  ]")
WARN = _c("33", "[WARN]")
FAIL = _c("31", "[FAIL]")

# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class Result(NamedTuple):
    level: str          # "ok" | "warn" | "fail"
    label: str
    detail: str
    fix: str = ""

    def badge(self) -> str:
        return {  "ok": OK, "warn": WARN, "fail": FAIL }[self.level]

    def __str__(self) -> str:
        lines = [f"  {self.badge()} {self.label}"]
        if self.detail:
            lines.append(f"       {self.detail}")
        if self.fix and self.level != "ok":
            lines.append(f"       Fix: {self.fix}")
        return "\n".join(lines)


results: list[Result] = []


def check(fn: Callable[[], Result]) -> Result:
    r = fn()
    results.append(r)
    print(r)
    return r


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO = pathlib.Path(__file__).resolve().parent.parent


def _env(key: str) -> str:
    """Read key from brain/.env, then repo .env, then os.environ."""
    for env_file in [REPO / "brain" / ".env", REPO / ".env"]:
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.strip() == key:
                    return v.strip().strip('"').strip("'")
    return os.environ.get(key, "")


def _run(*args: str, cwd: pathlib.Path | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(
            list(args),
            capture_output=True, text=True,
            cwd=str(cwd) if cwd else None,
            timeout=15,
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)


def _ensure_dir(path: pathlib.Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        test = path / ".preflight_write_test"
        test.write_text("ok")
        test.unlink()
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_python_venv() -> Result:
    venv = REPO / ".venv"
    prefix = pathlib.Path(sys.prefix).resolve()
    inside = str(prefix).startswith(str(venv.resolve()))
    version = sys.version_info
    ver_str = f"{version.major}.{version.minor}.{version.micro}"

    if not inside:
        return Result("warn", "Python venv",
                      f"Running {prefix}, expected {venv}",
                      r"Activate: . .venv\Scripts\Activate.ps1")
    if (version.major, version.minor) < (3, 12):
        return Result("fail", "Python version",
                      f"{ver_str} — need >= 3.12 (StrEnum in brain/models.py)",
                      "Install Python 3.12+")
    return Result("ok", "Python venv + version", f"{prefix} — Python {ver_str}")


def check_python_deps() -> Result:
    missing = []
    for pkg in ["openai", "chromadb", "fastapi", "dotenv", "elevenlabs", "convex"]:
        mod = "python_dotenv" if pkg == "dotenv" else pkg
        # dotenv is imported as dotenv in the check list but installed as python-dotenv
        import_name = "dotenv" if pkg == "dotenv" else pkg
        try:
            __import__(import_name)
        except ImportError:
            missing.append(pkg)
    if missing:
        return Result("fail", "Python deps",
                      f"Missing: {', '.join(missing)}",
                      "pip install -r brain/requirements.txt")
    return Result("ok", "Python deps", "openai chromadb fastapi dotenv elevenlabs convex")


def check_node() -> Result:
    code, out = _run("node", "--version")
    if code != 0:
        return Result("fail", "Node.js", "not found", "Install Node.js >= 18")
    ver = out.lstrip("v").split(".")
    try:
        major = int(ver[0])
    except ValueError:
        major = 0
    if major < 18:
        return Result("fail", "Node.js version", f"{out} — need >= 18",
                      "Install Node.js 18 LTS")
    mineflayer = REPO / "bot" / "node_modules" / "mineflayer" / "package.json"
    if not mineflayer.exists():
        return Result("warn", "bot/node_modules",
                      "mineflayer not installed",
                      "cd bot && npm install")
    return Result("ok", "Node.js + mineflayer", out)


def check_dashboard_deps() -> Result:
    next_pkg = REPO / "dashboard" / "node_modules" / "next" / "package.json"
    if not next_pkg.exists():
        return Result("warn", "dashboard/node_modules",
                      "next not installed",
                      "cd dashboard && npm install")
    return Result("ok", "dashboard/node_modules", "next found")


def check_env_keys() -> Result:
    """Check required and optional .env keys."""
    openai_key = _env("OPENAI_API_KEY")
    if not openai_key:
        return Result("fail", ".env OPENAI_API_KEY",
                      "not set — agent cannot call GPT",
                      r"Add to brain\.env: OPENAI_API_KEY=sk-...")

    warns = []
    for key, default in [
        ("MINECRAFT_HOST", "localhost"),
        ("MINECRAFT_PORT", "25565"),
        ("MINECRAFT_USERNAME", "Voyager"),
        ("MINECRAFT_VERSION", "1.20.4"),
    ]:
        val = _env(key)
        if not val:
            warns.append(f"{key} (default: {default})")

    optionals = []
    for key in ["CONVEX_URL", "ELEVENLABS_API_KEY"]:
        if not _env(key):
            optionals.append(key)

    detail_parts = [f"OPENAI_API_KEY=***{openai_key[-4:]}"]
    if warns:
        detail_parts.append(f"WARN missing (will use defaults): {', '.join(warns)}")
    if optionals:
        detail_parts.append(f"WARN optional missing: {', '.join(optionals)}")

    level = "warn" if (warns or optionals) else "ok"
    return Result(level, ".env keys", " | ".join(detail_parts))


def check_minecraft_server() -> Result:
    host = _env("MINECRAFT_HOST") or "localhost"
    try:
        port = int(_env("MINECRAFT_PORT") or "25565")
    except ValueError:
        port = 25565
    try:
        with socket.create_connection((host, port), timeout=2):
            pass
        return Result("ok", "Minecraft server", f"TCP {host}:{port} reachable")
    except OSError as exc:
        return Result("fail", "Minecraft server",
                      f"TCP {host}:{port} — {exc}",
                      r"Run scripts\start_server.bat in a separate window")


def check_convex_cli() -> Result:
    convex_url = _env("CONVEX_URL")
    if not convex_url:
        return Result("warn", "Convex CLI",
                      "CONVEX_URL not set — skipping (graceful fallback active)",
                      "Set CONVEX_URL in brain/.env to enable real-time memory")
    code, out = _run("npx", "convex", "--version")
    if code != 0:
        return Result("warn", "Convex CLI",
                      f"npx convex --version failed: {out[:120]}",
                      "npm install at repo root, then npx convex dev")
    return Result("ok", "Convex CLI", out.splitlines()[0] if out else "ok")


def check_writable_paths() -> Result:
    narration_dir = _env("OMNIPLAY_NARRATION_DIR") or str(REPO / "outputs" / "narration")
    chroma_dir    = _env("CHROMA_DIR") or str(REPO / "brain" / ".chroma")
    memory_dir    = _env("OMNIPLAY_LOCAL_MEMORY") or str(REPO / ".omniplay-memory")

    failed = []
    for p in [pathlib.Path(narration_dir), pathlib.Path(chroma_dir), pathlib.Path(memory_dir)]:
        if not _ensure_dir(p):
            failed.append(str(p))

    if failed:
        return Result("fail", "Writable paths",
                      f"Cannot write: {', '.join(failed)}",
                      "Check disk permissions / available space")
    return Result("ok", "Writable paths",
                  "outputs/narration  brain/.chroma  .omniplay-memory")


def check_npx_tsx() -> Result:
    """Mirrors the command brain/bot_client.py uses to launch the bot bridge."""
    bot_dir = REPO / "bot"
    code, out = _run("npx", "--yes", "tsx", "--version", cwd=bot_dir)
    if code != 0:
        return Result("warn", "npx tsx",
                      f"tsx not runnable from bot/: {out[:120]}",
                      "cd bot && npm install  (tsx is in devDependencies)")
    return Result("ok", "npx tsx", out.splitlines()[0] if out else "ok")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

CHECKS: list[Callable[[], Result]] = [
    check_python_venv,
    check_python_deps,
    check_node,
    check_dashboard_deps,
    check_env_keys,
    check_minecraft_server,
    check_convex_cli,
    check_writable_paths,
    check_npx_tsx,
]


def main() -> int:
    print()
    print(_c("1", "=== OmniPlay-MC Preflight ==="))
    print(f"  Repo: {REPO}")
    print()

    for fn in CHECKS:
        check(fn)

    fails  = [r for r in results if r.level == "fail"]
    warns  = [r for r in results if r.level == "warn"]
    oks    = [r for r in results if r.level == "ok"]

    print()
    summary_parts = [
        _c("32", f"{len(oks)} OK"),
        _c("33", f"{len(warns)} WARN"),
        _c("31", f"{len(fails)} FAIL"),
    ]
    print("  " + "  ".join(summary_parts))

    if fails:
        print()
        print(_c("31", "  Fix the FAIL items above before starting the demo."))
        return 1

    if warns:
        print()
        print(_c("33", "  WARNs are non-blocking — demo can proceed, some features may be limited."))

    print()
    print(_c("32", "  All clear — run scripts\\start_all.ps1 to launch."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
