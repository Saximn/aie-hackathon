"""TDD: LLMClient.stream_chat() must collect streaming chunks into full text.

RED:  run before adding stream_chat — will fail with AttributeError.
GREEN: pass once stream_chat is implemented in llm_client.py.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "brain"))


def _make_chunk(content: str | None) -> MagicMock:
    """Build a mock streaming chunk mimicking openai ChatCompletionChunk."""
    chunk = MagicMock()
    delta = MagicMock()
    delta.content = content
    choice = MagicMock()
    choice.delta = delta
    chunk.choices = [choice]
    return chunk


def test_stream_chat_method_exists():
    """LLMClient must expose a stream_chat() method."""
    from llm_client import LLMClient

    mock_openai = MagicMock()
    client = LLMClient(client=mock_openai)
    assert callable(getattr(client, "stream_chat", None)), (
        "LLMClient must have a stream_chat() method"
    )


def test_llm_client_stream_chat_returns_complete_text():
    """stream_chat() must collect all chunk deltas and return the full string."""
    from llm_client import LLMClient

    chunks = [
        _make_chunk("Hello "),
        _make_chunk("world"),
        _make_chunk("!"),
        _make_chunk(None),  # final sentinel with no content
    ]

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = iter(chunks)

    client = LLMClient(client=mock_openai)
    result = client.stream_chat([{"role": "user", "content": "say hello world"}])

    assert result == "Hello world!", (
        f"stream_chat should concatenate all chunk deltas, got {result!r}"
    )


def test_stream_chat_skips_none_deltas():
    """stream_chat() must silently skip chunks where delta.content is None."""
    from llm_client import LLMClient

    chunks = [
        _make_chunk(None),
        _make_chunk("first"),
        _make_chunk(None),
        _make_chunk(" second"),
    ]

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = iter(chunks)

    client = LLMClient(client=mock_openai)
    result = client.stream_chat([{"role": "user", "content": "test"}])

    assert result == "first second"


def test_stream_chat_uses_stream_true():
    """stream_chat() must call chat.completions.create with stream=True."""
    from llm_client import LLMClient

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = iter([])

    client = LLMClient(client=mock_openai)
    client.stream_chat([{"role": "user", "content": "hi"}])

    call_kwargs = mock_openai.chat.completions.create.call_args
    assert call_kwargs is not None
    kwargs = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs[1]
    assert kwargs.get("stream") is True, (
        "stream_chat must pass stream=True to the OpenAI client"
    )


def test_stream_chat_logs_timing(caplog):
    """stream_chat() must emit a [timing] log line after completion."""
    import logging
    from llm_client import LLMClient

    mock_openai = MagicMock()
    mock_openai.chat.completions.create.return_value = iter([_make_chunk("ok")])

    client = LLMClient(client=mock_openai)
    with caplog.at_level(logging.INFO, logger="omniplay.llm"):
        client.stream_chat([{"role": "user", "content": "ping"}])

    timing_lines = [r.message for r in caplog.records if "[timing]" in r.message]
    assert timing_lines, "stream_chat must emit a [timing] log line"
