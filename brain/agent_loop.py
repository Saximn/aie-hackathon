"""AgentLoop orchestration scaffold."""

from models import RecoveryTransition


class AgentLoop:
    """Owns sequencing, retries, replanning, research, and memory updates."""

    async def run_once(self) -> RecoveryTransition:
        """Run one scaffold cycle.

        TODO(Person B): observe, plan, validate, execute, verify, diagnose,
        recover, update memory, and emit events.
        """
        return RecoveryTransition.ABORT
