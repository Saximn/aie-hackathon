"""External game knowledge retrieval scaffold."""

from models import ResearchNote


class Researcher:
    """Retrieves game profile and strategy knowledge when the AgentLoop asks."""

    async def research(self, query: str) -> ResearchNote:
        """Return structured strategy notes for a query.

        TODO(Person B): integrate Exa for new game profiles, missing strategy,
        repeated failures, unknown mechanics, or explicit user coaching such as
        "learn this game".
        """
        return ResearchNote(
            query=query,
            summary="Research integration not implemented. Static profile and local skill memory are active.",
            source_urls=[],
            confidence=0.0,
        )
