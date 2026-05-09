"""External knowledge retrieval scaffold."""


class Researcher:
    """Retrieves survival knowledge when the AgentLoop allows research."""

    async def research(self, query: str) -> list[dict]:
        # TODO(Person B): integrate Exa behind ENABLE_RESEARCH.
        return [{"query": query, "status": "TODO"}]
