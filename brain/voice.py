"""Voice narration scaffold."""

from models import DashboardEvent


class VoiceNarrator:
    """Narrates dashboard events without affecting the control loop."""

    async def narrate(self, event: DashboardEvent) -> bytes | None:
        # TODO(Person B): integrate Gemini or ElevenLabs behind VOICE_PROVIDER.
        _ = event
        return None
