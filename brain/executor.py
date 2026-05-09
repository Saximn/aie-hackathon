"""Code-as-policy executor for OmniPlay-MC.

Runs a `JsCodeAction` through the Mineflayer bridge. The brain's planner emits
JS bodies; this module wraps them in an `ExecutionResult` so the AgentLoop can
hand the outcome to the critic.

Depth added here (not just a pass-through):
- Wall-clock timing around the full execute() call and the run_js() call.
- Structured [timing] log lines so ops can see bottlenecks without reading traces.
- wallMs injected into evidence so the critic and dashboard see real elapsed time.
"""

from __future__ import annotations

import logging
import time

from bot_client import BotClient, RunJsResult
from models import ExecutionResult, JsCodeAction

LOG = logging.getLogger("omniplay.executor")


class Executor:
    """Runs `JsCodeAction`s via the Mineflayer JSON-RPC bridge.

    This is the single place that owns execution timing — callers (AgentLoop)
    just call execute() and receive a rich ExecutionResult with timing baked in.
    """

    def __init__(self, *, client: BotClient) -> None:
        self.client = client

    async def execute(self, action: JsCodeAction) -> tuple[ExecutionResult, RunJsResult]:
        LOG.info(
            "executing %s (%d chars, timeout %dms)",
            action.name, len(action.code), action.timeout_ms,
        )

        execute_start = time.perf_counter()

        run_js_start = time.perf_counter()
        run = await self.client.run_js(action.code, timeout_ms=action.timeout_ms)
        run_js_wall_ms = int((time.perf_counter() - run_js_start) * 1000)

        execute_wall_ms = int((time.perf_counter() - execute_start) * 1000)

        LOG.info(
            "[timing] run_js took %.1fs (bridge-reported %dms) skill=%s",
            run_js_wall_ms / 1000,
            run.duration_ms,
            action.name,
        )

        verdict = "success" if run.ok else "failure"
        evidence = {
            "durationMs": run.duration_ms,
            "wallMs": run_js_wall_ms,
            "executeWallMs": execute_wall_ms,
            "stateAfter": run.state_after,
            "result": run.result,
            "error": run.error,
        }

        if run.ok:
            description = str(run.result) if run.result is not None else "ok"
            result = ExecutionResult(action_id=action.id, success=True, result=description, evidence=evidence)
        else:
            err = run.error or {}
            result = ExecutionResult(
                action_id=action.id,
                success=False,
                result=str(err.get("message", "unknown error")),
                evidence=evidence,
            )

        LOG.info(
            "[cycle] skill=%r exec=%.1fs verdict=%s",
            action.name,
            execute_wall_ms / 1000,
            verdict,
        )
        return result, run


__all__ = ["Executor"]
