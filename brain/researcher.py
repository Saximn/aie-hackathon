"""Researcher — out-of-scope for the hackathon build.

OmniPlay-MC does not call external strategy retrieval. Module preserved so the
AgentLoop / event taxonomy stays consistent. If implemented later, drop in an
Exa or Hyperspell client here and route via `RecoveryTransition.RESEARCH`.
"""

from __future__ import annotations

import logging

from models import ResearchNote

LOG = logging.getLogger("omniplay.researcher")


class Researcher:
    enabled: bool = False

    async def lookup(self, query: str) -> ResearchNote | None:
        LOG.debug("researcher disabled; ignoring query: %s", query)
        return None


__all__ = ["Researcher"]
