"""Optional voice coaching scaffold."""


class VoiceCoach:
    """Accepts optional voice coaching and emits optional spoken responses."""

    async def transcribe(self, audio: bytes) -> str:
        """TODO(Person B): optional speech-to-text coaching input."""
        raise NotImplementedError("VoiceCoach.transcribe is scaffold-only")

    async def speak(self, text: str) -> bytes:
        """TODO(Person B): optional text-to-speech response."""
        raise NotImplementedError("VoiceCoach.speak is scaffold-only")
