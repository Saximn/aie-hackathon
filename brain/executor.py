"""Primitive Action execution scaffold."""

from models import ExecutionResult, PrimitiveAction


class Executor:
    """Dispatches validated PrimitiveActions to the runtime."""

    async def execute(self, action: PrimitiveAction) -> ExecutionResult:
        """Run a PrimitiveAction without reasoning at execution time."""
        raise NotImplementedError("Executor.execute is scaffold-only")
