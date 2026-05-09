"""Code-as-policy executor for OmniPlay-MC.

Runs a `JsCodeAction` through the Mineflayer bridge. The brain's planner emits
JS bodies; this module wraps them in an `ExecutionResult` so the AgentLoop can
hand the outcome to the critic.
"""

from __future__ import annotations

import logging

from bot_client import BotClient, RunJsResult
from models import ExecutionResult, JsCodeAction

LOG = logging.getLogger("omniplay.executor")


class Executor:
    """Runs `JsCodeAction`s via the Mineflayer JSON-RPC bridge."""

    def __init__(self, *, client: BotClient) -> None:
        self.client = client

    async def execute(self, action: JsCodeAction) -> tuple[ExecutionResult, RunJsResult]:
        LOG.info("executing %s (%d chars, timeout %dms)", action.name, len(action.code), action.timeout_ms)
        run = await self.client.run_js(action.code, timeout_ms=action.timeout_ms)
        evidence = {
            "durationMs": run.duration_ms,
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
        return result, run


__all__ = ["Executor"]
