"""Imagined future image generation scaffold."""

from models import Plan


class Imaginer:
    """Generates optional plan-linked images for the dashboard."""

    async def imagine(self, plan: Plan) -> str | None:
        # TODO(Person B): call GPT Image 2 behind ENABLE_IMAGE_GEN.
        _ = plan
        return None
