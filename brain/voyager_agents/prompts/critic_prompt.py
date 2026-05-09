"""Critic-agent prompts for OmniPlay-MC."""

from __future__ import annotations

from typing import Any

CRITIC_SYSTEM = """You are the Critic Agent for Voyager.

Given:
- the task the action agent attempted,
- the JS body it ran,
- whether the runtime threw or returned,
- the inventory + nearby state BEFORE and AFTER execution,

decide whether the task SUCCEEDED, was INCOMPLETE, or FAILED.

Rules:
- "Mine N X" succeeds only if the after-inventory has at least N more X than before.
- "Craft X" succeeds only if the after-inventory contains X.
- "Place X" succeeds only if X appears in nearby_blocks_after that wasn't there before.
- "Move to / Reach Y" succeeds if the after-position is within 3 blocks of Y.
- A runtime error that nonetheless produced the desired inventory delta still SUCCEEDS.
- A clean return that did NOT achieve the inventory/state change is INCOMPLETE.
- Refusal to even try, or hard runtime failure with no progress, is FAILED.

Be terse. Your `feedback` will be inlined into the next action prompt as a hint for the retry.
"""


def critic_messages(
    *,
    task: str,
    code: str,
    runtime_ok: bool,
    runtime_error: str | None,
    runtime_result: str | None,
    inventory_before: dict[str, int],
    inventory_after: dict[str, int],
    nearby_blocks_before: list[str],
    nearby_blocks_after: list[str],
    position_before: dict[str, float] | None,
    position_after: dict[str, float] | None,
) -> list[dict[str, Any]]:
    body = (
        f"Task: {task}\n\n"
        f"runtime_ok: {runtime_ok}\n"
        f"runtime_error: {runtime_error}\n"
        f"runtime_result: {runtime_result}\n\n"
        f"inventory_before: {inventory_before}\n"
        f"inventory_after:  {inventory_after}\n\n"
        f"nearby_blocks_before: {nearby_blocks_before[:20]}\n"
        f"nearby_blocks_after:  {nearby_blocks_after[:20]}\n\n"
        f"position_before: {position_before}\n"
        f"position_after:  {position_after}\n\n"
        f"Code:\n```js\n{code[:4000]}\n```\n\n"
        "Return JSON: { verdict: 'success'|'incomplete'|'failed', confidence: 0..1, "
        "feedback: 1-3 sentences telling the action agent what to try next or why it succeeded }"
    )
    return [
        {"role": "system", "content": CRITIC_SYSTEM},
        {"role": "user", "content": body},
    ]
