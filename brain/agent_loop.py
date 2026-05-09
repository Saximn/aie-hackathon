"""AgentLoop orchestration scaffold."""

from models import RecoveryTransition


class AgentLoop:
    """Owns sequencing, retries, replanning, research, and memory updates."""

    async def run_once(self) -> RecoveryTransition:
        """Run one OmniForge cycle.

        TODO(Person B): sequence observe -> memory -> plan -> validate ->
        execute -> verify -> diagnose -> recover -> store -> retry.
        """
        raise NotImplementedError("AgentLoop.run_once is scaffold-only")
