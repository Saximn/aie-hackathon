"""External game knowledge retrieval."""

from __future__ import annotations

from typing import Protocol

from models import ResearchNote


class ResearchProvider(Protocol):
    """Adapter seam for retrieval providers hidden behind Researcher."""

    async def search(self, query: str) -> ResearchNote:
        """Return a structured Research Note for the query."""


class Researcher:
    """Retrieves game profile and strategy knowledge when the AgentLoop asks."""

    def __init__(self, provider: ResearchProvider | None = None) -> None:
        self._provider = provider or NoopResearchProvider()

    async def research(self, query: str) -> ResearchNote:
        """Return structured strategy notes for a query."""
        clean_query = " ".join(query.split())
        if not clean_query:
            return ResearchNote(
                query=query,
                summary="No research query was provided.",
                confidence=0.0,
            )

        try:
            note = await self._provider.search(clean_query)
        except Exception as exc:
            return ResearchNote(
                query=clean_query,
                summary=f"Research unavailable: {type(exc).__name__}",
                source_urls=[],
                confidence=0.0,
            )

        return ResearchNote(
            query=clean_query,
            summary=note.summary.strip(),
            source_urls=_dedupe_urls(note.source_urls),
            confidence=max(0.0, min(1.0, note.confidence)),
        )


class NoopResearchProvider:
    """Default adapter that keeps external retrieval optional."""

    async def search(self, query: str) -> ResearchNote:
        return ResearchNote(
            query=query,
            summary="No research provider is configured.",
            source_urls=[],
            confidence=0.0,
        )


def _dedupe_urls(urls: list[str]) -> list[str]:
    deduped: list[str] = []
    for url in urls:
        clean_url = url.strip()
        if clean_url and clean_url not in deduped:
            deduped.append(clean_url)
    return deduped
