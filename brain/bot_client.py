"""JSON-RPC client over stdin/stdout for the OmniPlay-MC Mineflayer bridge.

Spawns `bot/` as a subprocess, sends line-delimited JSON requests, awaits
matched line-delimited JSON responses.

Methods mirror the bridge API: `connect`, `run_js`, `get_state`, `chat`, `disconnect`, `ping`.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOG = logging.getLogger("omniplay.bot_client")

DEFAULT_TIMEOUT = float(os.getenv("BRIDGE_REQUEST_TIMEOUT", "120"))


@dataclass
class RunJsResult:
    ok: bool
    result: Any
    error: dict[str, Any] | None
    duration_ms: int
    state_after: dict[str, Any] | None


class BridgeError(RuntimeError):
    pass


class BotClient:
    """Async stdin/stdout bridge to `bot/` (Mineflayer JSON-RPC)."""

    def __init__(
        self,
        *,
        bot_dir: Path | str | None = None,
        node_args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.bot_dir = Path(bot_dir) if bot_dir else Path(__file__).resolve().parents[1] / "bot"
        self.node_args = node_args
        self.env = env
        self._proc: asyncio.subprocess.Process | None = None
        self._pending: dict[str, asyncio.Future[dict[str, Any]]] = {}
        self._reader_task: asyncio.Task[None] | None = None
        self._stderr_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()
        self._last_connect_params: dict[str, Any] | None = None

    async def start(self) -> None:
        if self._proc is not None:
            return
        cmd = self._build_command()
        merged_env = {**os.environ, **(self.env or {})}
        LOG.info("starting bridge: %s in %s", " ".join(cmd), self.bot_dir)
        self._proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.bot_dir),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=merged_env,
        )
        self._reader_task = asyncio.create_task(self._read_loop())
        self._stderr_task = asyncio.create_task(self._read_stderr())
        ack = await self.call("ping", timeout=15.0)
        if not ack.get("pong"):
            raise BridgeError(f"bridge did not pong on start: {ack}")

    def _build_command(self) -> list[str]:
        if self.node_args:
            return self.node_args
        npx = shutil.which("npx") or shutil.which("npx.cmd")
        if npx is None:
            raise BridgeError("npx not found on PATH; install Node.js >=18")
        return [npx, "--yes", "tsx", "src/main.ts"]

    async def stop(self) -> None:
        if self._proc is None:
            return
        try:
            await self.call("disconnect", timeout=5.0)
        except Exception as exc:
            LOG.warning("disconnect call failed: %s", exc)
        try:
            assert self._proc.stdin is not None
            self._proc.stdin.close()
        except Exception:
            pass
        try:
            await asyncio.wait_for(self._proc.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            LOG.warning("bridge did not exit; terminating")
            self._proc.terminate()
            try:
                await asyncio.wait_for(self._proc.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                self._proc.kill()
        self._proc = None
        if self._reader_task is not None:
            self._reader_task.cancel()
        if self._stderr_task is not None:
            self._stderr_task.cancel()

    async def call(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> dict[str, Any]:
        if self._proc is None or self._proc.stdin is None:
            raise BridgeError("bridge not started; call start() first")
        request_id = uuid.uuid4().hex
        payload = {"id": request_id, "method": method, "params": params or {}}
        future: asyncio.Future[dict[str, Any]] = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        line = (json.dumps(payload) + "\n").encode("utf-8")
        async with self._lock:
            self._proc.stdin.write(line)
            await self._proc.stdin.drain()
        try:
            response = await asyncio.wait_for(future, timeout=timeout)
        except asyncio.TimeoutError as exc:
            self._pending.pop(request_id, None)
            raise BridgeError(f"bridge call {method} timed out after {timeout}s") from exc
        if not response.get("ok", False):
            err = response.get("error") or {}
            raise BridgeError(f"bridge call {method} failed: {err.get('message')}")
        return response.get("result") or {}

    async def _read_loop(self) -> None:
        assert self._proc is not None and self._proc.stdout is not None
        stdout = self._proc.stdout
        while not stdout.at_eof():
            try:
                raw = await stdout.readline()
            except Exception as exc:
                LOG.error("bridge stdout read failed: %s", exc)
                break
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                LOG.warning("bridge produced non-JSON line: %s", line[:200])
                continue
            request_id = payload.get("id")
            future = self._pending.pop(request_id, None) if isinstance(request_id, str) else None
            if future is None:
                LOG.warning("bridge response for unknown id: %s", request_id)
                continue
            future.set_result(payload)
        for future in self._pending.values():
            if not future.done():
                future.set_exception(BridgeError("bridge stdout closed"))
        self._pending.clear()

    async def _read_stderr(self) -> None:
        assert self._proc is not None and self._proc.stderr is not None
        stderr = self._proc.stderr
        while not stderr.at_eof():
            raw = await stderr.readline()
            if not raw:
                break
            text = raw.decode("utf-8", errors="replace").rstrip()
            if text:
                print(f"[bridge:err] {text}", file=sys.stderr)

    async def connect(
        self,
        *,
        host: str = "localhost",
        port: int = 25565,
        username: str = "Voyager",
        version: str | None = "1.20.4",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"host": host, "port": port, "username": username}
        if version:
            params["version"] = version
        self._last_connect_params = params
        return await self.call("connect", params, timeout=60.0)

    async def run_js(self, code: str, *, timeout_ms: int = 60_000) -> RunJsResult:
        call_timeout = (timeout_ms / 1000.0) + 30.0
        try:
            result = await self.call("runJs", {"code": code, "timeoutMs": timeout_ms}, timeout=call_timeout)
        except BridgeError as exc:
            if "not connected" in str(exc) and self._last_connect_params:
                LOG.warning("mineflayer disconnected; attempting reconnect before retry")
                await self.call("connect", self._last_connect_params, timeout=60.0)
                result = await self.call("runJs", {"code": code, "timeoutMs": timeout_ms}, timeout=call_timeout)
            else:
                raise
        return RunJsResult(
            ok=bool(result.get("ok", False)),
            result=result.get("result"),
            error=result.get("error"),
            duration_ms=int(result.get("durationMs") or 0),
            state_after=result.get("stateAfter"),
        )

    async def get_state(self) -> dict[str, Any]:
        return await self.call("getState", timeout=10.0)

    async def chat(self, message: str) -> None:
        await self.call("chat", {"message": message}, timeout=5.0)

    async def ping(self) -> dict[str, Any]:
        return await self.call("ping", timeout=5.0)


__all__ = ["BotClient", "BridgeError", "RunJsResult"]
