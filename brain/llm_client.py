"""Centralized OpenAI client for OmniPlay-MC.

All GPT-5.5 calls in the brain go through `LLMClient.complete` so we can:
- swap the model id from one place,
- enforce JSON shape via Structured Outputs (Responses API),
- retry once on shape failure with a tightening reminder,
- log token usage for the cost cap.

Use the Responses API exclusively (not legacy chat completions) per CONTEXT.md.
"""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from pydantic import BaseModel

LOG = logging.getLogger("omniplay.llm")

DEFAULT_MODEL = os.getenv("GPT_MODEL", "gpt-5.5")
DEFAULT_REASONING_EFFORT = os.getenv("GPT_REASONING_EFFORT", "medium")
DEFAULT_EMBED_MODEL = os.getenv("GPT_EMBED_MODEL", "text-embedding-3-small")


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_input_tokens: int = 0
    reasoning_tokens: int = 0


@dataclass
class LLMResponse:
    text: str
    parsed: Any | None
    usage: TokenUsage
    model: str
    raw: Any


class LLMShapeError(RuntimeError):
    """Raised when GPT-5.5 returns text we can't parse into the requested schema."""


class _UsageTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.total = TokenUsage()
        self.calls = 0

    def add(self, usage: TokenUsage) -> None:
        with self._lock:
            self.total.input_tokens += usage.input_tokens
            self.total.output_tokens += usage.output_tokens
            self.total.cached_input_tokens += usage.cached_input_tokens
            self.total.reasoning_tokens += usage.reasoning_tokens
            self.calls += 1

    def snapshot(self) -> dict[str, int]:
        with self._lock:
            return {
                "input_tokens": self.total.input_tokens,
                "output_tokens": self.total.output_tokens,
                "cached_input_tokens": self.total.cached_input_tokens,
                "reasoning_tokens": self.total.reasoning_tokens,
                "calls": self.calls,
            }


_TRACKER = _UsageTracker()


def usage_snapshot() -> dict[str, int]:
    """Process-wide cumulative token usage. Used by the cost-cap check."""
    return _TRACKER.snapshot()


def _coerce_usage(usage: Any) -> TokenUsage:
    if usage is None:
        return TokenUsage()
    input_tokens = getattr(usage, "input_tokens", 0) or 0
    output_tokens = getattr(usage, "output_tokens", 0) or 0
    cached_input_tokens = 0
    reasoning_tokens = 0
    details = getattr(usage, "input_tokens_details", None)
    if details is not None:
        cached_input_tokens = getattr(details, "cached_tokens", 0) or 0
    out_details = getattr(usage, "output_tokens_details", None)
    if out_details is not None:
        reasoning_tokens = getattr(out_details, "reasoning_tokens", 0) or 0
    return TokenUsage(
        input_tokens=int(input_tokens),
        output_tokens=int(output_tokens),
        cached_input_tokens=int(cached_input_tokens),
        reasoning_tokens=int(reasoning_tokens),
    )


def _extract_text(response: Any) -> str:
    text = getattr(response, "output_text", None)
    if text:
        return str(text)
    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            t = getattr(content, "text", None)
            if t:
                chunks.append(str(t))
    return "".join(chunks)


def _schema_from_pydantic(model: type[BaseModel]) -> dict[str, Any]:
    schema = model.model_json_schema()
    schema = _strict_schema(schema)
    return {
        "type": "json_schema",
        "name": model.__name__,
        "schema": schema,
        "strict": True,
    }


def _strict_schema(node: Any) -> Any:
    """Adapt a Pydantic JSON schema to the strict subset accepted by Responses
    API Structured Outputs: every object must declare additionalProperties=false
    and list every key under "required".
    """
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for k, v in node.items():
            out[k] = _strict_schema(v)
        if out.get("type") == "object" and "properties" in out:
            out.setdefault("additionalProperties", False)
            out["required"] = list(out["properties"].keys())
        return out
    if isinstance(node, list):
        return [_strict_schema(v) for v in node]
    return node


class LLMClient:
    """Thin wrapper around `openai.OpenAI` for GPT-5.5 Responses API calls."""

    def __init__(
        self,
        *,
        model: str | None = None,
        reasoning_effort: str | None = None,
        embed_model: str | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self.model = model or DEFAULT_MODEL
        self.reasoning_effort = reasoning_effort or DEFAULT_REASONING_EFFORT
        self.embed_model = embed_model or DEFAULT_EMBED_MODEL
        self._client = client or OpenAI()

    def complete(
        self,
        messages: list[dict[str, Any]] | str,
        *,
        schema: type[BaseModel] | None = None,
        reasoning_effort: str | None = None,
        max_output_tokens: int | None = None,
        retry_on_shape_error: bool = True,
    ) -> LLMResponse:
        """Run one Responses API call.

        - `messages`: a list of `{role, content}` dicts or a single string treated as a user message.
        - `schema`: optional Pydantic model. If supplied, we ask for structured output and parse on return.
        - On shape mismatch we retry once with a tightening reminder, then raise `LLMShapeError`.
        """
        kwargs: dict[str, Any] = {
            "model": self.model,
            "input": _normalize_input(messages),
            "reasoning": {"effort": reasoning_effort or self.reasoning_effort},
        }
        if max_output_tokens is not None:
            kwargs["max_output_tokens"] = max_output_tokens
        if schema is not None:
            kwargs["text"] = {"format": _schema_from_pydantic(schema)}

        response = self._client.responses.create(**kwargs)
        text = _extract_text(response)
        usage = _coerce_usage(getattr(response, "usage", None))
        _TRACKER.add(usage)

        parsed: Any = None
        if schema is not None:
            try:
                parsed = schema.model_validate_json(text)
            except Exception as exc:
                LOG.warning("structured output parse failed: %s", exc)
                if not retry_on_shape_error:
                    raise LLMShapeError(f"failed to parse structured output: {exc}") from exc
                parsed = self._retry_for_shape(messages, schema, exc)
                if parsed is None:
                    raise LLMShapeError("retry also failed to produce valid JSON") from exc

        return LLMResponse(text=text, parsed=parsed, usage=usage, model=self.model, raw=response)

    def _retry_for_shape(
        self,
        messages: list[dict[str, Any]] | str,
        schema: type[BaseModel],
        first_error: Exception,
    ) -> BaseModel | None:
        normalized = _normalize_input(messages)
        retry_messages = list(normalized) + [
            {
                "role": "system",
                "content": (
                    "Your previous response did not match the required JSON schema. "
                    f"Validation error: {first_error}. "
                    "Reply with ONLY valid JSON conforming to the schema. No prose, no fences."
                ),
            }
        ]
        try:
            response = self._client.responses.create(
                model=self.model,
                input=retry_messages,
                reasoning={"effort": self.reasoning_effort},
                text={"format": _schema_from_pydantic(schema)},
            )
        except Exception as exc:
            LOG.error("structured retry call raised: %s", exc)
            return None
        usage = _coerce_usage(getattr(response, "usage", None))
        _TRACKER.add(usage)
        text = _extract_text(response)
        try:
            return schema.model_validate_json(text)
        except Exception as exc:
            LOG.error("structured retry parse failed: %s", exc)
            return None

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed strings via `text-embedding-3-small` (or override)."""
        if not texts:
            return []
        response = self._client.embeddings.create(model=self.embed_model, input=texts)
        return [item.embedding for item in response.data]


def _normalize_input(messages: list[dict[str, Any]] | str) -> list[dict[str, Any]]:
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]
    return messages


_DEFAULT_CLIENT: LLMClient | None = None
_DEFAULT_LOCK = threading.Lock()


def default_client() -> LLMClient:
    global _DEFAULT_CLIENT
    if _DEFAULT_CLIENT is None:
        with _DEFAULT_LOCK:
            if _DEFAULT_CLIENT is None:
                _DEFAULT_CLIENT = LLMClient()
    return _DEFAULT_CLIENT


__all__ = [
    "DEFAULT_MODEL",
    "LLMClient",
    "LLMResponse",
    "LLMShapeError",
    "TokenUsage",
    "default_client",
    "usage_snapshot",
]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    class _Echo(BaseModel):
        word: str
        length: int

    out = default_client().complete(
        [
            {"role": "system", "content": "Echo the user's word and report its length as JSON."},
            {"role": "user", "content": "minecraft"},
        ],
        schema=_Echo,
    )
    print("text:", out.text)
    print("parsed:", out.parsed)
    print("usage:", usage_snapshot())
